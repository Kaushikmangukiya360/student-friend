from typing import List, Dict, Any
from datetime import datetime
from app.db.models.test_model import Question, TestAttempt


class TestService:
    """Service for handling mock tests"""
    
    def evaluate_test(
        self,
        questions: List[Question],
        submitted_answers: List[int],
        student_id: str,
        test_id: str
    ) -> Dict[str, Any]:
        """Evaluate a submitted test"""
        
        if len(submitted_answers) != len(questions):
            return {
                "error": "Number of answers doesn't match number of questions"
            }
        
        score = 0
        total_marks = 0
        detailed_results = []
        
        for i, question in enumerate(questions):
            total_marks += question.marks
            is_correct = submitted_answers[i] == question.correct_answer
            
            if is_correct:
                score += question.marks
            
            detailed_results.append({
                "question_number": i + 1,
                "question_text": question.question_text,
                "submitted_answer": submitted_answers[i],
                "correct_answer": question.correct_answer,
                "is_correct": is_correct,
                "marks_obtained": question.marks if is_correct else 0,
                "total_marks": question.marks
            })
        
        percentage = (score / total_marks * 100) if total_marks > 0 else 0
        
        return {
            "test_id": test_id,
            "student_id": student_id,
            "score": score,
            "total_marks": total_marks,
            "percentage": round(percentage, 2),
            "detailed_results": detailed_results,
            "submitted_at": datetime.utcnow()
        }
    
    def calculate_analytics(self, test_attempts: List[TestAttempt]) -> Dict[str, Any]:
        """Calculate analytics for a test"""
        
        if not test_attempts:
            return {
                "total_attempts": 0,
                "average_score": 0,
                "highest_score": 0,
                "lowest_score": 0,
                "pass_rate": 0
            }
        
        scores = [attempt.score for attempt in test_attempts]
        percentages = [attempt.percentage for attempt in test_attempts]
        
        pass_count = sum(1 for p in percentages if p >= 40)  # 40% as passing criteria
        
        return {
            "total_attempts": len(test_attempts),
            "average_score": round(sum(scores) / len(scores), 2),
            "average_percentage": round(sum(percentages) / len(percentages), 2),
            "highest_score": max(scores),
            "lowest_score": min(scores),
            "pass_rate": round((pass_count / len(test_attempts)) * 100, 2) if test_attempts else 0
        }
    
    def generate_performance_report(
        self,
        student_attempts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate performance report for a student"""
        
        if not student_attempts:
            return {
                "total_tests": 0,
                "average_percentage": 0,
                "tests_passed": 0,
                "tests_failed": 0
            }
        
        percentages = [attempt["percentage"] for attempt in student_attempts]
        passed = sum(1 for p in percentages if p >= 40)
        failed = len(percentages) - passed
        
        return {
            "total_tests": len(student_attempts),
            "average_percentage": round(sum(percentages) / len(percentages), 2),
            "tests_passed": passed,
            "tests_failed": failed,
            "recent_attempts": student_attempts[-5:]  # Last 5 attempts
        }


# Singleton instance
test_service = TestService()
