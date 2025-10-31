# API Examples - StudyFriend

Complete collection of API request/response examples.

## Base URL
```
http://localhost:8000/api/v1
```

## Authentication

### 1. Register Student
**Request:**
```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "name": "Alice Johnson",
  "email": "alice@university.edu",
  "password": "securepass123",
  "role": "student",
  "institution": "MIT"
}
```

**Response:**
```json
{
  "success": true,
  "message": "User registered successfully",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "user": {
      "id": "507f1f77bcf86cd799439011",
      "name": "Alice Johnson",
      "email": "alice@university.edu",
      "role": "student",
      "institution": "MIT",
      "verified": true,
      "wallet_balance": 0.0,
      "created_at": "2025-10-30T10:00:00"
    }
  }
}
```

### 2. Login
**Request:**
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "alice@university.edu",
  "password": "securepass123"
}
```

### 3. Get Profile
**Request:**
```http
GET /api/v1/auth/profile
Authorization: Bearer YOUR_TOKEN
```

## Student Endpoints

### 4. Upload Material
**Request:**
```http
POST /api/v1/students/upload-material
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json

{
  "title": "Introduction to Machine Learning",
  "description": "Comprehensive guide to ML basics",
  "file_url": "https://example.com/ml-intro.pdf",
  "subject": "Computer Science",
  "tags": ["machine-learning", "ai", "python"],
  "visibility": "public"
}
```

### 5. Ask Question
**Request:**
```http
POST /api/v1/students/ask-question
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json

{
  "question_text": "What is the difference between supervised and unsupervised learning?",
  "subject": "Machine Learning"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Question answered successfully",
  "data": {
    "id": "507f1f77bcf86cd799439012",
    "question": "What is the difference between supervised and unsupervised learning?",
    "answer": "Supervised learning uses labeled data where the algorithm learns from input-output pairs...",
    "answered_by": "AI"
  }
}
```

### 6. Get Available Tests
**Request:**
```http
GET /api/v1/students/tests?subject=Python
Authorization: Bearer YOUR_TOKEN
```

### 7. Submit Test
**Request:**
```http
POST /api/v1/students/take-mock-test/507f1f77bcf86cd799439013
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json

{
  "answers": [0, 2, 1, 3, 0]
}
```

**Response:**
```json
{
  "success": true,
  "message": "Test submitted successfully",
  "data": {
    "test_title": "Python Basics Quiz",
    "score": 4,
    "total_marks": 5,
    "percentage": 80.0,
    "detailed_results": [
      {
        "question_number": 1,
        "question_text": "What is Python?",
        "submitted_answer": 0,
        "correct_answer": 0,
        "is_correct": true,
        "marks_obtained": 1,
        "total_marks": 1
      }
    ]
  }
}
```

### 8. Book Session
**Request:**
```http
POST /api/v1/students/book-session
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json

{
  "faculty_id": "507f1f77bcf86cd799439014",
  "scheduled_time": "2025-11-05T14:00:00",
  "duration_minutes": 60,
  "topic": "Advanced Data Structures",
  "amount": 500.0
}
```

## Faculty Endpoints

### 9. Create Assignment
**Request:**
```http
POST /api/v1/faculties/create-assignment
Authorization: Bearer FACULTY_TOKEN
Content-Type: application/json

{
  "title": "Data Structures Assignment",
  "description": "Implement a binary search tree",
  "subject": "Computer Science",
  "total_marks": 100,
  "assigned_to": ["507f1f77bcf86cd799439011"],
  "due_date": "2025-11-15T23:59:59"
}
```

### 10. Create Test
**Request:**
```http
POST /api/v1/faculties/create-test
Authorization: Bearer FACULTY_TOKEN
Content-Type: application/json

{
  "test_title": "Python Fundamentals",
  "description": "Basic Python concepts test",
  "subject": "Python",
  "duration_minutes": 30,
  "total_marks": 10,
  "questions": [
    {
      "question_text": "What is Python?",
      "options": [
        "A programming language",
        "A snake",
        "A database",
        "An operating system"
      ],
      "correct_answer": 0,
      "marks": 2
    }
  ]
}
```

### 11. Generate Quiz Questions (AI)
**Request:**
```http
POST /api/v1/faculties/generate-test-questions?topic=JavaScript&num_questions=5
Authorization: Bearer FACULTY_TOKEN
```

**Response:**
```json
{
  "success": true,
  "message": "Questions generated successfully",
  "data": {
    "topic": "JavaScript",
    "questions": [
      {
        "question_text": "What is JavaScript?",
        "options": [
          "A programming language for web development",
          "A coffee brand",
          "A Java framework",
          "A markup language"
        ],
        "correct_answer": 0,
        "marks": 1
      }
    ]
  }
}
```

### 12. Answer Student Query
**Request:**
```http
POST /api/v1/faculties/answer-query/507f1f77bcf86cd799439015
Authorization: Bearer FACULTY_TOKEN
Content-Type: application/json

{
  "answer_text": "The key difference is that supervised learning requires labeled training data..."
}
```

### 13. Update Session Status
**Request:**
```http
PATCH /api/v1/faculties/update-session/sess_abc123
Authorization: Bearer FACULTY_TOKEN
Content-Type: application/json

{
  "status": "accepted",
  "meeting_link": "https://meet.google.com/abc-defg-hij",
  "notes": "Looking forward to discussing advanced topics"
}
```

## AI Assistant Endpoints

### 14. AI Query (Multi-purpose)
**Request (Q&A):**
```http
POST /api/v1/ai/query
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json

{
  "question": "Explain the concept of Big O notation",
  "query_type": "explain",
  "subject": "Algorithms"
}
```

**Request (Summarize):**
```http
POST /api/v1/ai/query
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json

{
  "question": "Summarize this",
  "context": "Long educational text about quantum physics...",
  "query_type": "summarize",
  "subject": "Physics"
}
```

**Request (Generate Quiz):**
```http
POST /api/v1/ai/query
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json

{
  "question": "React Hooks",
  "query_type": "generate_quiz",
  "subject": "React"
}
```

### 15. Summarize Text
**Request:**
```http
POST /api/v1/ai/summarize
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json

{
  "text": "Photosynthesis is a process used by plants...",
  "subject": "Biology"
}
```

### 16. Explain Concept
**Request:**
```http
POST /api/v1/ai/explain?concept=Recursion
Authorization: Bearer YOUR_TOKEN
```

## Admin Endpoints

### 17. Verify Faculty
**Request:**
```http
POST /api/v1/admin/verify-faculty/507f1f77bcf86cd799439014
Authorization: Bearer ADMIN_TOKEN
```

### 18. Get Platform Overview
**Request:**
```http
GET /api/v1/admin/reports/overview
Authorization: Bearer ADMIN_TOKEN
```

**Response:**
```json
{
  "success": true,
  "message": "Platform overview retrieved successfully",
  "data": {
    "users": {
      "total_students": 150,
      "total_faculties": 25,
      "verified_faculties": 20,
      "pending_faculties": 5
    },
    "content": {
      "total_materials": 350,
      "total_queries": 1200,
      "total_tests": 85,
      "total_assignments": 120
    },
    "sessions": {
      "total_sessions": 200,
      "completed_sessions": 180,
      "pending_sessions": 15,
      "completion_rate": 90.0
    }
  }
}
```

### 19. Get Test Analytics
**Request:**
```http
GET /api/v1/admin/reports/test-analytics?test_id=507f1f77bcf86cd799439013
Authorization: Bearer ADMIN_TOKEN
```

### 20. Get User Activity
**Request:**
```http
GET /api/v1/admin/reports/user-activity/507f1f77bcf86cd799439011
Authorization: Bearer ADMIN_TOKEN
```

## Payment Endpoints

### 21. Initiate Payment
**Request:**
```http
POST /api/v1/payment/initiate
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json

{
  "amount": 1000.0,
  "purpose": "wallet_recharge",
  "metadata": {
    "payment_method": "card"
  }
}
```

### 22. Verify Payment
**Request:**
```http
POST /api/v1/payment/verify
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json

{
  "payment_id": "pay_abc123",
  "order_id": "order_xyz789",
  "signature": "mock_signature"
}
```

### 23. Get Wallet Balance
**Request:**
```http
GET /api/v1/payment/wallet
Authorization: Bearer YOUR_TOKEN
```

### 24. Get Transaction History
**Request:**
```http
GET /api/v1/payment/transactions?limit=20
Authorization: Bearer YOUR_TOKEN
```

## Error Responses

### 401 Unauthorized
```json
{
  "success": false,
  "message": "Invalid authentication credentials",
  "details": {
    "status_code": 401
  }
}
```

### 403 Forbidden
```json
{
  "success": false,
  "message": "Access denied. Required roles: faculty",
  "details": {
    "status_code": 403
  }
}
```

### 404 Not Found
```json
{
  "success": false,
  "message": "User not found",
  "details": {
    "status_code": 404
  }
}
```

### 400 Bad Request
```json
{
  "success": false,
  "message": "Invalid request data",
  "details": {
    "status_code": 400
  }
}
```

## Notes

- All timestamps are in ISO 8601 format (UTC)
- IDs are MongoDB ObjectIds (24-character hex strings)
- Tokens expire after 24 hours (configurable)
- File uploads should be handled separately (not shown here)
- All responses follow the standard format: `{success, message, data}`
