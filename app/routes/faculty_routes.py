from fastapi import APIRouter, HTTPException, status, Depends
from app.core.auth import require_role
from app.db.connection import get_database
from app.db.models.material_model import MaterialCreate, MaterialUpdate
from app.db.models.test_model import TestCreate, Question, TestUpdate, AssignmentCreate, AssignmentUpdate
from app.db.models.query_model import AnswerQuery
from app.db.models.session_model import SessionUpdate
from app.db.models.user_model import UserUpdate
from app.utils.helpers import success_response, get_timestamp
from app.services.ai_service import ai_service
from app.services.vector_service import vector_service
from bson import ObjectId
from typing import List, Optional

router = APIRouter(prefix="/faculties", tags=["Faculty"])


@router.post("/upload-material", response_model=dict)
async def upload_material(
    material: MaterialCreate,
    current_user: dict = Depends(require_role(["faculty"]))
):
    """Upload study material as faculty"""
    db = get_database()
    
    # Check if faculty is verified
    faculty = await db.users.find_one({"_id": ObjectId(current_user["user_id"])})
    if not faculty.get("verified"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Faculty account not verified"
        )
    
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


@router.post("/create-assignment", response_model=dict)
async def create_assignment(
    assignment: AssignmentCreate,
    current_user: dict = Depends(require_role(["faculty"]))
):
    """Create a new assignment"""
    db = get_database()
    
    # Check if faculty is verified
    faculty = await db.users.find_one({"_id": ObjectId(current_user["user_id"])})
    if not faculty.get("verified"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Faculty account not verified"
        )
    
    assignment_doc = {
        "title": assignment.title,
        "description": assignment.description,
        "subject": assignment.subject,
        "course_id": assignment.course_id,
        "total_marks": assignment.total_marks,
        "created_by": current_user["user_id"],
        "assigned_to": assignment.assigned_to,
        "due_date": assignment.due_date,
        "submissions": [],
        "created_at": get_timestamp()
    }
    
    result = await db.assignments.insert_one(assignment_doc)
    
    # Create notifications for assigned students
    for student_id in assignment.assigned_to:
        await db.notifications.insert_one({
            "user_id": student_id,
            "message": f"New assignment: {assignment.title} - Due: {assignment.due_date.strftime('%Y-%m-%d')}",
            "type": "info",
            "read_status": False,
            "timestamp": get_timestamp()
        })
    
    return success_response(
        data={"id": str(result.inserted_id), **assignment_doc},
        message="Assignment created successfully"
    )


@router.post("/create-test", response_model=dict)
async def create_test(
    test: TestCreate,
    current_user: dict = Depends(require_role(["faculty"]))
):
    """Create a new mock test"""
    db = get_database()
    
    # Check if faculty is verified
    faculty = await db.users.find_one({"_id": ObjectId(current_user["user_id"])})
    if not faculty.get("verified"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Faculty account not verified"
        )
    
    test_doc = {
        "test_title": test.test_title,
        "description": test.description,
        "subject": test.subject,
        "course_id": test.course_id,
        "duration_minutes": test.duration_minutes,
        "total_marks": test.total_marks,
        "questions": [q.dict() for q in test.questions],
        "created_by": current_user["user_id"],
        "created_at": get_timestamp()
    }
    
    result = await db.mock_tests.insert_one(test_doc)
    
    return success_response(
        data={"id": str(result.inserted_id), **test_doc},
        message="Test created successfully"
    )


@router.post("/generate-test-questions", response_model=dict)
async def generate_test_questions(
    topic: str,
    num_questions: int = 5,
    current_user: dict = Depends(require_role(["faculty"]))
):
    """Generate test questions using AI"""
    
    # Check if faculty is verified
    db = get_database()
    faculty = await db.users.find_one({"_id": ObjectId(current_user["user_id"])})
    if not faculty.get("verified"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Faculty account not verified"
        )
    
    questions = await ai_service.generate_quiz_questions(topic, num_questions)
    
    return success_response(
        data={"topic": topic, "questions": questions},
        message="Questions generated successfully"
    )


@router.get("/unanswered-queries", response_model=dict)
async def get_unanswered_queries(
    subject: str = None,
    current_user: dict = Depends(require_role(["faculty"]))
):
    """Get all unanswered queries (or queries needing faculty attention)"""
    db = get_database()
    
    query = {}
    if subject:
        query["subject"] = subject
    
    queries = await db.queries.find(query).sort("timestamp", -1).to_list(100)
    
    for q in queries:
        q["id"] = str(q.pop("_id"))
        
        # Get student details
        student = await db.users.find_one({"_id": ObjectId(q["asked_by"])})
        if student:
            q["student_name"] = student["name"]
            q["student_email"] = student["email"]
    
    return success_response(
        data=queries,
        message="Queries retrieved successfully"
    )


@router.post("/answer-query/{query_id}", response_model=dict)
async def answer_query(
    query_id: str,
    answer: AnswerQuery,
    current_user: dict = Depends(require_role(["faculty"]))
):
    """Answer a student's query"""
    db = get_database()
    
    # Check if faculty is verified
    faculty = await db.users.find_one({"_id": ObjectId(current_user["user_id"])})
    if not faculty.get("verified"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Faculty account not verified"
        )
    
    # Update query
    result = await db.queries.update_one(
        {"_id": ObjectId(query_id)},
        {
            "$set": {
                "answer_text": answer.answer_text,
                "answered_by": current_user["user_id"],
                "answered_by_type": "faculty",
                "answered_at": get_timestamp()
            }
        }
    )
    
    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Query not found"
        )
    
    # Get query details for notification
    query = await db.queries.find_one({"_id": ObjectId(query_id)})
    
    # Create notification for student
    await db.notifications.insert_one({
        "user_id": query["asked_by"],
        "message": f"Your question has been answered by {faculty['name']}",
        "type": "success",
        "read_status": False,
        "timestamp": get_timestamp()
    })
    
    return success_response(
        data={"query_id": query_id, "answered": True},
        message="Query answered successfully"
    )


@router.get("/my-sessions", response_model=dict)
async def get_faculty_sessions(
    current_user: dict = Depends(require_role(["faculty"]))
):
    """Get all sessions for current faculty"""
    db = get_database()
    
    sessions = await db.sessions.find(
        {"faculty_id": current_user["user_id"]}
    ).sort("scheduled_time", -1).to_list(100)
    
    for session in sessions:
        session["id"] = str(session.pop("_id"))
        
        # Get student details
        student = await db.users.find_one({"_id": ObjectId(session["student_id"])})
        if student:
            session["student_name"] = student["name"]
            session["student_email"] = student["email"]
    
    return success_response(
        data=sessions,
        message="Sessions retrieved successfully"
    )


@router.patch("/update-session/{session_id}", response_model=dict)
async def update_session(
    session_id: str,
    update: SessionUpdate,
    current_user: dict = Depends(require_role(["faculty"]))
):
    """Update session status (accept/reject/complete)"""
    db = get_database()
    
    # Get session
    session = await db.sessions.find_one({"session_id": session_id})
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Check if faculty owns this session
    if session["faculty_id"] != current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this session"
        )
    
    update_data = {"updated_at": get_timestamp()}
    
    if update.status:
        update_data["status"] = update.status
        
        # Handle refunds for rejected/cancelled sessions
        if update.status in ["rejected", "cancelled"] and session["payment_status"] != "refunded":
            # Refund to student
            await db.users.update_one(
                {"_id": ObjectId(session["student_id"])},
                {"$inc": {"wallet_balance": session["amount"]}}
            )
            
            update_data["payment_status"] = "refunded"
            
            # Create refund transaction
            await db.transactions.insert_one({
                "user_id": session["student_id"],
                "amount": session["amount"],
                "type": "credit",
                "purpose": f"Session refund: {session_id}",
                "reference_id": session_id,
                "timestamp": get_timestamp()
            })
        
        # Mark payment as completed for accepted sessions
        if update.status == "accepted":
            update_data["payment_status"] = "completed"
    
    if update.meeting_link:
        update_data["meeting_link"] = update.meeting_link
    
    if update.notes:
        update_data["notes"] = update.notes
    
    # Update session
    await db.sessions.update_one(
        {"session_id": session_id},
        {"$set": update_data}
    )
    
    # Create notification for student
    faculty = await db.users.find_one({"_id": ObjectId(current_user["user_id"])})
    status_message = {
        "accepted": "accepted your session request",
        "rejected": "declined your session request",
        "completed": "marked your session as completed",
        "cancelled": "cancelled your session"
    }.get(update.status, "updated your session")
    
    await db.notifications.insert_one({
        "user_id": session["student_id"],
        "message": f"{faculty['name']} {status_message}",
        "type": "info" if update.status == "accepted" else "warning",
        "read_status": False,
        "timestamp": get_timestamp()
    })
    
    return success_response(
        data={"session_id": session_id, "status": update.status},
        message="Session updated successfully"
    )


@router.get("/my-assignments", response_model=dict)
async def get_faculty_assignments(
    current_user: dict = Depends(require_role(["faculty"]))
):
    """Get all assignments created by current faculty"""
    db = get_database()
    
    assignments = await db.assignments.find(
        {"created_by": current_user["user_id"]}
    ).sort("created_at", -1).to_list(100)
    
    for assignment in assignments:
        assignment["id"] = str(assignment.pop("_id"))
    
    return success_response(
        data=assignments,
        message="Assignments retrieved successfully"
    )


@router.get("/my-tests", response_model=dict)
async def get_faculty_tests(
    current_user: dict = Depends(require_role(["faculty"]))
):
    """Get all tests created by current faculty"""
    db = get_database()
    
    tests = await db.mock_tests.find(
        {"created_by": current_user["user_id"]}
    ).sort("created_at", -1).to_list(100)
    
    for test in tests:
        test["id"] = str(test.pop("_id"))
    
    return success_response(
        data=tests,
        message="Tests retrieved successfully"
    )


# Additional Faculty Routes

@router.get("/materials/subject/{subject}", response_model=dict)
async def get_materials_by_subject(
    subject: str,
    current_user: dict = Depends(require_role(["faculty"]))
):
    """Get materials by subject (faculty can see all materials)"""
    db = get_database()

    materials = await db.materials.find({"subject": subject}).sort("timestamp", -1).to_list(100)

    for material in materials:
        material["id"] = str(material.pop("_id"))

        # Get uploader details
        uploader = await db.users.find_one({"_id": ObjectId(material["uploaded_by"])})
        if uploader:
            material["uploaded_by_name"] = uploader["name"]

    return success_response(
        data=materials,
        message=f"Materials for subject '{subject}' retrieved successfully"
    )


@router.get("/materials/course/{course_id}", response_model=dict)
async def get_materials_by_course(
    course_id: str,
    current_user: dict = Depends(require_role(["faculty"]))
):
    """Get materials by course (faculty can see all materials)"""
    db = get_database()

    materials = await db.materials.find({"course_id": course_id}).sort("timestamp", -1).to_list(100)

    for material in materials:
        material["id"] = str(material.pop("_id"))

        # Get uploader details
        uploader = await db.users.find_one({"_id": ObjectId(material["uploaded_by"])})
        if uploader:
            material["uploaded_by_name"] = uploader["name"]

    return success_response(
        data=materials,
        message=f"Materials for course '{course_id}' retrieved successfully"
    )


@router.put("/materials/{material_id}", response_model=dict)
async def update_material(
    material_id: str,
    material_update: MaterialUpdate,
    current_user: dict = Depends(require_role(["faculty"]))
):
    """Update a material (only faculty can update)"""
    db = get_database()

    # Check if material exists
    material = await db.materials.find_one({"_id": ObjectId(material_id)})
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found"
        )

    update_data = material_update.model_dump(exclude_unset=True)
    update_data["timestamp"] = get_timestamp()

    await db.materials.update_one(
        {"_id": ObjectId(material_id)},
        {"$set": update_data}
    )

    # Get updated material
    updated_material = await db.materials.find_one({"_id": ObjectId(material_id)})
    updated_material["id"] = str(updated_material.pop("_id"))

    return success_response(
        data=updated_material,
        message="Material updated successfully"
    )


@router.delete("/materials/{material_id}", response_model=dict)
async def delete_material(
    material_id: str,
    current_user: dict = Depends(require_role(["faculty"]))
):
    """Delete a material (only faculty can delete)"""
    db = get_database()

    # Check if material exists
    material = await db.materials.find_one({"_id": ObjectId(material_id)})
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found"
        )

    await db.materials.delete_one({"_id": ObjectId(material_id)})

    return success_response(
        data={"material_id": material_id, "deleted": True},
        message="Material deleted successfully"
    )


@router.get("/assignments/subject/{subject}", response_model=dict)
async def get_assignments_by_subject(
    subject: str,
    current_user: dict = Depends(require_role(["faculty"]))
):
    """Get assignments by subject created by current faculty"""
    db = get_database()

    assignments = await db.assignments.find({
        "subject": subject,
        "created_by": current_user["user_id"]
    }).sort("due_date", -1).to_list(100)

    for assignment in assignments:
        assignment["id"] = str(assignment.pop("_id"))

    return success_response(
        data=assignments,
        message=f"Assignments for subject '{subject}' retrieved successfully"
    )


@router.get("/assignments/course/{course_id}", response_model=dict)
async def get_assignments_by_course(
    course_id: str,
    current_user: dict = Depends(require_role(["faculty"]))
):
    """Get assignments by course created by current faculty"""
    db = get_database()

    assignments = await db.assignments.find({
        "course_id": course_id,
        "created_by": current_user["user_id"]
    }).sort("due_date", -1).to_list(100)

    for assignment in assignments:
        assignment["id"] = str(assignment.pop("_id"))

    return success_response(
        data=assignments,
        message=f"Assignments for course '{course_id}' retrieved successfully"
    )


@router.put("/assignments/{assignment_id}", response_model=dict)
async def update_assignment(
    assignment_id: str,
    assignment_update: AssignmentUpdate,
    current_user: dict = Depends(require_role(["faculty"]))
):
    """Update an assignment"""
    db = get_database()

    # Check if assignment exists and belongs to current faculty
    assignment = await db.assignments.find_one({
        "_id": ObjectId(assignment_id),
        "created_by": current_user["user_id"]
    })
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found or access denied"
        )

    update_data = assignment_update.model_dump(exclude_unset=True)

    await db.assignments.update_one(
        {"_id": ObjectId(assignment_id)},
        {"$set": update_data}
    )

    # Get updated assignment
    updated_assignment = await db.assignments.find_one({"_id": ObjectId(assignment_id)})
    updated_assignment["id"] = str(updated_assignment.pop("_id"))

    return success_response(
        data=updated_assignment,
        message="Assignment updated successfully"
    )


@router.delete("/assignments/{assignment_id}", response_model=dict)
async def delete_assignment(
    assignment_id: str,
    current_user: dict = Depends(require_role(["faculty"]))
):
    """Delete an assignment"""
    db = get_database()

    # Check if assignment exists and belongs to current faculty
    assignment = await db.assignments.find_one({
        "_id": ObjectId(assignment_id),
        "created_by": current_user["user_id"]
    })
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found or access denied"
        )

    await db.assignments.delete_one({"_id": ObjectId(assignment_id)})

    return success_response(
        data={"assignment_id": assignment_id, "deleted": True},
        message="Assignment deleted successfully"
    )


@router.get("/assignment-submissions/{assignment_id}", response_model=dict)
async def get_assignment_submissions(
    assignment_id: str,
    current_user: dict = Depends(require_role(["faculty"]))
):
    """Get all submissions for an assignment"""
    db = get_database()

    # Check if assignment exists and belongs to current faculty
    assignment = await db.assignments.find_one({
        "_id": ObjectId(assignment_id),
        "created_by": current_user["user_id"]
    })
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found or access denied"
        )

    submissions = []
    for submission in assignment.get("submissions", []):
        # Get student details
        student = await db.users.find_one({"_id": ObjectId(submission["student_id"])})
        submission_data = {
            "student_id": submission["student_id"],
            "student_name": student["name"] if student else "Unknown",
            "student_email": student["email"] if student else "Unknown",
            "submitted_at": submission["submitted_at"],
            "submission_text": submission.get("submission_text"),
            "file_url": submission.get("file_url"),
            "marks_obtained": submission.get("marks_obtained"),
            "feedback": submission.get("feedback")
        }
        submissions.append(submission_data)

    return success_response(
        data={
            "assignment_title": assignment["title"],
            "submissions": submissions
        },
        message="Assignment submissions retrieved successfully"
    )


@router.post("/grade-submission/{assignment_id}/{student_id}", response_model=dict)
async def grade_submission(
    assignment_id: str,
    student_id: str,
    marks_obtained: int,
    feedback: Optional[str] = None,
    current_user: dict = Depends(require_role(["faculty"]))
):
    """Grade a student submission"""
    db = get_database()

    # Check if assignment exists and belongs to current faculty
    assignment = await db.assignments.find_one({
        "_id": ObjectId(assignment_id),
        "created_by": current_user["user_id"]
    })
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found or access denied"
        )

    # Find and update the submission
    submissions = assignment.get("submissions", [])
    submission_found = False

    for submission in submissions:
        if submission["student_id"] == student_id:
            submission["marks_obtained"] = marks_obtained
            submission["feedback"] = feedback
            submission_found = True
            break

    if not submission_found:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )

    await db.assignments.update_one(
        {"_id": ObjectId(assignment_id)},
        {"$set": {"submissions": submissions}}
    )

    return success_response(
        data={
            "assignment_id": assignment_id,
            "student_id": student_id,
            "marks_obtained": marks_obtained,
            "feedback": feedback
        },
        message="Submission graded successfully"
    )


@router.get("/tests/subject/{subject}", response_model=dict)
async def get_tests_by_subject(
    subject: str,
    current_user: dict = Depends(require_role(["faculty"]))
):
    """Get tests by subject created by current faculty"""
    db = get_database()

    tests = await db.mock_tests.find({
        "subject": subject,
        "created_by": current_user["user_id"]
    }).sort("created_at", -1).to_list(100)

    for test in tests:
        test["id"] = str(test.pop("_id"))

    return success_response(
        data=tests,
        message=f"Tests for subject '{subject}' retrieved successfully"
    )


@router.get("/tests/course/{course_id}", response_model=dict)
async def get_tests_by_course(
    course_id: str,
    current_user: dict = Depends(require_role(["faculty"]))
):
    """Get tests by course created by current faculty"""
    db = get_database()

    tests = await db.mock_tests.find({
        "course_id": course_id,
        "created_by": current_user["user_id"]
    }).sort("created_at", -1).to_list(100)

    for test in tests:
        test["id"] = str(test.pop("_id"))

    return success_response(
        data=tests,
        message=f"Tests for course '{course_id}' retrieved successfully"
    )


@router.put("/tests/{test_id}", response_model=dict)
async def update_test(
    test_id: str,
    test_update: TestUpdate,
    current_user: dict = Depends(require_role(["faculty"]))
):
    """Update a test"""
    db = get_database()

    # Check if test exists and belongs to current faculty
    test = await db.mock_tests.find_one({
        "_id": ObjectId(test_id),
        "created_by": current_user["user_id"]
    })
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test not found or access denied"
        )

    update_data = test_update.model_dump(exclude_unset=True)

    await db.mock_tests.update_one(
        {"_id": ObjectId(test_id)},
        {"$set": update_data}
    )

    # Get updated test
    updated_test = await db.mock_tests.find_one({"_id": ObjectId(test_id)})
    updated_test["id"] = str(updated_test.pop("_id"))

    return success_response(
        data=updated_test,
        message="Test updated successfully"
    )


@router.delete("/tests/{test_id}", response_model=dict)
async def delete_test(
    test_id: str,
    current_user: dict = Depends(require_role(["faculty"]))
):
    """Delete a test"""
    db = get_database()

    # Check if test exists and belongs to current faculty
    test = await db.mock_tests.find_one({
        "_id": ObjectId(test_id),
        "created_by": current_user["user_id"]
    })
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test not found or access denied"
        )

    await db.mock_tests.delete_one({"_id": ObjectId(test_id)})

    return success_response(
        data={"test_id": test_id, "deleted": True},
        message="Test deleted successfully"
    )


@router.get("/test-attempts/{test_id}", response_model=dict)
async def get_test_attempts(
    test_id: str,
    current_user: dict = Depends(require_role(["faculty"]))
):
    """Get all attempts for a test"""
    db = get_database()

    # Check if test exists and belongs to current faculty
    test = await db.mock_tests.find_one({
        "_id": ObjectId(test_id),
        "created_by": current_user["user_id"]
    })
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test not found or access denied"
        )

    attempts = await db.test_attempts.find({"test_id": test_id}).sort("submitted_at", -1).to_list(1000)

    for attempt in attempts:
        attempt["id"] = str(attempt.pop("_id"))

        # Get student details
        student = await db.users.find_one({"_id": ObjectId(attempt["student_id"])})
        if student:
            attempt["student_name"] = student["name"]
            attempt["student_email"] = student["email"]

    return success_response(
        data={
            "test_title": test["test_title"],
            "attempts": attempts
        },
        message="Test attempts retrieved successfully"
    )


@router.patch("/update-profile", response_model=dict)
async def update_faculty_profile(
    profile_update: UserUpdate,
    current_user: dict = Depends(require_role(["faculty"]))
):
    """Update faculty profile"""
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
