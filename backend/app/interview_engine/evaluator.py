"""
Evaluation Engine
Comprehensive evaluation with 6 specific metrics
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime

from app.llm.gemini_client import gemini_client

logger = logging.getLogger(__name__)


class EvaluationMetrics:
    """
    Evaluation metrics for interview answers
    """
    TECHNICAL_DEPTH = "technical_depth"
    COMMUNICATION = "communication"
    CONFIDENCE = "confidence"
    LOGICAL_THINKING = "logical_thinking"
    PROBLEM_SOLVING = "problem_solving"
    CULTURE_FIT = "culture_fit"
    
    ALL_METRICS = [
        TECHNICAL_DEPTH,
        COMMUNICATION,
        CONFIDENCE,
        LOGICAL_THINKING,
        PROBLEM_SOLVING,
        CULTURE_FIT
    ]


class AnswerEvaluation:
    """
    Represents evaluation of a single answer
    """
    def __init__(
        self,
        question: str,
        answer: str,
        scores: Dict[str, float],
        needs_followup: bool = False,
        weaknesses: List[str] = None,
        strengths: List[str] = None,
        reasoning: str = ""
    ):
        self.question = question
        self.answer = answer
        self.scores = scores  # Dict of metric -> score (0-10)
        self.needs_followup = needs_followup
        self.weaknesses = weaknesses or []
        self.strengths = strengths or []
        self.reasoning = reasoning
        self.timestamp = datetime.utcnow()
    
    def get_average_score(self) -> float:
        """Calculate average score across all metrics"""
        if not self.scores:
            return 0.0
        return sum(self.scores.values()) / len(self.scores)
    
    def get_metric_score(self, metric: str) -> float:
        """Get score for a specific metric"""
        return self.scores.get(metric, 0.0)


class EvaluationEngine:
    """
    Comprehensive evaluation engine using Gemini
    Evaluates answers across 6 metrics
    """
    
    def __init__(self):
        """Initialize evaluation engine"""
        pass
    
    async def evaluate_answer(
        self,
        question: str,
        answer: str,
        job_role: str,
        job_description: str,
        question_number: int = 0
    ) -> AnswerEvaluation:
        """
        Evaluate an answer across all 6 metrics
        
        Args:
            question: The question asked
            answer: The candidate's answer
            job_role: Job role being interviewed for
            job_description: Job description
            question_number: Current question number
            
        Returns:
            AnswerEvaluation with all scores and insights
        """
        # Use Gemini to evaluate with all 6 metrics
        evaluation_result = await gemini_client.evaluate_answer_detailed(
            question=question,
            answer=answer,
            job_role=job_role,
            job_description=job_description
        )
        
        # Extract scores
        scores = {
            EvaluationMetrics.TECHNICAL_DEPTH: evaluation_result.get("technical_depth", 5.0),
            EvaluationMetrics.COMMUNICATION: evaluation_result.get("communication", 5.0),
            EvaluationMetrics.CONFIDENCE: evaluation_result.get("confidence", 5.0),
            EvaluationMetrics.LOGICAL_THINKING: evaluation_result.get("logical_thinking", 5.0),
            EvaluationMetrics.PROBLEM_SOLVING: evaluation_result.get("problem_solving", 5.0),
            EvaluationMetrics.CULTURE_FIT: evaluation_result.get("culture_fit", 5.0),
        }
        
        # Ensure all scores are in valid range
        for metric in scores:
            scores[metric] = max(0.0, min(10.0, scores[metric]))
        
        evaluation = AnswerEvaluation(
            question=question,
            answer=answer,
            scores=scores,
            needs_followup=evaluation_result.get("needs_followup", False),
            weaknesses=evaluation_result.get("weaknesses", []),
            strengths=evaluation_result.get("strengths", []),
            reasoning=evaluation_result.get("reasoning", "")
        )
        
        logger.info(
            f"Evaluated answer - Avg: {evaluation.get_average_score():.1f}, "
            f"Follow-up: {evaluation.needs_followup}"
        )
        
        return evaluation
    
    def aggregate_evaluations(
        self,
        evaluations: List[AnswerEvaluation],
        weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, float]:
        """
        Aggregate multiple evaluations into final scores
        
        Args:
            evaluations: List of answer evaluations
            weights: Optional weights for each metric (default: equal weights)
            
        Returns:
            Dictionary of metric -> aggregated score
        """
        if not evaluations:
            return {metric: 0.0 for metric in EvaluationMetrics.ALL_METRICS}
        
        # Default equal weights
        if weights is None:
            weights = {metric: 1.0 for metric in EvaluationMetrics.ALL_METRICS}
        
        aggregated_scores = {}
        
        for metric in EvaluationMetrics.ALL_METRICS:
            metric_scores = [eval.get_metric_score(metric) for eval in evaluations]
            weight = weights.get(metric, 1.0)
            
            # Weighted average
            if metric_scores:
                weighted_sum = sum(score * weight for score in metric_scores)
                total_weight = sum(weights.get(metric, 1.0) for _ in metric_scores)
                aggregated_scores[metric] = weighted_sum / total_weight if total_weight > 0 else 0.0
            else:
                aggregated_scores[metric] = 0.0
        
        return aggregated_scores
    
    def calculate_overall_score(
        self,
        aggregated_scores: Dict[str, float],
        metric_weights: Optional[Dict[str, float]] = None
    ) -> float:
        """
        Calculate overall score from aggregated metrics
        
        Args:
            aggregated_scores: Aggregated scores per metric
            metric_weights: Optional weights for each metric
            
        Returns:
            Overall score (0-10)
        """
        if metric_weights is None:
            # Default weights - can be customized
            metric_weights = {
                EvaluationMetrics.TECHNICAL_DEPTH: 1.2,
                EvaluationMetrics.COMMUNICATION: 1.0,
                EvaluationMetrics.CONFIDENCE: 0.8,
                EvaluationMetrics.LOGICAL_THINKING: 1.1,
                EvaluationMetrics.PROBLEM_SOLVING: 1.2,
                EvaluationMetrics.CULTURE_FIT: 0.9,
            }
        
        weighted_sum = 0.0
        total_weight = 0.0
        
        for metric in EvaluationMetrics.ALL_METRICS:
            score = aggregated_scores.get(metric, 0.0)
            weight = metric_weights.get(metric, 1.0)
            weighted_sum += score * weight
            total_weight += weight
        
        overall_score = weighted_sum / total_weight if total_weight > 0 else 0.0
        return max(0.0, min(10.0, overall_score))
    
    def determine_verdict(self, overall_score: float) -> str:
        """
        Determine hire verdict based on overall score
        
        Args:
            overall_score: Overall evaluation score (0-10)
            
        Returns:
            Verdict: "Hire", "Borderline", or "No-Hire"
        """
        if overall_score >= 7.5:
            return "Hire"
        elif overall_score >= 6.0:
            return "Borderline"
        else:
            return "No-Hire"
    
    def generate_evaluation_insights(
        self,
        evaluations: List[AnswerEvaluation],
        aggregated_scores: Dict[str, float]
    ) -> Dict[str, any]:
        """
        Generate insights from evaluations
        
        Args:
            evaluations: List of answer evaluations
            aggregated_scores: Aggregated scores per metric
            
        Returns:
            Dictionary with insights
        """
        # Find strongest and weakest metrics
        sorted_metrics = sorted(
            aggregated_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        strongest_metric = sorted_metrics[0][0] if sorted_metrics else None
        weakest_metric = sorted_metrics[-1][0] if sorted_metrics else None
        
        # Collect all weaknesses and strengths
        all_weaknesses = []
        all_strengths = []
        
        for eval in evaluations:
            all_weaknesses.extend(eval.weaknesses)
            all_strengths.extend(eval.strengths)
        
        # Get unique items
        unique_weaknesses = list(set(all_weaknesses))
        unique_strengths = list(set(all_strengths))
        
        return {
            "strongest_metric": strongest_metric,
            "weakest_metric": weakest_metric,
            "common_weaknesses": unique_weaknesses[:5],  # Top 5
            "common_strengths": unique_strengths[:5],  # Top 5
            "total_answers": len(evaluations),
            "average_score": sum(eval.get_average_score() for eval in evaluations) / len(evaluations) if evaluations else 0.0
        }


# Global evaluation engine instance
evaluation_engine = EvaluationEngine()
