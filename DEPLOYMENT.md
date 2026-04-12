# Deployment Guide for Pulse of Korea

## Files Included in Deployment-Ready Project

```
Pulse-of-Korea/
├── .env.example              # Environment variables template
├── .gitignore               # Git exclusions (comprehensive)
├── main.py                  # FastAPI application entry point
├── population_manager.py    # Population calculation logic
├── Procfile                 # Render/Heroku start command
├── README.md                # Project documentation
├── requirements.txt         # Python dependencies
├── runtime.txt              # Python version pin (for Render and similar platforms)
├── static/                  # (empty - reserved for future assets)
└── templates/               # HTML templates
    ├── base.html            # Shared base layout
    ├── nav.html             # Navigation partial
    ├── footer.html          # Footer partial
    ├── index.html           # Main dashboard
    ├── contact.html         # Contact form (email-based)
    ├── about.html           # About page
    ├── privacy.html         # Privacy policy
    ├── korea.svg            # Korean Peninsula map
    ├── 404.html             # Not-found error page
    └── 500.html             # Server error page
```

## Render Deployment Instructions

### 1. GitHub Repository Setup
```bash
# Initialize git repository
git init
git add .
git commit -m "Initial deployment-ready commit"

# Push to GitHub
git remote add origin https://github.com/yourusername/pulse-of-korea.git
git branch -M main
git push -u origin main
```

### 2. Create Render Web Service

1. **Connect Repository**
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click "New +" → "Web Service"
   - Connect your GitHub repository

2. **Configure Service**
   - **Name**: `pulse-of-korea`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: Free tier or starter ($7/month recommended)

3. **Environment Variables**
   ```
   ENVIRONMENT=production
   SECRET_KEY=your-super-secret-key-here-make-it-long-and-random
   ALLOWED_HOSTS=your-app-name.onrender.com,localhost
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=your-email@gmail.com
   SMTP_PASSWORD=your-gmail-app-password
   ADMIN_UPDATE_KEY=your-admin-secret-key
   ```

### 3. Email Configuration (Gmail Example)

1. **Enable 2FA** on your Google account
2. **Create App Password**:
   - Go to Google Account Settings
   - Security → 2-Step Verification → App passwords
   - Generate password for "Mail"
3. **Use App Password** in `SMTP_PASSWORD` environment variable

### 4. Deploy

- Render will automatically deploy when you push to the main branch
- Monitor deployment logs in Render dashboard
- Access your app at: `https://your-app-name.onrender.com`

## Environment Variables Reference

| Variable | Description | Example |
|----------|-------------|---------|
| `ENVIRONMENT` | Deployment environment | `production` |
| `SECRET_KEY` | FastAPI secret key | `super-secret-key-123` |
| `ALLOWED_HOSTS` | Comma-separated allowed domains | `myapp.onrender.com,localhost` |
| `SMTP_HOST` | Email server hostname | `smtp.gmail.com` |
| `SMTP_PORT` | Email server port | `587` |
| `SMTP_USER` | Email username | `your-email@gmail.com` |
| `SMTP_PASSWORD` | Email password/app password | `your-app-password` |
| `ADMIN_UPDATE_KEY` | Admin API access key | `admin-secret-key` |

## Features

✅ **Production-Ready**
- Modern FastAPI with lifespan management
- Comprehensive security headers
- Rate limiting on contact form
- Environment-based configuration

✅ **Real-Time Population Tracking**
- WebSocket-powered live updates
- Hybrid deterministic/simulated system
- Individual country tracking
- Mathematical precision with visual engagement

✅ **Contact System**
- Email-based contact form (no database required)
- SMTP delivery to admin@pulseofhumanity.org
- Form validation and rate limiting
- Mobile-responsive design

✅ **Security**
- No hardcoded secrets
- Comprehensive .gitignore
- Security middleware
- Input validation

## Development

```bash
# Local development
python -m venv venv
source venv/bin/activate          # Linux/macOS
# venv\Scripts\activate.bat       # Windows (Command Prompt)
# venv\Scripts\Activate.ps1       # Windows (PowerShell)
pip install -r requirements.txt
cp .env.example .env              # then edit .env with your values
uvicorn main:app --reload
```

## Troubleshooting

**Common Issues:**

1. **Email not sending**
   - Verify SMTP credentials
   - Check Gmail App Password setup
   - Ensure 2FA is enabled

2. **Application not starting**
   - Check environment variables
   - Verify all dependencies in requirements.txt
   - Check Render build logs

3. **WebSocket issues**
   - Ensure Render instance stays awake
   - Consider upgrading to paid tier for persistent connections

## Monitoring

- **Health Check**: `GET /api/realtime/current`
- **Population Data**: `GET /api/data`
- **Contact Form**: `POST /contact`

## Cost Optimization

- **Free Tier**: Basic functionality, may sleep after 15 minutes
- **Starter ($7/month)**: Better performance, no sleeping
- **Pro ($25/month)**: Production workloads, custom domains

---

**Ready for deployment!** 🚀