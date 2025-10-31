# StudyFriend - System Architecture

## 🏗️ High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Client Layer                         │
│  (Web App / Mobile App / Postman / Any HTTP Client)         │
└───────────────────────┬─────────────────────────────────────┘
                        │ HTTPS/REST
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Application                       │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              Middleware Layer                         │  │
│  │  - CORS Handler                                       │  │
│  │  - JWT Authentication                                 │  │
│  │  - Exception Handler                                  │  │
│  └───────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              API Routes                               │  │
│  │  /auth  /students  /faculties  /ai  /admin  /payment │  │
│  └───────────────────────────────────────────────────────┘  │
└───────────────────────┬─────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
┌──────────────┐ ┌─────────────┐ ┌────────────────┐
│   Services   │ │  Database   │ │  External API  │
│              │ │             │ │                │
│ • AI Service │ │  MongoDB    │ │  Groq API      │
│ • Payment    │ │             │ │  (LangChain)   │
│ • Test Eval  │ │  Collections│ │                │
└──────────────┘ └─────────────┘ └────────────────┘
```

## 📦 Component Architecture

### 1. Core Layer (`app/core/`)

**config.py**
- Environment configuration management
- Settings validation
- Centralized configuration access

**auth.py**
- JWT verification middleware
- Role-based access control
- Current user extraction

### 2. Database Layer (`app/db/`)

**connection.py**
- MongoDB connection management (Motor async client)
- Database lifecycle (connect/disconnect)
- Database instance provider

**models/** (Pydantic schemas)
- `user_model.py`: User registration, login, profile
- `material_model.py`: Study materials schema
- `query_model.py`: Q&A schema
- `test_model.py`: Tests, assignments, submissions
- `session_model.py`: Sessions, transactions, notifications

### 3. Routes Layer (`app/routes/`)

Each route file handles specific domain endpoints:

**auth_routes.py**
- User registration
- Login/logout
- Profile management
- Account verification

**student_routes.py**
- Material access and upload
- Question submission
- Test taking
- Session booking
- Assignment viewing

**faculty_routes.py**
- Material creation
- Assignment management
- Test creation
- Query answering
- Session management

**ai_routes.py**
- AI-powered Q&A
- Text summarization
- Concept explanation
- Quiz generation

**admin_routes.py**
- Faculty verification
- Platform analytics
- User management
- Transaction reports

**payment_routes.py**
- Payment initiation
- Payment verification
- Refund processing
- Wallet management

### 4. Services Layer (`app/services/`)

**ai_service.py**
- LangChain integration
- Groq API communication
- Multiple AI chains:
  - Question answering
  - Summarization
  - Quiz generation
  - Concept explanation

**payment_service.py**
- Mock payment processing
- Payment verification
- Refund handling
- Transaction creation

**test_service.py**
- Test evaluation logic
- Score calculation
- Analytics generation
- Performance reports

### 5. Utils Layer (`app/utils/`)

**jwt_handler.py**
- Token creation
- Token validation
- Token decoding

**helpers.py**
- Password hashing
- Standard response formatting
- Utility functions
- File management

## 🔄 Data Flow Diagrams

### Student Asks Question Flow

```
Student → POST /students/ask-question
    │
    ├─→ Validate JWT Token
    │
    ├─→ Call AI Service
    │       │
    │       ├─→ LangChain Chain
    │       │       │
    │       │       └─→ Groq API
    │       │
    │       └─→ Return AI Response
    │
    ├─→ Store Query in MongoDB
    │       - question_text
    │       - asked_by
    │       - answer_text
    │       - answered_by: "AI"
    │
    └─→ Return Response to Student
```

### Session Booking Flow

```
Student → POST /students/book-session
    │
    ├─→ Validate JWT & Check Balance
    │
    ├─→ Verify Faculty Exists & Verified
    │
    ├─→ Create Session Record
    │       - status: pending
    │       - payment_status: pending
    │
    ├─→ Deduct from Student Wallet
    │
    ├─→ Create Transaction Record
    │
    ├─→ Notify Faculty
    │       - Send notification
    │
    └─→ Return Session Details

Faculty → PATCH /faculties/update-session/{id}
    │
    ├─→ Validate JWT & Ownership
    │
    ├─→ Update Session Status
    │       - accepted/rejected
    │
    ├─→ If Rejected → Refund Student
    │       - Credit wallet
    │       - Create refund transaction
    │
    ├─→ Notify Student
    │
    └─→ Return Updated Session
```

### Test Submission Flow

```
Student → POST /students/take-mock-test/{test_id}
    │
    ├─→ Validate JWT Token
    │
    ├─→ Fetch Test from MongoDB
    │
    ├─→ Call Test Service
    │       │
    │       ├─→ Compare Answers
    │       │
    │       ├─→ Calculate Score
    │       │
    │       └─→ Generate Detailed Results
    │
    ├─→ Store Test Attempt
    │       - student_id
    │       - answers
    │       - score
    │       - percentage
    │
    └─→ Return Results to Student
```

## 🗄️ Database Schema

### Collections Overview

```
studyfriend_db
├── users
│   ├── _id (ObjectId)
│   ├── name
│   ├── email (unique)
│   ├── role (student/faculty/admin)
│   ├── hashed_password
│   ├── verified
│   ├── wallet_balance
│   └── created_at
│
├── materials
│   ├── _id
│   ├── title
│   ├── description
│   ├── file_url
│   ├── uploaded_by (user_id)
│   ├── subject
│   ├── tags []
│   ├── visibility
│   └── timestamp
│
├── queries
│   ├── _id
│   ├── question_text
│   ├── asked_by (user_id)
│   ├── answered_by (user_id or "AI")
│   ├── answer_text
│   ├── answered_by_type (ai/faculty)
│   ├── timestamp
│   └── answered_at
│
├── mock_tests
│   ├── _id
│   ├── test_title
│   ├── description
│   ├── subject
│   ├── duration_minutes
│   ├── total_marks
│   ├── questions []
│   │   ├── question_text
│   │   ├── options []
│   │   ├── correct_answer
│   │   └── marks
│   ├── created_by (user_id)
│   └── created_at
│
├── test_attempts
│   ├── _id
│   ├── test_id
│   ├── student_id
│   ├── answers []
│   ├── score
│   ├── total_marks
│   ├── percentage
│   ├── started_at
│   └── submitted_at
│
├── assignments
│   ├── _id
│   ├── title
│   ├── description
│   ├── subject
│   ├── total_marks
│   ├── created_by (faculty_id)
│   ├── assigned_to [] (student_ids)
│   ├── due_date
│   ├── submissions []
│   └── created_at
│
├── sessions
│   ├── _id
│   ├── session_id (unique)
│   ├── student_id
│   ├── faculty_id
│   ├── scheduled_time
│   ├── duration_minutes
│   ├── topic
│   ├── amount
│   ├── status (pending/accepted/rejected/completed)
│   ├── payment_status
│   ├── meeting_link
│   └── created_at
│
├── transactions
│   ├── _id
│   ├── user_id
│   ├── amount
│   ├── type (credit/debit)
│   ├── purpose
│   ├── reference_id
│   └── timestamp
│
├── notifications
│   ├── _id
│   ├── user_id
│   ├── message
│   ├── type (info/success/warning/error)
│   ├── read_status
│   └── timestamp
│
└── payments
    ├── _id
    ├── payment_id (unique)
    ├── order_id
    ├── user_id
    ├── amount
    ├── status
    ├── purpose
    └── created_at
```

## 🔐 Security Architecture

### Authentication Flow

```
1. User Registration
   ↓
   Password → bcrypt hash → Store in DB

2. User Login
   ↓
   Verify password → Generate JWT
   ↓
   JWT payload: {user_id, email, role, exp}
   ↓
   Sign with SECRET_KEY → Return token

3. Protected Request
   ↓
   Extract token from Authorization header
   ↓
   Verify signature & expiration
   ↓
   Extract user_id and role
   ↓
   Check role permissions
   ↓
   Allow/Deny access
```

### Role-Based Access Control

```
┌────────────────────────────────────────────┐
│           Permission Matrix                │
├────────────┬──────────┬──────────┬─────────┤
│ Endpoint   │ Student  │ Faculty  │ Admin   │
├────────────┼──────────┼──────────┼─────────┤
│ Register   │    ✓     │    ✓     │    ✓    │
│ Login      │    ✓     │    ✓     │    ✓    │
│ Upload Mat │    ✓     │    ✓     │    ✗    │
│ Ask Quest  │    ✓     │    ✗     │    ✗    │
│ Take Test  │    ✓     │    ✗     │    ✗    │
│ Create Test│    ✗     │    ✓*    │    ✗    │
│ Answer Q   │    ✗     │    ✓*    │    ✗    │
│ Verify Fac │    ✗     │    ✗     │    ✓    │
│ Reports    │    ✗     │    ✗     │    ✓    │
└────────────┴──────────┴──────────┴─────────┘
* Requires verification
```

## 🤖 AI Integration Architecture

### LangChain + Groq Pipeline

```
User Request
    │
    ├─→ Question Answering
    │       │
    │       ├─→ Prompt Template
    │       │   "You are an educational assistant..."
    │       │
    │       ├─→ LLMChain
    │       │
    │       └─→ Groq API (mixtral-8x7b)
    │
    ├─→ Summarization
    │       │
    │       ├─→ Text Splitter (if > 10k chars)
    │       │
    │       ├─→ Load Summarize Chain
    │       │
    │       └─→ Groq API
    │
    ├─→ Quiz Generation
    │       │
    │       ├─→ Prompt Template
    │       │   "Generate N questions for topic..."
    │       │
    │       ├─→ LLMChain
    │       │
    │       ├─→ Groq API
    │       │
    │       └─→ Parse Questions
    │
    └─→ Concept Explanation
            │
            ├─→ Prompt Template
            │   "Explain concept for students..."
            │
            └─→ Groq API
```

## 📊 Scalability Considerations

### Horizontal Scaling

```
Load Balancer
    │
    ├─→ FastAPI Instance 1
    │
    ├─→ FastAPI Instance 2
    │
    └─→ FastAPI Instance N
            │
            └─→ MongoDB (Replica Set)
```

### Caching Strategy (Future)

```
Request → Check Cache → Cache Hit? → Return
                            │
                            No
                            ↓
                        MongoDB → Store in Cache → Return
```

### Background Jobs (Future)

```
Task Queue (Celery/RQ)
    │
    ├─→ Send Email Notifications
    ├─→ Generate Reports
    ├─→ Process Large Files
    └─→ Cleanup Old Data
```

## 🔄 API Request Lifecycle

```
1. HTTP Request arrives
   ↓
2. CORS Middleware
   ↓
3. JWT Authentication (if protected)
   ↓
4. Route Handler
   ↓
5. Input Validation (Pydantic)
   ↓
6. Business Logic
   │
   ├─→ Database Operations
   ├─→ External API Calls
   └─→ Service Layer
   ↓
7. Response Formatting
   ↓
8. Exception Handling (if error)
   ↓
9. HTTP Response
```

## 🛠️ Technology Stack Summary

| Layer | Technology |
|-------|-----------|
| API Framework | FastAPI 0.109+ |
| Database | MongoDB 4.4+ |
| ODM | Motor (async) |
| AI Framework | LangChain |
| LLM Provider | Groq API |
| Authentication | JWT (python-jose) |
| Password Hash | bcrypt (passlib) |
| Validation | Pydantic v2 |
| ASGI Server | Uvicorn |

## 📈 Performance Optimization

1. **Async Operations**: All I/O operations are async
2. **Connection Pooling**: Motor handles MongoDB connection pooling
3. **Efficient Queries**: Indexed fields (email, timestamps)
4. **Pagination**: Limit results with `.to_list(limit)`
5. **Response Optimization**: Only return necessary fields

## 🔮 Future Enhancements

1. **WebSocket Support**: Real-time notifications
2. **File Upload Service**: S3/CloudStorage integration
3. **Email Service**: Verification emails, notifications
4. **Rate Limiting**: Prevent API abuse
5. **Caching**: Redis for frequent queries
6. **Background Tasks**: Celery for async jobs
7. **Monitoring**: Prometheus + Grafana
8. **Logging**: ELK Stack integration

---

This architecture provides a solid foundation for a scalable, maintainable educational platform.
