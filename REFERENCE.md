# 🎴 StudyFriend API - Quick Reference Card

## 🚀 Quick Start
```powershell
.\setup.ps1                    # Setup everything
cd app && python main.py      # Run server
.\test_api.ps1                # Test API
```

## 🌐 URLs
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs
- **Health**: http://localhost:8000/health

## 🔑 Default Test Credentials
```json
{
  "student": "student@test.com / password123",
  "faculty": "faculty@test.com / password123"
}
```

## 📋 Essential Endpoints

### Auth
- `POST /api/v1/auth/register` - Register
- `POST /api/v1/auth/login` - Login
- `GET /api/v1/auth/profile` - Profile

### Students
- `POST /api/v1/students/ask-question` - Ask AI
- `POST /api/v1/students/take-mock-test/{id}` - Test
- `POST /api/v1/students/book-session` - Session

### Faculty
- `POST /api/v1/faculties/create-test` - Create test
- `POST /api/v1/faculties/generate-test-questions` - AI gen
- `POST /api/v1/faculties/answer-query/{id}` - Answer

### AI
- `POST /api/v1/ai/query` - AI query (multi-purpose)
- `POST /api/v1/ai/summarize` - Summarize
- `POST /api/v1/ai/explain` - Explain

### Admin
- `GET /api/v1/admin/reports/overview` - Dashboard
- `POST /api/v1/admin/verify-faculty/{id}` - Verify

## 🔐 Authentication Header
```
Authorization: Bearer eyJhbGci...
```

## 📦 Response Format
```json
{
  "success": true,
  "message": "Operation successful",
  "data": {}
}
```

## 🗄️ Database Collections
- users, materials, queries, mock_tests
- test_attempts, assignments, sessions
- transactions, notifications, payments

## 🐛 Quick Debug
```powershell
# Check MongoDB
Get-Process mongod

# Check Python
python --version

# Check .env
Get-Content .env

# View logs
# (terminal where server runs)
```

## 🧪 Quick Test
```powershell
# Register
Invoke-RestMethod http://localhost:8000/api/v1/auth/register `
  -Method Post -ContentType "application/json" `
  -Body '{"name":"Test","email":"test@ex.com","password":"pass123","role":"student"}'

# Health
Invoke-RestMethod http://localhost:8000/health
```

## 📚 Documentation Files
- **README.md** - Complete guide
- **QUICKSTART.md** - Getting started
- **API_EXAMPLES.md** - API usage
- **ARCHITECTURE.md** - System design
- **DEVELOPMENT.md** - Dev guide
- **PROJECT_SUMMARY.md** - Overview

## 🛠️ Common Commands
```powershell
# Activate venv
.\venv\Scripts\activate

# Install deps
pip install -r requirements.txt

# Run server
python app/main.py

# Format code
black app/

# MongoDB shell
mongosh
```

## 🔧 Environment Variables
```env
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=studyfriend_db
SECRET_KEY=your-secret-key
GROQ_API_KEY=your-groq-key
```

## 📊 Key Features
✅ JWT Authentication
✅ Role-based Access
✅ AI Q&A (Groq)
✅ Test Management
✅ Session Booking
✅ Payment System
✅ Admin Dashboard

## 🚨 Troubleshooting
| Issue | Solution |
|-------|----------|
| Port in use | `Stop-Process -Id <PID>` |
| MongoDB error | `net start MongoDB` |
| Import error | Reinstall requirements |
| API key error | Check .env GROQ_API_KEY |

## 📞 Support
- API Docs: /docs
- ReDoc: /redoc
- Postman: Import collection file

---
**Version**: 1.0.0  
**Last Updated**: October 30, 2025  
**Status**: Production Ready ✅
