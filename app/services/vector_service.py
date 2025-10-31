import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Optional
import uuid
import os
from app.core.config import settings


class VectorService:
    """Vector database service for semantic search of learning materials"""
    
    def __init__(self):
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=os.path.join(os.getcwd(), "vector_db")
        )
        
        # Initialize sentence transformer for embeddings
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Create or get collections
        self.materials_collection = self.client.get_or_create_collection(
            name="materials",
            metadata={"description": "Learning materials and content"}
        )
        
        self.courses_collection = self.client.get_or_create_collection(
            name="courses",
            metadata={"description": "Course information and syllabi"}
        )
        
        self.queries_collection = self.client.get_or_create_collection(
            name="queries",
            metadata={"description": "User queries and AI responses"}
        )
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text"""
        return self.embedding_model.encode(text).tolist()
    
    async def index_material(self, material_id: str, title: str, content: str, 
                           subject: str = "", course_id: str = "", tags: List[str] = None) -> bool:
        """Index a learning material in the vector database"""
        try:
            # Create searchable text
            searchable_text = f"{title}. {content}"
            if subject:
                searchable_text += f" Subject: {subject}"
            if tags:
                searchable_text += f" Tags: {' '.join(tags)}"
            
            # Generate embedding
            embedding = self.generate_embedding(searchable_text)
            
            # Prepare metadata
            metadata = {
                "material_id": material_id,
                "title": title,
                "subject": subject,
                "course_id": course_id,
                "type": "material"
            }
            
            if tags:
                metadata["tags"] = ",".join(tags)
            
            # Add to collection
            self.materials_collection.add(
                embeddings=[embedding],
                documents=[searchable_text],
                metadatas=[metadata],
                ids=[material_id]
            )
            
            return True
        except Exception as e:
            print(f"Error indexing material: {e}")
            return False
    
    async def index_course(self, course_id: str, name: str, description: str, 
                         subject_id: str, syllabus: str = "") -> bool:
        """Index a course in the vector database"""
        try:
            # Create searchable text
            searchable_text = f"{name}. {description}"
            if syllabus:
                searchable_text += f" Syllabus: {syllabus}"
            
            # Generate embedding
            embedding = self.generate_embedding(searchable_text)
            
            # Prepare metadata
            metadata = {
                "course_id": course_id,
                "name": name,
                "subject_id": subject_id,
                "type": "course"
            }
            
            # Add to collection
            self.courses_collection.add(
                embeddings=[embedding],
                documents=[searchable_text],
                metadatas=[metadata],
                ids=[course_id]
            )
            
            return True
        except Exception as e:
            print(f"Error indexing course: {e}")
            return False
    
    async def index_query(self, query_id: str, question: str, answer: str, 
                        subject: str = "", user_id: str = "") -> bool:
        """Index a Q&A pair in the vector database"""
        try:
            # Create searchable text
            searchable_text = f"Question: {question} Answer: {answer}"
            if subject:
                searchable_text += f" Subject: {subject}"
            
            # Generate embedding
            embedding = self.generate_embedding(searchable_text)
            
            # Prepare metadata
            metadata = {
                "query_id": query_id,
                "question": question,
                "subject": subject,
                "user_id": user_id,
                "type": "query"
            }
            
            # Add to collection
            self.queries_collection.add(
                embeddings=[embedding],
                documents=[searchable_text],
                metadatas=[metadata],
                ids=[query_id]
            )
            
            return True
        except Exception as e:
            print(f"Error indexing query: {e}")
            return False
    
    async def search_materials(self, query: str, subject: str = "", course_id: str = "", 
                             limit: int = 5) -> List[Dict[str, Any]]:
        """Search for relevant materials using semantic search"""
        try:
            # Generate query embedding
            query_embedding = self.generate_embedding(query)
            
            # Build where clause
            where_clause = {}
            if subject:
                where_clause["subject"] = subject
            if course_id:
                where_clause["course_id"] = course_id
            
            # Search
            results = self.materials_collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where=where_clause if where_clause else None
            )
            
            # Format results
            formatted_results = []
            if results['documents']:
                for i, doc in enumerate(results['documents'][0]):
                    metadata = results['metadatas'][0][i]
                    distance = results['distances'][0][i]
                    
                    formatted_results.append({
                        "material_id": metadata.get("material_id"),
                        "title": metadata.get("title"),
                        "content": doc,
                        "subject": metadata.get("subject"),
                        "course_id": metadata.get("course_id"),
                        "tags": metadata.get("tags", "").split(",") if metadata.get("tags") else [],
                        "relevance_score": 1 - distance  # Convert distance to similarity score
                    })
            
            return formatted_results
        except Exception as e:
            print(f"Error searching materials: {e}")
            return []
    
    async def search_courses(self, query: str, subject_id: str = "", limit: int = 5) -> List[Dict[str, Any]]:
        """Search for relevant courses using semantic search"""
        try:
            # Generate query embedding
            query_embedding = self.generate_embedding(query)
            
            # Build where clause
            where_clause = {}
            if subject_id:
                where_clause["subject_id"] = subject_id
            
            # Search
            results = self.courses_collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where=where_clause if where_clause else None
            )
            
            # Format results
            formatted_results = []
            if results['documents']:
                for i, doc in enumerate(results['documents'][0]):
                    metadata = results['metadatas'][0][i]
                    distance = results['distances'][0][i]
                    
                    formatted_results.append({
                        "course_id": metadata.get("course_id"),
                        "name": metadata.get("name"),
                        "content": doc,
                        "subject_id": metadata.get("subject_id"),
                        "relevance_score": 1 - distance
                    })
            
            return formatted_results
        except Exception as e:
            print(f"Error searching courses: {e}")
            return []
    
    async def search_similar_queries(self, query: str, subject: str = "", 
                                   user_id: str = "", limit: int = 3) -> List[Dict[str, Any]]:
        """Find similar previous queries and answers"""
        try:
            # Generate query embedding
            query_embedding = self.generate_embedding(query)
            
            # Build where clause
            where_clause = {}
            if subject:
                where_clause["subject"] = subject
            if user_id:
                where_clause["user_id"] = user_id
            
            # Search
            results = self.queries_collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where=where_clause if where_clause else None
            )
            
            # Format results
            formatted_results = []
            if results['documents']:
                for i, doc in enumerate(results['documents'][0]):
                    metadata = results['metadatas'][0][i]
                    distance = results['distances'][0][i]
                    
                    formatted_results.append({
                        "query_id": metadata.get("query_id"),
                        "question": metadata.get("question"),
                        "content": doc,
                        "subject": metadata.get("subject"),
                        "relevance_score": 1 - distance
                    })
            
            return formatted_results
        except Exception as e:
            print(f"Error searching queries: {e}")
            return []
    
    async def delete_material(self, material_id: str) -> bool:
        """Remove a material from the vector database"""
        try:
            self.materials_collection.delete(ids=[material_id])
            return True
        except Exception as e:
            print(f"Error deleting material: {e}")
            return False
    
    async def delete_course(self, course_id: str) -> bool:
        """Remove a course from the vector database"""
        try:
            self.courses_collection.delete(ids=[course_id])
            return True
        except Exception as e:
            print(f"Error deleting course: {e}")
            return False


# Singleton instance
vector_service = VectorService()