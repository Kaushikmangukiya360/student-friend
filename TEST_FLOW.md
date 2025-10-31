# 🧪 Test Script Flow Diagram

## Complete End-to-End Test Flow

```
┌─────────────────────────────────────────────────────────────┐
│           START: test_all_endpoints.sh                      │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  PHASE 1: SETUP & AUTHENTICATION                            │
├─────────────────────────────────────────────────────────────┤
│  1. ✓ Health Check                                          │
│  2. ✓ Register Student    → Store STUDENT_TOKEN            │
│  3. ✓ Login Student       → Store STUDENT_ID               │
│  4. ✓ Register Faculty    → Store FACULTY_TOKEN            │
│  5. ✓ Login Faculty       → Store FACULTY_ID               │
│  6. ✓ Register Admin      → Store ADMIN_TOKEN              │
│  7. ✓ Login Admin         → Store ADMIN_ID                 │
│  8. ✓ Get Student Profile                                   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  PHASE 2: ADMIN OPERATIONS                                  │
├─────────────────────────────────────────────────────────────┤
│  9. ✓ Admin Verify Faculty (using ADMIN_TOKEN)             │
│     → Faculty now verified and can create content          │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  PHASE 3: STUDENT MATERIALS & QUESTIONS                     │
├─────────────────────────────────────────────────────────────┤
│ 10. ✓ Student Upload Material → Store MATERIAL_ID          │
│ 11. ✓ Get All Materials                                     │
│ 12. ✓ Student Ask Question (AI) → Store QUERY_ID          │
│ 13. ✓ Get Student's Questions                              │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  PHASE 4: FACULTY TEST CREATION                             │
├─────────────────────────────────────────────────────────────┤
│ 14. ✓ Faculty Create Test → Store TEST_ID                  │
│     (5 Python questions with correct answers)               │
│ 15. ✓ Get Available Tests                                   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  PHASE 5: STUDENT TEST TAKING                               │
├─────────────────────────────────────────────────────────────┤
│ 16. ✓ Student Take Test (using TEST_ID)                    │
│     Submit answers: [0, 1, 1, 2, 0]                        │
│     → Auto-evaluated, score calculated                      │
│ 17. ✓ Get Test Results                                      │
│     Shows score, percentage, detailed results               │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  PHASE 6: ASSIGNMENTS                                       │
├─────────────────────────────────────────────────────────────┤
│ 18. ✓ Faculty Create Assignment → Store ASSIGNMENT_ID      │
│     Assigned to: STUDENT_ID                                 │
│ 19. ✓ Get Student Assignments                              │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  PHASE 7: AI FEATURES                                       │
├─────────────────────────────────────────────────────────────┤
│ 20. ✓ AI Explain Concept                                    │
│     Query: "Explain recursion in programming"               │
│ 21. ✓ AI Generate Quiz                                      │
│     Topic: JavaScript, 3 questions                          │
│ 22. ✓ AI Summarize Text                                     │
│     Summarizes Python description                           │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  PHASE 8: PAYMENT SYSTEM                                    │
├─────────────────────────────────────────────────────────────┤
│ 23. ✓ Initiate Payment → Store PAYMENT_ID, ORDER_ID       │
│     Amount: 1000.0, Purpose: wallet_recharge                │
│ 24. ✓ Verify Payment                                        │
│     → Wallet balance updated                                │
│ 25. ✓ Get Wallet Balance                                    │
│     Shows updated balance: 1000.0                           │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  PHASE 9: SESSION BOOKING                                   │
├─────────────────────────────────────────────────────────────┤
│ 26. ✓ Student Book Session → Store SESSION_ID              │
│     With: FACULTY_ID, Amount: 500.0                        │
│     → Deducts from wallet                                   │
│ 27. ✓ Get Student Sessions                                  │
│ 28. ✓ Get Faculty Sessions                                  │
│ 29. ✓ Faculty Accept Session (using SESSION_ID)            │
│     Status: accepted, Meeting link added                    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  PHASE 10: FACULTY QUERY MANAGEMENT                         │
├─────────────────────────────────────────────────────────────┤
│ 30. ✓ Faculty Get Student Queries                          │
│ 31. ✓ Faculty Answer Query (using QUERY_ID)                │
│     Provides detailed answer to student question            │
│ 32. ✓ Get Faculty Assignments                              │
│ 33. ✓ Get Faculty Tests                                     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  PHASE 11: ADMIN REPORTS & ANALYTICS                        │
├─────────────────────────────────────────────────────────────┤
│ 34. ✓ Get Pending Faculties                                │
│ 35. ✓ Get Platform Overview                                │
│     Users, content, sessions statistics                     │
│ 36. ✓ Get Test Analytics                                    │
│     Average scores, pass rates                              │
│ 37. ✓ Get Transaction Report                               │
│     All platform transactions                               │
│ 38. ✓ Get User Activity (using STUDENT_ID)                 │
│     Student's activity details                              │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  PHASE 12: HISTORY & TRACKING                               │
├─────────────────────────────────────────────────────────────┤
│ 39. ✓ Get Transaction History                              │
│     Student's payment history                               │
│ 40. ✓ Get AI Query History                                 │
│     All AI interactions                                     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│           TEST COMPLETE - SUMMARY DISPLAYED                 │
├─────────────────────────────────────────────────────────────┤
│  ✅ All 40 endpoints tested                                 │
│  ✅ All tokens captured and used                            │
│  ✅ All IDs tracked and reused                             │
│  📊 Generated IDs displayed:                                │
│     • Student ID                                            │
│     • Faculty ID                                            │
│     • Admin ID                                              │
│     • Material ID                                           │
│     • Query ID                                              │
│     • Test ID                                               │
│     • Assignment ID                                         │
│     • Session ID                                            │
│     • Payment ID & Order ID                                 │
└─────────────────────────────────────────────────────────────┘
```

## 🔄 Data Flow Between Tests

```
Register Student (2) 
    ↓ [STUDENT_TOKEN, STUDENT_ID]
Login Student (3)
    ↓ [Uses STUDENT_TOKEN]
Upload Material (10)
    ↓ [Creates MATERIAL_ID]
Ask Question (12)
    ↓ [Creates QUERY_ID]
    
Register Faculty (4)
    ↓ [FACULTY_TOKEN, FACULTY_ID]
Verify Faculty (9)
    ↓ [Uses ADMIN_TOKEN, FACULTY_ID]
Create Test (14)
    ↓ [Creates TEST_ID]
Take Test (16)
    ↓ [Uses STUDENT_TOKEN, TEST_ID]
    
Initiate Payment (23)
    ↓ [Creates PAYMENT_ID, ORDER_ID]
Verify Payment (24)
    ↓ [Uses PAYMENT_ID, ORDER_ID]
    ↓ [Updates wallet balance]
Book Session (26)
    ↓ [Uses STUDENT_TOKEN, FACULTY_ID]
    ↓ [Deducts from wallet]
    ↓ [Creates SESSION_ID]
Accept Session (29)
    ↓ [Uses FACULTY_TOKEN, SESSION_ID]
```

## 🎯 Role-Based Test Distribution

### Student Role Tests (19 tests)
- Authentication & Profile
- Upload Materials
- Ask Questions
- Take Tests
- View Assignments
- AI Features
- Payment Operations
- Book Sessions

### Faculty Role Tests (12 tests)
- Authentication
- Create Tests & Assignments
- Generate Quiz with AI
- Answer Queries
- Manage Sessions
- View Created Content

### Admin Role Tests (9 tests)
- Authentication
- Verify Faculty
- Platform Analytics
- Test Analytics
- Transaction Reports
- User Activity Tracking

## 🔐 Token Usage Pattern

```
┌──────────────────┐
│  STUDENT_TOKEN   │──→ Student endpoints (10-13, 15-17, 19-22, 25-27, 39-40)
└──────────────────┘

┌──────────────────┐
│  FACULTY_TOKEN   │──→ Faculty endpoints (14, 21, 28-33)
└──────────────────┘

┌──────────────────┐
│  ADMIN_TOKEN     │──→ Admin endpoints (9, 34-38)
└──────────────────┘
```

## 📊 Success Criteria

✅ **Authentication**: All 3 roles registered and logged in
✅ **Token Management**: Tokens stored and reused correctly
✅ **ID Tracking**: All IDs captured from responses
✅ **Cross-Reference**: IDs used in subsequent requests
✅ **Data Flow**: Complete user journeys tested
✅ **Error Handling**: Graceful handling of failures
✅ **Output**: Color-coded, readable results

## 🎉 Expected Results

```
40 Tests Run
├── 40 Passed ✅
├── 0 Failed
└── 0 Skipped

All Endpoints Covered:
├── Auth: 100%
├── Students: 100%
├── Faculty: 100%
├── AI: 100%
├── Admin: 100%
└── Payment: 100%
```

---

**Run Time**: ~2-3 minutes
**Coverage**: 100% of API endpoints
**Automation**: Fully automated, no manual input needed
