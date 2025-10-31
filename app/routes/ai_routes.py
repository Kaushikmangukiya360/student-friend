from fastapi import APIRouter, HTTPException, status, Depends
from app.core.auth import get_current_user, require_role
from app.db.connection import get_database
from app.services.ai_service import ai_service
from app.services.vector_service import vector_service
from app.utils.helpers import success_response, get_timestamp
from app.db.models.chat_model import ChatConversationCreate, ChatConversationResponse, ChatMessageRequest, ChatMessage
from pydantic import BaseModel
from typing import Optional, Literal, List
from bson import ObjectId

router = APIRouter(prefix="/ai", tags=["AI Assistant"])


class AIQueryRequest(BaseModel):
    question: str
    context: Optional[str] = None
    query_type: Literal["qa", "summarize", "explain", "generate_quiz"] = "qa"
    subject: Optional[str] = None


class SummarizeRequest(BaseModel):
    text: str
    subject: Optional[str] = None


class GenerateQuizRequest(BaseModel):
    topic: str
    num_questions: int = 5


@router.post("/query", response_model=dict)
async def ai_query(
    request: AIQueryRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    AI-powered query endpoint
    Supports: Q&A, summarization, explanations, and quiz generation
    """
    db = get_database()
    
    response_data = {}
    
    try:
        if request.query_type == "qa":
            # Question answering
            answer = await ai_service.answer_question(
                question=request.question,
                context=request.context or f"Subject: {request.subject or 'General'}",
                user_id=current_user["user_id"]
            )
            response_data = {
                "type": "qa",
                "question": request.question,
                "answer": answer
            }
            
            # Store query in database
            query_doc = {
                "question_text": request.question,
                "subject": request.subject,
                "asked_by": current_user["user_id"],
                "answered_by": "AI",
                "answer_text": answer,
                "answered_by_type": "ai",
                "timestamp": get_timestamp(),
                "answered_at": get_timestamp()
            }
            result = await db.queries.insert_one(query_doc)
            
            # Index in vector database
            await vector_service.index_query(
                query_id=str(result.inserted_id),
                question=request.question,
                answer=answer,
                subject=request.subject,
                user_id=current_user["user_id"]
            )
        
        elif request.query_type == "summarize":
            # Text summarization
            if not request.context:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Context/text is required for summarization"
                )
            
            summary = await ai_service.summarize_text(request.context)
            response_data = {
                "type": "summarize",
                "original_length": len(request.context),
                "summary": summary
            }
        
        elif request.query_type == "explain":
            # Concept explanation
            explanation = await ai_service.explain_concept(request.question)
            response_data = {
                "type": "explain",
                "concept": request.question,
                "explanation": explanation
            }
            
            # Store in database
            await db.queries.insert_one({
                "question_text": f"Explain: {request.question}",
                "subject": request.subject,
                "asked_by": current_user["user_id"],
                "answered_by": "AI",
                "answer_text": explanation,
                "answered_by_type": "ai",
                "timestamp": get_timestamp(),
                "answered_at": get_timestamp()
            })
        
        elif request.query_type == "generate_quiz":
            # Generate quiz questions
            topic = request.question
            questions = await ai_service.generate_quiz_questions(topic, 5)
            response_data = {
                "type": "generate_quiz",
                "topic": topic,
                "questions": questions,
                "count": len(questions)
            }
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid query type"
            )
        
        return success_response(
            data=response_data,
            message="AI query processed successfully"
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI processing error: {str(e)}"
        )


@router.post("/summarize", response_model=dict)
async def summarize_material(
    request: SummarizeRequest,
    current_user: dict = Depends(get_current_user)
):
    """Summarize educational material"""
    
    try:
        summary = await ai_service.summarize_text(request.text)
        
        return success_response(
            data={
                "original_length": len(request.text),
                "summary_length": len(summary),
                "summary": summary,
                "subject": request.subject
            },
            message="Text summarized successfully"
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Summarization error: {str(e)}"
        )


@router.post("/generate-quiz", response_model=dict)
async def generate_quiz(
    request: GenerateQuizRequest,
    current_user: dict = Depends(get_current_user)
):
    """Generate quiz questions for a topic"""
    
    try:
        questions = await ai_service.generate_quiz_questions(
            topic=request.topic,
            num_questions=request.num_questions
        )
        
        return success_response(
            data={
                "topic": request.topic,
                "questions": questions,
                "count": len(questions)
            },
            message="Quiz questions generated successfully"
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Quiz generation error: {str(e)}"
        )


@router.post("/explain", response_model=dict)
async def explain_concept(
    concept: str,
    current_user: dict = Depends(get_current_user)
):
    """Get detailed explanation of a concept"""
    
    try:
        explanation = await ai_service.explain_concept(concept)
        
        # Store in database
        db = get_database()
        query_doc = {
            "question_text": f"Explain: {concept}",
            "subject": None,
            "asked_by": current_user["user_id"],
            "answered_by": "AI",
            "answer_text": explanation,
            "answered_by_type": "ai",
            "timestamp": get_timestamp(),
            "answered_at": get_timestamp()
        }
        result = await db.queries.insert_one(query_doc)
        
        # Index in vector database
        await vector_service.index_query(
            query_id=str(result.inserted_id),
            question=f"Explain: {concept}",
            answer=explanation,
            subject=None,
            user_id=current_user["user_id"]
        )
        
        return success_response(
            data={
                "concept": concept,
                "explanation": explanation
            },
            message="Concept explained successfully"
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Explanation error: {str(e)}"
        )


@router.get("/query-history", response_model=dict)
async def get_query_history(
    limit: int = 20,
    current_user: dict = Depends(get_current_user)
):
    """Get AI query history for current user"""
    db = get_database()
    
    queries = await db.queries.find(
        {
            "asked_by": current_user["user_id"],
            "answered_by_type": "ai"
        }
    ).sort("timestamp", -1).limit(limit).to_list(limit)
    
    for q in queries:
        q["id"] = str(q.pop("_id"))
    
    return success_response(
        data=queries,
        message="Query history retrieved successfully"
    )


# Chat Conversation Endpoints

@router.post("/chat/start", response_model=dict)
async def start_chat_conversation(
    conversation: ChatConversationCreate,
    current_user: dict = Depends(get_current_user)
):
    """Start a new chat conversation"""
    db = get_database()
    
    # Validate user
    if conversation.user_id != current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create conversation for another user"
        )
    
    conversation_data = conversation.model_dump()
    conversation_data["messages"] = []
    conversation_data["created_at"] = get_timestamp()
    conversation_data["updated_at"] = get_timestamp()
    conversation_data["is_active"] = True
    
    result = await db.chat_conversations.insert_one(conversation_data)
    conversation_data["id"] = str(result.inserted_id)
    
    return success_response(
        data=ChatConversationResponse(**conversation_data).model_dump(),
        message="Chat conversation started successfully"
    )


@router.post("/chat/message", response_model=dict)
async def send_chat_message(
    request: ChatMessageRequest,
    current_user: dict = Depends(get_current_user)
):
    """Send a message in a chat conversation"""
    db = get_database()
    
    conversation = None
    conversation_id = request.conversation_id
    
    if conversation_id:
        # Get existing conversation
        conversation = await db.chat_conversations.find_one({
            "_id": ObjectId(conversation_id),
            "user_id": current_user["user_id"],
            "is_active": True
        })
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found or inactive"
            )
    else:
        # Create new conversation
        conversation_data = {
            "user_id": current_user["user_id"],
            "title": f"Chat {get_timestamp().strftime('%Y-%m-%d %H:%M')}",
            "messages": [],
            "created_at": get_timestamp(),
            "updated_at": get_timestamp(),
            "is_active": True
        }
        result = await db.chat_conversations.insert_one(conversation_data)
        conversation_id = str(result.inserted_id)
        conversation = conversation_data
        conversation["_id"] = result.inserted_id
    
    # Add user message
    user_message = ChatMessage(
        role="user",
        content=request.message,
        timestamp=get_timestamp()
    )
    
    # Get conversation history for context
    messages = conversation.get("messages", [])
    messages.append(user_message.model_dump())
    
    # Generate AI response
    conversation_history = [{"role": msg["role"], "content": msg["content"]} for msg in messages[:-1]]  # Exclude current message
    ai_response = await ai_service.chat_response(request.message, conversation_history, current_user["user_id"])
    
    # Add AI response
    ai_message = ChatMessage(
        role="assistant",
        content=ai_response,
        timestamp=get_timestamp()
    )
    messages.append(ai_message.model_dump())
    
    # Update conversation
    await db.chat_conversations.update_one(
        {"_id": ObjectId(conversation_id)},
        {
            "$set": {
                "messages": messages,
                "updated_at": get_timestamp()
            }
        }
    )
    
    return success_response(
        data={
            "conversation_id": conversation_id,
            "user_message": user_message.model_dump(),
            "ai_response": ai_message.model_dump()
        },
        message="Message sent successfully"
    )


@router.get("/chat/conversations", response_model=dict)
async def get_chat_conversations(
    skip: int = 0,
    limit: int = 20,
    current_user: dict = Depends(get_current_user)
):
    """Get user's chat conversations"""
    db = get_database()
    
    conversations = await db.chat_conversations.find(
        {"user_id": current_user["user_id"]}
    ).sort("updated_at", -1).skip(skip).limit(limit).to_list(limit)
    
    for conv in conversations:
        conv["id"] = str(conv.pop("_id"))
        # Don't include full messages in list view
        conv.pop("messages", None)
    
    total = await db.chat_conversations.count_documents({"user_id": current_user["user_id"]})
    
    return success_response(
        data={
            "conversations": conversations,
            "total": total,
            "skip": skip,
            "limit": limit
        },
        message="Conversations retrieved successfully"
    )


@router.get("/chat/conversations/{conversation_id}", response_model=dict)
async def get_chat_conversation(
    conversation_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific chat conversation with messages"""
    db = get_database()
    
    conversation = await db.chat_conversations.find_one({
        "_id": ObjectId(conversation_id),
        "user_id": current_user["user_id"]
    })
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    conversation["id"] = str(conversation.pop("_id"))
    
    return success_response(
        data=conversation,
        message="Conversation retrieved successfully"
    )


@router.delete("/chat/conversations/{conversation_id}", response_model=dict)
async def delete_chat_conversation(
    conversation_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a chat conversation"""
    db = get_database()
    
    result = await db.chat_conversations.delete_one({
        "_id": ObjectId(conversation_id),
        "user_id": current_user["user_id"]
    })
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    return success_response(
        data={"conversation_id": conversation_id, "deleted": True},
        message="Conversation deleted successfully"
    )


@router.post("/code-explain", response_model=dict)
async def explain_code(
    code: str,
    language: str = "python",
    current_user: dict = Depends(get_current_user)
):
    """Get explanation for code snippets"""
    
    try:
        explanation = await ai_service.generate_code_explanation(code, language)
        
        # Store in database as query
        db = get_database()
        query_doc = {
            "question_text": f"Code explanation ({language}): {code[:100]}...",
            "subject": "Programming",
            "asked_by": current_user["user_id"],
            "answered_by": "AI",
            "answer_text": explanation,
            "answered_by_type": "ai",
            "timestamp": get_timestamp(),
            "answered_at": get_timestamp()
        }
        result = await db.queries.insert_one(query_doc)
        
        # Index in vector database
        await vector_service.index_query(
            query_id=str(result.inserted_id),
            question=query_doc["question_text"],
            answer=explanation,
            subject="Programming",
            user_id=current_user["user_id"]
        )
        
        return success_response(
            data={
                "code": code,
                "language": language,
                "explanation": explanation
            },
            message="Code explained successfully"
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Code explanation error: {str(e)}"
        )


@router.post("/solve-problem", response_model=dict)
async def solve_academic_problem(
    problem: str,
    subject: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Solve academic problems step by step"""
    
    try:
        solution = await ai_service.solve_problem(problem, subject)
        
        # Store in database as query
        db = get_database()
        query_doc = {
            "question_text": f"Problem: {problem}",
            "subject": subject,
            "asked_by": current_user["user_id"],
            "answered_by": "AI",
            "answer_text": solution,
            "answered_by_type": "ai",
            "timestamp": get_timestamp(),
            "answered_at": get_timestamp()
        }
        result = await db.queries.insert_one(query_doc)
        
        # Index in vector database
        await vector_service.index_query(
            query_id=str(result.inserted_id),
            question=f"Problem: {problem}",
            answer=solution,
            subject=subject,
            user_id=current_user["user_id"]
        )
        
        return success_response(
            data={
                "problem": problem,
                "subject": subject,
                "solution": solution
            },
            message="Problem solved successfully"
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Problem solving error: {str(e)}"
        )


# Vector Database Management Routes (Admin only)

@router.post("/vector/index-material/{material_id}", response_model=dict)
async def index_material_in_vector_db(
    material_id: str,
    current_user: dict = Depends(require_role(["admin"]))
):
    """Index a material in the vector database for semantic search"""
    db = get_database()
    
    # Get material from database
    material = await db.materials.find_one({"_id": ObjectId(material_id)})
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found"
        )
    
    # Index in vector database
    success = await vector_service.index_material(
        material_id=material_id,
        title=material.get("title", ""),
        content=material.get("description", ""),
        subject=material.get("subject", ""),
        course_id=material.get("course_id", ""),
        tags=material.get("tags", [])
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to index material in vector database"
        )
    
    return success_response(
        data={"material_id": material_id, "indexed": True},
        message="Material indexed successfully in vector database"
    )


@router.post("/vector/index-course/{course_id}", response_model=dict)
async def index_course_in_vector_db(
    course_id: str,
    current_user: dict = Depends(require_role(["admin"]))
):
    """Index a course in the vector database for semantic search"""
    db = get_database()
    
    # Get course from database
    course = await db.courses.find_one({"_id": ObjectId(course_id)})
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # Index in vector database
    success = await vector_service.index_course(
        course_id=course_id,
        name=course.get("name", ""),
        description=course.get("description", ""),
        subject_id=course.get("subject_id", ""),
        syllabus=course.get("syllabus", "")
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to index course in vector database"
        )
    
    return success_response(
        data={"course_id": course_id, "indexed": True},
        message="Course indexed successfully in vector database"
    )


@router.post("/vector/index-query/{query_id}", response_model=dict)
async def index_query_in_vector_db(
    query_id: str,
    current_user: dict = Depends(require_role(["admin"]))
):
    """Index a query in the vector database for semantic search"""
    db = get_database()
    
    # Get query from database
    query = await db.queries.find_one({"_id": ObjectId(query_id)})
    if not query:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Query not found"
        )
    
    # Index in vector database
    success = await vector_service.index_query(
        query_id=query_id,
        question=query.get("question_text", ""),
        answer=query.get("answer_text", ""),
        subject=query.get("subject", ""),
        user_id=query.get("asked_by", "")
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to index query in vector database"
        )
    
    return success_response(
        data={"query_id": query_id, "indexed": True},
        message="Query indexed successfully in vector database"
    )


@router.post("/vector/bulk-index", response_model=dict)
async def bulk_index_content(
    content_type: Literal["materials", "courses", "queries"],
    limit: int = 100,
    current_user: dict = Depends(require_role(["admin"]))
):
    """Bulk index content in vector database"""
    db = get_database()
    
    indexed_count = 0
    errors = []
    
    if content_type == "materials":
        materials = await db.materials.find().limit(limit).to_list(limit)
        for material in materials:
            material_id = str(material["_id"])
            success = await vector_service.index_material(
                material_id=material_id,
                title=material.get("title", ""),
                content=material.get("description", ""),
                subject=material.get("subject", ""),
                course_id=material.get("course_id", ""),
                tags=material.get("tags", [])
            )
            if success:
                indexed_count += 1
            else:
                errors.append(f"Failed to index material {material_id}")
    
    elif content_type == "courses":
        courses = await db.courses.find().limit(limit).to_list(limit)
        for course in courses:
            course_id = str(course["_id"])
            success = await vector_service.index_course(
                course_id=course_id,
                name=course.get("name", ""),
                description=course.get("description", ""),
                subject_id=course.get("subject_id", ""),
                syllabus=course.get("syllabus", "")
            )
            if success:
                indexed_count += 1
            else:
                errors.append(f"Failed to index course {course_id}")
    
    elif content_type == "queries":
        queries = await db.queries.find().limit(limit).to_list(limit)
        for query in queries:
            query_id = str(query["_id"])
            success = await vector_service.index_query(
                query_id=query_id,
                question=query.get("question_text", ""),
                answer=query.get("answer_text", ""),
                subject=query.get("subject", ""),
                user_id=query.get("asked_by", "")
            )
            if success:
                indexed_count += 1
            else:
                errors.append(f"Failed to index query {query_id}")
    
    return success_response(
        data={
            "content_type": content_type,
            "indexed_count": indexed_count,
            "total_attempted": len(materials) if content_type == "materials" else len(courses) if content_type == "courses" else len(queries),
            "errors": errors
        },
        message=f"Bulk indexing completed for {content_type}"
    )


@router.get("/vector/search", response_model=dict)
async def search_vector_database(
    query: str,
    content_type: Literal["materials", "courses", "queries"] = "materials",
    subject: Optional[str] = None,
    course_id: Optional[str] = None,
    limit: int = 5,
    current_user: dict = Depends(get_current_user)
):
    """Search vector database for relevant content"""
    
    if content_type == "materials":
        results = await vector_service.search_materials(
            query=query,
            subject=subject,
            course_id=course_id,
            limit=limit
        )
    elif content_type == "courses":
        results = await vector_service.search_courses(
            query=query,
            subject_id=subject,
            limit=limit
        )
    elif content_type == "queries":
        results = await vector_service.search_similar_queries(
            query=query,
            subject=subject,
            user_id=current_user["user_id"],
            limit=limit
        )
    
    return success_response(
        data={
            "query": query,
            "content_type": content_type,
            "results": results,
            "count": len(results)
        },
        message="Vector search completed successfully"
    )
