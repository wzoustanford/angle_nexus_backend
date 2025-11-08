# Web Directory

This directory contains the core Flask web application for the `angle_backend` project. The application features a modern, modular architecture with specialized AI agents for financial analysis, legal compliance, and information gathering.

## Project Structure

```
web/
├── routes/                # REST API Blueprint modules (RESTful endpoints)
│   ├── chat.py           # Chat endpoints for AI agents
│   ├── crypto.py         # Cryptocurrency data API
│   ├── data.py           # DynamoDB data fetching
│   ├── equity.py         # Equity market data API
│   └── health.py         # Health check endpoints
├── clients/               # External API client wrappers
│   ├── fmp_api.py        # Financial Modeling Prep API client
│   └── reasoning.py      # OpenAI/DeepSeek reasoning API client
├── services/              # Business logic layer
│   ├── chat_service.py   # Daimon agent processing
│   ├── classification_service.py  # Query classification
│   ├── dynamo_service.py # DynamoDB operations
│   ├── weaver_service.py # Weaver agent processing
│   └── widget_service.py # Widget generation
├── middleware/            # Request/response middleware
│   ├── cors.py           # CORS headers handling
│   └── error_handler.py  # Global error handling
├── static/               # Static assets
│   ├── css/
│   │   └── anglenexus.css  # Complete UI styling (1100+ lines)
│   └── js/
│       └── anglenexus.js   # Agent interaction logic with LocalStorage
├── templates/            # HTML templates
│   ├── anglenexus.html   # Main AI agent interface (default)
│   └── index.html        # Legacy Illumenti interface
├── utils/                # Utility functions
├── widgets/              # Widget rendering components
├── __init__.py           # Flask app factory
├── config.py             # Configuration management
├── extensions.py         # Shared Flask extensions
├── main.py               # Legacy entry point (backward compatibility)
├── views.py              # Template rendering routes
└── README.md             # This file
```

## Architecture Overview

### Service Layer Pattern
The application follows a modular service-oriented architecture:

- **Routes Layer** (`routes/`): RESTful endpoints organized by feature (chat, equity, crypto, data, health)
- **Clients Layer** (`clients/`): External API integrations (FMP, OpenAI, DeepSeek)
- **Service Layer** (`services/`): Business logic and AI agent processing
- **Middleware** (`middleware/`): Cross-cutting concerns (CORS, error handling)
- **Views** (`views.py`): Template rendering for web pages

### AI Agents

#### 1. Daimon Agent (Financial Analysis)
- **Endpoint**: `/api/chat/daimon`
- **Purpose**: Main financial reasoning agent for market analysis and investment insights
- **Pipeline**: Classification → Data Fetching → Widget Generation
- **Features**: 
  - Intelligent query classification (equity, crypto, general)
  - Real-time data retrieval from DynamoDB
  - Dynamic widget generation for visualizations
  - Multi-model support (o3-mini, GPT-4o, o1, o1-mini, deepseek-reasoner)

#### 2. Weaver Agent (Information Gathering)
- **Endpoint**: `/chat` with `/weaver` prefix or `/api/chat/weaver`
- **Purpose**: Gathers and synthesizes information from multiple external sources
- **Features**:
  - Concurrent API data fetching using ThreadPoolExecutor
  - Financial Modeling Prep (FMP) API integration
  - Reasoning model for synthesis and analysis
  - Chat history persistence via browser LocalStorage
  - Clear history functionality

#### 3. Avvocato Agent (Legal Compliance)
- **Endpoint**: `/api/chat/avvocato`
- **Purpose**: Legal and compliance guidance for financial regulations
- **Features**:
  - US financial law knowledge base
  - Compliance advisory (not qualified legal advice)
  - Regulatory interpretation assistance

#### 4. Sophon Agent (Interface Intelligence)
- **Status**: Coming Soon
- **Purpose**: Interface discovery and UX orchestration

### Data Persistence

#### LocalStorage Implementation (Weaver Agent)
The Weaver agent implements client-side chat persistence:

- **Storage Key**: `weaver_chat_history`
- **Capacity**: 100 messages (configurable via `MAX_STORED_MESSAGES`)
- **Features**:
  - Automatic save on each message exchange
  - Auto-restore on agent toggle
  - Quota overflow protection (reduces to 50 messages)
  - Clear history button in chat header
  - Message structure: `{role, content, timestamp}`

#### DynamoDB Integration
- **Service**: `dynamo_service.py`
- **Purpose**: Fetch historical equity and crypto data
- **Features**: 
  - Decimal conversion for JSON compatibility
  - Date-based queries
  - Multi-symbol batch retrieval

## Requirements

Ensure you have the following installed:

1. **Python 3.9+**
2. **Virtual Environment**
3. **Flask** and dependencies listed in `requirements.txt`
4. **AWS Credentials** (for DynamoDB access)
5. **API Keys**: OpenAI, DeepSeek, Financial Modeling Prep

## Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/your-repo/angle_backend.git
   cd angle_backend/web
   ```

2. **Create and Activate a Virtual Environment**

   ```bash
   # Create a virtual environment
   python3 -m venv venv

   # Activate the virtual environment
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate    # Windows
   ```

3. **Install Dependencies**

   ```bash
   pip install -r ../requirements.txt
   ```

## Configuration

### Environment Variables

The application uses the `.flaskenv` file and environment variables for configuration:

```env
# Flask Configuration
FLASK_APP=web.main
FLASK_ENV=development
FLASK_RUN_PORT=5001

# AWS Configuration (required for DynamoDB)
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1

# API Keys
OPENAI_API_KEY=your_openai_key
DEEPSEEK_API_KEY=your_deepseek_key
FMP_API_KEY=your_fmp_key

# Application Settings (optional)
DEFAULT_MODEL=o3-mini
DEBUG=True
HOST=0.0.0.0
PORT=5001
```

### Configuration Classes

The `config.py` file provides environment-specific configurations:

- **DevelopmentConfig**: Debug mode enabled, verbose logging
- **ProductionConfig**: Debug disabled, optimized for deployment
- **TestingConfig**: Testing mode with isolated settings

### Key Configuration Options

- **DEFAULT_MODEL**: `o3-mini` (default AI model)
- **ALLOWED_MODELS**: `['o3-mini', 'gpt-4o', 'deepseek-reasoner', 'o1', 'o1-mini']`
- **AWS_DYNAMO_TABLE**: DynamoDB table name for financial data
- **API_KEYS**: OpenAI, DeepSeek, Financial Modeling Prep credentials

## Running the Application

1. **Using `flask run`**

   Ensure you're in the `angle_backend` directory and the virtual environment is activated. Then run:

   ```bash
   flask run
   ```

   The app will be available at `http://localhost:5001`.

2. **Using `python`**

   You can also run the app directly using Python. Navigate to the `web` directory and execute:

   ```bash
   python main.py
   ```

   The app will be available at `http://localhost:5001`.

## API Endpoints

### Modern REST API (Recommended)

#### Chat Endpoints

**1. Daimon Agent (Financial Analysis)**
```bash
POST /api/chat/daimon
Content-Type: application/json

{
  "message": "What is the current price of Apple stock?",
  "model_name": "o3-mini",
  "history": []
}

Response:
{
  "message": "Based on the latest data...",
  "classification": {...},
  "widget": {...}
}
```

**2. Weaver Agent (Information Gathering)**
```bash
POST /api/chat/weaver
Content-Type: application/json

{
  "message": "Research the latest trends in AI technology",
  "model_name": "o3-mini",
  "history": []
}

Response:
{
  "message": "Here's what I found from multiple sources..."
}
```

**3. Avvocato Agent (Legal Compliance)**
```bash
POST /api/chat/avvocato
Content-Type: application/json

{
  "message": "What are SEC regulations for insider trading?",
  "model_name": "o3-mini"
}

Response:
{
  "message": "According to SEC regulations..."
}
```

**4. Sophon Agent (Coming Soon)**
```bash
POST /api/chat/sophon
```

#### Data Endpoints

**1. Equity Search**
```bash
GET /api/equity/search?query=Apple

Response:
[
  {
    "symbol": "AAPL",
    "name": "Apple Inc.",
    "exchange": "NASDAQ",
    "price": 150.25
  }
]
```

**2. Crypto Search**
```bash
GET /api/crypto/search?query=Bitcoin

Response:
[
  {
    "symbol": "BTC",
    "name": "Bitcoin",
    "price": 45000.00
  }
]
```

**3. Fetch Historical Data**
```bash
POST /api/data/fetch
Content-Type: application/json

{
  "date": "2024-01-15",
  "symbols": ["AAPL", "MSFT", "GOOGL"]
}

Response:
{
  "data": {
    "AAPL": {...},
    "MSFT": {...},
    "GOOGL": {...}
  }
}
```

#### Health Endpoints

**1. Health Check**
```bash
GET /api/health

Response:
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**2. Status Check**
```bash
GET /api/status

Response:
{
  "app": "angle_backend",
  "version": "1.0.0",
  "uptime": 3600
}
```

### Legacy Endpoints (Backward Compatibility)

The following endpoints maintain backward compatibility with existing clients:

- `POST /chat` - Legacy chat endpoint (supports `/weaver` command detection)
- `GET /equity-api?query=<term>` - Legacy equity search
- `GET /crypto-api?query=<term>` - Legacy crypto search
- `POST /fetch_data` - Legacy DynamoDB fetch
- `GET /companies` - Legacy companies query

## Frontend Interface

### AngleNexus (Default Homepage)
- **Route**: `/` or `/anglenexus`
- **Template**: `anglenexus.html`
- **Features**:
  - Modern glassmorphism design with gradient animations
  - Four specialized AI agent cards (Daimon, Avvocato, Weaver, Sophon)
  - Interactive chat interfaces with toggle functionality
  - Real-time message streaming
  - LocalStorage chat history (Weaver agent)
  - Responsive design with smooth animations
  - SVG icons and pulse indicators

### Legacy Illumenti Interface
- **Route**: `/illumenti`
- **Template**: `index.html`
- **Purpose**: Maintained for backward compatibility

### JavaScript Functionality

**Agent Interaction** (`anglenexus.js`):
- `toggleDaimon()` - Show/hide Daimon chat window
- `sendDaimon()` - Send messages to Daimon agent
- `toggleAvvocato()` - Show/hide Avvocato chat window
- `sendAvvocato()` - Send messages to Avvocato agent
- `toggleWeaver()` - Show/hide Weaver chat window with history restore
- `sendWeaver()` - Send messages to Weaver agent with LocalStorage save
- `clearWeaverHistory()` - Clear stored chat history
- `escapeHtml()` - Prevent XSS attacks
- Smooth scrolling and keyboard support (Enter key to send)

### CSS Architecture

**Styling System** (`anglenexus.css`):
- CSS Variables for theme consistency
- Glassmorphism effects with backdrop-filter
- Gradient animations and transitions
- Agent-specific namespaces:
  - `.d-*` - Daimon agent styles
  - `.a-*` - Avvocato agent styles
  - `.w-*` - Weaver agent styles
- Responsive design patterns
- Custom scrollbar styling
- Loading animations
- Pulse effects for status indicators

## Development Notes

### Service Layer Design Principles

1. **Single Responsibility**: Each service handles one specific domain
2. **Dependency Injection**: Services receive dependencies via parameters
3. **Error Handling**: Try-catch blocks with proper logging
4. **Type Safety**: Pydantic models for request validation
5. **Testability**: Pure functions enable easy unit testing

### API Blueprint Pattern

Each routes module follows this structure:
```python
from flask import Blueprint, request, jsonify

blueprint_bp = Blueprint('name', __name__, url_prefix='/api/path')

@blueprint_bp.route('/endpoint', methods=['POST'])
def endpoint_function():
    # Validation
    # Service layer call
    # Response formatting
    pass
```

### External API Clients

The `clients/` folder contains wrappers for external services:
- **fmp_api.py**: Financial Modeling Prep API for market data
- **reasoning.py**: OpenAI and DeepSeek API clients for AI reasoning

### Middleware Stack

Request flow:
1. CORS middleware adds headers
2. Error handler catches exceptions
3. Blueprint routes to appropriate service
4. Service processes business logic
5. Response formatted and returned

### Static and Template Files
- Place CSS/JavaScript in `static/` with appropriate subdirectories
- HTML templates in `templates/` folder
- Use Flask's `url_for()` for asset paths
- Maintain separation of concerns (structure/style/behavior)

### Dataset Loading

Datasets are loaded from the `data/` directory in the root project:

- `data/equity_nyse_exported_table.csv` - NYSE equity data
- `data/equity_nasdaq_exported_table.csv` - NASDAQ equity data
- `data/crypto_info_table_full.csv` - Cryptocurrency information

Paths resolved using Python's `os.path` for cross-platform compatibility.

## Testing

### Running Tests
```bash
# Unit tests for services
python -m pytest tests/test_services.py

# Integration tests for API endpoints
python -m pytest tests/test_api.py

# Test coverage report
python -m pytest --cov=web tests/
```

### Manual Testing with curl

**Test Daimon Agent:**
```bash
curl -X POST http://localhost:5001/api/chat/daimon \
  -H "Content-Type: application/json" \
  -d '{"message": "What is AAPL current price?", "model_name": "o3-mini"}'
```

**Test Weaver Agent:**
```bash
curl -X POST http://localhost:5001/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "/weaver Research Tesla stock", "model_name": "o3-mini"}'
```

**Test Equity Search:**
```bash
curl http://localhost:5001/api/equity/search?query=Apple
```

## Debugging

### Enable Debug Mode
Set environment variable:
```bash
export FLASK_ENV=development
export DEBUG=True
```

### Logging Configuration
The application uses Python's logging module with the following levels:

- **DEBUG**: Detailed diagnostic information
- **INFO**: General informational messages
- **WARNING**: Warning messages for potentially harmful situations
- **ERROR**: Error messages for serious problems
- **CRITICAL**: Critical errors causing application failure

Logs are written to:
- Console (stdout) in development
- `app.log` file in production

### Common Issues

**Issue**: LocalStorage not persisting
- **Solution**: Check browser privacy settings, ensure cookies/storage enabled

**Issue**: CORS errors in browser
- **Solution**: CORS middleware should handle this automatically, check `middleware/cors.py`

**Issue**: DynamoDB connection failed
- **Solution**: Verify AWS credentials and region in environment variables

**Issue**: API rate limits
- **Solution**: Check API key quotas for OpenAI, DeepSeek, FMP

## Deployment

### Production Checklist

1. Set `FLASK_ENV=production`
2. Disable `DEBUG=False`
3. Configure production database credentials
4. Set up HTTPS with SSL certificates
5. Configure reverse proxy (Nginx/Caddy)
6. Set up monitoring and logging
7. Enable rate limiting
8. Configure CORS for specific origins
9. Set secure session cookies
10. Review security headers

### Docker Deployment

```bash
# Build Docker image
docker build -t angle_backend .

# Run container
docker run -p 5001:5001 \
  -e FLASK_ENV=production \
  -e OPENAI_API_KEY=your_key \
  angle_backend
```

### Using Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Future Improvements

1. **Complete Sophon Agent**: Implement interface intelligence and UX orchestration
2. **Extend LocalStorage**: Add persistence for Daimon and Avvocato agents
3. **Backend Chat History**: Implement database-backed chat persistence with user authentication
4. **WebSocket Support**: Real-time streaming responses for better UX
5. **Caching Layer**: Redis integration for API response caching
6. **Rate Limiting**: Implement per-user/per-IP rate limits
7. **Unit Test Coverage**: Achieve 80%+ test coverage
8. **API Documentation**: Generate OpenAPI/Swagger documentation
9. **Performance Monitoring**: Add APM tools (New Relic, DataDog)
10. **Multi-language Support**: Internationalization (i18n)
11. **Advanced Analytics**: User behavior tracking and insights
12. **Export Functionality**: Allow users to export chat history
13. **Voice Input**: Speech-to-text for agent interactions
14. **Mobile App**: Native iOS/Android applications
15. **Batch Processing**: Queue system for long-running queries

## Security Considerations

- Input validation using Pydantic models
- XSS prevention with HTML escaping
- CSRF protection for state-changing operations
- Rate limiting to prevent abuse
- API key rotation policies
- Secure session management
- SQL injection prevention (parameterized queries)
- Environment variable encryption
- Audit logging for sensitive operations

## Performance Optimization

- Concurrent API calls using ThreadPoolExecutor
- Database query optimization
- Response compression (gzip)
- Static asset caching with ETags
- CDN integration for static files
- Database connection pooling
- Lazy loading of large datasets
- Message truncation in LocalStorage (100 message limit)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Follow PEP 8 style guidelines
4. Add unit tests for new features
5. Update documentation
6. Submit pull request with detailed description

## Support

For issues and questions:
- GitHub Issues: Repository issue tracker
- Documentation: This README and inline code comments
- API Reference: See API Endpoints section above

---

## License

This project is licensed under the MIT License. See the `LICENSE` file for more details.
