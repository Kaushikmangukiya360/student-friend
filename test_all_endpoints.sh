#!/bin/bash

# StudyFriend API - Complete End-to-End Test Script
# Tests all endpoints with automatic token and ID management

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Base URLs
BASE_URL="http://localhost:8000/api/v1"
HEALTH_URL="http://localhost:8000/health"

# Global variables for tokens and IDs
STUDENT_TOKEN=""
STUDENT_ID=""
FACULTY_TOKEN=""
FACULTY_ID=""
ADMIN_TOKEN=""
ADMIN_ID=""
MATERIAL_ID=""
QUERY_ID=""
TEST_ID=""
ASSIGNMENT_ID=""
SESSION_ID=""
PAYMENT_ID=""
ORDER_ID=""

# Helper function to print colored output
print_header() {
    echo -e "\n${CYAN}========================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Helper function to extract JSON values
extract_json_value() {
    echo "$1" | grep -o "\"$2\"[[:space:]]*:[[:space:]]*\"[^\"]*\"" | sed 's/.*"\([^"]*\)".*/\1/' | head -1
}

extract_json_bool() {
    echo "$1" | grep -o "\"$2\"[[:space:]]*:[[:space:]]*[a-z]*" | sed 's/.*:[[:space:]]*//' | head -1
}

# Test health endpoint
test_health() {
    print_header "TEST 1: Health Check"
    
    response=$(curl -s -X GET "$HEALTH_URL")
    
    if [[ $response == *"healthy"* ]]; then
        print_success "Health check passed"
        echo "$response" | head -c 200
    else
        print_error "Health check failed"
        exit 1
    fi
}

# Test student registration
test_student_registration() {
    print_header "TEST 2: Register Student"
    
    response=$(curl -s -X POST "$BASE_URL/auth/register" \
        -H "Content-Type: application/json" \
        -d '{
            "name": "Alice Student",
            "email": "alice.student@test.com",
            "password": "student123",
            "role": "student",
            "institution": "MIT"
        }')
    
    if [[ $response == *"success\":true"* ]] || [[ $response == *"already registered"* ]]; then
        STUDENT_TOKEN=$(extract_json_value "$response" "access_token")
        STUDENT_ID=$(extract_json_value "$response" "id")
        
        if [ -z "$STUDENT_TOKEN" ]; then
            print_warning "Student already exists, attempting login..."
            test_student_login
        else
            print_success "Student registered successfully"
            print_info "Student ID: $STUDENT_ID"
            print_info "Token: ${STUDENT_TOKEN:0:30}..."
        fi
    else
        print_error "Student registration failed"
        echo "$response"
    fi
}

# Test student login
test_student_login() {
    print_header "TEST 3: Student Login"
    
    response=$(curl -s -X POST "$BASE_URL/auth/login" \
        -H "Content-Type: application/json" \
        -d '{
            "email": "alice.student@test.com",
            "password": "student123"
        }')
    
    STUDENT_TOKEN=$(extract_json_value "$response" "access_token")
    STUDENT_ID=$(extract_json_value "$response" "id")
    
    if [ ! -z "$STUDENT_TOKEN" ]; then
        print_success "Student login successful"
        print_info "Student ID: $STUDENT_ID"
        print_info "Token: ${STUDENT_TOKEN:0:30}..."
    else
        print_error "Student login failed"
        echo "$response"
        exit 1
    fi
}

# Test faculty registration
test_faculty_registration() {
    print_header "TEST 4: Register Faculty"
    
    response=$(curl -s -X POST "$BASE_URL/auth/register" \
        -H "Content-Type: application/json" \
        -d '{
            "name": "Dr. Bob Faculty",
            "email": "bob.faculty@test.com",
            "password": "faculty123",
            "role": "faculty",
            "institution": "Stanford"
        }')
    
    if [[ $response == *"success\":true"* ]] || [[ $response == *"already registered"* ]]; then
        FACULTY_TOKEN=$(extract_json_value "$response" "access_token")
        FACULTY_ID=$(extract_json_value "$response" "id")
        
        if [ -z "$FACULTY_TOKEN" ]; then
            print_warning "Faculty already exists, attempting login..."
            test_faculty_login
        else
            print_success "Faculty registered successfully"
            print_info "Faculty ID: $FACULTY_ID"
            print_info "Token: ${FACULTY_TOKEN:0:30}..."
        fi
    else
        print_error "Faculty registration failed"
        echo "$response"
    fi
}

# Test faculty login
test_faculty_login() {
    print_header "TEST 5: Faculty Login"
    
    response=$(curl -s -X POST "$BASE_URL/auth/login" \
        -H "Content-Type: application/json" \
        -d '{
            "email": "bob.faculty@test.com",
            "password": "faculty123"
        }')
    
    FACULTY_TOKEN=$(extract_json_value "$response" "access_token")
    FACULTY_ID=$(extract_json_value "$response" "id")
    
    if [ ! -z "$FACULTY_TOKEN" ]; then
        print_success "Faculty login successful"
        print_info "Faculty ID: $FACULTY_ID"
        print_info "Token: ${FACULTY_TOKEN:0:30}..."
    else
        print_error "Faculty login failed"
        echo "$response"
        exit 1
    fi
}

# Test admin registration
test_admin_registration() {
    print_header "TEST 6: Register Admin"
    
    response=$(curl -s -X POST "$BASE_URL/auth/register" \
        -H "Content-Type: application/json" \
        -d '{
            "name": "Admin User",
            "email": "admin@test.com",
            "password": "admin123",
            "role": "admin",
            "institution": "Platform"
        }')
    
    if [[ $response == *"success\":true"* ]] || [[ $response == *"already registered"* ]]; then
        ADMIN_TOKEN=$(extract_json_value "$response" "access_token")
        ADMIN_ID=$(extract_json_value "$response" "id")
        
        if [ -z "$ADMIN_TOKEN" ]; then
            print_warning "Admin already exists, attempting login..."
            test_admin_login
        else
            print_success "Admin registered successfully"
            print_info "Admin ID: $ADMIN_ID"
            print_info "Token: ${ADMIN_TOKEN:0:30}..."
        fi
    else
        print_error "Admin registration failed"
        echo "$response"
    fi
}

# Test admin login
test_admin_login() {
    print_header "TEST 7: Admin Login"
    
    response=$(curl -s -X POST "$BASE_URL/auth/login" \
        -H "Content-Type: application/json" \
        -d '{
            "email": "admin@test.com",
            "password": "admin123"
        }')
    
    ADMIN_TOKEN=$(extract_json_value "$response" "access_token")
    ADMIN_ID=$(extract_json_value "$response" "id")
    
    if [ ! -z "$ADMIN_TOKEN" ]; then
        print_success "Admin login successful"
        print_info "Admin ID: $ADMIN_ID"
        print_info "Token: ${ADMIN_TOKEN:0:30}..."
    else
        print_error "Admin login failed"
        echo "$response"
        exit 1
    fi
}

# Test get student profile
test_student_profile() {
    print_header "TEST 8: Get Student Profile"
    
    response=$(curl -s -X GET "$BASE_URL/auth/profile" \
        -H "Authorization: Bearer $STUDENT_TOKEN")
    
    if [[ $response == *"success\":true"* ]]; then
        print_success "Student profile retrieved"
        echo "$response" | head -c 300
    else
        print_error "Failed to get student profile"
        echo "$response"
    fi
}

# Test admin verify faculty
test_verify_faculty() {
    print_header "TEST 9: Admin Verify Faculty"
    
    response=$(curl -s -X POST "$BASE_URL/admin/verify-faculty/$FACULTY_ID" \
        -H "Authorization: Bearer $ADMIN_TOKEN")
    
    if [[ $response == *"success\":true"* ]]; then
        print_success "Faculty verified by admin"
    else
        print_error "Faculty verification failed"
        echo "$response"
    fi
}

# Test student upload material
test_student_upload_material() {
    print_header "TEST 10: Student Upload Material"
    
    response=$(curl -s -X POST "$BASE_URL/students/upload-material" \
        -H "Authorization: Bearer $STUDENT_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
            "title": "Introduction to Python",
            "description": "Complete Python programming guide for beginners",
            "file_url": "https://example.com/python-intro.pdf",
            "subject": "Programming",
            "tags": ["python", "programming", "beginner"],
            "visibility": "public"
        }')
    
    MATERIAL_ID=$(extract_json_value "$response" "id")
    
    if [[ $response == *"success\":true"* ]]; then
        print_success "Material uploaded successfully"
        print_info "Material ID: $MATERIAL_ID"
    else
        print_error "Material upload failed"
        echo "$response"
    fi
}

# Test get materials
test_get_materials() {
    print_header "TEST 11: Get Study Materials"
    
    response=$(curl -s -X GET "$BASE_URL/students/materials" \
        -H "Authorization: Bearer $STUDENT_TOKEN")
    
    if [[ $response == *"success\":true"* ]]; then
        print_success "Materials retrieved successfully"
        material_count=$(echo "$response" | grep -o "\"id\"" | wc -l)
        print_info "Total materials: $material_count"
    else
        print_error "Failed to get materials"
        echo "$response"
    fi
}

# Test student ask question
test_ask_question() {
    print_header "TEST 12: Student Ask Question (AI)"
    
    response=$(curl -s -X POST "$BASE_URL/students/ask-question" \
        -H "Authorization: Bearer $STUDENT_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
            "question_text": "What is the difference between supervised and unsupervised learning?",
            "subject": "Machine Learning"
        }')
    
    QUERY_ID=$(extract_json_value "$response" "id")
    
    if [[ $response == *"success\":true"* ]]; then
        print_success "Question asked and answered by AI"
        print_info "Query ID: $QUERY_ID"
        echo "$response" | head -c 400
    else
        print_error "Failed to ask question"
        echo "$response"
    fi
}

# Test get student questions
test_get_my_questions() {
    print_header "TEST 13: Get Student's Questions"
    
    response=$(curl -s -X GET "$BASE_URL/students/my-questions" \
        -H "Authorization: Bearer $STUDENT_TOKEN")
    
    if [[ $response == *"success\":true"* ]]; then
        print_success "Questions retrieved successfully"
        question_count=$(echo "$response" | grep -o "\"id\"" | wc -l)
        print_info "Total questions: $question_count"
    else
        print_error "Failed to get questions"
        echo "$response"
    fi
}

# Test faculty create test
test_faculty_create_test() {
    print_header "TEST 14: Faculty Create Mock Test"
    
    response=$(curl -s -X POST "$BASE_URL/faculties/create-test" \
        -H "Authorization: Bearer $FACULTY_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
            "test_title": "Python Fundamentals Quiz",
            "description": "Test your Python basics",
            "subject": "Python",
            "duration_minutes": 30,
            "total_marks": 10,
            "questions": [
                {
                    "question_text": "What is Python?",
                    "options": ["A programming language", "A snake", "A database", "An OS"],
                    "correct_answer": 0,
                    "marks": 2
                },
                {
                    "question_text": "Which keyword is used for function in Python?",
                    "options": ["function", "def", "func", "define"],
                    "correct_answer": 1,
                    "marks": 2
                },
                {
                    "question_text": "What is the output of print(2 ** 3)?",
                    "options": ["6", "8", "9", "5"],
                    "correct_answer": 1,
                    "marks": 2
                },
                {
                    "question_text": "Which of these is a mutable data type?",
                    "options": ["tuple", "string", "list", "int"],
                    "correct_answer": 2,
                    "marks": 2
                },
                {
                    "question_text": "What does PEP stand for?",
                    "options": ["Python Enhancement Proposal", "Python Execution Plan", "Python Editor Plugin", "Python Educational Program"],
                    "correct_answer": 0,
                    "marks": 2
                }
            ]
        }')
    
    TEST_ID=$(extract_json_value "$response" "id")
    
    if [[ $response == *"success\":true"* ]]; then
        print_success "Test created successfully"
        print_info "Test ID: $TEST_ID"
    else
        print_error "Test creation failed"
        echo "$response"
    fi
}

# Test get available tests
test_get_available_tests() {
    print_header "TEST 15: Get Available Tests"
    
    response=$(curl -s -X GET "$BASE_URL/students/tests" \
        -H "Authorization: Bearer $STUDENT_TOKEN")
    
    if [[ $response == *"success\":true"* ]]; then
        print_success "Tests retrieved successfully"
        test_count=$(echo "$response" | grep -o "\"id\"" | wc -l)
        print_info "Total tests available: $test_count"
        
        # Extract first test ID if we don't have one
        if [ -z "$TEST_ID" ] && [ $test_count -gt 0 ]; then
            TEST_ID=$(echo "$response" | grep -o "\"id\"[[:space:]]*:[[:space:]]*\"[^\"]*\"" | head -1 | sed 's/.*"\([^"]*\)".*/\1/')
            print_info "Using Test ID: $TEST_ID"
        fi
    else
        print_error "Failed to get tests"
        echo "$response"
    fi
}

# Test student take test
test_student_take_test() {
    print_header "TEST 16: Student Take Mock Test"
    
    if [ -z "$TEST_ID" ]; then
        print_warning "No test ID available, skipping..."
        return
    fi
    
    response=$(curl -s -X POST "$BASE_URL/students/take-mock-test/$TEST_ID" \
        -H "Authorization: Bearer $STUDENT_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
            "answers": [0, 1, 1, 2, 0]
        }')
    
    if [[ $response == *"success\":true"* ]]; then
        print_success "Test submitted successfully"
        score=$(echo "$response" | grep -o "\"score\"[[:space:]]*:[[:space:]]*[0-9]*" | sed 's/.*:[[:space:]]*//')
        percentage=$(echo "$response" | grep -o "\"percentage\"[[:space:]]*:[[:space:]]*[0-9.]*" | sed 's/.*:[[:space:]]*//')
        print_info "Score: $score"
        print_info "Percentage: $percentage%"
    else
        print_error "Test submission failed"
        echo "$response"
    fi
}

# Test get test results
test_get_test_results() {
    print_header "TEST 17: Get Student Test Results"
    
    response=$(curl -s -X GET "$BASE_URL/students/my-test-results" \
        -H "Authorization: Bearer $STUDENT_TOKEN")
    
    if [[ $response == *"success\":true"* ]]; then
        print_success "Test results retrieved successfully"
        result_count=$(echo "$response" | grep -o "\"id\"" | wc -l)
        print_info "Total test attempts: $result_count"
    else
        print_error "Failed to get test results"
        echo "$response"
    fi
}

# Test faculty create assignment
test_faculty_create_assignment() {
    print_header "TEST 18: Faculty Create Assignment"
    
    response=$(curl -s -X POST "$BASE_URL/faculties/create-assignment" \
        -H "Authorization: Bearer $FACULTY_TOKEN" \
        -H "Content-Type: application/json" \
        -d "{
            \"title\": \"Data Structures Assignment\",
            \"description\": \"Implement a binary search tree in Python\",
            \"subject\": \"Computer Science\",
            \"total_marks\": 100,
            \"assigned_to\": [\"$STUDENT_ID\"],
            \"due_date\": \"2025-11-15T23:59:59\"
        }")
    
    ASSIGNMENT_ID=$(extract_json_value "$response" "id")
    
    if [[ $response == *"success\":true"* ]]; then
        print_success "Assignment created successfully"
        print_info "Assignment ID: $ASSIGNMENT_ID"
    else
        print_error "Assignment creation failed"
        echo "$response"
    fi
}

# Test get student assignments
test_get_student_assignments() {
    print_header "TEST 19: Get Student Assignments"
    
    response=$(curl -s -X GET "$BASE_URL/students/assignments" \
        -H "Authorization: Bearer $STUDENT_TOKEN")
    
    if [[ $response == *"success\":true"* ]]; then
        print_success "Assignments retrieved successfully"
        assignment_count=$(echo "$response" | grep -o "\"id\"" | wc -l)
        print_info "Total assignments: $assignment_count"
    else
        print_error "Failed to get assignments"
        echo "$response"
    fi
}

# Test AI query - explain
test_ai_explain() {
    print_header "TEST 20: AI Explain Concept"
    
    response=$(curl -s -X POST "$BASE_URL/ai/query" \
        -H "Authorization: Bearer $STUDENT_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
            "question": "Explain recursion in programming",
            "query_type": "explain",
            "subject": "Computer Science"
        }')
    
    if [[ $response == *"success\":true"* ]]; then
        print_success "AI explanation generated"
        echo "$response" | head -c 400
    else
        print_error "AI explanation failed"
        echo "$response"
    fi
}

# Test AI generate quiz
test_ai_generate_quiz() {
    print_header "TEST 21: AI Generate Quiz Questions"
    
    response=$(curl -s -X POST "$BASE_URL/ai/generate-quiz" \
        -H "Authorization: Bearer $FACULTY_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
            "topic": "JavaScript Basics",
            "num_questions": 3
        }')
    
    if [[ $response == *"success\":true"* ]]; then
        print_success "Quiz questions generated by AI"
        question_count=$(echo "$response" | grep -o "\"question_text\"" | wc -l)
        print_info "Questions generated: $question_count"
    else
        print_error "Quiz generation failed"
        echo "$response"
    fi
}

# Test AI summarize
test_ai_summarize() {
    print_header "TEST 22: AI Summarize Text"
    
    response=$(curl -s -X POST "$BASE_URL/ai/summarize" \
        -H "Authorization: Bearer $STUDENT_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
            "text": "Python is a high-level, interpreted programming language known for its simplicity and readability. It was created by Guido van Rossum and first released in 1991. Python supports multiple programming paradigms including procedural, object-oriented, and functional programming. It has a comprehensive standard library and a large ecosystem of third-party packages.",
            "subject": "Programming"
        }')
    
    if [[ $response == *"success\":true"* ]]; then
        print_success "Text summarized by AI"
        echo "$response" | head -c 300
    else
        print_error "Summarization failed"
        echo "$response"
    fi
}

# Test payment initiate
test_payment_initiate() {
    print_header "TEST 23: Initiate Payment (Wallet Recharge)"
    
    response=$(curl -s -X POST "$BASE_URL/payment/initiate" \
        -H "Authorization: Bearer $STUDENT_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
            "amount": 1000.0,
            "purpose": "wallet_recharge",
            "metadata": {"payment_method": "card"}
        }')
    
    PAYMENT_ID=$(extract_json_value "$response" "payment_id")
    ORDER_ID=$(extract_json_value "$response" "order_id")
    
    if [[ $response == *"success\":true"* ]]; then
        print_success "Payment initiated"
        print_info "Payment ID: $PAYMENT_ID"
        print_info "Order ID: $ORDER_ID"
    else
        print_error "Payment initiation failed"
        echo "$response"
    fi
}

# Test payment verify
test_payment_verify() {
    print_header "TEST 24: Verify Payment"
    
    if [ -z "$PAYMENT_ID" ] || [ -z "$ORDER_ID" ]; then
        print_warning "No payment to verify, skipping..."
        return
    fi
    
    response=$(curl -s -X POST "$BASE_URL/payment/verify" \
        -H "Authorization: Bearer $STUDENT_TOKEN" \
        -H "Content-Type: application/json" \
        -d "{
            \"payment_id\": \"$PAYMENT_ID\",
            \"order_id\": \"$ORDER_ID\",
            \"signature\": \"mock_signature_123\"
        }")
    
    if [[ $response == *"success\":true"* ]]; then
        print_success "Payment verified successfully"
    else
        print_error "Payment verification failed"
        echo "$response"
    fi
}

# Test get wallet balance
test_get_wallet() {
    print_header "TEST 25: Get Wallet Balance"
    
    response=$(curl -s -X GET "$BASE_URL/payment/wallet" \
        -H "Authorization: Bearer $STUDENT_TOKEN")
    
    if [[ $response == *"success\":true"* ]]; then
        print_success "Wallet balance retrieved"
        balance=$(echo "$response" | grep -o "\"wallet_balance\"[[:space:]]*:[[:space:]]*[0-9.]*" | sed 's/.*:[[:space:]]*//')
        print_info "Current balance: $balance"
    else
        print_error "Failed to get wallet balance"
        echo "$response"
    fi
}

# Test book session
test_book_session() {
    print_header "TEST 26: Student Book Session"
    
    response=$(curl -s -X POST "$BASE_URL/students/book-session" \
        -H "Authorization: Bearer $STUDENT_TOKEN" \
        -H "Content-Type: application/json" \
        -d "{
            \"faculty_id\": \"$FACULTY_ID\",
            \"scheduled_time\": \"2025-11-10T15:00:00\",
            \"duration_minutes\": 60,
            \"topic\": \"Advanced Python Concepts\",
            \"amount\": 500.0
        }")
    
    SESSION_ID=$(extract_json_value "$response" "session_id")
    
    if [[ $response == *"success\":true"* ]]; then
        print_success "Session booked successfully"
        print_info "Session ID: $SESSION_ID"
    else
        print_error "Session booking failed"
        echo "$response"
    fi
}

# Test get student sessions
test_get_student_sessions() {
    print_header "TEST 27: Get Student Sessions"
    
    response=$(curl -s -X GET "$BASE_URL/students/my-sessions" \
        -H "Authorization: Bearer $STUDENT_TOKEN")
    
    if [[ $response == *"success\":true"* ]]; then
        print_success "Student sessions retrieved"
        session_count=$(echo "$response" | grep -o "\"id\"" | wc -l)
        print_info "Total sessions: $session_count"
    else
        print_error "Failed to get student sessions"
        echo "$response"
    fi
}

# Test get faculty sessions
test_get_faculty_sessions() {
    print_header "TEST 28: Get Faculty Sessions"
    
    response=$(curl -s -X GET "$BASE_URL/faculties/my-sessions" \
        -H "Authorization: Bearer $FACULTY_TOKEN")
    
    if [[ $response == *"success\":true"* ]]; then
        print_success "Faculty sessions retrieved"
        session_count=$(echo "$response" | grep -o "\"id\"" | wc -l)
        print_info "Total sessions: $session_count"
    else
        print_error "Failed to get faculty sessions"
        echo "$response"
    fi
}

# Test faculty update session
test_faculty_update_session() {
    print_header "TEST 29: Faculty Accept Session"
    
    if [ -z "$SESSION_ID" ]; then
        print_warning "No session to update, skipping..."
        return
    fi
    
    response=$(curl -s -X PATCH "$BASE_URL/faculties/update-session/$SESSION_ID" \
        -H "Authorization: Bearer $FACULTY_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
            "status": "accepted",
            "meeting_link": "https://meet.google.com/abc-defg-hij",
            "notes": "Looking forward to the session!"
        }')
    
    if [[ $response == *"success\":true"* ]]; then
        print_success "Session accepted by faculty"
    else
        print_error "Session update failed"
        echo "$response"
    fi
}

# Test faculty get queries
test_faculty_get_queries() {
    print_header "TEST 30: Faculty Get Student Queries"
    
    response=$(curl -s -X GET "$BASE_URL/faculties/unanswered-queries" \
        -H "Authorization: Bearer $FACULTY_TOKEN")
    
    if [[ $response == *"success\":true"* ]]; then
        print_success "Queries retrieved by faculty"
        query_count=$(echo "$response" | grep -o "\"id\"" | wc -l)
        print_info "Total queries: $query_count"
    else
        print_error "Failed to get queries"
        echo "$response"
    fi
}

# Test faculty answer query
test_faculty_answer_query() {
    print_header "TEST 31: Faculty Answer Student Query"
    
    if [ -z "$QUERY_ID" ]; then
        print_warning "No query to answer, skipping..."
        return
    fi
    
    response=$(curl -s -X POST "$BASE_URL/faculties/answer-query/$QUERY_ID" \
        -H "Authorization: Bearer $FACULTY_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
            "answer_text": "The key difference is that supervised learning uses labeled training data where each example has a known output, while unsupervised learning works with unlabeled data to find patterns and structures. Supervised learning is used for classification and regression tasks, while unsupervised learning is used for clustering and dimensionality reduction."
        }')
    
    if [[ $response == *"success\":true"* ]]; then
        print_success "Query answered by faculty"
    else
        print_error "Failed to answer query"
        echo "$response"
    fi
}

# Test faculty get assignments
test_faculty_get_assignments() {
    print_header "TEST 32: Get Faculty Assignments"
    
    response=$(curl -s -X GET "$BASE_URL/faculties/my-assignments" \
        -H "Authorization: Bearer $FACULTY_TOKEN")
    
    if [[ $response == *"success\":true"* ]]; then
        print_success "Faculty assignments retrieved"
        assignment_count=$(echo "$response" | grep -o "\"id\"" | wc -l)
        print_info "Total assignments created: $assignment_count"
    else
        print_error "Failed to get faculty assignments"
        echo "$response"
    fi
}

# Test faculty get tests
test_faculty_get_tests() {
    print_header "TEST 33: Get Faculty Tests"
    
    response=$(curl -s -X GET "$BASE_URL/faculties/my-tests" \
        -H "Authorization: Bearer $FACULTY_TOKEN")
    
    if [[ $response == *"success\":true"* ]]; then
        print_success "Faculty tests retrieved"
        test_count=$(echo "$response" | grep -o "\"id\"" | wc -l)
        print_info "Total tests created: $test_count"
    else
        print_error "Failed to get faculty tests"
        echo "$response"
    fi
}

# Test admin get pending faculties
test_admin_pending_faculties() {
    print_header "TEST 34: Admin Get Pending Faculties"
    
    response=$(curl -s -X GET "$BASE_URL/admin/pending-faculties" \
        -H "Authorization: Bearer $ADMIN_TOKEN")
    
    if [[ $response == *"success\":true"* ]]; then
        print_success "Pending faculties retrieved"
        faculty_count=$(echo "$response" | grep -o "\"id\"" | wc -l)
        print_info "Pending faculties: $faculty_count"
    else
        print_error "Failed to get pending faculties"
        echo "$response"
    fi
}

# Test admin get platform overview
test_admin_platform_overview() {
    print_header "TEST 35: Admin Get Platform Overview"
    
    response=$(curl -s -X GET "$BASE_URL/admin/reports/overview" \
        -H "Authorization: Bearer $ADMIN_TOKEN")
    
    if [[ $response == *"success\":true"* ]]; then
        print_success "Platform overview retrieved"
        echo "$response" | head -c 500
    else
        print_error "Failed to get platform overview"
        echo "$response"
    fi
}

# Test admin get test analytics
test_admin_test_analytics() {
    print_header "TEST 36: Admin Get Test Analytics"
    
    response=$(curl -s -X GET "$BASE_URL/admin/reports/test-analytics" \
        -H "Authorization: Bearer $ADMIN_TOKEN")
    
    if [[ $response == *"success\":true"* ]]; then
        print_success "Test analytics retrieved"
        echo "$response" | head -c 400
    else
        print_error "Failed to get test analytics"
        echo "$response"
    fi
}

# Test admin get transactions
test_admin_transactions() {
    print_header "TEST 37: Admin Get Transaction Report"
    
    response=$(curl -s -X GET "$BASE_URL/admin/reports/transactions" \
        -H "Authorization: Bearer $ADMIN_TOKEN")
    
    if [[ $response == *"success\":true"* ]]; then
        print_success "Transaction report retrieved"
        txn_count=$(echo "$response" | grep -o "\"id\"" | wc -l)
        print_info "Total transactions: $txn_count"
    else
        print_error "Failed to get transactions"
        echo "$response"
    fi
}

# Test admin get user activity
test_admin_user_activity() {
    print_header "TEST 38: Admin Get User Activity"
    
    response=$(curl -s -X GET "$BASE_URL/admin/reports/user-activity/$STUDENT_ID" \
        -H "Authorization: Bearer $ADMIN_TOKEN")
    
    if [[ $response == *"success\":true"* ]]; then
        print_success "User activity retrieved"
        echo "$response" | head -c 400
    else
        print_error "Failed to get user activity"
        echo "$response"
    fi
}

# Test get transaction history
test_get_transactions() {
    print_header "TEST 39: Get User Transaction History"
    
    response=$(curl -s -X GET "$BASE_URL/payment/transactions?limit=20" \
        -H "Authorization: Bearer $STUDENT_TOKEN")
    
    if [[ $response == *"success\":true"* ]]; then
        print_success "Transaction history retrieved"
        txn_count=$(echo "$response" | grep -o "\"id\"" | wc -l)
        print_info "Total transactions: $txn_count"
    else
        print_error "Failed to get transaction history"
        echo "$response"
    fi
}

# Test AI query history
test_ai_query_history() {
    print_header "TEST 40: Get AI Query History"
    
    response=$(curl -s -X GET "$BASE_URL/ai/query-history?limit=10" \
        -H "Authorization: Bearer $STUDENT_TOKEN")
    
    if [[ $response == *"success\":true"* ]]; then
        print_success "AI query history retrieved"
        query_count=$(echo "$response" | grep -o "\"id\"" | wc -l)
        print_info "Total AI queries: $query_count"
    else
        print_error "Failed to get AI query history"
        echo "$response"
    fi
}

# Main execution
main() {
    print_header "🚀 StudyFriend API - Complete End-to-End Testing"
    print_info "Base URL: $BASE_URL"
    print_info "Started at: $(date)"
    
    # Test execution
    test_health
    test_student_registration
    test_student_login
    test_faculty_registration
    test_faculty_login
    test_admin_registration
    test_admin_login
    test_student_profile
    test_verify_faculty
    test_student_upload_material
    test_get_materials
    test_ask_question
    test_get_my_questions
    test_faculty_create_test
    test_get_available_tests
    test_student_take_test
    test_get_test_results
    test_faculty_create_assignment
    test_get_student_assignments
    test_ai_explain
    test_ai_generate_quiz
    test_ai_summarize
    test_payment_initiate
    test_payment_verify
    test_get_wallet
    test_book_session
    test_get_student_sessions
    test_get_faculty_sessions
    test_faculty_update_session
    test_faculty_get_queries
    test_faculty_answer_query
    test_faculty_get_assignments
    test_faculty_get_tests
    test_admin_pending_faculties
    test_admin_platform_overview
    test_admin_test_analytics
    test_admin_transactions
    test_admin_user_activity
    test_get_transactions
    test_ai_query_history
    
    # Summary
    print_header "🎉 Testing Complete!"
    print_info "Finished at: $(date)"
    echo -e "\n${GREEN}========================================${NC}"
    echo -e "${GREEN}All 40 endpoint tests completed!${NC}"
    echo -e "${GREEN}========================================${NC}\n"
    
    print_info "Generated IDs Summary:"
    echo -e "${CYAN}Student ID:${NC} $STUDENT_ID"
    echo -e "${CYAN}Faculty ID:${NC} $FACULTY_ID"
    echo -e "${CYAN}Admin ID:${NC} $ADMIN_ID"
    echo -e "${CYAN}Material ID:${NC} $MATERIAL_ID"
    echo -e "${CYAN}Query ID:${NC} $QUERY_ID"
    echo -e "${CYAN}Test ID:${NC} $TEST_ID"
    echo -e "${CYAN}Assignment ID:${NC} $ASSIGNMENT_ID"
    echo -e "${CYAN}Session ID:${NC} $SESSION_ID"
    echo -e "${CYAN}Payment ID:${NC} $PAYMENT_ID"
    echo ""
}

# Run all tests
main
