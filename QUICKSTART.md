# 🚀 Quick Start Guide

## Prerequisites
- Python 3.9 or higher
- MongoDB 4.4 or higher
- Groq API Key (get from https://console.groq.com)

## Step-by-Step Setup

### 1. Install Python Dependencies

```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

Edit the `.env` file and add your Groq API key:

```env
GROQ_API_KEY=gsk_your_actual_groq_api_key_here
```

### 3. Start MongoDB

Ensure MongoDB is running:

```powershell
# Windows (if installed as service)
net start MongoDB

# Or check if already running
Get-Process mongod
```

### 4. Run the Application

```powershell
cd app
python main.py
```

The server will start at: `http://localhost:8000`

### 5. Access API Documentation

Open your browser and visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🧪 Testing the API

### Option 1: Use the Test Script

```powershell
.\test_api.ps1
```

### Option 2: Manual Testing via Swagger UI

1. Go to http://localhost:8000/docs
2. Try the `/auth/register` endpoint to create a user
3. Copy the access token from the response
4. Click "Authorize" button at the top
5. Paste the token and click "Authorize"
6. Now you can test all protected endpoints

### Option 3: Using cURL/PowerShell

**Register a student:**
```powershell
$body = @{
    name = "John Doe"
    email = "john@example.com"
    password = "securepass123"
    role = "student"
    institution = "MIT"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/register" `
    -Method Post `
    -Body $body `
    -ContentType "application/json"
```

**Login:**
```powershell
$body = @{
    email = "john@example.com"
    password = "securepass123"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" `
    -Method Post `
    -Body $body `
    -ContentType "application/json"

$token = $response.data.access_token
```

**Get Profile:**
```powershell
$headers = @{
    "Authorization" = "Bearer $token"
}

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/profile" `
    -Method Get `
    -Headers $headers
```

**Ask AI a Question:**
```powershell
$body = @{
    question = "What is machine learning?"
    query_type = "explain"
    subject = "Computer Science"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/ai/query" `
    -Method Post `
    -Body $body `
    -Headers $headers `
    -ContentType "application/json"
```

## 📝 Sample API Flows

### Student Flow

1. **Register** → `/api/v1/auth/register` (role: student)
2. **Login** → `/api/v1/auth/login`
3. **Ask Question** → `/api/v1/students/ask-question`
4. **Take Test** → `/api/v1/students/take-mock-test/{test_id}`
5. **Book Session** → `/api/v1/students/book-session`

### Faculty Flow

1. **Register** → `/api/v1/auth/register` (role: faculty)
2. **Wait for Admin Verification** → Faculty needs verification
3. **Create Test** → `/api/v1/faculties/create-test`
4. **Generate Questions with AI** → `/api/v1/faculties/generate-test-questions`
5. **Answer Queries** → `/api/v1/faculties/answer-query/{query_id}`

### Admin Flow

1. **Register** → `/api/v1/auth/register` (role: admin)
2. **Verify Faculty** → `/api/v1/admin/verify-faculty/{user_id}`
3. **View Reports** → `/api/v1/admin/reports/overview`

## 🎯 Key Features to Try

### 1. AI-Powered Q&A
```json
POST /api/v1/ai/query
{
  "question": "Explain photosynthesis",
  "query_type": "explain",
  "subject": "Biology"
}
```

### 2. Generate Quiz Questions
```json
POST /api/v1/faculties/generate-test-questions?topic=Python&num_questions=5
```

### 3. Summarize Text
```json
POST /api/v1/ai/summarize
{
  "text": "Your long educational content here...",
  "subject": "Physics"
}
```

### 4. Book a Session
```json
POST /api/v1/students/book-session
{
  "faculty_id": "faculty_user_id_here",
  "scheduled_time": "2025-11-01T10:00:00",
  "duration_minutes": 60,
  "topic": "Advanced Machine Learning",
  "amount": 500.0
}
```

## 🔧 Troubleshooting

### MongoDB Connection Error
```
Error: Could not connect to MongoDB
```
**Solution**: Ensure MongoDB is running on `localhost:27017`

### Groq API Error
```
Error: Invalid API key
```
**Solution**: Check your `GROQ_API_KEY` in `.env` file

### Import Errors
```
ModuleNotFoundError: No module named 'fastapi'
```
**Solution**: Activate virtual environment and reinstall dependencies
```powershell
.\venv\Scripts\activate
pip install -r requirements.txt
```

### Port Already in Use
```
Error: Address already in use
```
**Solution**: Change port in `main.py` or kill the process using port 8000

## 📚 Default User Roles

After registration:
- **Students**: Automatically verified
- **Faculty**: Requires admin verification
- **Admin**: Automatically verified (create admin user first)

## 🔐 Security Notes

⚠️ **Important for Production:**
1. Change `SECRET_KEY` in `.env`
2. Use strong passwords
3. Enable HTTPS
4. Restrict CORS origins
5. Add rate limiting
6. Use environment-specific configs

## 📞 Need Help?

- Check the full documentation: `README.md`
- View API docs: http://localhost:8000/docs
- Check logs in the terminal

## 🎉 You're Ready!

Your StudyFriend backend is now running. Start building your frontend or test the API!
