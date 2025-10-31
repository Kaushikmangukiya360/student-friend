from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File
from app.core.auth import get_current_user, require_role
from app.db.connection import get_database
from app.db.models.material_model import MaterialCreate, MaterialResponse, MaterialUpdate
from app.db.models.query_model import QueryCreate, QueryResponse
from app.db.models.test_model import TestSubmission, TestResult, AssignmentSubmit
from app.db.models.session_model import SessionCreate, SessionResponse
from app.db.models.user_model import UserUpdate
from app.db.models.enrollment_model import EnrollmentCreate, EnrollmentResponse, EnrollmentUpdate
from app.services.ai_service import ai_service
from app.services.test_service import test_service
from app.services.payment_service import payment_service
from app.services.vector_service import vector_service
from app.utils.helpers import success_response, get_timestamp, ensure_upload_dir
from bson import ObjectId
from typing import List, Optional
import uuid
import os

router = APIRouter(prefix="/students", tags=["Students"])


@router.post("/upload-material", response_model=dict)
async def upload_material(
    material: MaterialCreate,
    current_user: dict = Depends(require_role(["student", "faculty"]))
):
    """Upload study material"""
    db = get_database()
    
    material_doc = {
        "title": material.title,
        "description": material.description,
        "file_url": material.file_url,
        "uploaded_by": current_user["user_id"],
        "subject": material.subject,
        "course_id": material.course_id,
        "tags": material.tags,
        "visibility": material.visibility,
        "timestamp": get_timestamp()
    }
    
    result = await db.materials.insert_one(material_doc)
    material_doc["_id"] = str(result.inserted_id)
    
    # Index in vector database for semantic search
    await vector_service.index_material(
        material_id=str(result.inserted_id),
        title=material.title,
        content=material.description,
        subject=material.subject,
        course_id=material.course_id,
        tags=material.tags
    )
    
    return success_response(
        data={"id": str(result.inserted_id), **material_doc},
        message="Material uploaded successfully"
    )


@router.get("/materials", response_model=dict)
async def get_materials(
    subject: str = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all accessible materials"""
    db = get_database()
    
    query = {
        "$or": [
            {"visibility": "public"},
            {"uploaded_by": current_user["user_id"]}
        ]
    }
    
    if subject:
        query["subject"] = subject
    
    materials = await db.materials.find(query).sort("timestamp", -1).to_list(100)
    
    for material in materials:
        material["id"] = str(material.pop("_id"))
    
    return success_response(
        data=materials,
        message="Materials retrieved successfully"
    )


@router.post("/ask-question", response_model=dict)
async def ask_question(
    query: QueryCreate,
    current_user: dict = Depends(require_role(["student"]))
):
    """Ask a question - will be answered by AI or faculty"""
    db = get_database()
    
    # Get AI answer
    ai_answer = await ai_service.answer_question(
        question=query.question_text,
        context=f"Subject: {query.subject or 'General'}"
    )
    
    query_doc = {
        "question_text": query.question_text,
        "subject": query.subject,
        "asked_by": current_user["user_id"],
        "answered_by": "AI",
        "answer_text": ai_answer,
        "answered_by_type": "ai",
        "timestamp": get_timestamp(),
        "answered_at": get_timestamp()
    }
    
    result = await db.queries.insert_one(query_doc)
    query_doc["_id"] = str(result.inserted_id)
    
    return success_response(
        data={
            "id": str(result.inserted_id),
            "question": query.question_text,
            "answer": ai_answer,
            "answered_by": "AI"
        },
        message="Question answered successfully"
    )


@router.get("/my-questions", response_model=dict)
async def get_my_questions(
    current_user: dict = Depends(require_role(["student"]))
):
    """Get all questions asked by current student"""
    db = get_database()
    
    questions = await db.queries.find(
        {"asked_by": current_user["user_id"]}
    ).sort("timestamp", -1).to_list(100)
    
    for q in questions:
        q["id"] = str(q.pop("_id"))
    
    return success_response(
        data=questions,
        message="Questions retrieved successfully"
    )


@router.get("/tests", response_model=dict)
async def get_available_tests(
    subject: str = None,
    current_user: dict = Depends(require_role(["student"]))
):
    """Get all available tests"""
    db = get_database()
    
    query = {}
    if subject:
        query["subject"] = subject
    
    tests = await db.mock_tests.find(query).sort("created_at", -1).to_list(100)
    
    # Remove correct answers from response
    for test in tests:
        test["id"] = str(test.pop("_id"))
        for question in test.get("questions", []):
            question.pop("correct_answer", None)
    
    return success_response(
        data=tests,
        message="Tests retrieved successfully"
    )


@router.post("/take-mock-test/{test_id}", response_model=dict)
async def submit_test(
    test_id: str,
    submission: TestSubmission,
    current_user: dict = Depends(require_role(["student"]))
):
    """Submit a mock test and get results"""
    db = get_database()
    
    # Get test
    test = await db.mock_tests.find_one({"_id": ObjectId(test_id)})
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test not found"
        )
    
    # Evaluate test
    result = test_service.evaluate_test(
        questions=test["questions"],
        submitted_answers=submission.answers,
        student_id=current_user["user_id"],
        test_id=test_id
    )
    
    # Store test attempt
    attempt_doc = {
        "test_id": test_id,
        "student_id": current_user["user_id"],
        "answers": submission.answers,
        "score": result["score"],
        "total_marks": result["total_marks"],
        "percentage": result["percentage"],
        "started_at": get_timestamp(),
        "submitted_at": get_timestamp()
    }
    
    await db.test_attempts.insert_one(attempt_doc)
    
    return success_response(
        data={
            "test_title": test["test_title"],
            "score": result["score"],
            "total_marks": result["total_marks"],
            "percentage": result["percentage"],
            "detailed_results": result["detailed_results"]
        },
        message="Test submitted successfully"
    )


@router.get("/my-test-results", response_model=dict)
async def get_my_test_results(
    current_user: dict = Depends(require_role(["student"]))
):
    """Get all test results for current student"""
    db = get_database()
    
    attempts = await db.test_attempts.find(
        {"student_id": current_user["user_id"]}
    ).sort("submitted_at", -1).to_list(100)
    
    for attempt in attempts:
        attempt["id"] = str(attempt.pop("_id"))
        
        # Get test title
        test = await db.mock_tests.find_one({"_id": ObjectId(attempt["test_id"])})
        if test:
            attempt["test_title"] = test["test_title"]
    
    return success_response(
        data=attempts,
        message="Test results retrieved successfully"
    )


@router.post("/book-session", response_model=dict)
async def book_session(
    session: SessionCreate,
    current_user: dict = Depends(require_role(["student"]))
):
    """Book a 1:1 session with a faculty"""
    db = get_database()
    
    # Check if faculty exists and is verified
    faculty = await db.users.find_one({
        "_id": ObjectId(session.faculty_id),
        "role": "faculty",
        "verified": True
    })
    
    if not faculty:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Faculty not found or not verified"
        )
    
    # Check student wallet balance
    student = await db.users.find_one({"_id": ObjectId(current_user["user_id"])})
    if student["wallet_balance"] < session.amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient wallet balance"
        )
    
    # Create session
    session_id = f"sess_{uuid.uuid4().hex[:12]}"
    session_doc = {
        "session_id": session_id,
        "student_id": current_user["user_id"],
        "faculty_id": session.faculty_id,
        "course_id": session.course_id,
        "scheduled_time": session.scheduled_time,
        "duration_minutes": session.duration_minutes,
        "topic": session.topic,
        "amount": session.amount,
        "status": "pending",
        "payment_status": "pending",
        "created_at": get_timestamp(),
        "updated_at": get_timestamp()
    }
    
    result = await db.sessions.insert_one(session_doc)
    
    # Deduct from student wallet
    await db.users.update_one(
        {"_id": ObjectId(current_user["user_id"])},
        {"$inc": {"wallet_balance": -session.amount}}
    )
    
    # Create transaction
    await db.transactions.insert_one({
        "user_id": current_user["user_id"],
        "amount": session.amount,
        "type": "debit",
        "purpose": f"Session booking: {session_id}",
        "reference_id": session_id,
        "timestamp": get_timestamp()
    })
    
    # Create notification for faculty
    await db.notifications.insert_one({
        "user_id": session.faculty_id,
        "message": f"New session booking request from {student['name']} for {session.topic}",
        "type": "info",
        "read_status": False,
        "timestamp": get_timestamp()
    })
    
    session_doc["_id"] = str(result.inserted_id)
    
    return success_response(
        data={
            "session_id": session_id,
            "id": str(result.inserted_id),
            "status": "pending",
            "message": "Session booked. Waiting for faculty confirmation."
        },
        message="Session booked successfully"
    )


@router.get("/my-sessions", response_model=dict)
async def get_my_sessions(
    current_user: dict = Depends(require_role(["student"]))
):
    """Get all sessions for current student"""
    db = get_database()
    
    sessions = await db.sessions.find(
        {"student_id": current_user["user_id"]}
    ).sort("scheduled_time", -1).to_list(100)
    
    for session in sessions:
        session["id"] = str(session.pop("_id"))
        
        # Get faculty details
        faculty = await db.users.find_one({"_id": ObjectId(session["faculty_id"])})
        if faculty:
            session["faculty_name"] = faculty["name"]
            session["faculty_email"] = faculty["email"]
    
    return success_response(
        data=sessions,
        message="Sessions retrieved successfully"
    )


@router.get("/assignments", response_model=dict)
async def get_my_assignments(
    current_user: dict = Depends(require_role(["student"]))
):
    """Get assignments assigned to current student"""
    db = get_database()
    
    assignments = await db.assignments.find(
        {"assigned_to": current_user["user_id"]}
    ).sort("due_date", -1).to_list(100)
    
    for assignment in assignments:
        assignment["id"] = str(assignment.pop("_id"))
        
        # Get faculty details
        faculty = await db.users.find_one({"_id": ObjectId(assignment["created_by"])})
        if faculty:
            assignment["created_by_name"] = faculty["name"]
    
    return success_response(
        data=assignments,
        message="Assignments retrieved successfully"
    )


# Additional Student Routes

@router.get("/materials/subject/{subject}", response_model=dict)
async def get_materials_by_subject(
    subject: str,
    current_user: dict = Depends(get_current_user)
):
    """Get materials by subject"""
    db = get_database()

    query = {
        "subject": subject,
        "$or": [
            {"visibility": "public"},
            {"uploaded_by": current_user["user_id"]}
        ]
    }

    materials = await db.materials.find(query).sort("timestamp", -1).to_list(100)

    for material in materials:
        material["id"] = str(material.pop("_id"))

    return success_response(
        data=materials,
        message=f"Materials for subject '{subject}' retrieved successfully"
    )


@router.get("/materials/course/{course_id}", response_model=dict)
async def get_materials_by_course(
    course_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get materials by course"""
    db = get_database()

    query = {
        "course_id": course_id,
        "$or": [
            {"visibility": "public"},
            {"uploaded_by": current_user["user_id"]}
        ]
    }

    materials = await db.materials.find(query).sort("timestamp", -1).to_list(100)

    for material in materials:
        material["id"] = str(material.pop("_id"))

    return success_response(
        data=materials,
        message=f"Materials for course '{course_id}' retrieved successfully"
    )


@router.get("/assignments/subject/{subject}", response_model=dict)
async def get_assignments_by_subject(
    subject: str,
    current_user: dict = Depends(require_role(["student"]))
):
    """Get assignments by subject"""
    db = get_database()

    assignments = await db.assignments.find({
        "subject": subject,
        "assigned_to": current_user["user_id"]
    }).sort("due_date", -1).to_list(100)

    for assignment in assignments:
        assignment["id"] = str(assignment.pop("_id"))

        # Get faculty details
        faculty = await db.users.find_one({"_id": ObjectId(assignment["created_by"])})
        if faculty:
            assignment["created_by_name"] = faculty["name"]

    return success_response(
        data=assignments,
        message=f"Assignments for subject '{subject}' retrieved successfully"
    )


@router.get("/assignments/course/{course_id}", response_model=dict)
async def get_assignments_by_course(
    course_id: str,
    current_user: dict = Depends(require_role(["student"]))
):
    """Get assignments by course"""
    db = get_database()

    assignments = await db.assignments.find({
        "course_id": course_id,
        "assigned_to": current_user["user_id"]
    }).sort("due_date", -1).to_list(100)

    for assignment in assignments:
        assignment["id"] = str(assignment.pop("_id"))

        # Get faculty details
        faculty = await db.users.find_one({"_id": ObjectId(assignment["created_by"])})
        if faculty:
            assignment["created_by_name"] = faculty["name"]

    return success_response(
        data=assignments,
        message=f"Assignments for course '{course_id}' retrieved successfully"
    )


@router.get("/tests/subject/{subject}", response_model=dict)
async def get_tests_by_subject(
    subject: str,
    current_user: dict = Depends(require_role(["student"]))
):
    """Get available tests by subject"""
    db = get_database()

    tests = await db.mock_tests.find({"subject": subject}).sort("created_at", -1).to_list(100)

    for test in tests:
        test["id"] = str(test.pop("_id"))

        # Check if student has already taken this test
        attempt = await db.test_attempts.find_one({
            "test_id": test["id"],
            "student_id": current_user["user_id"]
        })
        test["attempted"] = attempt is not None
        if attempt:
            test["score"] = attempt["score"]
            test["percentage"] = attempt["percentage"]

    return success_response(
        data=tests,
        message=f"Tests for subject '{subject}' retrieved successfully"
    )


@router.get("/tests/course/{course_id}", response_model=dict)
async def get_tests_by_course(
    course_id: str,
    current_user: dict = Depends(require_role(["student"]))
):
    """Get available tests by course"""
    db = get_database()

    tests = await db.mock_tests.find({"course_id": course_id}).sort("created_at", -1).to_list(100)

    for test in tests:
        test["id"] = str(test.pop("_id"))

        # Check if student has already taken this test
        attempt = await db.test_attempts.find_one({
            "test_id": test["id"],
            "student_id": current_user["user_id"]
        })
        test["attempted"] = attempt is not None
        if attempt:
            test["score"] = attempt["score"]
            test["percentage"] = attempt["percentage"]

    return success_response(
        data=tests,
        message=f"Tests for course '{course_id}' retrieved successfully"
    )


@router.post("/submit-assignment/{assignment_id}", response_model=dict)
async def submit_assignment(
    assignment_id: str,
    submission: AssignmentSubmit,
    current_user: dict = Depends(require_role(["student"]))
):
    """Submit an assignment"""
    db = get_database()

    # Check if assignment exists
    assignment = await db.assignments.find_one({"_id": ObjectId(assignment_id)})
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )

    # Check if student is assigned to this assignment
    if current_user["user_id"] not in assignment["assigned_to"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not assigned to this assignment"
        )

    # Check if already submitted
    existing_submission = None
    for sub in assignment.get("submissions", []):
        if sub["student_id"] == current_user["user_id"]:
            existing_submission = sub
            break

    if existing_submission:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already submitted this assignment"
        )

    # Add submission
    submission_data = {
        "student_id": current_user["user_id"],
        "submission_text": submission.submission_text,
        "file_url": submission.file_url,
        "submitted_at": get_timestamp()
    }

    result = await db.assignments.update_one(
        {"_id": ObjectId(assignment_id)},
        {"$push": {"submissions": submission_data}}
    )

    return success_response(
        data={"assignment_id": assignment_id, "submitted": True},
        message="Assignment submitted successfully"
    )


@router.get("/my-submissions", response_model=dict)
async def get_my_submissions(
    current_user: dict = Depends(require_role(["student"]))
):
    """Get all my assignment submissions"""
    db = get_database()

    # Find all assignments where student has submitted
    assignments = await db.assignments.find({
        "assigned_to": current_user["user_id"]
    }).to_list(100)

    submissions = []
    for assignment in assignments:
        for submission in assignment.get("submissions", []):
            if submission["student_id"] == current_user["user_id"]:
                submissions.append({
                    "assignment_id": str(assignment["_id"]),
                    "assignment_title": assignment["title"],
                    "subject": assignment["subject"],
                    "course_id": assignment.get("course_id"),
                    "submitted_at": submission["submitted_at"],
                    "submission_text": submission.get("submission_text"),
                    "file_url": submission.get("file_url"),
                    "marks_obtained": submission.get("marks_obtained"),
                    "feedback": submission.get("feedback")
                })

    return success_response(
        data=submissions,
        message="Submissions retrieved successfully"
    )


@router.patch("/update-profile", response_model=dict)
async def update_student_profile(
    profile_update: UserUpdate,
    current_user: dict = Depends(require_role(["student"]))
):
    """Update student profile"""
    db = get_database()

    update_data = profile_update.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )

    # Update user
    await db.users.update_one(
        {"_id": ObjectId(current_user["user_id"])},
        {"$set": update_data}
    )

    # Get updated user
    updated_user = await db.users.find_one({"_id": ObjectId(current_user["user_id"])})
    updated_user["id"] = str(updated_user.pop("_id"))
    updated_user.pop("hashed_password", None)

    return success_response(
        data=updated_user,
        message="Profile updated successfully"
    )


# Course Enrollment Routes

@router.post("/enroll", response_model=dict)
async def enroll_in_course(
    enrollment: EnrollmentCreate,
    current_user: dict = Depends(require_role(["student"]))
):
    """Enroll in a course"""
    db = get_database()
    
    # Validate student
    if enrollment.student_id != current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot enroll for another student"
        )
    
    # Check if course exists
    course = await db.courses.find_one({"_id": ObjectId(enrollment.course_id)})
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # Check if already enrolled
    existing = await db.enrollments.find_one({
        "student_id": enrollment.student_id,
        "course_id": enrollment.course_id
    })
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already enrolled in this course"
        )
    
    enrollment_data = enrollment.model_dump()
    enrollment_data["progress_percentage"] = 0.0
    
    result = await db.enrollments.insert_one(enrollment_data)
    enrollment_data["id"] = str(result.inserted_id)
    
    return success_response(
        data=EnrollmentResponse(**enrollment_data).model_dump(),
        message="Enrolled in course successfully"
    )


@router.get("/enrollments", response_model=dict)
async def get_my_enrollments(
    current_user: dict = Depends(require_role(["student"]))
):
    """Get student's course enrollments"""
    db = get_database()
    
    enrollments = await db.enrollments.find({
        "student_id": current_user["user_id"]
    }).to_list(100)
    
    # Populate course details
    for enrollment in enrollments:
        enrollment["id"] = str(enrollment.pop("_id"))
        
        course = await db.courses.find_one({"_id": ObjectId(enrollment["course_id"])})
        if course:
            enrollment["course"] = {
                "id": str(course["_id"]),
                "name": course["name"],
                "description": course.get("description"),
                "subject_id": course.get("subject_id"),
                "faculty_id": course.get("faculty_id")
            }
    
    return success_response(
        data=enrollments,
        message="Enrollments retrieved successfully"
    )


@router.put("/enrollments/{enrollment_id}", response_model=dict)
async def update_enrollment(
    enrollment_id: str,
    update: EnrollmentUpdate,
    current_user: dict = Depends(require_role(["student"]))
):
    """Update enrollment progress or status"""
    db = get_database()
    
    # Check if enrollment exists and belongs to user
    enrollment = await db.enrollments.find_one({
        "_id": ObjectId(enrollment_id),
        "student_id": current_user["user_id"]
    })
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enrollment not found"
        )
    
    update_data = update.model_dump(exclude_unset=True)
    if update_data:
        await db.enrollments.update_one(
            {"_id": ObjectId(enrollment_id)},
            {"$set": update_data}
        )
    
    # Get updated enrollment
    updated = await db.enrollments.find_one({"_id": ObjectId(enrollment_id)})
    updated["id"] = str(updated.pop("_id"))
    
    return success_response(
        data=updated,
        message="Enrollment updated successfully"
    )


@router.get("/courses/available", response_model=dict)
async def get_available_courses(
    subject_id: Optional[str] = None,
    current_user: dict = Depends(require_role(["student"]))
):
    """Get courses available for enrollment"""
    db = get_database()
    
    query = {}
    if subject_id:
        query["subject_id"] = subject_id
    
    courses = await db.courses.find(query).to_list(100)
    
    # Filter out already enrolled courses
    enrolled_course_ids = await db.enrollments.distinct(
        "course_id",
        {"student_id": current_user["user_id"]}
    )
    enrolled_course_ids = [str(id) for id in enrolled_course_ids]
    
    available_courses = []
    for course in courses:
        course_id_str = str(course["_id"])
        if course_id_str not in enrolled_course_ids:
            course["id"] = course_id_str
            course.pop("_id")
            
            # Add subject and faculty info
            subject = await db.subjects.find_one({"_id": ObjectId(course["subject_id"])})
            if subject:
                course["subject"] = {
                    "id": str(subject["_id"]),
                    "name": subject["name"]
                }
            
            faculty = await db.users.find_one({"_id": ObjectId(course["faculty_id"])})
            if faculty:
                course["faculty"] = {
                    "id": str(faculty["_id"]),
                    "name": faculty["name"]
                }
            
            available_courses.append(course)
    
    return success_response(
        data=available_courses,
        message="Available courses retrieved successfully"
    )
