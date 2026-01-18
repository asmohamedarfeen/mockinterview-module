"""
Interview Orchestrator
Manages interview state machine, question flow, and follow-up logic
"""
import logging
from typing import List, Tuple, Optional, Dict, Set, Any
from datetime import datetime
from enum import Enum

from app.models.interview import InterviewSession, InterviewState
from app.llm.gemini_client import gemini_client
from app.interview_engine.state_machine import InterviewStateMachine, StateTransitionError

logger = logging.getLogger(__name__)


class DifficultyLevel(str, Enum):
    """Question difficulty levels"""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class QuestionType(str, Enum):
    """Types of interview questions"""
    BEHAVIORAL = "behavioral"
    TECHNICAL = "technical"
    CULTURE_FIT = "culture_fit"
    PROBLEM_SOLVING = "problem_solving"
    LEADERSHIP = "leadership"
    GENERAL = "general"


class InterviewOrchestrator:
    """
    Orchestrates interview flow:
    - Question generation
    - Answer evaluation
    - Follow-up decision
    - State transitions
    """
    
    def __init__(self, session: InterviewSession):
        """
        Initialize orchestrator with interview session
        
        Args:
            session: Interview session to orchestrate
        """
        self.session = session
        self.state_machine = InterviewStateMachine(initial_state=InterviewState.SETUP)
        self.conversation_history: List[Tuple[str, str]] = []  # (question, answer) pairs
        self.current_answer_buffer: str = ""  # Buffer for current answer being transcribed
        self.pending_followup: bool = False  # Whether we need to ask a follow-up
        
        # Enhanced context memory
        self.covered_topics: Set[str] = set()  # Topics already discussed
        self.question_types_asked: List[QuestionType] = []  # Types of questions asked
        self.difficulty_progression: List[DifficultyLevel] = []  # Difficulty progression
        self.current_difficulty: DifficultyLevel = DifficultyLevel.EASY
        self.weak_areas: List[str] = []  # Areas where candidate struggled
        self.strengths: List[str] = []  # Areas where candidate excelled
    
    async def generate_first_question(self) -> Dict[str, str]:
        """
        Generate the first interview question
        
        Returns:
            Dict containing 'text' and 'topic'
        """
        try:
            # Transition to ASK_QUESTION state
            self.state_machine.transition_to(InterviewState.ASK_QUESTION)
        except StateTransitionError as e:
            logger.warning(f"State transition error: {e}, continuing anyway")
        
        result = await gemini_client.generate_first_question(
            job_role=self.session.job_role,
            job_description=self.session.job_description
        )
        
        question_text = result["text"]
        
        self.session.questions.append(question_text)
        self.session.current_question_number = 1
        self.session.state = InterviewState.ASK_QUESTION
        self.current_difficulty = DifficultyLevel.EASY
        self.difficulty_progression.append(self.current_difficulty)
        self.question_types_asked.append(QuestionType.GENERAL)
        
        logger.info(f"Generated first question for session {self.session.session_id}")
        return result
    
    async def generate_next_question(self) -> Dict[str, str]:
        """
        Generate the next question based on conversation history with difficulty ramping
        
        Returns:
            Dict containing 'text' and 'topic'
        """
        # Check if we've reached the question limit
        if self.session.current_question_number >= self.session.question_count:
            logger.info(f"Reached question limit for session {self.session.session_id}")
            return None
        
        # Determine difficulty based on progression
        self._update_difficulty()
        
        try:
            # Transition to ASK_QUESTION state
            self.state_machine.transition_to(InterviewState.ASK_QUESTION)
        except StateTransitionError as e:
            logger.warning(f"State transition error: {e}, continuing anyway")
        
        result = await gemini_client.generate_next_question(
            job_role=self.session.job_role,
            job_description=self.session.job_description,
            conversation_history=self.conversation_history,
            current_question_number=self.session.current_question_number - 1,
            total_questions=self.session.question_count
        )
        
        question_text = result["text"]
        
        self.session.questions.append(question_text)
        self.session.current_question_number += 1
        self.session.state = InterviewState.ASK_QUESTION
        self.pending_followup = False
        self.difficulty_progression.append(self.current_difficulty)
        
        logger.info(
            f"Generated question {self.session.current_question_number} "
            f"(difficulty: {self.current_difficulty.value}) for session {self.session.session_id}"
        )
        return result
    
    def _update_difficulty(self):
        """
        Update difficulty level based on interview progression
        Easy → Medium → Hard
        """
        question_num = self.session.current_question_number
        total = self.session.question_count
        
        # Ramp difficulty: first 30% easy, next 40% medium, last 30% hard
        if question_num <= total * 0.3:
            self.current_difficulty = DifficultyLevel.EASY
        elif question_num <= total * 0.7:
            self.current_difficulty = DifficultyLevel.MEDIUM
        else:
            self.current_difficulty = DifficultyLevel.HARD
    
    def add_transcript_chunk(self, transcript: str, is_final: bool = False):
        """
        Add transcript chunk to current answer buffer
        
        Args:
            transcript: Transcript text
            is_final: Whether this is the final transcript
        """
        if is_final:
            # Final transcript - add to buffer and process
            self.current_answer_buffer += " " + transcript
            self.current_answer_buffer = self.current_answer_buffer.strip()
        else:
            # Interim transcript - update buffer
            self.current_answer_buffer = transcript
    
    async def process_answer(self) -> Dict:
        """
        Process the current answer:
        - Evaluate answer quality
        - Decide on follow-up
        - Update conversation history
        
        Returns:
            Dictionary with evaluation results and next action
        """
        if not self.current_answer_buffer:
            logger.warning(f"No answer to process for session {self.session.session_id}")
            return {
                "needs_followup": False,
                "next_action": "next_question"
            }
        
        # Get the last question
        if not self.session.questions:
            logger.warning(f"No questions available for evaluation")
            return {
                "needs_followup": False,
                "next_action": "next_question"
            }
        
        current_question = self.session.questions[-1]
        answer = self.current_answer_buffer
        
        # Evaluate answer
        evaluation = await gemini_client.evaluate_answer(
            question=current_question,
            answer=answer,
            job_role=self.session.job_role,
            job_description=self.session.job_description
        )
        
        # Update scores (simple average for now, Phase 5 will refine)
        quality_score = evaluation["quality_score"]
        if "answer_quality" not in self.session.scores:
            self.session.scores["answer_quality"] = []
        self.session.scores["answer_quality"].append(quality_score)
        
        # Add to conversation history
        self.conversation_history.append((current_question, answer))
        self.session.answers.append(answer)
        
        # Update context memory with evaluation insights
        if evaluation.get("weaknesses"):
            self.weak_areas.extend(evaluation["weaknesses"])
        if evaluation.get("strengths"):
            self.strengths.extend(evaluation["strengths"])
        
        # Decide on follow-up
        needs_followup = evaluation["needs_followup"] and not self.pending_followup
        
        # Update state machine
        try:
            self.state_machine.transition_to(InterviewState.EVALUATE)
        except StateTransitionError as e:
            logger.warning(f"State transition error: {e}")
        
        # Reset answer buffer
        self.current_answer_buffer = ""
        
        logger.info(
            f"Processed answer for session {self.session.session_id}: "
            f"score={quality_score:.1f}, followup={needs_followup}"
        )
        
        return {
            "evaluation": evaluation,
            "needs_followup": needs_followup,
            "next_action": "followup" if needs_followup else "next_question",
            "quality_score": quality_score
        }
    
    async def generate_followup_question(self, evaluation: Dict) -> Dict[str, str]:
        """
        Generate a follow-up question based on answer evaluation
        
        Args:
            evaluation: Evaluation results from process_answer
            
        Returns:
            Dict containing 'text' and 'topic'
        """
        if not self.session.questions:
            return None
        
        current_question = self.session.questions[-1]
        current_answer = self.session.answers[-1] if self.session.answers else ""
        weaknesses = evaluation.get("weaknesses", [])
        
        result = await gemini_client.generate_followup_question(
            original_question=current_question,
            answer=current_answer,
            weaknesses=weaknesses,
            job_role=self.session.job_role
        )
        
        question_text = result["text"]
        
        # Add follow-up as a new question (but don't increment question number)
        self.session.questions.append(question_text)
        self.pending_followup = True
        
        # Update state machine
        try:
            self.state_machine.transition_to(InterviewState.FOLLOWUP)
            self.state_machine.transition_to(InterviewState.ASK_QUESTION)
        except StateTransitionError as e:
            logger.warning(f"State transition error: {e}")
        
        self.session.state = InterviewState.ASK_QUESTION
        
        logger.info(f"Generated follow-up question for session {self.session.session_id}")
        return result
    
    def should_continue(self) -> bool:
        """
        Check if interview should continue
        
        Returns:
            True if more questions should be asked
        """
        # Continue if we haven't reached question limit
        return self.session.current_question_number < self.session.question_count
    
    def complete_interview(self):
        """
        Mark interview as completed and calculate final evaluation
        """
        try:
            # Transition through final states
            if self.state_machine.get_current_state() != InterviewState.FINAL_EVALUATION:
                self.state_machine.transition_to(InterviewState.FINAL_EVALUATION)
            self.state_machine.transition_to(InterviewState.REPORT)
            self.state_machine.transition_to(InterviewState.COMPLETED)
        except StateTransitionError as e:
            logger.warning(f"State transition error during completion: {e}")
        
        self.session.state = InterviewState.FINAL_EVALUATION
        self.session.updated_at = datetime.utcnow()
        
        # Calculate final evaluation using evaluation engine (Phase 5)
        from app.interview_engine.evaluator import evaluation_engine, AnswerEvaluation, EvaluationMetrics
        
        if self.session.evaluation_history:
            # Convert evaluation records to AnswerEvaluation objects
            evaluations = []
            for eval_record in self.session.evaluation_history:
                eval_obj = AnswerEvaluation(
                    question=eval_record.question,
                    answer=eval_record.answer,
                    scores={
                        EvaluationMetrics.TECHNICAL_DEPTH: eval_record.metrics.technical_depth,
                        EvaluationMetrics.COMMUNICATION: eval_record.metrics.communication,
                        EvaluationMetrics.CONFIDENCE: eval_record.metrics.confidence,
                        EvaluationMetrics.LOGICAL_THINKING: eval_record.metrics.logical_thinking,
                        EvaluationMetrics.PROBLEM_SOLVING: eval_record.metrics.problem_solving,
                        EvaluationMetrics.CULTURE_FIT: eval_record.metrics.culture_fit,
                    },
                    needs_followup=eval_record.needs_followup,
                    weaknesses=eval_record.weaknesses,
                    strengths=eval_record.strengths,
                    reasoning=eval_record.reasoning or ""
                )
                evaluations.append(eval_obj)
            
            # Aggregate scores
            aggregated_scores = evaluation_engine.aggregate_evaluations(evaluations)
            overall_score = evaluation_engine.calculate_overall_score(aggregated_scores)
            verdict = evaluation_engine.determine_verdict(overall_score)
            insights = evaluation_engine.generate_evaluation_insights(evaluations, aggregated_scores)
            
            # Store in session scores for backward compatibility
            self.session.scores["overall_score"] = overall_score
            self.session.scores.update({
                "technical_depth": aggregated_scores[EvaluationMetrics.TECHNICAL_DEPTH],
                "communication": aggregated_scores[EvaluationMetrics.COMMUNICATION],
                "confidence": aggregated_scores[EvaluationMetrics.CONFIDENCE],
                "logical_thinking": aggregated_scores[EvaluationMetrics.LOGICAL_THINKING],
                "problem_solving": aggregated_scores[EvaluationMetrics.PROBLEM_SOLVING],
                "culture_fit": aggregated_scores[EvaluationMetrics.CULTURE_FIT],
            })
            
            # Store final evaluation
            from app.models.interview import FinalEvaluation, EvaluationMetrics as EvalMetricsModel
            self.session.final_evaluation = FinalEvaluation(
                overall_score=overall_score,
                aggregated_metrics=EvalMetricsModel(
                    technical_depth=aggregated_scores[EvaluationMetrics.TECHNICAL_DEPTH],
                    communication=aggregated_scores[EvaluationMetrics.COMMUNICATION],
                    confidence=aggregated_scores[EvaluationMetrics.CONFIDENCE],
                    logical_thinking=aggregated_scores[EvaluationMetrics.LOGICAL_THINKING],
                    problem_solving=aggregated_scores[EvaluationMetrics.PROBLEM_SOLVING],
                    culture_fit=aggregated_scores[EvaluationMetrics.CULTURE_FIT],
                ),
                verdict=verdict,
                insights=insights,
                total_questions=self.session.question_count,
                total_answers=len(self.session.answers)
            )
            
            logger.info(
                f"Interview completed for session {self.session.session_id}: "
                f"Overall: {overall_score:.1f}, Verdict: {verdict}"
            )
        else:
            # Fallback to simple average if no evaluation history
            if "answer_quality" in self.session.scores:
                scores_list = self.session.scores["answer_quality"]
                if scores_list:
                    avg_score = sum(scores_list) / len(scores_list)
                    self.session.scores["overall_score"] = avg_score
            logger.info(f"Interview completed for session {self.session.session_id} (no evaluation history)")
    
    def get_context_summary(self) -> Dict:
        """
        Get enhanced context summary for reporting
        
        Returns:
            Dictionary with context information
        """
        return {
            "covered_topics": list(self.covered_topics),
            "question_types": [qt.value for qt in self.question_types_asked],
            "difficulty_progression": [d.value for d in self.difficulty_progression],
            "weak_areas": list(set(self.weak_areas)),  # Remove duplicates
            "strengths": list(set(self.strengths)),  # Remove duplicates
            "transition_history": self.state_machine.get_transition_history()
        }
    
    def get_conversation_summary(self) -> str:
        """
        Get a summary of the conversation for reporting
        
        Returns:
            Conversation summary text
        """
        summary = f"Interview for {self.session.job_role}\n\n"
        
        for i, (q, a) in enumerate(self.conversation_history, 1):
            summary += f"Q{i}: {q}\n"
            summary += f"A{i}: {a}\n\n"
        
        return summary
    
    async def handle_user_answer(self, session_id: str, user_answer: str) -> Dict[str, Any]:
        """
        Handle a complete user answer:
        1. Process the answer (evaluate)
        2. Decide next step (follow-up or next question)
        3. Generate appropriate content
        
        Args:
            session_id: Session ID
            user_answer: Complete user answer text
            
        Returns:
            Dict containing next question info or completion status
        """
        # Update buffer with final answer
        self.current_answer_buffer = user_answer
        
        # Process the answer (evaluation)
        process_result = await self.process_answer()
        
        next_question = None
        is_followup = False
        
        # Decide next step based on process result
        if process_result["needs_followup"]:
            # Generate follow-up
            next_question = await self.generate_followup_question(process_result["evaluation"])
            is_followup = True
            
            if not next_question:
                # Fallback if follow-up generation fails
                logger.warning("Follow-up generation failed, proceeding to next question")
                if self.should_continue():
                    next_question = await self.generate_next_question()
                    is_followup = False
        
        else:
            # Regular flow
            if self.should_continue():
                next_question = await self.generate_next_question()
                is_followup = False
        
        if next_question:
            return {
                "next_question": next_question,
                "is_followup": is_followup,
                "question_index": self.session.current_question_number,
                "is_interview_complete": False
            }
        else:
            # No next question generated => Interview Complete
            self.complete_interview()
            return {
                "next_question": None,
                "is_followup": False,
                "question_index": self.session.current_question_number,
                "is_interview_complete": True
            }
