from fastapi import APIRouter, HTTPException, status, Depends, Query, Request
from app.core.auth import require_role
from app.db.connection import get_database
from app.utils.helpers import success_response, get_timestamp
from app.utils.enhanced_responses import (
    success_response as enhanced_success_response,
    paginated_response,
    ValidationException,
    NotFoundException,
    ForbiddenException,
    validate_object_id,
    sanitize_string
)
from app.services.test_service import test_service
from app.services.vector_service import vector_service
from app.middleware.caching import cached, cache
from app.db.models.subject_model import SubjectCreate, SubjectUpdate, SubjectResponse
from app.db.models.course_model import CourseCreate, CourseUpdate, CourseResponse
from app.db.models.college_model import CollegeCreate, CollegeUpdate, CollegeResponse
from bson import ObjectId
from datetime import datetime, timedelta
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.post("/verify-faculty/{user_id}", response_model=dict)
async def verify_faculty(
    user_id: str,
    current_user: dict = Depends(require_role(["admin"]))
):
    """Verify a faculty member"""
    try:
        logger.info(f"Faculty verification attempt for user {user_id} by admin {current_user['user_id']}")

        # Validate user ID
        user_id = validate_object_id(user_id)

        db = get_database()

        # Check if user exists and is faculty
        user = await db.users.find_one({
            "_id": ObjectId(user_id),
            "role": "faculty"
        })

        if not user:
            logger.warning(f"Faculty verification failed: user {user_id} not found or not faculty")
            raise NotFoundException("faculty", user_id)

        if user.get("verified", False):
            raise ValidationException("Faculty is already verified")

        # Update verification status
        result = await db.users.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$set": {
                    "verified": True,
                    "verified_at": get_timestamp(),
                    "verified_by": current_user["user_id"]
                }
            }
        )

        if result.modified_count == 0:
            logger.error(f"Failed to update verification status for faculty {user_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to verify faculty"
            )

        # Create notification for faculty
        await db.notifications.insert_one({
            "user_id": user_id,
            "message": "Your faculty account has been verified! You can now create assignments and tests.",
            "type": "success",
            "read_status": False,
            "timestamp": get_timestamp(),
            "created_by": current_user["user_id"]
        })

        # Invalidate cache for faculty lists
        cache.delete(f"pending_faculties")
        cache.delete(f"faculty_stats")

        logger.info(f"Faculty {user_id} verified successfully by admin {current_user['user_id']}")
        return enhanced_success_response(
            data={"user_id": user_id, "verified": True},
            message="Faculty verified successfully"
        )

    except ValidationException as e:
        logger.warning(f"Validation error in verify faculty: {str(e)}")
        raise
    except NotFoundException as e:
        logger.warning(f"Not found error in verify faculty: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in verify faculty: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Faculty verification failed"
        )


@router.get("/pending-faculties", response_model=dict)
@cached(ttl=300, key_prefix="pending_faculties")  # Cache for 5 minutes
async def get_pending_faculties(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(require_role(["admin"]))
):
    """Get all unverified faculty members with pagination"""
    try:
        logger.info(f"Pending faculties request by admin {current_user['user_id']} - page {page}, limit {limit}")

        db = get_database()

        # Calculate skip
        skip = (page - 1) * limit

        # Get total count
        total_count = await db.users.count_documents({
            "role": "faculty",
            "verified": False
        })

        # Get paginated results
        faculties = await db.users.find({
            "role": "faculty",
            "verified": False
        }).skip(skip).limit(limit).to_list(length=None)

        # Process faculties data
        for faculty in faculties:
            faculty["id"] = str(faculty.pop("_id"))
            faculty.pop("hashed_password", None)
            faculty.pop("password", None)

        logger.info(f"Retrieved {len(faculties)} pending faculties (total: {total_count})")
        return paginated_response(
            items=faculties,
            total=total_count,
            page=page,
            limit=limit,
            message="Pending faculties retrieved successfully"
        )

    except Exception as e:
        logger.error(f"Unexpected error in get pending faculties: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve pending faculties"
        )


@router.get("/reports/overview", response_model=dict)
@cached(ttl=600, key_prefix="platform_overview")  # Cache for 10 minutes
async def get_platform_overview(
    current_user: dict = Depends(require_role(["admin"]))
):
    """Get platform overview statistics"""
    try:
        logger.info(f"Platform overview request by admin {current_user['user_id']}")

        db = get_database()

        # Count users by role
        total_students = await db.users.count_documents({"role": "student"})
        total_faculties = await db.users.count_documents({"role": "faculty"})
        verified_faculties = await db.users.count_documents({"role": "faculty", "verified": True})

        # Count content
        total_materials = await db.materials.count_documents({})
        total_queries = await db.queries.count_documents({})
        total_tests = await db.mock_tests.count_documents({})
        total_assignments = await db.assignments.count_documents({})

        # Count sessions
        total_sessions = await db.sessions.count_documents({})
        completed_sessions = await db.sessions.count_documents({"status": "completed"})
        pending_sessions = await db.sessions.count_documents({"status": "pending"})

        # Get recent activity (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)

        recent_signups = await db.users.count_documents({
            "created_at": {"$gte": thirty_days_ago}
        })

        recent_materials = await db.materials.count_documents({
            "timestamp": {"$gte": thirty_days_ago}
        })

        recent_queries = await db.queries.count_documents({
            "timestamp": {"$gte": thirty_days_ago}
        })

        # Calculate completion rate safely
        completion_rate = 0.0
        if total_sessions > 0:
            completion_rate = round((completed_sessions / total_sessions * 100), 2)

        overview = {
            "users": {
                "total_students": total_students,
                "total_faculties": total_faculties,
                "verified_faculties": verified_faculties,
                "pending_faculties": total_faculties - verified_faculties
            },
            "content": {
                "total_materials": total_materials,
                "total_queries": total_queries,
                "total_tests": total_tests,
                "total_assignments": total_assignments
            },
            "sessions": {
                "total_sessions": total_sessions,
                "completed_sessions": completed_sessions,
                "pending_sessions": pending_sessions,
                "completion_rate": completion_rate
            },
            "recent_activity": {
                "new_signups": recent_signups,
                "new_materials": recent_materials,
                "new_queries": recent_queries,
                "period_days": 30
            },
            "generated_at": datetime.utcnow().isoformat()
        }

        logger.info(f"Platform overview generated for admin {current_user['user_id']}")
        return enhanced_success_response(
            data=overview,
            message="Platform overview retrieved successfully"
        )

    except Exception as e:
        logger.error(f"Unexpected error in platform overview: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve platform overview"
        )


@router.get("/reports/test-analytics", response_model=dict)
async def get_test_analytics(
    test_id: Optional[str] = None,
    current_user: dict = Depends(require_role(["admin"]))
):
    """Get analytics for tests"""
    db = get_database()
    
    if test_id:
        # Get analytics for specific test
        test = await db.mock_tests.find_one({"_id": ObjectId(test_id)})
        if not test:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Test not found"
            )
        
        attempts = await db.test_attempts.find({"test_id": test_id}).to_list(1000)
        
        analytics = test_service.calculate_analytics(attempts)
        analytics["test_title"] = test["test_title"]
        analytics["test_id"] = test_id
        
        return success_response(
            data=analytics,
            message="Test analytics retrieved successfully"
        )
    else:
        # Get overall test analytics
        total_tests = await db.mock_tests.count_documents({})
        total_attempts = await db.test_attempts.count_documents({})
        
        # Get average scores
        pipeline = [
            {
                "$group": {
                    "_id": None,
                    "avg_score": {"$avg": "$score"},
                    "avg_percentage": {"$avg": "$percentage"}
                }
            }
        ]
        
        result = await db.test_attempts.aggregate(pipeline).to_list(1)
        avg_data = result[0] if result else {"avg_score": 0, "avg_percentage": 0}
        
        analytics = {
            "total_tests": total_tests,
            "total_attempts": total_attempts,
            "average_score": round(avg_data.get("avg_score", 0), 2),
            "average_percentage": round(avg_data.get("avg_percentage", 0), 2)
        }
        
        return success_response(
            data=analytics,
            message="Overall test analytics retrieved successfully"
        )


@router.get("/reports/transactions", response_model=dict)
async def get_transaction_report(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(require_role(["admin"]))
):
    """Get transaction report"""
    db = get_database()
    
    query = {}
    
    if start_date:
        query["timestamp"] = {"$gte": datetime.fromisoformat(start_date)}
    
    if end_date:
        if "timestamp" not in query:
            query["timestamp"] = {}
        query["timestamp"]["$lte"] = datetime.fromisoformat(end_date)
    
    transactions = await db.transactions.find(query).sort("timestamp", -1).to_list(1000)
    
    # Calculate summary
    total_credits = sum(t["amount"] for t in transactions if t["type"] == "credit")
    total_debits = sum(t["amount"] for t in transactions if t["type"] == "debit")
    
    for txn in transactions:
        txn["id"] = str(txn.pop("_id"))
    
    report = {
        "transactions": transactions,
        "summary": {
            "total_transactions": len(transactions),
            "total_credits": round(total_credits, 2),
            "total_debits": round(total_debits, 2),
            "net_amount": round(total_credits - total_debits, 2)
        }
    }
    
    return success_response(
        data=report,
        message="Transaction report retrieved successfully"
    )


@router.get("/reports/user-activity/{user_id}", response_model=dict)
async def get_user_activity(
    user_id: str,
    current_user: dict = Depends(require_role(["admin"]))
):
    """Get detailed activity report for a user"""
    db = get_database()
    
    # Get user
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    activity = {
        "user_info": {
            "id": str(user["_id"]),
            "name": user["name"],
            "email": user["email"],
            "role": user["role"],
            "verified": user["verified"]
        }
    }
    
    if user["role"] == "student":
        # Student activity
        materials_uploaded = await db.materials.count_documents({"uploaded_by": user_id})
        queries_asked = await db.queries.count_documents({"asked_by": user_id})
        tests_taken = await db.test_attempts.count_documents({"student_id": user_id})
        sessions_booked = await db.sessions.count_documents({"student_id": user_id})
        
        activity["activity"] = {
            "materials_uploaded": materials_uploaded,
            "queries_asked": queries_asked,
            "tests_taken": tests_taken,
            "sessions_booked": sessions_booked
        }
    
    elif user["role"] == "faculty":
        # Faculty activity
        materials_uploaded = await db.materials.count_documents({"uploaded_by": user_id})
        queries_answered = await db.queries.count_documents({
            "answered_by": user_id,
            "answered_by_type": "faculty"
        })
        tests_created = await db.mock_tests.count_documents({"created_by": user_id})
        assignments_created = await db.assignments.count_documents({"created_by": user_id})
        sessions_conducted = await db.sessions.count_documents({
            "faculty_id": user_id,
            "status": "completed"
        })
        
        activity["activity"] = {
            "materials_uploaded": materials_uploaded,
            "queries_answered": queries_answered,
            "tests_created": tests_created,
            "assignments_created": assignments_created,
            "sessions_conducted": sessions_conducted
        }
    
    return success_response(
        data=activity,
        message="User activity retrieved successfully"
    )


@router.delete("/users/{user_id}", response_model=dict)
async def delete_user(
    user_id: str,
    current_user: dict = Depends(require_role(["admin"]))
):
    """Delete a user (soft delete or hard delete)"""
    db = get_database()
    
    # Check if user exists
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Don't allow deleting admin users
    if user["role"] == "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete admin users"
        )
    
    # Hard delete (be careful with this in production)
    await db.users.delete_one({"_id": ObjectId(user_id)})
    
    return success_response(
        data={"user_id": user_id, "deleted": True},
        message="User deleted successfully"
    )


# College CRUD Operations

@router.post("/colleges", response_model=dict)
async def create_college(
    college: CollegeCreate,
    current_user: dict = Depends(require_role(["admin"]))
):
    """Create a new college"""
    db = get_database()
    
    # Check if college with same name already exists
    existing = await db.colleges.find_one({"name": college.name})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="College with this name already exists"
        )
    
    college_data = college.model_dump()
    college_data["created_at"] = get_timestamp()
    college_data["updated_at"] = get_timestamp()
    
    result = await db.colleges.insert_one(college_data)
    college_data["id"] = str(result.inserted_id)
    
    return success_response(
        data=CollegeResponse(**college_data).model_dump(),
        message="College created successfully"
    )


@router.get("/colleges", response_model=dict)
async def get_all_colleges(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: dict = Depends(require_role(["admin"]))
):
    """Get all colleges with pagination"""
    db = get_database()
    
    colleges = await db.colleges.find().skip(skip).limit(limit).to_list(limit)
    
    for college in colleges:
        college["id"] = str(college.pop("_id"))
    
    total = await db.colleges.count_documents({})
    
    return success_response(
        data={
            "colleges": colleges,
            "total": total,
            "skip": skip,
            "limit": limit
        },
        message="Colleges retrieved successfully"
    )


@router.get("/colleges/{college_id}", response_model=dict)
async def get_college(
    college_id: str,
    current_user: dict = Depends(require_role(["admin"]))
):
    """Get a specific college by ID"""
    db = get_database()
    
    college = await db.colleges.find_one({"_id": ObjectId(college_id)})
    if not college:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="College not found"
        )
    
    college["id"] = str(college.pop("_id"))
    
    return success_response(
        data=college,
        message="College retrieved successfully"
    )


@router.put("/colleges/{college_id}", response_model=dict)
async def update_college(
    college_id: str,
    college_update: CollegeUpdate,
    current_user: dict = Depends(require_role(["admin"]))
):
    """Update a college"""
    db = get_database()
    
    # Check if college exists
    existing = await db.colleges.find_one({"_id": ObjectId(college_id)})
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="College not found"
        )
    
    # Check if updating to a name that already exists
    if college_update.name:
        duplicate = await db.colleges.find_one({
            "name": college_update.name,
            "_id": {"$ne": ObjectId(college_id)}
        })
        if duplicate:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="College with this name already exists"
            )
    
    update_data = college_update.model_dump(exclude_unset=True)
    update_data["updated_at"] = get_timestamp()
    
    await db.colleges.update_one(
        {"_id": ObjectId(college_id)},
        {"$set": update_data}
    )
    
    # Get updated college
    updated_college = await db.colleges.find_one({"_id": ObjectId(college_id)})
    updated_college["id"] = str(updated_college.pop("_id"))
    
    return success_response(
        data=updated_college,
        message="College updated successfully"
    )


@router.delete("/colleges/{college_id}", response_model=dict)
async def delete_college(
    college_id: str,
    current_user: dict = Depends(require_role(["admin"]))
):
    """Delete a college"""
    db = get_database()
    
    # Check if college exists
    college = await db.colleges.find_one({"_id": ObjectId(college_id)})
    if not college:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="College not found"
        )
    
    # Check if college has associated subjects
    subjects_count = await db.subjects.count_documents({"college_id": college_id})
    if subjects_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete college. It has associated subjects: {subjects_count} subject(s)"
        )
    
    await db.colleges.delete_one({"_id": ObjectId(college_id)})
    
    return success_response(
        data={"college_id": college_id, "deleted": True},
        message="College deleted successfully"
    )


# Subject CRUD Operations

@router.post("/subjects", response_model=dict)
async def create_subject(
    subject: SubjectCreate,
    current_user: dict = Depends(require_role(["admin"]))
):
    """Create a new subject"""
    db = get_database()
    
    # Validate college exists
    college = await db.colleges.find_one({"_id": ObjectId(subject.college_id)})
    if not college:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="College not found"
        )
    
    # Check if subject with same name already exists in the college
    existing = await db.subjects.find_one({
        "name": subject.name,
        "college_id": subject.college_id
    })
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Subject with this name already exists in the college"
        )
    
    subject_data = subject.model_dump()
    subject_data["created_at"] = get_timestamp()
    subject_data["updated_at"] = get_timestamp()
    
    result = await db.subjects.insert_one(subject_data)
    subject_data["id"] = str(result.inserted_id)
    
    return success_response(
        data=SubjectResponse(**subject_data).model_dump(),
        message="Subject created successfully"
    )


@router.get("/subjects", response_model=dict)
async def get_all_subjects(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    college_id: Optional[str] = None,
    current_user: dict = Depends(require_role(["admin"]))
):
    """Get all subjects with optional college filtering"""
    db = get_database()
    
    query = {}
    if college_id:
        query["college_id"] = college_id
    
    subjects = await db.subjects.find(query).skip(skip).limit(limit).to_list(limit)
    
    # Populate college info
    for subject in subjects:
        subject["id"] = str(subject.pop("_id"))
        
        # Get college info
        college = await db.colleges.find_one({"_id": ObjectId(subject["college_id"])})
        if college:
            subject["college"] = {
                "id": str(college["_id"]),
                "name": college["name"],
                "location": college.get("location")
            }
    
    total = await db.subjects.count_documents(query)
    
    return success_response(
        data={
            "subjects": subjects,
            "total": total,
            "skip": skip,
            "limit": limit
        },
        message="Subjects retrieved successfully"
    )


@router.get("/subjects/{subject_id}", response_model=dict)
async def get_subject(
    subject_id: str,
    current_user: dict = Depends(require_role(["admin"]))
):
    """Get a specific subject by ID"""
    db = get_database()
    
    subject = await db.subjects.find_one({"_id": ObjectId(subject_id)})
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    
    subject["id"] = str(subject.pop("_id"))
    
    return success_response(
        data=subject,
        message="Subject retrieved successfully"
    )


@router.put("/subjects/{subject_id}", response_model=dict)
async def update_subject(
    subject_id: str,
    subject_update: SubjectUpdate,
    current_user: dict = Depends(require_role(["admin"]))
):
    """Update a subject"""
    db = get_database()
    
    # Check if subject exists
    existing = await db.subjects.find_one({"_id": ObjectId(subject_id)})
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    
    # Validate college if being updated
    if subject_update.college_id:
        college = await db.colleges.find_one({"_id": ObjectId(subject_update.college_id)})
        if not college:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="College not found"
            )
    
    # Check if updating to a name that already exists in the college
    if subject_update.name:
        college_id = subject_update.college_id or existing["college_id"]
        duplicate = await db.subjects.find_one({
            "name": subject_update.name,
            "college_id": college_id,
            "_id": {"$ne": ObjectId(subject_id)}
        })
        if duplicate:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Subject with this name already exists in the college"
            )
    
    update_data = subject_update.model_dump(exclude_unset=True)
    update_data["updated_at"] = get_timestamp()
    
    await db.subjects.update_one(
        {"_id": ObjectId(subject_id)},
        {"$set": update_data}
    )
    
    # Get updated subject
    updated_subject = await db.subjects.find_one({"_id": ObjectId(subject_id)})
    updated_subject["id"] = str(updated_subject.pop("_id"))
    
    return success_response(
        data=updated_subject,
        message="Subject updated successfully"
    )


@router.delete("/subjects/{subject_id}", response_model=dict)
async def delete_subject(
    subject_id: str,
    current_user: dict = Depends(require_role(["admin"]))
):
    """Delete a subject"""
    db = get_database()
    
    # Check if subject exists
    subject = await db.subjects.find_one({"_id": ObjectId(subject_id)})
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    
    # Check if subject is being used by courses
    courses_using = await db.courses.count_documents({"subject_id": subject_id})
    if courses_using > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete subject. It is being used by {courses_using} course(s)"
        )
    
    await db.subjects.delete_one({"_id": ObjectId(subject_id)})
    
    return success_response(
        data={"subject_id": subject_id, "deleted": True},
        message="Subject deleted successfully"
    )


# Course CRUD Operations

@router.post("/courses", response_model=dict)
async def create_course(
    course: CourseCreate,
    current_user: dict = Depends(require_role(["admin"]))
):
    """Create a new course"""
    db = get_database()
    
    # Validate college exists
    college = await db.colleges.find_one({"_id": ObjectId(course.college_id)})
    if not college:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="College not found"
        )
    
    # Validate subject exists and belongs to the college
    subject = await db.subjects.find_one({
        "_id": ObjectId(course.subject_id),
        "college_id": course.college_id
    })
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found or does not belong to the specified college"
        )
    
    # Validate faculty exists and is verified
    faculty = await db.users.find_one({
        "_id": ObjectId(course.faculty_id),
        "role": "faculty",
        "verified": True
    })
    if not faculty:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Faculty not found or not verified"
        )
    
    course_data = course.model_dump()
    course_data["created_at"] = get_timestamp()
    course_data["updated_at"] = get_timestamp()
    
    result = await db.courses.insert_one(course_data)
    course_data["id"] = str(result.inserted_id)
    
    # Index in vector database for semantic search
    await vector_service.index_course(
        course_id=str(result.inserted_id),
        name=course.name,
        description=course.description,
        subject_id=course.subject_id,
        syllabus=course.syllabus
    )
    
    return success_response(
        data=CourseResponse(**course_data).model_dump(),
        message="Course created successfully"
    )


@router.get("/courses", response_model=dict)
async def get_all_courses(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    college_id: Optional[str] = None,
    subject_id: Optional[str] = None,
    faculty_id: Optional[str] = None,
    current_user: dict = Depends(require_role(["admin"]))
):
    """Get all courses with optional filtering"""
    db = get_database()
    
    query = {}
    if college_id:
        query["college_id"] = college_id
    if subject_id:
        query["subject_id"] = subject_id
    if faculty_id:
        query["faculty_id"] = faculty_id
    
    courses = await db.courses.find(query).skip(skip).limit(limit).to_list(limit)
    
    # Populate college, subject and faculty info
    for course in courses:
        course["id"] = str(course.pop("_id"))
        
        # Get college info
        college = await db.colleges.find_one({"_id": ObjectId(course["college_id"])})
        if college:
            course["college"] = {
                "id": str(college["_id"]),
                "name": college["name"],
                "location": college.get("location")
            }
        
        # Get subject info
        subject = await db.subjects.find_one({"_id": ObjectId(course["subject_id"])})
        if subject:
            course["subject"] = {
                "id": str(subject["_id"]),
                "name": subject["name"],
                "category": subject.get("category")
            }
        
        # Get faculty info
        faculty = await db.users.find_one({"_id": ObjectId(course["faculty_id"])})
        if faculty:
            course["faculty"] = {
                "id": str(faculty["_id"]),
                "name": faculty["name"],
                "email": faculty["email"]
            }
    
    total = await db.courses.count_documents(query)
    
    return success_response(
        data={
            "courses": courses,
            "total": total,
            "skip": skip,
            "limit": limit
        },
        message="Courses retrieved successfully"
    )


@router.get("/courses/{course_id}", response_model=dict)
async def get_course(
    course_id: str,
    current_user: dict = Depends(require_role(["admin"]))
):
    """Get a specific course by ID"""
    db = get_database()
    
    course = await db.courses.find_one({"_id": ObjectId(course_id)})
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    course["id"] = str(course.pop("_id"))
    
    # Get college info
    college = await db.colleges.find_one({"_id": ObjectId(course["college_id"])})
    if college:
        course["college"] = {
            "id": str(college["_id"]),
            "name": college["name"],
            "location": college.get("location")
        }
    
    # Get subject info
    subject = await db.subjects.find_one({"_id": ObjectId(course["subject_id"])})
    if subject:
        course["subject"] = {
            "id": str(subject["_id"]),
            "name": subject["name"],
            "category": subject.get("category")
        }
    
    # Get faculty info
    faculty = await db.users.find_one({"_id": ObjectId(course["faculty_id"])})
    if faculty:
        course["faculty"] = {
            "id": str(faculty["_id"]),
            "name": faculty["name"],
            "email": faculty["email"]
        }
    
    return success_response(
        data=course,
        message="Course retrieved successfully"
    )


@router.put("/courses/{course_id}", response_model=dict)
async def update_course(
    course_id: str,
    course_update: CourseUpdate,
    current_user: dict = Depends(require_role(["admin"]))
):
    """Update a course"""
    db = get_database()
    
    # Check if course exists
    existing = await db.courses.find_one({"_id": ObjectId(course_id)})
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # Validate college if being updated
    if course_update.college_id:
        college = await db.colleges.find_one({"_id": ObjectId(course_update.college_id)})
        if not college:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="College not found"
            )
    
    # Validate subject if being updated
    if course_update.subject_id:
        college_id = course_update.college_id or existing["college_id"]
        subject = await db.subjects.find_one({
            "_id": ObjectId(course_update.subject_id),
            "college_id": college_id
        })
        if not subject:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subject not found or does not belong to the specified college"
            )
    
    # Validate faculty if being updated
    if course_update.faculty_id:
        faculty = await db.users.find_one({
            "_id": ObjectId(course_update.faculty_id),
            "role": "faculty",
            "verified": True
        })
        if not faculty:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Faculty not found or not verified"
            )
    
    update_data = course_update.model_dump(exclude_unset=True)
    update_data["updated_at"] = get_timestamp()
    
    await db.courses.update_one(
        {"_id": ObjectId(course_id)},
        {"$set": update_data}
    )
    
    # Get updated course
    updated_course = await db.courses.find_one({"_id": ObjectId(course_id)})
    updated_course["id"] = str(updated_course.pop("_id"))
    
    return success_response(
        data=updated_course,
        message="Course updated successfully"
    )


@router.delete("/courses/{course_id}", response_model=dict)
async def delete_course(
    course_id: str,
    current_user: dict = Depends(require_role(["admin"]))
):
    """Delete a course"""
    db = get_database()
    
    # Check if course exists
    course = await db.courses.find_one({"_id": ObjectId(course_id)})
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # Check if course has associated materials, tests, assignments, or sessions
    materials_count = await db.materials.count_documents({"course_id": course_id})
    tests_count = await db.mock_tests.count_documents({"course_id": course_id})
    assignments_count = await db.assignments.count_documents({"course_id": course_id})
    sessions_count = await db.sessions.count_documents({"course_id": course_id})
    
    if any([materials_count, tests_count, assignments_count, sessions_count]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete course. It has associated content: {materials_count} materials, {tests_count} tests, {assignments_count} assignments, {sessions_count} sessions"
        )
    
    await db.courses.delete_one({"_id": ObjectId(course_id)})
    
    return success_response(
        data={"course_id": course_id, "deleted": True},
        message="Course deleted successfully"
    )
