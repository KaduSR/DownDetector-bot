# DownDetector Notification Bot

A real-time service outage monitoring and notification system that tracks DownDetector.com for service status changes and delivers intelligent notifications via email and WebSocket.

## Features

- **Real-time Monitoring**: Scrapes DownDetector.com at configurable intervals (default: 10 minutes)
- **Change Detection**: Intelligent delta-based detection to avoid duplicate notifications
- **Email Notifications**: HTML email alerts with professional templates
- **WebSocket Support**: Real-time notifications for connected clients
- **AI-Powered Summaries** (v2): Generate article-style outage summaries using OpenAI or Anthropic
- **REST API**: Full API for third-party integration
- **Rate Limiting**: Built-in protection against API abuse
- **Docker Support**: Easy deployment with Docker and Docker Compose

## Quick Start

### Prerequisites

- Python 3.9+
- Docker & Docker Compose (optional)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/DownDetector-Bot-Hybrid.git
cd DownDetector-Bot-Hybrid
```

2. Create virtual environment and install dependencies:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Run the application:
```bash
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000
```

### Docker Deployment

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

## Configuration

All configuration is done via environment variables. See `.env.example` for all options.

### Key Configuration Options

| Variable | Description | Default |
|----------|-------------|---------|
| `SCRAPER_SCRAPE_INTERVAL_MINUTES` | Scraping interval | 10 |
| `SCRAPER_MONITORED_SERVICES` | Comma-separated list of services | google,facebook,twitter |
| `EMAIL_SMTP_HOST` | SMTP server host | localhost |
| `EMAIL_RECIPIENT_EMAILS` | Comma-separated recipient emails | - |
| `AI_PROVIDER` | AI provider (openai/anthropic) | openai |
| `AI_API_KEY` | AI service API key | - |

## API Endpoints

### Health & Metrics

- `GET /api/v1/health` - System health check
- `GET /api/v1/metrics` - System metrics

### Status

- `GET /api/v1/status` - Get all monitored services status
- `GET /api/v1/status/{service}` - Get specific service status
- `GET /api/v1/changes` - Get recent changes (last 24 hours)
- `GET /api/v1/services` - List all monitored services

### WebSocket

Connect to `/ws` for real-time outage updates.

## API Documentation

Once running, access interactive API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
DownDetector-Bot-Hybrid/
├── src/
│   ├── api/           # REST API endpoints
│   ├── ai/            # AI article generation
│   ├── detector/      # Change detection logic
│   ├── middleware/    # Rate limiting, security
│   ├── models/        # Pydantic data models
│   ├── notifier/      # Email & WebSocket notifications
│   ├── scheduler/     # Job scheduling
│   ├── scraper/       # DownDetector scraper
│   ├── utils/         # Logging, metrics
│   └── main.py        # Application entry point
├── templates/         # Email templates
├── tests/             # Test suite
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_detector.py -v
```

## Change Types Detected

- **NEW_OUTAGE**: Service newly detected as down
- **STATUS_CHANGED**: Status changed (up/issues/down)
- **SEVERITY_INCREASED**: Outage severity escalated
- **SEVERITY_DECREASED**: Outage severity reduced
- **REPORT_COUNT_SPIKE**: Significant increase in user reports
- **OUTAGE_RESOLVED**: Service restored to normal

## Email Templates

Two email templates are included:
- `email_basic.html` - Standard notification template
- `email_ai_article.html` - AI-enhanced article template

## Version 2 Features (AI-Enhanced)

Enable AI article generation by setting:
```
AI_PROVIDER=openai  # or anthropic
AI_API_KEY=your-api-key
AI_MODEL=gpt-4-turbo-preview
```

AI generates:
- Contextual outage summaries
- Impact analysis
- Professional article-style reports

## Development

### Running in Development Mode

```bash
# With Docker
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Without Docker
DEBUG=true python -m uvicorn src.main:app --reload
```

### Code Style

The project follows PEP 8 guidelines. Use the included tools:
```bash
black src/ tests/
flake8 src/ tests/
mypy src/
```

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## Support

For issues and feature requests, please use the GitHub issue tracker.
