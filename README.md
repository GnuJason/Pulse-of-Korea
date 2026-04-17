<p align="center">
  <img src="public/branding/pulseofkorea_gif.jpg" style="max-width: 100%; height: auto;" />
</p>
# Pulse of Korea

A FastAPI web application displaying real-time demographic data for the Korean Peninsula with interactive visualizations and WebSocket-powered live updates.

## Prerequisites

- **Python 3.11 or 3.12** (other versions may work but are not tested)
- `pip` package manager (included with Python)

## Features

- **Real-time Population Tracking**: Live population counters with WebSocket synchronization
- **Interactive SVG Map**: Detailed Korean Peninsula visualization
- **Official Data Integration**: Anchored to KOSIS (South Korea) and CIA World Factbook (North Korea) data
- **Contact Form**: Secure email-based contact system with SMTP delivery
- **Security Hardened**: Production-ready with comprehensive security middleware
- **Responsive Design**: Mobile-friendly interface with Tailwind CSS
- **Animated Background**: Dynamic Vanta.js network visualization

## Installation

1. Clone the repository (or download and extract the ZIP):
   ```bash
   git clone https://github.com/GnuJason/Pulse-of-Korea.git
   cd Pulse-of-Korea
   ```

2. Create a virtual environment:
   ```bash
   python3 -m venv venv
   ```

3. Activate the virtual environment:

   **Linux / macOS:**
   ```bash
   source venv/bin/activate
   ```

   **Windows (Command Prompt):**
   ```bat
   venv\Scripts\activate.bat
   ```

   **Windows (PowerShell):**
   ```powershell
   venv\Scripts\Activate.ps1
   ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Set up your environment variables:
   ```bash
   cp .env.example .env
   ```
   Open `.env` and fill in at minimum a `SECRET_KEY`. Email settings are optional — the contact form will return an error if SMTP is not configured, but all other features work without it.

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
- **Contact Form**: `/contact` with validation and rate limiting (5 submissions per minute)
- **Email Delivery**: SMTP-based delivery to the configured admin address
- **Rate Limiting**: IP-based submission limits via SlowAPI

### Security Features
- **HTTPS Redirect**: Production HTTPS enforcement
- **Security Headers**: CSP, HSTS, XSS protection
- **Rate Limiting**: SlowAPI integration for API protection
- **Trusted Hosts**: Domain allowlist configuration

## Project Structure

```
Pulse-of-Korea/
├── main.py                    # FastAPI application with security middleware
├── population_manager.py      # Real-time population state management
├── requirements.txt           # Python dependencies
├── Procfile                   # Render/Heroku deployment start command
├── .env.example               # Environment variables template
├── templates/                 # Jinja2 HTML templates
│   ├── base.html              # Shared base layout
│   ├── nav.html               # Navigation partial
│   ├── footer.html            # Footer partial
│   ├── index.html             # Main real-time dashboard
│   ├── contact.html           # Contact form page
│   ├── about.html             # About page
│   ├── privacy.html           # Privacy policy
│   ├── korea.svg              # Korean Peninsula SVG map
│   ├── 404.html               # Not-found error page
│   └── 500.html               # Server error page
└── static/                    # Static assets (reserved for future use)
```

## API Endpoints

### Public Endpoints
- `GET /` - Main dashboard with real-time population data
- `GET /contact` - Contact form page
- `POST /contact` - Submit contact form (rate limited: 5 requests/minute per IP)
- `GET /about` - About page
- `GET /privacy` - Privacy policy
- `GET /api/data` - Current demographic data (JSON)
- `GET /api/data/south-korea-only` - South Korea data only (JSON)
- `GET /api/data/north-korea-only` - North Korea data only (JSON)
- `GET /api/realtime/current` - Real-time population snapshot (JSON)
- `GET /api/validation` - Validate demographic data calculations (JSON)
- `WebSocket /ws/population` - Real-time population updates

### Admin Endpoints
- `POST /api/admin/update-base-data` - Update population base data (requires `X-Admin-Key` header)

## Environment Configuration

Copy `.env.example` to `.env` and adjust the values:

```bash
cp .env.example .env
```

```env
ENVIRONMENT=development
SECRET_KEY=your-secret-key-here

# Comma-separated list of trusted hostnames
ALLOWED_HOSTS=localhost,127.0.0.1

# Admin key for the /api/admin/update-base-data endpoint
ADMIN_UPDATE_KEY=admin-secret-key-change-in-production

# Email Configuration (optional — required only for the contact form to send emails)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

> **Note:** The application starts and runs without any email configuration. If SMTP is not configured, submitting the contact form will return a 500 error, but all other pages and features work normally.

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
