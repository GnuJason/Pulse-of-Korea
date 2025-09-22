import os
import asyncio
import json
import smtplib
import ssl
from contextlib import asynccontextmanager
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi import FastAPI, Request, HTTPException, Depends, WebSocket, WebSocketDisconnect, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from population_manager import population_manager
import aiosmtplib
from email_validator import validate_email, EmailNotValidError

# Load environment variables
load_dotenv()

# Security configuration
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
DEBUG = ENVIRONMENT == "development"
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

# Email configuration
SMTP_SERVER = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
ADMIN_EMAIL = "admin@pulseofhumanity.org"

# Rate limiting
limiter = Limiter(key_func=get_remote_address)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    asyncio.create_task(population_manager.start_broadcasting())
    yield
    # Shutdown (if needed)

app = FastAPI(
    title="Pulse of Korea",
    description="Real-time demographic data for the Korean Peninsula",
    version="1.0.0",
    debug=DEBUG,
    lifespan=lifespan
)

# Security middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://cdn.jsdelivr.net https://cdn.tailwindcss.com; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdn.tailwindcss.com https://fonts.googleapis.com; "
            "img-src 'self' data:; "
            "connect-src 'self'; "
            "font-src 'self' https: https://fonts.gstatic.com; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
        
        return response

# Add security middleware
if not DEBUG:
    app.add_middleware(HTTPSRedirectMiddleware)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=ALLOWED_HOSTS)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(SlowAPIMiddleware)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Mount static files (only if directory exists)
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Add custom Jinja2 filter for comma-separated numbers
def comma_filter(value):
    try:
        return f"{int(value):,}"
    except (ValueError, TypeError):
        return value
templates.env.filters["comma"] = comma_filter

# WebSocket endpoint for real-time population updates
@app.websocket("/ws/population")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    population_manager.add_client(websocket)
    
    try:
        # Send initial state
        current_state = population_manager.calculate_current_population()
        initial_message = {
            "type": "initial_state",
            "data": {
                "south_korea_population": current_state.south_korea_population,
                "north_korea_population": current_state.north_korea_population,
                "total_population": current_state.total_population,
                "sk_births_today": current_state.sk_births_today,
                "sk_deaths_today": current_state.sk_deaths_today,
                "nk_births_today": current_state.nk_births_today,
                "nk_deaths_today": current_state.nk_deaths_today,
                "korea_time": population_manager.get_korea_timezone_now().strftime("%H:%M:%S"),
                "event_indicators": {
                    "south_korea_birth": False,
                    "south_korea_death": False,
                    "north_korea_birth": False,
                    "north_korea_death": False,
                    "any_birth": False,
                    "any_death": False
                },
                "recent_visual_events": [],
                "recent_events": []
            }
        }
        await websocket.send_text(json.dumps(initial_message))
        
        # Keep connection alive
        while True:
            # Wait for client messages (heartbeat, etc.)
            try:
                data = await websocket.receive_text()
                # Handle client messages if needed
            except WebSocketDisconnect:
                break
                
    except WebSocketDisconnect:
        pass
    finally:
        population_manager.remove_client(websocket)

# Get current real-time population data
@app.get("/api/realtime/current")
async def get_realtime_current():
    """Get current real-time population state with event-based changes"""
    current_state = population_manager.calculate_current_population()
    return {
        "timestamp": current_state.timestamp,
        "south_korea_population": current_state.south_korea_population,
        "north_korea_population": current_state.north_korea_population,
        "total_population": current_state.total_population,
        "births_deaths_today": {
            "south_korea": {
                "births": current_state.sk_births_today,
                "deaths": current_state.sk_deaths_today
            },
            "north_korea": {
                "births": current_state.nk_births_today,
                "deaths": current_state.nk_deaths_today
            }
        },
        "korea_time": population_manager.get_korea_timezone_now().isoformat()
    }

# Get precise real-time population data with decimal precision
@app.get("/api/realtime/precise")
async def get_realtime_precise():
    """Get event-based real-time population state with recent events"""
    current_state = population_manager.calculate_current_population()
    return {
        "timestamp": current_state.timestamp,
        "south_korea_population": current_state.south_korea_population,
        "north_korea_population": current_state.north_korea_population,
        "total_population": current_state.total_population,
        "births_deaths_today": {
            "south_korea": {
                "births": current_state.sk_births_today,
                "deaths": current_state.sk_deaths_today
            },
            "north_korea": {
                "births": current_state.nk_births_today,
                "deaths": current_state.nk_deaths_today
            }
        },
        "recent_events": [
            {
                "country": event.country,
                "type": event.event_type,
                "timestamp": event.timestamp,
                "time_ago_seconds": current_state.timestamp - event.timestamp
            }
            for event in current_state.recent_events[-20:]  # Last 20 events
        ],
        "realtime_rates_per_second": {
            "south_korea": {
                "births_per_sec": round(population_manager.sk_births_per_sec, 8),
                "deaths_per_sec": round(population_manager.sk_deaths_per_sec, 8),
                "net_change_per_sec": round(population_manager.sk_births_per_sec - population_manager.sk_deaths_per_sec, 8)
            },
            "north_korea": {
                "births_per_sec": round(population_manager.nk_births_per_sec, 8),
                "deaths_per_sec": round(population_manager.nk_deaths_per_sec, 8),
                "net_change_per_sec": round(population_manager.nk_births_per_sec - population_manager.nk_deaths_per_sec, 8)
            },
            "combined": {
                "total_births_per_sec": round(population_manager.sk_births_per_sec + population_manager.nk_births_per_sec, 8),
                "total_deaths_per_sec": round(population_manager.sk_deaths_per_sec + population_manager.nk_deaths_per_sec, 8),
                "total_net_change_per_sec": round((population_manager.sk_births_per_sec + population_manager.nk_births_per_sec) - (population_manager.sk_deaths_per_sec + population_manager.nk_deaths_per_sec), 8)
            }
        },
        "expected_integer_changes": {
            "births_every_n_seconds": {
                "south_korea": round(1.0 / population_manager.sk_births_per_sec, 1),
                "north_korea": round(1.0 / population_manager.nk_births_per_sec, 1)
            },
            "deaths_every_n_seconds": {
                "south_korea": round(1.0 / population_manager.sk_deaths_per_sec, 1),
                "north_korea": round(1.0 / population_manager.nk_deaths_per_sec, 1)
            }
        },
        "korea_time": population_manager.get_korea_timezone_now().isoformat()
    }

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    # Get static data for initial page load
    static_data = population_manager.get_static_data()
    current_state = population_manager.calculate_current_population()
    
    # Format data for template compatibility
    template_data = {
        "south_korea": {
            "name": static_data["south_korea"]["name"],
            "population": current_state.south_korea_population,
            "births_2024": static_data["south_korea"]["annual_births"],
            "deaths_2024": static_data["south_korea"]["annual_deaths"],
            "fertility_rate": static_data["south_korea"]["fertility_rate"],
            "life_expectancy": static_data["south_korea"]["life_expectancy"],
            "birth_rate": static_data["south_korea"]["birth_rate"],
            "death_rate": static_data["south_korea"]["death_rate"],
            "population_growth_rate": static_data["south_korea"]["annual_growth_rate"]
        },
        "north_korea": {
            "name": static_data["north_korea"]["name"],
            "population": current_state.north_korea_population,
            "births_2024": static_data["north_korea"]["annual_births"],
            "deaths_2024": static_data["north_korea"]["annual_deaths"],
            "fertility_rate": static_data["north_korea"]["fertility_rate"],
            "life_expectancy": static_data["north_korea"]["life_expectancy"],
            "birth_rate": static_data["north_korea"]["birth_rate"],
            "death_rate": static_data["north_korea"]["death_rate"],
            "population_growth_rate": static_data["north_korea"]["annual_growth_rate"]
        }
    }
    
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "title": "Pulse of Korea",
            "data": template_data,
        },
    )

@app.get("/api/data")
async def get_all_data():
    """Get all demographic data with current real-time populations"""
    static_data = population_manager.get_static_data()
    current_state = population_manager.calculate_current_population()
    
    return {
        "countries": {
            "south_korea": {
                **static_data["south_korea"],
                "current_population": current_state.south_korea_population,
                "births_today": current_state.sk_births_today,
                "deaths_today": current_state.sk_deaths_today
            },
            "north_korea": {
                **static_data["north_korea"],
                "current_population": current_state.north_korea_population,
                "births_today": current_state.nk_births_today,
                "deaths_today": current_state.nk_deaths_today
            }
        },
        "total_current_population": current_state.total_population,
        "last_updated": static_data["last_updated"],
        "realtime_enabled": True
    }

@app.get("/api/data/north-korea-only")
async def get_north_korea_only():
    """Get North Korea data only (CIA World Factbook 2024)"""
    static_data = population_manager.get_static_data()
    current_state = population_manager.calculate_current_population()
    
    return {
        "country": {
            **static_data["north_korea"],
            "current_population": current_state.north_korea_population,
            "births_today": current_state.nk_births_today,
            "deaths_today": current_state.nk_deaths_today
        },
        "data_source": "CIA World Factbook 2024",
        "note": "This data may have limitations due to restricted access to North Korea",
        "last_updated": static_data["last_updated"]
    }

@app.get("/api/data/south-korea-only") 
async def get_south_korea_only():
    """Get South Korea data only (KOSIS)"""
    static_data = population_manager.get_static_data()
    current_state = population_manager.calculate_current_population()
    
    return {
        "country": {
            **static_data["south_korea"],
            "current_population": current_state.south_korea_population,
            "births_today": current_state.sk_births_today,
            "deaths_today": current_state.sk_deaths_today
        },
        "data_source": "KOSIS (Korean Statistical Information Service)",
        "note": "Official government statistics from South Korea",
        "last_updated": static_data["last_updated"]
    }

@app.get("/api/validation")
async def validate_demographic_data():
    """Validate demographic data calculations"""
    static_data = population_manager.get_static_data()
    validation_results = {}
    
    for country_key, data in static_data.items():
        if country_key in ["last_updated"]:
            continue
            
        birth_rate = data["birth_rate"] 
        death_rate = data["death_rate"]
        calculated_growth_percent = (birth_rate - death_rate) / 10
        actual_growth_rate = data.get("annual_growth_rate", 0)
        
        validation_results[country_key] = {
            "country": data["name"],
            "birth_rate_per_1000": birth_rate,
            "death_rate_per_1000": death_rate,
            "calculated_growth_rate_percent": round(calculated_growth_percent, 2),
            "actual_growth_rate_percent": actual_growth_rate,
            "difference": round(abs(calculated_growth_percent - actual_growth_rate), 2),
            "validates": abs(calculated_growth_percent - actual_growth_rate) < 1.0
        }
    
    return {"validation": validation_results}

@app.post("/api/admin/update-base-data")
@limiter.limit("10/hour")
async def update_base_data(request: Request, country: str, population: int, year: int, 
                          births: Optional[int] = None, deaths: Optional[int] = None, 
                          growth_rate: Optional[float] = None, admin_key: Optional[str] = None):
    """Admin endpoint to update base population data when new official statistics are released"""
    
    # Simple admin authentication (in production, use proper authentication)
    expected_admin_key = os.getenv("ADMIN_UPDATE_KEY", "admin-secret-key")
    if admin_key != expected_admin_key:
        raise HTTPException(status_code=401, detail="Invalid admin key")
    
    if country.lower() not in ["south_korea", "north_korea"]:
        raise HTTPException(status_code=400, detail="Country must be 'south_korea' or 'north_korea'")
    
    # Prepare update data
    update_data = {
        "population": population,
        "year": year,
        "date": f"{year}-01-01T00:00:00Z"
    }
    
    if births is not None:
        update_data["births"] = births
    if deaths is not None:
        update_data["deaths"] = deaths
    if growth_rate is not None:
        update_data["growth_rate"] = growth_rate
    
    # Update the population manager
    population_manager.update_base_data(country.lower(), update_data)
    
    return {
        "status": "success",
        "message": f"Updated {country} base data",
        "updated_data": update_data,
        "timestamp": population_manager.get_korea_timezone_now().isoformat()
    }

@app.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    """About page explaining the project"""
    return templates.TemplateResponse(
        "about.html",
        {
            "request": request,
            "title": "About - Pulse of Korea"
        }
    )

@app.get("/privacy", response_class=HTMLResponse)
async def privacy(request: Request):
    """Privacy policy page"""
    return templates.TemplateResponse(
        "privacy.html",
        {
            "request": request,
            "title": "Privacy Policy - Pulse of Korea"
        }
    )

async def send_contact_email(name: str, email: str, subject: str, message: str):
    """Send contact form email to admin"""
    try:
        # Create message
        msg = MIMEMultipart()
        msg["From"] = SMTP_USERNAME
        msg["To"] = ADMIN_EMAIL
        msg["Subject"] = f"Contact Form: {subject}"
        
        # Email body
        body = f"""
New contact form submission from Pulse of Korea:

Name: {name}
Email: {email}
Subject: {subject}

Message:
{message}

---
This message was sent from the Pulse of Korea contact form.
"""
        
        msg.attach(MIMEText(body, "plain"))
        
        # Send email using aiosmtplib
        await aiosmtplib.send(
            msg,
            hostname=SMTP_SERVER,
            port=SMTP_PORT,
            start_tls=True,
            username=SMTP_USERNAME,
            password=SMTP_PASSWORD,
        )
        
        return True
        
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

@app.get("/contact", response_class=HTMLResponse)
async def contact_get(request: Request):
    """Contact form page"""
    return templates.TemplateResponse(
        "contact.html",
        {
            "request": request,
            "title": "Contact - Pulse of Korea"
        }
    )

@app.post("/contact")
@limiter.limit("5/minute")
async def contact_post(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    subject: str = Form(...),
    message: str = Form(...)
):
    """Handle contact form submission"""
    try:
        # Validate email
        try:
            validated_email = validate_email(email)
            email = validated_email.email
        except EmailNotValidError:
            raise HTTPException(status_code=400, detail="Invalid email address")
        
        # Validate required fields
        if not name or not subject or not message:
            raise HTTPException(status_code=400, detail="All fields are required")
        
        # Basic length validation
        if len(name) > 100 or len(subject) > 200 or len(message) > 2000:
            raise HTTPException(status_code=400, detail="Input too long")
        
        # Send email
        success = await send_contact_email(name, email, subject, message)
        
        if success:
            return JSONResponse(
                status_code=200,
                content={"message": "Thank you! Your message has been sent successfully."}
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to send message")
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Contact form error: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while processing your message")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
