# StudyFriend - Student-Faculty Learning Platform

A comprehensive backend API built with FastAPI, MongoDB, LangChain, and Groq AI for connecting students and faculty in an educational ecosystem.

## 🎯 Features

### For Students
- 📚 Upload and access study materials
- ❓ Ask questions (answered by AI or faculty)
- 📝 Take mock tests with auto-evaluation
- 👥 Book 1:1 sessions with verified faculty
- 📊 View test results and performance analytics
- 💰 Wallet system for session payments

### For Faculty
- 📤 Upload educational materials
- ✏️ Create assignments and mock tests
- 🤖 Generate quiz questions using AI
- 💬 Answer student queries
- 👨‍🏫 Conduct paid 1:1 sessions
- 📈 View session and assignment analytics

### For Admins
- ✅ Verify faculty accounts
- 📊 Platform analytics and reports
- 👥 User activity monitoring
- 💳 Transaction reports

### AI-Powered Features (LangChain + Groq)
- 🤖 Intelligent Q&A assistant
- 📝 Material summarization
- 💡 Concept explanations
- 🎯 Auto-generate quiz questions

## 🛠️ Tech Stack

- **Framework**: FastAPI
- **Database**: MongoDB (Motor for async operations)
- **AI**: LangChain + Groq API
- **Authentication**: JWT-based
- **Payment**: Mock integration (Razorpay/Stripe ready)

## 📁 Project Structure

```
app/
├── main.py                     # FastAPI application entry point
├── core/
│   ├── config.py              # Configuration settings
│   └── auth.py                # Authentication middleware
├── db/
│   ├── connection.py          # MongoDB connection
│   └── models/
│       ├── user_model.py      # User schemas
│       ├── material_model.py  # Material schemas
│       ├── query_model.py     # Query schemas
│       ├── test_model.py      # Test & assignment schemas
│       └── session_model.py   # Session & transaction schemas
├── routes/
│   ├── auth_routes.py         # Authentication endpoints
│   ├── student_routes.py      # Student endpoints
│   ├── faculty_routes.py      # Faculty endpoints
│   ├── ai_routes.py           # AI assistant endpoints
│   ├── admin_routes.py        # Admin endpoints
│   └── payment_routes.py      # Payment endpoints
├── services/
│   ├── ai_service.py          # LangChain + Groq integration
│   ├── payment_service.py     # Payment processing
│   └── test_service.py        # Test evaluation
└── utils/
    ├── jwt_handler.py         # JWT token management
    └── helpers.py             # Utility functions
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- MongoDB 4.4+
- Groq API Key

### Installation

1. **Clone the repository**
```bash
cd d:\StudyFriend
```

2. **Create virtual environment**
```bash
python -m venv venv
.\venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
Copy-Item .env.example .env
```

Edit `.env` file with your configuration:
```env
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=studyfriend_db
SECRET_KEY=your-secret-key-change-this
GROQ_API_KEY=your-groq-api-key
```

5. **Start MongoDB**
```bash
# Make sure MongoDB is running on your system
# Windows: Start MongoDB service
# Linux/Mac: sudo systemctl start mongod
```

6. **Run the application**
```bash
cd app
python main.py
```

Or using uvicorn:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

7. **Access the API**
- API: http://localhost:8000
- Interactive Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 📚 API Endpoints

### Authentication (`/api/v1/auth`)
- `POST /register` - Register new user
- `POST /login` - User login
- `GET /profile` - Get current user profile
- `GET /verify/{user_id}` - Verify user (admin only)

### Students (`/api/v1/students`)
- `POST /upload-material` - Upload study material
- `GET /materials` - Get accessible materials
- `POST /ask-question` - Ask a question
- `GET /my-questions` - Get user's questions
- `GET /tests` - Get available tests
- `POST /take-mock-test/{test_id}` - Submit test
- `GET /my-test-results` - Get test results
- `POST /book-session` - Book faculty session
- `GET /my-sessions` - Get booked sessions
- `GET /assignments` - Get assignments

### Faculty (`/api/v1/faculties`)
- `POST /upload-material` - Upload material
- `POST /create-assignment` - Create assignment
- `POST /create-test` - Create mock test
- `POST /generate-test-questions` - AI-generate questions
- `GET /unanswered-queries` - Get queries
- `POST /answer-query/{query_id}` - Answer query
- `GET /my-sessions` - Get sessions
- `PATCH /update-session/{session_id}` - Update session
- `GET /my-assignments` - Get created assignments
- `GET /my-tests` - Get created tests

### AI Assistant (`/api/v1/ai`)
- `POST /query` - AI-powered query (Q&A, summarize, explain, quiz)
- `POST /summarize` - Summarize text
- `POST /generate-quiz` - Generate quiz questions
- `POST /explain` - Explain concept
- `GET /query-history` - Get AI query history

### Admin (`/api/v1/admin`)
- `POST /verify-faculty/{user_id}` - Verify faculty
- `GET /pending-faculties` - Get unverified faculty
- `GET /reports/overview` - Platform overview
- `GET /reports/test-analytics` - Test analytics
- `GET /reports/transactions` - Transaction report
- `GET /reports/user-activity/{user_id}` - User activity
- `DELETE /users/{user_id}` - Delete user

### Payment (`/api/v1/payment`)
- `POST /initiate` - Initiate payment
- `POST /verify` - Verify payment
- `POST /refund/{payment_id}` - Process refund
- `GET /wallet` - Get wallet balance
- `GET /transactions` - Get transaction history

## 🔐 Authentication

All protected endpoints require JWT token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

### Role-based Access Control
- **Student**: Can access student endpoints
- **Faculty**: Can access faculty endpoints (requires verification)
- **Admin**: Full access to all endpoints

## 🤖 AI Integration

The platform uses **LangChain** with **Groq API** for:

1. **Question Answering**: Intelligent responses to student queries
2. **Summarization**: Summarize educational materials
3. **Quiz Generation**: Auto-generate test questions
4. **Concept Explanation**: Detailed explanations of topics

### Example AI Query

```json
POST /api/v1/ai/query
{
  "question": "Explain photosynthesis",
  "query_type": "explain",
  "subject": "Biology"
}
```

## 💳 Payment Flow

1. Student books session → Amount deducted from wallet
2. Faculty receives notification
3. Faculty accepts/rejects session
4. If rejected → Automatic refund
5. If completed → Payment confirmed

### Mock Payment Endpoints
Current implementation uses mock payments. To integrate real payment:
- Replace `payment_service.py` with actual Razorpay/Stripe SDK calls
- Add webhook handlers for payment notifications

## 🗄️ Database Collections

- **users**: User accounts (students, faculty, admin)
- **materials**: Study materials
- **queries**: Questions and answers
- **mock_tests**: Test definitions
- **test_attempts**: Test submissions
- **assignments**: Assignment details
- **sessions**: 1:1 session bookings
- **transactions**: Payment transactions
- **notifications**: User notifications
- **payments**: Payment records

## 🧪 Testing

### Create Test User

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Student",
    "email": "student@test.com",
    "password": "password123",
    "role": "student",
    "institution": "Test University"
  }'
```

### Test AI Query

```bash
curl -X POST "http://localhost:8000/api/v1/ai/query" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is machine learning?",
    "query_type": "explain"
  }'
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MONGODB_URL` | MongoDB connection string | `mongodb://localhost:27017` |
| `DATABASE_NAME` | Database name | `studyfriend_db` |
| `SECRET_KEY` | JWT secret key | Required |
| `GROQ_API_KEY` | Groq API key | Required |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiry | `1440` (24 hours) |
| `UPLOAD_DIR` | File upload directory | `./uploads` |

## 📊 Response Format

### Success Response
```json
{
  "success": true,
  "message": "Operation successful",
  "data": { }
}
```

### Error Response
```json
{
  "success": false,
  "message": "Error message",
  "details": { }
}
```

## 🚀 Deployment

### Using Uvicorn
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Using Gunicorn
```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Docker (Optional)
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 🔒 Security Best Practices

1. Change `SECRET_KEY` in production
2. Use strong passwords
3. Enable HTTPS in production
4. Restrict CORS origins
5. Implement rate limiting
6. Regular security audits
7. Keep dependencies updated

## 🐛 Troubleshooting

### MongoDB Connection Error
- Ensure MongoDB is running
- Check connection string in `.env`
- Verify network connectivity

### Groq API Error
- Verify API key is correct
- Check API rate limits
- Ensure internet connectivity

### Import Errors
- Activate virtual environment
- Reinstall dependencies: `pip install -r requirements.txt`

## 📝 License

This project is for educational purposes.

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

## 📧 Support

For issues and questions, please open an issue in the repository.

---

Built with ❤️ using FastAPI, MongoDB, LangChain, and Groq AI
