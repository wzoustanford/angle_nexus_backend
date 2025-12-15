# Angle Backend

Flask API backend for Angle Finance app with AI-powered financial analysis, data pipeline, and search capabilities.

## Tech Stack

- **Framework**: Flask 2.0.2 with Flask-CORS
- **Server**: Gunicorn with 3 workers, 120s timeout
- **AI/ML**: OpenAI GPT-4, NLTK for NLP
- **Database**: AWS DynamoDB
- **Search**: Custom search engine (equity & crypto)
- **APIs**: Financial Modeling Prep (FMP)

## Local Development Setup

### 1. Create Python Virtual Environment

```bash
# Install python3-venv if needed (Ubuntu/Debian)
sudo apt install python3-venv

# Create virtual environment
python3 -m venv venv

# Activate environment
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt

# Download NLTK data
python3 -c "import nltk; nltk.download('stopwords')"
```

### 3. Configure Environment Variables

Create `.env` file in root directory:

```bash
# AWS Configuration
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-west-2
DYNAMODB_TABLE=your_table_name

# API Keys
FINANCIAL_KEY=your_fmp_api_key
OPENAI_API_KEY=your_openai_key

# Flask Configuration
FLASK_ENV=development
FLASK_APP=web/main.py

# Model Configuration
DEFAULT_MODEL=o3-mini
ALLOWED_MODELS=o3-mini,deepseek-reasoner
```

### 4. Run Development Server

```bash
export FLASK_APP=web/main.py
flask run --host=0.0.0.0 --port=5001
```

Or with Gunicorn:

```bash
gunicorn --workers=3 --timeout=120 --bind=0.0.0.0:5001 web.main:app
```

## Production Deployment (Bare Metal)

### 1. System Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install python3 python3-venv python3-pip -y
```

### 2. Clone & Install

```bash
cd /home/ubuntu
git clone https://github.com/wzoustanford/angle_nexus_backend.git
cd angle_nexus_backend

# Create venv and install
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Download NLTK data
python3 -c "import nltk; nltk.download('stopwords')"
```

### 3. Configure Systemd Service

Create `/etc/systemd/system/angle-backend.service`:

```ini
[Unit]
Description=Angle Backend Flask API
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/angle_nexus_backend
Environment="PATH=/home/ubuntu/angle_nexus_backend/venv/bin"
ExecStart=/home/ubuntu/angle_nexus_backend/venv/bin/gunicorn --workers=3 --timeout=120 --bind=0.0.0.0:80 web.main:app
Restart=always
RestartSec=10
AmbientCapabilities=CAP_NET_BIND_SERVICE

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable angle-backend
sudo systemctl start angle-backend
sudo systemctl status angle-backend
```

### 4. View Logs

```bash
# Real-time logs
sudo journalctl -u angle-backend -f

# Last 100 lines
sudo journalctl -u angle-backend -n 100

# Filter errors only
sudo journalctl -u angle-backend -p err
```

### 5. Manage Service

```bash
# Restart after code changes
sudo systemctl restart angle-backend

# Stop service
sudo systemctl stop angle-backend

# Check status
sudo systemctl status angle-backend
```

## Data Pipeline (Cron Job)

The data pipeline updates financial datasets daily at 2 AM GMT.

### Setup Cron Job

```bash
crontab -e
```

Add:

```bash
# Set timezone to GMT
CRON_TZ=GMT
SHELL=/bin/bash
PATH=/home/ubuntu/angle_nexus_backend/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
VIRTUAL_ENV=/home/ubuntu/angle_nexus_backend/venv

# Run data pipeline at 2 AM GMT daily
0 2 * * * cd /home/ubuntu/angle_nexus_backend/datapipeline && bash run_all_instances.sh >> /home/ubuntu/datapipeline_cron.log 2>&1
```

### Monitor Cron Logs

```bash
# View cron log
tail -f /home/ubuntu/datapipeline_cron.log

# Check cron execution history
grep CRON /var/log/syslog | tail -20

# View worker logs
ls -lt /home/ubuntu/angle_nexus_backend/datapipeline/logs/
```

## API Endpoints

### Health Check
- `GET /health` - Service health status

### Chat & AI
- `POST /chat` - Main chat endpoint with AI models
- `POST /chat` (with `/weaver` command) - Financial analysis with API integration

### Data Endpoints
- `GET /equity/search/<query>` - Search equity symbols
- `GET /crypto/search/<query>` - Search cryptocurrency symbols
- `GET /equity/data/<symbol>` - Get equity data from DynamoDB
- `GET /crypto/data/<symbol>` - Get crypto data

### Subscription (Currently Disabled)
- `POST /api/subscription/verify` - Verify App Store receipts
- `GET /api/subscription/status/<account_id>` - Get subscription status

## Project Structure

```
angle_backend/
├── web/                      # Flask application
│   ├── __init__.py          # App factory
│   ├── main.py              # Main entry point, route handlers
│   ├── config.py            # Configuration management
│   ├── extensions.py        # Shared objects (search, DynamoDB)
│   ├── clients/             # External API clients
│   │   ├── fmp_api.py       # Financial Modeling Prep API
│   │   ├── reasoning.py     # OpenAI chat client
│   │   └── subscription_api.py # App Store verification
│   ├── services/            # Business logic layer
│   │   ├── weaver_service.py     # Financial analysis service
│   │   ├── widget_service.py     # Widget generation
│   │   ├── classification_service.py # Query classification
│   │   └── subscription_service.py # Subscription management
│   ├── routes/              # API route blueprints
│   ├── models/              # Pydantic models
│   ├── prompts/             # AI system prompts
│   └── utils/               # Helper utilities
├── search/                  # Search engine modules
│   ├── illumenti_search.py      # Equity search
│   └── illumenti_crypto_search.py # Crypto search
├── datapipeline/           # Data processing pipeline
│   ├── build_dataset.py    # Dataset builder
│   ├── run_all_instances.sh # Pipeline orchestrator
│   └── scripts/            # Update scripts
├── data/                   # Dataset files (CSV)
├── graphql/                # GraphQL schemas
└── requirements.txt        # Python dependencies
```

## Key Features

### 1. AI Chat with Financial Context
- Supports multiple AI models (o3-mini, deepseek-reasoner)
- `/weaver` command for advanced financial analysis
- Integrates real-time financial data from APIs
- Conversation history management

### 2. Financial Data Search
- Fast equity symbol search (NYSE, NASDAQ)
- Cryptocurrency search across 1800+ coins
- NLTK-powered text tokenization and indexing

### 3. Data Pipeline
- Automated daily updates at 2 AM GMT
- Multi-worker parallel processing
- Fetches data from Financial Modeling Prep API
- Updates DynamoDB and local CSV datasets

### 4. Rate Limiting
- Thread-safe rate limiter for FMP API
- Configurable calls per minute (default: 280)
- Exponential backoff on rate limit errors

## Troubleshooting

### Worker Timeout Errors
If requests take >30s (default), increase timeout:
```bash
# Edit systemd service
--timeout=120  # or higher
```

### NLTK Stopwords Missing
```bash
python3 -c "import nltk; nltk.download('stopwords')"
```

### Port 80 Permission Denied
Add `AmbientCapabilities=CAP_NET_BIND_SERVICE` to systemd service.

### Disk Space Issues
```bash
# Clean system
sudo apt clean && sudo apt autoremove
sudo journalctl --vacuum-time=7d

# Check space
df -h
```

### Import Errors (web.apis.*)
Modules moved from `web/apis/` to `web/clients/`. Update imports:
```python
# OLD: from .apis.fmp_api import ...
# NEW: from .clients.fmp_api import ...
```

## Environment Updates

After changing `.env` file:

```bash
# Systemd service
sudo systemctl restart angle-backend

# Manual gunicorn
# Kill process and restart (systemctl handles this automatically)
```

## Notes for Engineers

1. **CORS is enabled globally** - All origins allowed for development
2. **Subscription routes disabled** - Commented out in `web/main.py`
3. **Worker timeout set to 120s** - Handles slow FMP API responses
4. **Rate limiter is thread-safe** - Shared across workers
5. **NLTK data required** - Must be downloaded before first run
6. **DynamoDB credentials** - Must be set in `.env` for equity data
7. **Python 3.12+** - Tested on Python 3.12
8. **Gunicorn sync workers** - Using default sync worker class (not async)
9. **Log rotation** - Use journalctl vacuum to manage log size
10. **Cron uses venv Python** - PATH includes venv/bin in crontab
