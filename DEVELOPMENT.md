# 🛠️ Development Guide - StudyFriend Backend

## 🏁 Getting Started

### Prerequisites Check
```powershell
# Check Python
python --version  # Should be 3.9+

# Check MongoDB
Get-Process mongod  # Should show mongod process

# Check pip
pip --version
```

### Installation
```powershell
# 1. Navigate to project
cd d:\StudyFriend

# 2. Run setup script (recommended)
.\setup.ps1

# 3. Update .env with your Groq API key
code .env  # or notepad .env
```

---

## 🚀 Running the Application

### Development Mode
```powershell
# Activate virtual environment
.\venv\Scripts\activate

# Run with auto-reload
cd app
python main.py

# Or using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode
```powershell
# Without auto-reload
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# Or with Gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

---

## 🧪 Testing

### Manual Testing
```powershell
# Run test script
.\test_api.ps1

# Test health endpoint
Invoke-RestMethod http://localhost:8000/health
```

### Interactive Testing
1. Start the server
2. Open http://localhost:8000/docs
3. Try the endpoints
4. Use "Authorize" button for protected routes

### Postman Testing
1. Import `StudyFriend.postman_collection.json`
2. Set `base_url` variable
3. Register a user
4. Copy token to `token` variable
5. Test all endpoints

---

## 📝 Common Development Tasks

### Adding a New Endpoint

1. **Create route function in appropriate file**:
```python
# app/routes/student_routes.py

@router.get("/my-new-endpoint")
async def my_new_endpoint(
    current_user: dict = Depends(get_current_user)
):
    db = get_database()
    # Your logic here
    return success_response(data={}, message="Success")
```

2. **Test it**:
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/students/my-new-endpoint" `
    -Headers @{"Authorization" = "Bearer YOUR_TOKEN"}
```

### Adding a New Model

1. **Create Pydantic model**:
```python
# app/db/models/new_model.py

from pydantic import BaseModel, Field
from datetime import datetime

class NewModel(BaseModel):
    title: str
    description: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

2. **Use in routes**:
```python
from app.db.models.new_model import NewModel

@router.post("/create")
async def create_item(item: NewModel):
    # Your logic
    pass
```

### Adding a New Service

1. **Create service file**:
```python
# app/services/new_service.py

class NewService:
    def __init__(self):
        pass
    
    async def do_something(self, param: str) -> dict:
        # Your logic
        return {"result": "success"}

new_service = NewService()
```

2. **Use in routes**:
```python
from app.services.new_service import new_service

@router.post("/action")
async def perform_action():
    result = await new_service.do_something("param")
    return success_response(data=result)
```

---

## 🗄️ Database Operations

### Connecting to MongoDB
```powershell
# MongoDB Shell
mongosh

# Use database
use studyfriend_db

# View collections
show collections

# Query users
db.users.find().pretty()
```

### Common Queries
```javascript
// Find all students
db.users.find({role: "student"})

// Find pending sessions
db.sessions.find({status: "pending"})

// Count total tests
db.mock_tests.countDocuments()

// Delete test user
db.users.deleteOne({email: "student@test.com"})
```

### Indexes (Recommended)
```javascript
// Create indexes for better performance
db.users.createIndex({email: 1}, {unique: true})
db.queries.createIndex({asked_by: 1, timestamp: -1})
db.sessions.createIndex({student_id: 1, faculty_id: 1})
db.test_attempts.createIndex({student_id: 1, test_id: 1})
```

---

## 🐛 Debugging

### Enable Debug Logs
```python
# In app/main.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check Database Connection
```python
# Test script
from app.db.connection import connect_to_mongo
import asyncio

async def test():
    await connect_to_mongo()
    print("Connected!")

asyncio.run(test())
```

### Test Groq API
```python
# Test AI service
from app.services.ai_service import ai_service
import asyncio

async def test():
    result = await ai_service.answer_question("What is Python?")
    print(result)

asyncio.run(test())
```

---

## 🔧 Configuration

### Environment Variables
```env
# Development
ENVIRONMENT=development
MONGODB_URL=mongodb://localhost:27017

# Production
ENVIRONMENT=production
MONGODB_URL=mongodb://user:pass@mongodb-server:27017
SECRET_KEY=complex-production-secret
```

### Changing Ports
```python
# In app/main.py
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8080,  # Change port here
        reload=True
    )
```

---

## 📦 Managing Dependencies

### Adding New Package
```powershell
# Activate venv
.\venv\Scripts\activate

# Install package
pip install package-name

# Update requirements
pip freeze > requirements.txt
```

### Updating Packages
```powershell
# Update all
pip install --upgrade -r requirements.txt

# Update specific
pip install --upgrade fastapi
```

---

## 🔐 Security Best Practices

### Production Checklist
- [ ] Change SECRET_KEY in .env
- [ ] Use strong passwords
- [ ] Enable HTTPS
- [ ] Restrict CORS origins
- [ ] Add rate limiting
- [ ] Enable MongoDB authentication
- [ ] Use environment-specific configs
- [ ] Set up logging
- [ ] Regular backups

### Example: Restrict CORS
```python
# In app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Specific domains
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

---

## 📊 Monitoring

### Health Checks
```powershell
# Basic health
Invoke-RestMethod http://localhost:8000/health

# Database check (custom endpoint)
Invoke-RestMethod http://localhost:8000/health/db
```

### Logs
```powershell
# View logs in terminal where server is running
# Or redirect to file
python main.py > app.log 2>&1
```

---

## 🚢 Deployment

### Docker (Optional)
```dockerfile
# Dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```powershell
# Build and run
docker build -t studyfriend-api .
docker run -p 8000:8000 --env-file .env studyfriend-api
```

### Using systemd (Linux)
```ini
# /etc/systemd/system/studyfriend.service
[Unit]
Description=StudyFriend API
After=network.target

[Service]
User=www-data
WorkingDirectory=/opt/studyfriend
Environment="PATH=/opt/studyfriend/venv/bin"
ExecStart=/opt/studyfriend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000

[Install]
WantedBy=multi-user.target
```

---

## 🧹 Maintenance

### Clean Database
```javascript
// MongoDB shell
use studyfriend_db

// Delete test data
db.users.deleteMany({email: /test\.com$/})
db.queries.deleteMany({asked_by: "test_user_id"})
```

### Reset Database
```javascript
// CAUTION: Deletes everything!
use studyfriend_db
db.dropDatabase()
```

### Backup Database
```powershell
# Backup
mongodump --db studyfriend_db --out ./backup

# Restore
mongorestore --db studyfriend_db ./backup/studyfriend_db
```

---

## 💡 Tips & Tricks

### Faster Development
```powershell
# Use aliases
Set-Alias run "python app/main.py"
Set-Alias test ".\test_api.ps1"

# Then just run
run
test
```

### VS Code Settings
```json
{
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true
}
```

### Auto-format Code
```powershell
# Install black
pip install black

# Format all files
black app/
```

---

## 🆘 Troubleshooting

### Problem: Port Already in Use
```powershell
# Find process using port 8000
Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess

# Kill it
Stop-Process -Id <PID>
```

### Problem: MongoDB Connection Failed
```powershell
# Start MongoDB
net start MongoDB

# Or check status
Get-Service MongoDB
```

### Problem: Import Errors
```powershell
# Reinstall dependencies
pip install --force-reinstall -r requirements.txt

# Or recreate venv
Remove-Item -Recurse venv
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### Problem: Groq API Errors
- Check API key in .env
- Verify internet connection
- Check Groq API status: https://status.groq.com
- Review rate limits

---

## 📚 Additional Resources

- **FastAPI Docs**: https://fastapi.tiangolo.com
- **MongoDB Docs**: https://docs.mongodb.com
- **LangChain Docs**: https://docs.langchain.com
- **Groq Docs**: https://console.groq.com/docs
- **Pydantic Docs**: https://docs.pydantic.dev

---

## 🤝 Contributing

### Code Style
- Follow PEP 8
- Use type hints
- Write docstrings
- Keep functions small
- Use async/await

### Git Workflow
```powershell
# Create branch
git checkout -b feature/new-feature

# Make changes
# ...

# Commit
git add .
git commit -m "Add: new feature description"

# Push
git push origin feature/new-feature
```

---

**Happy Coding! 🚀**
