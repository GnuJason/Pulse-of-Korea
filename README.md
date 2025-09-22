# Pulse of Korea

A FastAPI web application displaying real-time demographic data for the Korean Peninsula with interactive visualizations and WebSocket-powered live updates.

## Features

- **Real-time Population Tracking**: Live population counters with WebSocket synchronization
- **Interactive SVG Map**: Detailed Korean Peninsula visualization
- **Official Data Integration**: Anchored to KOSIS (South Korea) and CIA World Factbook (North Korea) data
- **Contact Form**: Secure email-based contact system with SMTP delivery
- **Security Hardened**: Production-ready with comprehensive security middleware
- **Responsive Design**: Mobile-friendly interface with Tailwind CSS
- **Animated Background**: Dynamic Vanta.js network visualization

## Installation

1. Create a virtual environment:
   ```bash
   python3 -m venv venv
   ```

2. Activate the virtual environment:
   ```bash
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

Start the development server:
```bash
uvicorn main:app --reload
```

The application will be available at `http://localhost:8000`

## Key Components

### Real-time Population System
- **WebSocket Endpoints**: `/ws/population` for live updates
- **Population Manager**: Authoritative state management with official data anchoring
- **Synchronized Updates**: Birth/death rate calculations broadcast to all connected clients

### Contact System
- **Contact Form**: `/contact` with validation and rate limiting (5 submissions per hour)
- **Database Storage**: SQLite backend for message persistence
- **Admin Interface**: `/admin/contacts` for message management
- **Rate Limiting**: IP and email-based submission limits

### Security Features
- **HTTPS Redirect**: Production HTTPS enforcement
- **Security Headers**: CSP, HSTS, XSS protection
- **Rate Limiting**: SlowAPI integration for API protection
- **Trusted Hosts**: Domain allowlist configuration

## Project Structure

```
pulse-of-korea/
├── main.py                    # FastAPI application with security middleware
├── population_manager.py      # Real-time population state management
├── contact_db.py             # Contact form database operations
├── requirements.txt          # Python dependencies
├── contacts.db              # SQLite database for contact messages
├── .env.example             # Environment variables template
├── templates/               # Jinja2 templates
│   ├── index.html          # Main real-time dashboard
│   ├── contact.html        # Contact form page
│   ├── admin_contacts.html # Admin dashboard
│   ├── about.html          # About page
│   └── privacy.html        # Privacy policy
└── static/                 # Static assets
```

## API Endpoints

### Public Endpoints
- `GET /` - Main dashboard with real-time population data
- `GET /contact` - Contact form page
- `POST /contact` - Submit contact form (rate limited)
- `GET /about` - About page
- `GET /privacy` - Privacy policy
- `GET /api/data` - Current demographic data (JSON)
- `WebSocket /ws/population` - Real-time population updates

### Admin Endpoints  
- `GET /admin/contacts` - Contact message dashboard
- `GET /api/admin/contacts` - Contact data API (rate limited)
- `POST /api/admin/update-base-data` - Update population base data (admin only)

## Environment Configuration

Create `.env` file based on `.env.example`:

```bash
ENVIRONMENT=production
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=pulseofkorea.org,pulseofkorea.com,your-app.onrender.com,localhost

# Email Configuration (for contact form)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### Email Setup

For Gmail:
1. Enable 2-factor authentication on your Google account
2. Generate an App Password: [Google Account Settings > Security > App Passwords](https://support.google.com/accounts/answer/185833)
3. Use the App Password (not your regular password) in `SMTP_PASSWORD`

For other email providers:
- **Outlook/Hotmail**: `SMTP_HOST=smtp-mail.outlook.com`, `SMTP_PORT=587`
- **Yahoo**: `SMTP_HOST=smtp.mail.yahoo.com`, `SMTP_PORT=587`
- **Custom SMTP**: Use your provider's SMTP settings

## Development

The application uses:
- **FastAPI** for the web framework with WebSocket support
- **Jinja2** for templating
- **aiosmtplib** for async email delivery
- **SlowAPI** for rate limiting
- **Tailwind CSS** for responsive styling
- **Vanta.js** for animated backgrounds
- **WebSockets** for real-time data synchronization

## Production Deployment

1. Set environment variables for production
2. Configure HTTPS certificates
3. Set up reverse proxy (nginx recommended)
4. Configure allowed hosts
5. Set up email SMTP credentials

## Contact Form Features

- **Email Delivery**: Direct SMTP delivery to admin@pulseofhumanity.org
- **Validation**: Client and server-side form validation with email validation
- **Rate Limiting**: 5 submissions per minute per IP address
- **Security**: XSS prevention, input sanitization, and length validation
- **Responsive Design**: Mobile-friendly contact form with success/error feedback