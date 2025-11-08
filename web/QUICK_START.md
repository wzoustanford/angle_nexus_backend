# 🚀 Quick Start Guide - AngleNexus

## Immediate Testing Steps

### 1. Start the Server
```bash
cd /Users/foluwa/Downloads/_projects/illumenti/angle/angle_backend
python -m web.main
```

### 2. Test Legacy Endpoints (Verify Nothing Broke)

#### A. Test Health Check (NEW)
```bash
curl http://localhost:5001/api/health
```
Expected: `{"status":"healthy","service":"AngleNexus API","version":"v1"}`

#### B. Test Legacy Chat
```bash
curl -X POST http://localhost:5001/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Tell me about Apple stock"}'
```

#### C. Test Legacy Equity Search
```bash
curl "http://localhost:5001/equity-api?query=apple"
```

#### D. Test Legacy Crypto Search
```bash
curl "http://localhost:5001/crypto-api?query=bitcoin"
```

### 3. Test New API Endpoints

#### A. Test Daimon Agent
```bash
curl -X POST http://localhost:5001/api/chat/daimon \
  -H "Content-Type: application/json" \
  -d '{"message": "Analyze Apple and Microsoft", "model_name": "o3-mini"}'
```

#### B. Test Weaver Agent
```bash
curl -X POST http://localhost:5001/api/chat/weaver \
  -H "Content-Type: application/json" \
  -d '{"message": "Get latest earnings for Tesla", "model_name": "o3-mini"}'
```

#### C. Test New Equity API
```bash
curl "http://localhost:5001/api/equity/search?query=tesla"
```

#### D. Test Status Endpoint
```bash
curl http://localhost:5001/api/status
```

### 4. Test UI Interfaces

#### A. Open Legacy Interface
```
http://localhost:5001/
```
- Should see the Illumenti landing page
- All existing functionality should work

#### B. Open AngleNexus Interface (NEW)
```
http://localhost:5001/anglenexus
```
- Should see modern dark theme with agents
- Try chatting with Daimon agent
- Try chatting with Avvocato agent

---

## 🎯 What to Verify

### Legacy Functionality ✓
- [ ] Old `/` homepage loads correctly
- [ ] Old `/chat` endpoint processes requests
- [ ] Search functionality works
- [ ] All API responses match previous format
- [ ] No console errors in browser

### New Functionality ✓
- [ ] `/anglenexus` page loads with styling
- [ ] Daimon chat button toggles chat window
- [ ] Can send messages to Daimon
- [ ] Avvocato chat works similarly
- [ ] Chat messages appear correctly
- [ ] Loading indicators work
- [ ] Error handling works

### API Structure ✓
- [ ] `/api/health` returns healthy status
- [ ] `/api/status` shows configuration
- [ ] CORS headers present on all responses
- [ ] Error responses are properly formatted

---

## 🐛 Troubleshooting

### If Server Won't Start

**Check Python Path:**
```bash
python --version  # Should be 3.8+
```

**Check Dependencies:**
```bash
pip install -r requirements.txt
```

**Check Environment Variables:**
```bash
cat .env  # Verify all keys are present
```

### If AngleNexus Page Won't Load

**Verify Static Files:**
```bash
ls -la angle_backend/web/static/css/anglenexus.css
ls -la angle_backend/web/static/js/anglenexus.js
```

**Check Browser Console:**
- Open DevTools (F12)
- Look for 404 errors on CSS/JS files
- Check for JavaScript errors

### If Chat Doesn't Work

**Check API Endpoint:**
```bash
# Test if endpoint responds
curl -X POST http://localhost:5001/api/chat/daimon \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}'
```

**Check Browser Network Tab:**
- Open DevTools → Network
- Send a chat message
- Look for failed requests (red)
- Check request/response details

### If Legacy Routes Break

**Check main.py imports:**
```python
# These should all work:
from web import create_app, iSearch, iCryptoSearch, fetch_data_from_dynamo
```

**Check extensions.py:**
```python
# DynamoDB should be initialized
from .extensions import iSearch, iCryptoSearch, equity_table
```

---

## 📊 Expected Performance

### API Response Times
- **Health Check**: < 50ms
- **Simple Chat**: 2-5 seconds (AI processing)
- **Weaver Agent**: 5-15 seconds (external API calls)
- **Search Endpoints**: < 200ms

### Browser Performance
- **Page Load**: < 2 seconds
- **Chat Open Animation**: 500ms
- **Message Send**: Instant (+ AI response time)

---

## 🔍 Key Files to Check

### Configuration
```
web/config.py          - All settings
web/.env               - Environment variables
```

### Services
```
web/services/chat_service.py          - Main chat logic
web/services/weaver_service.py        - Weaver agent
web/services/dynamo_service.py        - Database access
```

### API Routes
```
web/api/chat.py        - Chat endpoints
web/api/equity.py      - Equity endpoints
web/api/crypto.py      - Crypto endpoints
```

### Frontend
```
web/templates/anglenexus.html         - Main template
web/static/css/anglenexus.css         - Styles
web/static/js/anglenexus.js           - Chat logic
```

---

## ✅ Success Indicators

You know everything is working when:

1. ✅ Server starts without errors
2. ✅ `/api/health` returns healthy status
3. ✅ Old homepage (`/`) loads correctly
4. ✅ New AngleNexus page (`/anglenexus`) loads with all styles
5. ✅ Daimon agent responds to messages
6. ✅ Legacy `/chat` endpoint still works
7. ✅ No console errors in browser
8. ✅ All API calls return proper JSON

---

## 🎉 Next Steps After Verification

1. **Run Full Test Suite** (if you have tests)
2. **Update Documentation** with new endpoints
3. **Deploy to Staging** for team review
4. **Gather Feedback** on new interface
5. **Plan Sophon Agent** implementation
6. **Enhance Avvocato** with legal features
7. **Add Authentication** if needed
8. **Implement Analytics** tracking

---

## 📞 Quick Commands Reference

```bash
# Start server
python -m web.main

# Test health
curl http://localhost:5001/api/health

# Test Daimon
curl -X POST http://localhost:5001/api/chat/daimon \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}'

# Check logs
tail -f logs/app.log  # If you have logging setup

# View all routes
# Add this to main.py temporarily:
# for rule in app.url_map.iter_rules():
#     print(rule)
```

---

**Ready to Test!** 🚀

Start the server and begin testing from Step 1 above.
