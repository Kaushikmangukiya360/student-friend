# 🧪 Testing Guide - Complete Endpoint Testing

## Quick Test Script

A comprehensive bash script that tests **all 40 API endpoints** end-to-end with automatic token management and ID assignment.

## 📋 What It Tests

### Authentication & Users (7 tests)
1. Health check
2. Student registration
3. Student login
4. Faculty registration
5. Faculty login
6. Admin registration
7. Admin login
8. Get student profile

### Admin Operations (6 tests)
9. Verify faculty
34. Get pending faculties
35. Get platform overview
36. Get test analytics
37. Get transaction reports
38. Get user activity

### Materials & Content (3 tests)
10. Upload study material
11. Get all materials

### Questions & Queries (5 tests)
12. Ask question (AI-powered)
13. Get student's questions
30. Faculty get queries
31. Faculty answer query
40. Get AI query history

### Tests & Assignments (9 tests)
14. Faculty create test
15. Get available tests
16. Student take test
17. Get test results
18. Faculty create assignment
19. Get student assignments
32. Faculty get assignments
33. Faculty get tests

### AI Features (3 tests)
20. AI explain concept
21. AI generate quiz
22. AI summarize text

### Payments & Wallet (4 tests)
23. Initiate payment
24. Verify payment
25. Get wallet balance
39. Get transaction history

### Sessions (4 tests)
26. Book session
27. Get student sessions
28. Get faculty sessions
29. Faculty update session

## 🚀 How to Use

### On Windows (Git Bash / WSL)

```bash
# Make script executable
chmod +x test_all_endpoints.sh

# Run the script
./test_all_endpoints.sh
```

### On Linux/Mac

```bash
# Make script executable
chmod +x test_all_endpoints.sh

# Run the script
./test_all_endpoints.sh
```

### Using Git Bash on Windows

```bash
# Navigate to project directory
cd /d/StudyFriend

# Run script
bash test_all_endpoints.sh
```

## 📊 Script Features

### ✅ Automatic Token Management
- Registers/logs in users automatically
- Stores tokens for subsequent requests
- Uses appropriate tokens for each role

### ✅ ID Tracking
- Extracts and stores IDs from responses:
  - Student ID
  - Faculty ID
  - Admin ID
  - Material ID
  - Query ID
  - Test ID
  - Assignment ID
  - Session ID
  - Payment ID & Order ID

### ✅ Color-Coded Output
- 🟢 Green: Success messages
- 🔴 Red: Error messages
- 🔵 Blue: Info messages
- 🟡 Yellow: Warnings
- 🔷 Cyan: Section headers

### ✅ Error Handling
- Exits on critical errors
- Skips optional tests if dependencies missing
- Shows detailed error responses

## 📝 Prerequisites

1. **Server Running**
   ```bash
   cd app
   python main.py
   ```

2. **Dependencies**
   - `curl` - HTTP client
   - `grep` - Text search
   - `sed` - Text processing
   - `bash` - Shell (4.0+)

3. **MongoDB Running**
   ```bash
   # Windows
   net start MongoDB
   
   # Linux/Mac
   sudo systemctl start mongod
   ```

## 🎯 Expected Output

```
========================================
🚀 StudyFriend API - Complete End-to-End Testing
========================================

ℹ️  Base URL: http://localhost:8000/api/v1
ℹ️  Started at: Thu Oct 30 15:30:00 2025

========================================
TEST 1: Health Check
========================================

✅ Health check passed
{"status":"healthy","environment":"development"}

========================================
TEST 2: Register Student
========================================

✅ Student registered successfully
ℹ️  Student ID: 507f1f77bcf86cd799439011
ℹ️  Token: eyJhbGciOiJIUzI1NiIsInR5cCI...

[... 38 more tests ...]

========================================
🎉 Testing Complete!
========================================

ℹ️  Finished at: Thu Oct 30 15:32:00 2025

========================================
All 40 endpoint tests completed!
========================================

ℹ️  Generated IDs Summary:
Student ID: 507f1f77bcf86cd799439011
Faculty ID: 507f1f77bcf86cd799439012
Admin ID: 507f1f77bcf86cd799439013
Material ID: 507f1f77bcf86cd799439014
Query ID: 507f1f77bcf86cd799439015
Test ID: 507f1f77bcf86cd799439016
Assignment ID: 507f1f77bcf86cd799439017
Session ID: sess_abc123def456
Payment ID: pay_xyz789abc123
```

## 🔧 Customization

### Change Base URL
Edit the script:
```bash
BASE_URL="http://your-server:8000/api/v1"
```

### Add More Tests
Add new test functions following the pattern:
```bash
test_my_endpoint() {
    print_header "TEST XX: My Custom Test"
    
    response=$(curl -s -X POST "$BASE_URL/my-endpoint" \
        -H "Authorization: Bearer $STUDENT_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"data": "value"}')
    
    if [[ $response == *"success\":true"* ]]; then
        print_success "Test passed"
    else
        print_error "Test failed"
    fi
}
```

Then add to `main()`:
```bash
main() {
    # ... existing tests ...
    test_my_endpoint
}
```

## 🐛 Troubleshooting

### Issue: Permission Denied
```bash
chmod +x test_all_endpoints.sh
```

### Issue: curl not found
```bash
# Windows (using Chocolatey)
choco install curl

# Linux (Ubuntu/Debian)
sudo apt-get install curl

# Mac
brew install curl
```

### Issue: Script fails at authentication
- Check if server is running
- Verify MongoDB is running
- Check .env file has GROQ_API_KEY

### Issue: JSON parsing errors
- Install GNU grep and sed
- On Windows, use Git Bash or WSL

## 📊 Test Coverage

| Category | Endpoints | Coverage |
|----------|-----------|----------|
| Authentication | 4 | ✅ 100% |
| Students | 9 | ✅ 100% |
| Faculty | 8 | ✅ 100% |
| AI | 4 | ✅ 100% |
| Admin | 6 | ✅ 100% |
| Payment | 5 | ✅ 100% |
| **Total** | **40** | **✅ 100%** |

## 🎉 Benefits

✅ **End-to-End Testing** - Tests complete user flows
✅ **Automated** - No manual token/ID management
✅ **Comprehensive** - Covers all 40 endpoints
✅ **Reusable** - Run anytime to verify API
✅ **CI/CD Ready** - Can be integrated into pipelines
✅ **Color Coded** - Easy to read results
✅ **Error Handling** - Graceful failures

## 📚 Related Documentation

- `API_EXAMPLES.md` - Individual API examples
- `QUICKSTART.md` - Getting started guide
- `README.md` - Complete documentation

---

**Happy Testing! 🧪**
