"""
Dashboard Data Preparation
Format evaluation data for frontend visualization
"""
import logging
from typing import Dict, List, Any
from datetime import datetime

from app.models.interview import InterviewSession
from app.interview_engine.evaluator import EvaluationMetrics

logger = logging.getLogger(__name__)


class DashboardDataPreparer:
    """
    Prepare data for dashboard visualization
    """
    
    @staticmethod
    def prepare_dashboard_data(session: InterviewSession) -> Dict[str, Any]:
        """
        Prepare comprehensive dashboard data from session
        
        Args:
            session: Interview session with evaluation data
            
        Returns:
            Dictionary with formatted data for frontend
        """
        if not session:
            return {"error": "Session not found"}
        
        data = {
            "session_id": session.session_id,
            "job_role": session.job_role,
            "job_description": session.job_description,
            "created_at": session.created_at.isoformat(),
            "question_count": session.question_count,
            "total_answers": len(session.answers),
        }
        
        # Final evaluation data
        if session.final_evaluation:
            eval = session.final_evaluation
            data["final_evaluation"] = {
                "overall_score": eval.overall_score,
                "verdict": eval.verdict,
                "metrics": {
                    "technical_depth": eval.aggregated_metrics.technical_depth,
                    "communication": eval.aggregated_metrics.communication,
                    "confidence": eval.aggregated_metrics.confidence,
                    "logical_thinking": eval.aggregated_metrics.logical_thinking,
                    "problem_solving": eval.aggregated_metrics.problem_solving,
                    "culture_fit": eval.aggregated_metrics.culture_fit,
                },
                "insights": eval.insights or {},
            }
        else:
            data["final_evaluation"] = None
        
        # Evaluation history for progression chart
        if session.evaluation_history:
            data["evaluation_history"] = []
            for i, eval_record in enumerate(session.evaluation_history, 1):
                data["evaluation_history"].append({
                    "question_number": i,
                    "question": eval_record.question,
                    "answer": eval_record.answer,
                    "scores": {
                        "technical_depth": eval_record.metrics.technical_depth,
                        "communication": eval_record.metrics.communication,
                        "confidence": eval_record.metrics.confidence,
                        "logical_thinking": eval_record.metrics.logical_thinking,
                        "problem_solving": eval_record.metrics.problem_solving,
                        "culture_fit": eval_record.metrics.culture_fit,
                        "overall": (
                            eval_record.metrics.technical_depth +
                            eval_record.metrics.communication +
                            eval_record.metrics.confidence +
                            eval_record.metrics.logical_thinking +
                            eval_record.metrics.problem_solving +
                            eval_record.metrics.culture_fit
                        ) / 6.0
                    },
                    "weaknesses": eval_record.weaknesses,
                    "strengths": eval_record.strengths,
                })
        else:
            data["evaluation_history"] = []
        
        # Questions and answers
        data["qa_pairs"] = []
        for i, (q, a) in enumerate(zip(session.questions, session.answers), 1):
            data["qa_pairs"].append({
                "question_number": i,
                "question": q,
                "answer": a
            })
        
        # Prepare chart data
        data["chart_data"] = DashboardDataPreparer._prepare_chart_data(session)
        
        # Prepare improvement suggestions
        data["improvement_suggestions"] = DashboardDataPreparer._prepare_suggestions(session)
        
        return data
    
    @staticmethod
    def _prepare_chart_data(session: InterviewSession) -> Dict[str, Any]:
        """Prepare data for various chart visualizations"""
        chart_data = {
            "radar_data": [],
            "bar_data": [],
            "line_data": []
        }
        
        if not session.final_evaluation:
            return chart_data
        
        eval = session.final_evaluation
        metrics = eval.aggregated_metrics
        
        # Radar chart data (all metrics)
        chart_data["radar_data"] = [
            {"metric": "Technical Depth", "score": metrics.technical_depth},
            {"metric": "Communication", "score": metrics.communication},
            {"metric": "Confidence", "score": metrics.confidence},
            {"metric": "Logical Thinking", "score": metrics.logical_thinking},
            {"metric": "Problem Solving", "score": metrics.problem_solving},
            {"metric": "Culture Fit", "score": metrics.culture_fit},
        ]
        
        # Bar chart data (sorted by score)
        bar_data = [
            {"metric": "Technical Depth", "score": metrics.technical_depth},
            {"metric": "Communication", "score": metrics.communication},
            {"metric": "Confidence", "score": metrics.confidence},
            {"metric": "Logical Thinking", "score": metrics.logical_thinking},
            {"metric": "Problem Solving", "score": metrics.problem_solving},
            {"metric": "Culture Fit", "score": metrics.culture_fit},
        ]
        chart_data["bar_data"] = sorted(bar_data, key=lambda x: x["score"], reverse=True)
        
        # Line chart data (score progression)
        if session.evaluation_history:
            chart_data["line_data"] = []
            for i, eval_record in enumerate(session.evaluation_history, 1):
                overall = (
                    eval_record.metrics.technical_depth +
                    eval_record.metrics.communication +
                    eval_record.metrics.confidence +
                    eval_record.metrics.logical_thinking +
                    eval_record.metrics.problem_solving +
                    eval_record.metrics.culture_fit
                ) / 6.0
                chart_data["line_data"].append({
                    "question": i,
                    "score": overall
                })
        
        return chart_data
    
    @staticmethod
    def _prepare_suggestions(session: InterviewSession) -> List[str]:
        """Prepare improvement suggestions"""
        suggestions = []
        
        if not session.final_evaluation:
            return suggestions
        
        eval = session.final_evaluation
        metrics = eval.aggregated_metrics
        
        # Generate suggestions based on scores
        if metrics.technical_depth < 6.0:
            suggestions.append({
                "area": "Technical Depth",
                "suggestion": "Focus on deepening technical knowledge and understanding of core concepts relevant to the role."
            })
        
        if metrics.communication < 6.0:
            suggestions.append({
                "area": "Communication",
                "suggestion": "Practice articulating thoughts clearly and structuring responses using the STAR method."
            })
        
        if metrics.confidence < 6.0:
            suggestions.append({
                "area": "Confidence",
                "suggestion": "Work on building confidence through practice interviews and maintaining professional presence."
            })
        
        if metrics.logical_thinking < 6.0:
            suggestions.append({
                "area": "Logical Thinking",
                "suggestion": "Develop logical reasoning skills by practicing problem-solving exercises."
            })
        
        if metrics.problem_solving < 6.0:
            suggestions.append({
                "area": "Problem Solving",
                "suggestion": "Practice breaking down complex problems into smaller components and demonstrating analytical thinking."
            })
        
        if metrics.culture_fit < 6.0:
            suggestions.append({
                "area": "Culture Fit",
                "suggestion": "Research company values and culture. Prepare examples that demonstrate alignment with team collaboration."
            })
        
        if not suggestions:
            suggestions.append({
                "area": "General",
                "suggestion": "Continue practicing interview skills and maintaining strong performance across all areas."
            })
        
        return suggestions


# Global dashboard data preparer instance
dashboard_data_preparer = DashboardDataPreparer()
