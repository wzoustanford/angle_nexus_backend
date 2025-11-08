# 🏗️ AngleNexus Architecture Diagram

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────┐         ┌──────────────────────────┐     │
│  │ Legacy UI        │         │  AngleNexus UI           │     │
│  │ (Illumenti)      │         │  (Modern Interface)      │     │
│  │                  │         │                          │     │
│  │ /                │         │  /anglenexus             │     │
│  │ /search          │         │                          │     │
│  │ /privacy-policy  │         │  - Daimon Chat          │     │
│  └──────────────────┘         │  - Avvocato Chat        │     │
│                                │  - Sophon (Coming Soon) │     │
│                                │  - Weaver Info          │     │
│                                └──────────────────────────┘     │
│                                                                  │
└──────────────────────────────┬───────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FLASK APPLICATION                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │               MIDDLEWARE LAYER                            │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │  • CORS Handler       (All endpoints)                    │  │
│  │  • Error Handler      (Consistent error responses)       │  │
│  │  • Logging           (Request/Response tracking)         │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              ROUTING LAYER (Blueprints)                  │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │                                                           │   │
│  │  Legacy Routes (main.py)     New API Routes (api/)       │   │
│  │  ┌────────────────┐          ┌─────────────────────┐    │   │
│  │  │ /chat          │          │ /api/chat/daimon    │    │   │
│  │  │ /equity-api    │          │ /api/chat/weaver    │    │   │
│  │  │ /crypto-api    │          │ /api/chat/avvocato  │    │   │
│  │  │ /fetch_data    │          │ /api/chat/sophon    │    │   │
│  │  │ /companies     │          │ /api/equity/search  │    │   │
│  │  └────────────────┘          │ /api/crypto/search  │    │   │
│  │                               │ /api/data/fetch     │    │   │
│  │                               │ /api/health         │    │   │
│  │                               │ /api/status         │    │   │
│  │                               └─────────────────────┘    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                              ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              SERVICE LAYER (Business Logic)              │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │                                                           │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │   │
│  │  │ Chat Service │  │Weaver Service│  │Widget Service│  │   │
│  │  │ (Daimon)     │  │ (Info Gather)│  │(Visualization)│  │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  │   │
│  │                                                           │   │
│  │  ┌──────────────┐  ┌──────────────┐                     │   │
│  │  │Classification│  │Dynamo Service│                     │   │
│  │  │   Service    │  │   (Data)     │                     │   │
│  │  └──────────────┘  └──────────────┘                     │   │
│  │                                                           │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                              ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │           EXTERNAL INTEGRATIONS LAYER                    │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │                                                           │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │   │
│  │  │  DynamoDB    │  │ FMP API      │  │ OpenAI/      │  │   │
│  │  │  (AWS)       │  │ (Financial)  │  │ DeepSeek     │  │   │
│  │  │              │  │              │  │ (AI Models)  │  │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  │   │
│  │                                                           │   │
│  │  ┌──────────────┐  ┌──────────────┐                     │   │
│  │  │Illumenti     │  │Crypto Search │                     │   │
│  │  │Equity Search │  │   Engine     │                     │   │
│  │  └──────────────┘  └──────────────┘                     │   │
│  │                                                           │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Agent Communication Flow

### Daimon Agent (Financial Analysis)
```
User Input → Daimon Endpoint → Chat Service → Classification Service
                                                      ↓
                                              Extract Symbols & Intent
                                                      ↓
                                              Dynamo Service
                                                      ↓
                                              Fetch Financial Data
                                                      ↓
                                              Widget Service
                                                      ↓
                                          Generate Visualization
                                                      ↓
                                              Response to User
```

### Weaver Agent (Information Gathering)
```
User Input → Weaver Endpoint → Weaver Service → Parse Query
                                                      ↓
                                              Identify Topics
                                                      ↓
                                          Parallel API Calls
                                         (ThreadPoolExecutor)
                                        ↙        ↓        ↘
                                   FMP API    API 2    API 3
                                        ↘        ↓        ↙
                                          Combine Results
                                                ↓
                                        AI Synthesis
                                                ↓
                                          Response to User
```

### Legacy Chat Flow (Backward Compatible)
```
User Input → /chat Endpoint → Process Chat Request → Same as Daimon
                    ↓
            Check for Commands
                    ↓
            /weaver? → Weaver Service
                    ↓
            Default → Chat Service (Daimon)
```

---

## Data Flow Diagram

```
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │ HTTP Request
       ▼
┌─────────────┐
│  Flask App  │
└──────┬──────┘
       │
       ├─→ CORS Middleware
       ├─→ Error Handler
       │
       ▼
┌─────────────┐
│   Routing   │
└──────┬──────┘
       │
       ├─→ Legacy Routes (main.py)
       ├─→ API Blueprints (api/)
       │
       ▼
┌─────────────┐
│  Services   │
└──────┬──────┘
       │
       ├─→ Classification
       ├─→ Data Fetch
       ├─→ AI Processing
       ├─→ Widget Generation
       │
       ▼
┌─────────────┐
│ External    │
│ APIs & DB   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Response   │
│  (JSON)     │
└─────────────┘
```

---

## Module Dependency Graph

```
main.py
  ↓
create_app() [__init__.py]
  ├─→ config.py (Configuration)
  ├─→ extensions.py (DynamoDB, Search)
  ├─→ middleware/
  │    ├─→ cors.py
  │    └─→ error_handlers.py
  ├─→ api/
  │    ├─→ chat.py
  │    ├─→ equity.py
  │    ├─→ crypto.py
  │    ├─→ data.py
  │    └─→ health.py
  └─→ views.py (Template routes)

api/chat.py
  ├─→ services/chat_service.py
  └─→ services/weaver_service.py

services/chat_service.py
  ├─→ services/classification_service.py
  ├─→ services/dynamo_service.py
  └─→ services/widget_service.py

services/weaver_service.py
  ├─→ apis/fmp_api.py
  └─→ apis/reasoning.py
```

---

## File Size Comparison

### Before Refactoring
```
main.py:          ~500 lines   ████████████████████
__init__.py:      ~150 lines   ████████
```

### After Refactoring
```
main.py:          ~150 lines   ████████
__init__.py:      ~60 lines    ███
config.py:        ~90 lines    ████
extensions.py:    ~60 lines    ███
api/chat.py:      ~160 lines   ████████
api/equity.py:    ~30 lines    ██
api/crypto.py:    ~40 lines    ██
api/data.py:      ~50 lines    ███
api/health.py:    ~40 lines    ██
services/chat_service.py:          ~80 lines    ████
services/weaver_service.py:        ~120 lines   ██████
services/classification_service.py: ~80 lines    ████
services/widget_service.py:        ~80 lines    ████
services/dynamo_service.py:        ~100 lines   █████
middleware/cors.py:                ~30 lines    ██
middleware/error_handlers.py:      ~50 lines    ███
```

**Result**: Better organized, easier to find code, each file has single responsibility

---

## Request Lifecycle

### Example: User asks "Tell me about Apple stock"

```
1. Browser → POST /api/chat/daimon
   Body: {"message": "Tell me about Apple stock"}

2. Flask receives request
   ↓
3. CORS middleware adds headers
   ↓
4. Routes to api/chat.py → daimon_chat()
   ↓
5. Calls services/chat_service.py → process_chat_request()
   ↓
6. Classification Service
   - Extracts: symbols=["AAPL"], intent="Company analysis"
   ↓
7. DynamoDB Service
   - Fetches: Apple financial data for today
   ↓
8. Widget Service
   - Generates: Enhanced response with widget references
   ↓
9. Response sent to browser
   {
     "message": "Apple analysis with {leadership_widget:AAPL:company}...",
     "data": [{ symbol: "AAPL", price: 180.50, ... }]
   }
   ↓
10. Browser displays formatted response in chat
```

---

## Scaling Considerations

### Current Architecture Supports:

1. **Horizontal Scaling**
   - Stateless design
   - No in-memory sessions
   - Ready for load balancers

2. **Vertical Scaling**
   - Modular services
   - Can separate to microservices
   - Easy to add caching

3. **Feature Scaling**
   - New agents = new endpoint + service
   - New data sources = new service module
   - New UI = new template + static files

### Easy Additions:

```
api/
  └─ chat.py
      ├─ /api/chat/daimon    ✅ Done
      ├─ /api/chat/weaver    ✅ Done
      ├─ /api/chat/avvocato  ✅ Ready
      ├─ /api/chat/sophon    ✅ Ready
      └─ /api/chat/newagent  ⬜ Add here

services/
  └─ newagent_service.py     ⬜ Add business logic

templates/
  └─ anglenexus.html         ⬜ Add UI component
```

---

## Configuration Management

```
Environment
  ↓
config.py reads .env
  ↓
Config class (DevelopmentConfig, ProductionConfig, TestingConfig)
  ↓
get_config() returns appropriate config
  ↓
Used throughout application

Example:
  Config.DEFAULT_MODEL → "o3-mini"
  Config.AWS_REGION → "us-east-1"
  Config.ALLOWED_MODELS → ["o3-mini", "GPT-4o", ...]
```

---

## Error Handling Flow

```
Error occurs anywhere
  ↓
Exception raised
  ↓
Middleware catches
  ↓
error_handlers.py
  ├─ ValidationError → 400 response
  ├─ 404 Not Found → 404 response
  ├─ 500 Server Error → 500 response
  └─ Generic Exception → 500 response
  ↓
Logger records error
  ↓
User receives formatted JSON error
  {
    "error": "Descriptive message",
    "status": 400/404/500
  }
```

---

## Key Design Patterns Used

1. **Blueprint Pattern** - Modular routing
2. **Service Layer Pattern** - Business logic separation
3. **Factory Pattern** - App creation
4. **Middleware Pattern** - Cross-cutting concerns
5. **Repository Pattern** - Data access (DynamoDB service)
6. **Strategy Pattern** - Different AI models
7. **Facade Pattern** - Service layer simplifies complexity

---

This architecture ensures:
✅ Maintainability
✅ Scalability
✅ Testability
✅ Flexibility
✅ Performance
✅ Security (ready for auth)
✅ Monitoring (ready for metrics)
