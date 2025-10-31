import inspect
import sys
from typing import Any, Dict, List

# Python 3.12 compatibility patch for pydantic/typing ForwardRef used by langchain/langsmith
if sys.version_info >= (3, 12):
    try:
        from typing import ForwardRef

        if "recursive_guard" in inspect.signature(ForwardRef._evaluate).parameters:
            _original_forward_evaluate = ForwardRef._evaluate

            def _patched_forward_evaluate(self, *args, **kwargs):
                recursive_guard = kwargs.get("recursive_guard")
                if recursive_guard is None:
                    kwargs["recursive_guard"] = set()
                return _original_forward_evaluate(self, *args, **kwargs)

            ForwardRef._evaluate = _patched_forward_evaluate  # type: ignore[attr-defined]
    except Exception:
        # If anything goes wrong, we silently continue; downstream imports will raise useful errors
        pass

from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_groq import ChatGroq
from app.core.config import settings
from app.db.connection import get_database
from app.services.vector_service import vector_service
from bson import ObjectId
from typing import Any, Dict, List, Optional


class AIService:
    """AI Service using LangChain and Groq API"""
    
    def __init__(self):
        self.llm = ChatGroq(
            groq_api_key=settings.GROQ_API_KEY,
            model_name="mixtral-8x7b-32768",
            temperature=0.7
        )
    
    async def get_user_context(self, user_id: str, query: str = "") -> str:
        """Get user's learning context from database and vector search"""
        db = get_database()
        
        context_parts = []
        
        # Get user info
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if user:
            context_parts.append(f"User: {user['name']} ({user['role']})")
        
        # Get enrolled courses
        enrollments = await db.enrollments.find({"student_id": user_id}).to_list(50)
        enrolled_course_ids = [enrollment["course_id"] for enrollment in enrollments]
        
        # Get course details
        course_details = []
        subjects = set()
        for course_id in enrolled_course_ids:
            course = await db.courses.find_one({"_id": ObjectId(course_id)})
            if course:
                course_details.append(f"Course: {course['name']} - {course.get('description', '')} (Progress: {enrollments[enrolled_course_ids.index(course_id)]['progress_percentage']}%)")
                subjects.add(course.get("subject_id"))
        
        # Get subject details
        subject_details = []
        for subject_id in subjects:
            subject = await db.subjects.find_one({"_id": ObjectId(subject_id)})
            if subject:
                subject_details.append(f"Subject: {subject['name']} - {subject.get('description', '')}")
        
        # Use vector search to find relevant materials if query is provided
        relevant_materials = []
        if query:
            # Search for materials relevant to the query
            vector_results = await vector_service.search_materials(
                query=query,
                limit=5
            )
            
            for result in vector_results:
                if result['relevance_score'] > 0.7:  # Only include highly relevant results
                    relevant_materials.append(f"Relevant Material: {result['title']} - {result['content'][:300]}...")
        
        # Get recent queries
        recent_queries = await db.queries.find({"asked_by": user_id}).sort("timestamp", -1).limit(5).to_list(5)
        query_history = []
        for q in recent_queries:
            query_history.append(f"Previous Q: {q['question_text'][:100]}... A: {q.get('answer_text', '')[:100]}...")
        
        # Combine context
        context = "User Learning Context:\n"
        if course_details:
            context += "Enrolled Courses:\n" + "\n".join(course_details) + "\n\n"
        if subject_details:
            context += "Study Subjects:\n" + "\n".join(subject_details) + "\n\n"
        if relevant_materials:
            context += "Relevant Materials:\n" + "\n".join(relevant_materials) + "\n\n"
        if query_history:
            context += "Recent Q&A History:\n" + "\n".join(query_history) + "\n\n"
        
        return context
    
    async def answer_question(self, question: str, context: str = "", user_id: Optional[str] = None) -> str:
        """Answer a question using Groq API with user context"""
        # Get user-specific context with vector search
        user_context = ""
        if user_id:
            user_context = await self.get_user_context(user_id, question)
        
        full_context = f"{user_context}\nAdditional Context: {context}" if context else user_context
        
        prompt_template = """You are an intelligent educational assistant helping students and faculty.
        
{context}

Question: {question}

Answer based on the user's learning context, courses, and available materials. If the question is not related to the available context, say so and provide general educational guidance. Prioritize information from the user's enrolled courses and relevant materials.

Answer:"""
        
        prompt = PromptTemplate(
            input_variables=["context", "question"],
            template=prompt_template
        )
        
        chain = LLMChain(llm=self.llm, prompt=prompt)
        
        try:
            result = await chain.arun(context=full_context, question=question)
            return result.strip()
        except Exception as e:
            return f"I apologize, but I encountered an error: {str(e)}"
    
    async def summarize_text(self, text: str) -> str:
        """Summarize a given text"""
        prompt_template = """Summarize the following educational material in a clear and concise way:

Text: {text}

Summary:"""
        
        prompt = PromptTemplate(
            input_variables=["text"],
            template=prompt_template
        )
        
        chain = LLMChain(llm=self.llm, prompt=prompt)
        
        try:
            # Split text if too long
            if len(text) > 10000:
                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=8000,
                    chunk_overlap=200
                )
                chunks = text_splitter.split_text(text)
                summaries = []
                
                for chunk in chunks[:3]:  # Limit to first 3 chunks
                    summary = await chain.arun(text=chunk)
                    summaries.append(summary)
                
                # Combine summaries
                combined = " ".join(summaries)
                if len(summaries) > 1:
                    final_summary = await chain.arun(text=combined)
                    return final_summary.strip()
                return combined.strip()
            else:
                result = await chain.arun(text=text)
                return result.strip()
        except Exception as e:
            return f"Error during summarization: {str(e)}"
    
    async def generate_quiz_questions(self, topic: str, num_questions: int = 5) -> List[Dict[str, Any]]:
        """Generate quiz questions for a given topic"""
        prompt_template = """Generate {num_questions} multiple-choice questions for the topic: {topic}

Format each question as follows:
Q: [Question text]
A) [Option A]
B) [Option B]
C) [Option C]
D) [Option D]
Correct: [A/B/C/D]

Questions:"""
        
        prompt = PromptTemplate(
            input_variables=["topic", "num_questions"],
            template=prompt_template
        )
        
        chain = LLMChain(llm=self.llm, prompt=prompt)
        
        try:
            result = await chain.arun(topic=topic, num_questions=num_questions)
            questions = self._parse_quiz_questions(result)
            return questions
        except Exception as e:
            return [{"error": f"Error generating questions: {str(e)}"}]
    
    def _parse_quiz_questions(self, text: str) -> List[Dict[str, Any]]:
        """Parse generated quiz questions from text"""
        questions = []
        lines = text.strip().split('\n')
        current_question = None
        options = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if line.startswith('Q:') or line.startswith('Question'):
                if current_question and options:
                    questions.append({
                        "question_text": current_question,
                        "options": options,
                        "correct_answer": 0,
                        "marks": 1
                    })
                current_question = line.split(':', 1)[1].strip() if ':' in line else line
                options = []
            elif line.startswith(('A)', 'B)', 'C)', 'D)')):
                option_text = line[2:].strip()
                options.append(option_text)
            elif line.lower().startswith('correct:'):
                correct = line.split(':', 1)[1].strip().upper()
                correct_index = {'A': 0, 'B': 1, 'C': 2, 'D': 3}.get(correct, 0)
                if current_question and options:
                    questions.append({
                        "question_text": current_question,
                        "options": options,
                        "correct_answer": correct_index,
                        "marks": 1
                    })
                    current_question = None
                    options = []
        
        # Add last question if exists
        if current_question and options:
            questions.append({
                "question_text": current_question,
                "options": options,
                "correct_answer": 0,
                "marks": 1
            })
        
        return questions
    
    async def explain_concept(self, concept: str) -> str:
        """Explain a concept in detail"""
        prompt_template = """Explain the following concept in a clear, educational manner suitable for students:

Concept: {concept}

Provide a comprehensive explanation with examples if applicable.

Explanation:"""
        
        prompt = PromptTemplate(
            input_variables=["concept"],
            template=prompt_template
        )
        
        chain = LLMChain(llm=self.llm, prompt=prompt)
        
        try:
            result = await chain.arun(concept=concept)
            return result.strip()
        except Exception as e:
            return f"Error explaining concept: {str(e)}"
    
    async def chat_response(self, message: str, conversation_history: List[Dict[str, str]] = None, user_id: Optional[str] = None) -> str:
        """Generate a chat response with conversation context and user learning context"""
        if conversation_history is None:
            conversation_history = []
        
        # Get user-specific context with vector search
        user_context = ""
        if user_id:
            user_context = await self.get_user_context(user_id, message)
        
        # Build conversation context
        context = user_context + "\n\n"
        if conversation_history:
            context += "Previous conversation:\n" + "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in conversation_history[-10:]])  # Last 10 messages
        
        prompt_template = """You are an intelligent educational assistant engaged in a conversation with a student or faculty member. Be helpful, accurate, and maintain context from previous messages and the user's learning materials.

{context}

Current message: {message}

Respond based on the user's courses, subjects, and available materials. Prioritize information from their enrolled courses and relevant materials. If the question is not related to their learning context, provide general educational guidance.

Response:"""
        
        prompt = PromptTemplate(
            input_variables=["context", "message"],
            template=prompt_template
        )
        
        chain = LLMChain(llm=self.llm, prompt=prompt)
        
        try:
            result = await chain.arun(context=context, message=message)
            return result.strip()
        except Exception as e:
            return f"I apologize, but I encountered an error: {str(e)}"
    
    async def generate_code_explanation(self, code: str, language: str = "python") -> str:
        """Explain code snippets"""
        prompt_template = """Explain the following {language} code in detail:

Code:
{code}

Provide:
1. What the code does
2. How it works (step by step)
3. Key concepts used
4. Any potential improvements

Explanation:"""
        
        prompt = PromptTemplate(
            input_variables=["code", "language"],
            template=prompt_template
        )
        
        chain = LLMChain(llm=self.llm, prompt=prompt)
        
        try:
            result = await chain.arun(code=code, language=language)
            return result.strip()
        except Exception as e:
            return f"Error explaining code: {str(e)}"
    
    async def solve_problem(self, problem: str, subject: str = None) -> str:
        """Solve academic problems step by step"""
        subject_context = f" in {subject}" if subject else ""
        
        prompt_template = """Solve the following academic problem{subject_context} step by step:

Problem: {problem}

Provide a clear, step-by-step solution with explanations.

Solution:"""
        
        prompt = PromptTemplate(
            input_variables=["problem", "subject_context"],
            template=prompt_template
        )
        
        chain = LLMChain(llm=self.llm, prompt=prompt)
        
        try:
            result = await chain.arun(problem=problem, subject_context=subject_context)
            return result.strip()
        except Exception as e:
            return f"Error solving problem: {str(e)}"


# Singleton instance
ai_service = AIService()
