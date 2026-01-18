"""
WebSocket message handlers
Process incoming messages and route to appropriate handlers
"""
import json
import logging
from typing import Dict, Any
from fastapi import WebSocket

from app.websocket.manager import manager
from app.models.interview import (
    MessageType,
    ServerMessageType,
    InterviewState,
    StartInterviewMessage,
    TranscribeMessage,
    SilenceDetectedMessage,
    QuestionReadyMessage,
    TTSAudioMessage,
    ErrorMessage,
    StateUpdateMessage,
    InterviewSession,
    EvaluationUpdateMessage,
    InterviewCompleteMessage,
    EvaluationMetrics as EvaluationMetricsModel,
    AnswerEvaluationRecord,
    FinalEvaluation
)
from app.interview_engine.orchestrator import InterviewOrchestrator
from app.interview_engine.evaluator import evaluation_engine, EvaluationMetrics

logger = logging.getLogger(__name__)


async def handle_websocket_message(websocket: WebSocket, session_id: str, message: Dict[str, Any]):
    """
    Main message router - dispatches messages to appropriate handlers
    """
    try:
        msg_type = message.get("type")
        
        if msg_type == MessageType.START_INTERVIEW:
            await handle_start_interview(session_id, message)
        elif msg_type == MessageType.TRANSCRIBE:
            await handle_transcribe(session_id, message)
        elif msg_type == MessageType.SILENCE_DETECTED:
            await handle_silence_detected(session_id, message)
        elif msg_type == MessageType.END_INTERVIEW:
            await handle_end_interview(session_id)
        elif msg_type == MessageType.PING:
            await handle_ping(session_id)
        else:
            logger.warning(f"Unknown message type: {msg_type}")
            await send_error(session_id, "UNKNOWN_MESSAGE_TYPE", f"Unknown message type: {msg_type}")
    
    except Exception as e:
        logger.error(f"Error handling message for {session_id}: {e}", exc_info=True)
        await send_error(session_id, "HANDLER_ERROR", str(e))


async def handle_start_interview(session_id: str, message: Dict[str, Any]):
    """
    Initialize a new interview session and generate first question
    """
    try:
        # Validate message structure
        start_msg = StartInterviewMessage(**message)
        
        # Create interview session
        session = InterviewSession(
            session_id=session_id,
            state=InterviewState.SETUP,
            job_role=start_msg.job_role,
            job_description=start_msg.job_description,
            question_count=start_msg.question_count
        )
        
        manager.create_session(session)
        
        # Create orchestrator
        orchestrator = InterviewOrchestrator(session)
        
        # Store orchestrator in manager
        manager.orchestrators[session_id] = orchestrator
        
        # Generate first question using Gemini
        result = await orchestrator.generate_first_question()
        question_text = result["text"]
        topic = result.get("topic", "Introduction")
        
        # Update state
        manager.update_session_state(session_id, InterviewState.ASK_QUESTION)
        await send_state_update(session_id, InterviewState.ASK_QUESTION)
        
        # Send question
        logger.info(f"Sending first question to frontend: {session_id}")
        await manager.send_personal_message({
            "type": "question",
            "text": question_text,
            "topic": topic,
            "index": 1,
            "total": start_msg.question_count
        }, session_id)
        
        
        logger.info(f"Interview started: {session_id} - {start_msg.job_role}")
    
    except Exception as e:
        logger.error(f"Failed to start interview {session_id}: {e}", exc_info=True)
        await send_error(session_id, "START_INTERVIEW_ERROR", str(e))


async def handle_transcribe(session_id: str, message: Dict[str, Any]):
    """
    Handle transcript chunks from client
    """
    try:
        transcribe_msg = TranscribeMessage(**message)
        session = manager.get_session(session_id)
        
        if not session:
            await send_error(session_id, "SESSION_NOT_FOUND", "Session not found")
            return
        
        # Get orchestrator
        orchestrator = manager.orchestrators.get(session_id)
        if not orchestrator:
            logger.warning(f"No orchestrator found for session {session_id}")
            return
        
        # Add transcript to orchestrator buffer
        orchestrator.add_transcript_chunk(
            transcript=transcribe_msg.transcript,
            is_final=transcribe_msg.is_final
        )
        
        if transcribe_msg.is_final:
            logger.info(f"Final transcript received for {session_id}: {transcribe_msg.transcript[:50]}...")
            
            # --- START CONNECTED PIPELINE ---
            logger.info(f"Sending transcript to Orchestrator for {session_id}")
            
            # Update state to processing
            manager.update_session_state(session_id, InterviewState.EVALUATE)
            await send_state_update(session_id, InterviewState.EVALUATE)
            
            # Call orchestrator to handle the answer
            result = await orchestrator.handle_user_answer(session_id, transcribe_msg.transcript)
            
            if result["is_interview_complete"]:
                logger.info(f"Interview complete for {session_id}, generating report")
                # Send interview complete message
                await manager.send_personal_message({
                    "type": "interview_complete",
                    "report": result.get("report", {})
                }, session_id)
            else:
                next_question_data = result["next_question"]
                question_text = next_question_data["text"]
                topic = next_question_data.get("topic", "General")
                
                logger.info(f"Received next question: {question_text[:50]}...")
                logger.info("Transitioning to ASK_QUESTION state")
                
                # Update state back to asking question
                manager.update_session_state(session_id, InterviewState.ASK_QUESTION)
                await send_state_update(session_id, InterviewState.ASK_QUESTION)
                
                # Send question to client (Simple JSON format)
                logger.info(f"Sending next question to frontend: {session_id}")
                await manager.send_personal_message({
                    "type": "question",
                    "text": question_text,
                    "topic": topic,
                    "index": result["question_index"],
                    "total": session.question_count
                }, session_id)
            # --- END CONNECTED PIPELINE ---
    
    except Exception as e:
        logger.error(f"Failed to handle transcript for {session_id}: {e}", exc_info=True)
        await send_error(session_id, "TRANSCRIBE_ERROR", str(e))


async def handle_silence_detected(session_id: str, message: Dict[str, Any]):
    """
    Handle silence detection - process answer and generate next question
    """
    try:
        silence_msg = SilenceDetectedMessage(**message)
        session = manager.get_session(session_id)
        
        if not session:
            await send_error(session_id, "SESSION_NOT_FOUND", "Session not found")
            return
        
        logger.info(f"Silence detected for {session_id}: {silence_msg.duration_seconds}s")
        
        # Update state
        manager.update_session_state(session_id, InterviewState.SILENCE_DETECT)
        await send_state_update(session_id, InterviewState.SILENCE_DETECT)
        
        # Get orchestrator
        orchestrator = manager.orchestrators.get(session_id)
        if not orchestrator:
            logger.warning(f"No orchestrator found for session {session_id}")
            return
        
        # Process answer using evaluation engine
        current_question = session.questions[-1] if session.questions else ""
        current_answer = orchestrator.current_answer_buffer
        
        if current_answer:
            # Evaluate with all 6 metrics
            evaluation = await evaluation_engine.evaluate_answer(
                question=current_question,
                answer=current_answer,
                job_role=session.job_role,
                job_description=session.job_description,
                question_number=session.current_question_number
            )
            
            # Store evaluation in session
            eval_record = AnswerEvaluationRecord(
                question_number=session.current_question_number,
                question=current_question,
                answer=current_answer,
                metrics=EvaluationMetricsModel(
                    technical_depth=evaluation.scores[EvaluationMetrics.TECHNICAL_DEPTH],
                    communication=evaluation.scores[EvaluationMetrics.COMMUNICATION],
                    confidence=evaluation.scores[EvaluationMetrics.CONFIDENCE],
                    logical_thinking=evaluation.scores[EvaluationMetrics.LOGICAL_THINKING],
                    problem_solving=evaluation.scores[EvaluationMetrics.PROBLEM_SOLVING],
                    culture_fit=evaluation.scores[EvaluationMetrics.CULTURE_FIT],
                ),
                needs_followup=evaluation.needs_followup,
                weaknesses=evaluation.weaknesses,
                strengths=evaluation.strengths,
                reasoning=evaluation.reasoning
            )
            session.evaluation_history.append(eval_record)
            
            # Send real-time evaluation update
            await send_evaluation_update(session_id, evaluation, session.current_question_number)
            
            # Update orchestrator with evaluation
            result = {
                "evaluation": {
                    "quality_score": evaluation.get_average_score(),
                    "needs_followup": evaluation.needs_followup,
                    "weaknesses": evaluation.weaknesses,
                    "strengths": evaluation.strengths
                },
                "needs_followup": evaluation.needs_followup,
                "next_action": "followup" if evaluation.needs_followup else "next_question",
                "quality_score": evaluation.get_average_score()
            }
            
            # Add to conversation history
            orchestrator.conversation_history.append((current_question, current_answer))
            session.answers.append(current_answer)
            orchestrator.current_answer_buffer = ""
        else:
            # Fallback to old method if no answer
            result = await orchestrator.process_answer()
        
        # Update state to evaluation
        manager.update_session_state(session_id, InterviewState.EVALUATE)
        await send_state_update(session_id, InterviewState.EVALUATE)
        
        # Decide next action
        if result["needs_followup"]:
            # Generate follow-up question
            followup_result = await orchestrator.generate_followup_question(result["evaluation"])
            
            if followup_result:
                # Send follow-up question
                logger.info(f"Sending follow-up question to frontend: {session_id}")
                await manager.send_personal_message({
                    "type": "question",
                    "text": followup_result["text"],
                    "topic": followup_result.get("topic", "Deep Dive"),
                    "index": session.current_question_number,
                    "total": session.question_count
                }, session_id)
        else:
            # Check if we should continue
            if orchestrator.should_continue():
                # Generate next question
                next_result = await orchestrator.generate_next_question()
                
                if next_result:
                    # Send next question
                    logger.info(f"Sending next question to frontend: {session_id}")
                    await manager.send_personal_message({
                        "type": "question",
                        "text": next_result["text"],
                        "topic": next_result.get("topic", "General"),
                        "index": session.current_question_number,
                        "total": session.question_count
                    }, session_id)
                else:
                    # Interview complete
                    orchestrator.complete_interview()
                    await manager.send_personal_message({
                        "type": "interview_complete",
                        "report": {} 
                    }, session_id)
            else:
                # Interview complete
                orchestrator.complete_interview()
                await manager.send_personal_message({
                    "type": "interview_complete",
                    "report": {} 
                }, session_id)
    
    except Exception as e:
        logger.error(f"Failed to handle silence for {session_id}: {e}", exc_info=True)
        await send_error(session_id, "SILENCE_DETECTED_ERROR", str(e))


async def handle_end_interview(session_id: str):
    """
    Manually terminate interview session
    """
    try:
        session = manager.get_session(session_id)
        if session:
            manager.update_session_state(session_id, InterviewState.COMPLETED)
            await send_state_update(session_id, InterviewState.COMPLETED)
            logger.info(f"Interview ended manually: {session_id}")
        else:
            await send_error(session_id, "SESSION_NOT_FOUND", "Session not found")
    
    except Exception as e:
        logger.error(f"Failed to end interview {session_id}: {e}", exc_info=True)
        await send_error(session_id, "END_INTERVIEW_ERROR", str(e))


async def handle_ping(session_id: str):
    """
    Handle ping message (keepalive)
    """
    await manager.send_personal_message({
        "type": ServerMessageType.PONG,
        "session_id": session_id,
        "timestamp": None
    }, session_id)


# Helper functions to send server messages
async def send_question_ready(session_id: str, question: str, question_number: int, total_questions: int):
    """
    Send question ready message to client
    """
    msg = QuestionReadyMessage(
        session_id=session_id,
        question=question,
        question_number=question_number,
        total_questions=total_questions
    )
    await manager.send_personal_message(msg.model_dump(), session_id)


async def send_state_update(session_id: str, state: InterviewState):
    """
    Send state update to client
    """
    msg = StateUpdateMessage(
        session_id=session_id,
        state=state
    )
    await manager.send_personal_message(msg.model_dump(), session_id)


async def send_error(session_id: str, error_code: str, error_message: str):
    """
    Send error message to client
    """
    msg = ErrorMessage(
        session_id=session_id,
        error_code=error_code,
        error_message=error_message
    )
    await manager.send_personal_message(msg.model_dump(), session_id)




async def send_evaluation_update(session_id: str, evaluation, question_number: int):
    """
    Send real-time evaluation update with all 6 metrics
    
    Args:
        session_id: Session ID
        evaluation: AnswerEvaluation object
        question_number: Current question number
    """
    
    # Convert scores to dict format
    scores_dict = {
        "technical_depth": evaluation.scores[EvaluationMetrics.TECHNICAL_DEPTH],
        "communication": evaluation.scores[EvaluationMetrics.COMMUNICATION],
        "confidence": evaluation.scores[EvaluationMetrics.CONFIDENCE],
        "logical_thinking": evaluation.scores[EvaluationMetrics.LOGICAL_THINKING],
        "problem_solving": evaluation.scores[EvaluationMetrics.PROBLEM_SOLVING],
        "culture_fit": evaluation.scores[EvaluationMetrics.CULTURE_FIT],
        "overall": evaluation.get_average_score()
    }
    
    msg = EvaluationUpdateMessage(
        session_id=session_id,
        scores=scores_dict,
        current_question_number=question_number
    )
    await manager.send_personal_message(msg.model_dump(), session_id)


async def send_interview_complete(session_id: str, session: InterviewSession):
    """
    Send interview complete message with final scores
    """
    
    # Get orchestrator for final evaluation
    orchestrator = manager.orchestrators.get(session_id)
    
    # Calculate final evaluation if we have evaluation history
    if session.evaluation_history and orchestrator:
        # Aggregate evaluations
        from app.interview_engine.evaluator import AnswerEvaluation
        
        evaluations = []
        for eval_record in session.evaluation_history:
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
        
        # Store final evaluation
        session.final_evaluation = FinalEvaluation(
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
            total_questions=session.question_count,
            total_answers=len(session.answers)
        )
        
        # Prepare final scores dict
        final_scores = {
            "overall_score": overall_score,
            "technical_depth": aggregated_scores[EvaluationMetrics.TECHNICAL_DEPTH],
            "communication": aggregated_scores[EvaluationMetrics.COMMUNICATION],
            "confidence": aggregated_scores[EvaluationMetrics.CONFIDENCE],
            "logical_thinking": aggregated_scores[EvaluationMetrics.LOGICAL_THINKING],
            "problem_solving": aggregated_scores[EvaluationMetrics.PROBLEM_SOLVING],
            "culture_fit": aggregated_scores[EvaluationMetrics.CULTURE_FIT],
        }
    else:
        # Fallback to old method
        overall_score = session.scores.get("overall_score", 5.0)
        if overall_score >= 7.5:
            verdict = "Hire"
        elif overall_score >= 6.0:
            verdict = "Borderline"
        else:
            verdict = "No-Hire"
        final_scores = session.scores
    
    msg = InterviewCompleteMessage(
        session_id=session_id,
        final_scores=final_scores,
        verdict=verdict,
        report_url=f"/api/reports/{session_id}/pdf"
    )
    await manager.send_personal_message(msg.model_dump(), session_id)
