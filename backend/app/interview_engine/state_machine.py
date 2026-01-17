"""
Interview State Machine
Formal definition of interview states and transitions
"""
import logging
from typing import Dict, List, Optional
from enum import Enum
from datetime import datetime

from app.models.interview import InterviewState

logger = logging.getLogger(__name__)


class StateTransitionError(Exception):
    """Raised when an invalid state transition is attempted"""
    pass


class InterviewStateMachine:
    """
    Formal state machine for interview flow
    
    Valid transitions:
    SETUP → ASK_QUESTION
    ASK_QUESTION → PLAY_TTS
    PLAY_TTS → LISTEN
    LISTEN → SILENCE_DETECT
    SILENCE_DETECT → TRANSCRIBE
    TRANSCRIBE → EVALUATE
    EVALUATE → FOLLOWUP (if needed) or NEXT_QUESTION
    FOLLOWUP → ASK_QUESTION
    NEXT_QUESTION → ASK_QUESTION (if more questions) or FINAL_EVALUATION
    FINAL_EVALUATION → REPORT
    REPORT → COMPLETED
    """
    
    # Valid state transitions
    VALID_TRANSITIONS: Dict[InterviewState, List[InterviewState]] = {
        InterviewState.SETUP: [InterviewState.ASK_QUESTION, InterviewState.ERROR],
        InterviewState.ASK_QUESTION: [InterviewState.PLAY_TTS, InterviewState.ERROR],
        InterviewState.PLAY_TTS: [InterviewState.LISTEN, InterviewState.ERROR],
        InterviewState.LISTEN: [InterviewState.SILENCE_DETECT, InterviewState.ERROR],
        InterviewState.SILENCE_DETECT: [InterviewState.TRANSCRIBE, InterviewState.ERROR],
        InterviewState.TRANSCRIBE: [InterviewState.EVALUATE, InterviewState.ERROR],
        InterviewState.EVALUATE: [
            InterviewState.FOLLOWUP, 
            InterviewState.NEXT_QUESTION, 
            InterviewState.FINAL_EVALUATION,
            InterviewState.ERROR
        ],
        InterviewState.FOLLOWUP: [InterviewState.ASK_QUESTION, InterviewState.ERROR],
        InterviewState.NEXT_QUESTION: [
            InterviewState.ASK_QUESTION, 
            InterviewState.FINAL_EVALUATION,
            InterviewState.ERROR
        ],
        InterviewState.FINAL_EVALUATION: [InterviewState.REPORT, InterviewState.ERROR],
        InterviewState.REPORT: [InterviewState.COMPLETED, InterviewState.ERROR],
        InterviewState.ERROR: [InterviewState.SETUP, InterviewState.COMPLETED],
        InterviewState.COMPLETED: []  # Terminal state
    }
    
    def __init__(self, initial_state: InterviewState = InterviewState.SETUP):
        """
        Initialize state machine
        
        Args:
            initial_state: Starting state
        """
        self.current_state = initial_state
        self.transition_history: List[Dict] = []
        self.state_entry_times: Dict[InterviewState, datetime] = {}
        self.enter_state(initial_state)
    
    def can_transition_to(self, target_state: InterviewState) -> bool:
        """
        Check if transition to target state is valid
        
        Args:
            target_state: Target state to transition to
            
        Returns:
            True if transition is valid
        """
        valid_targets = self.VALID_TRANSITIONS.get(self.current_state, [])
        return target_state in valid_targets
    
    def transition_to(self, target_state: InterviewState) -> bool:
        """
        Transition to target state if valid
        
        Args:
            target_state: Target state to transition to
            
        Returns:
            True if transition successful, False otherwise
            
        Raises:
            StateTransitionError: If transition is invalid
        """
        if not self.can_transition_to(target_state):
            error_msg = (
                f"Invalid transition from {self.current_state.value} "
                f"to {target_state.value}"
            )
            logger.error(error_msg)
            raise StateTransitionError(error_msg)
        
        previous_state = self.current_state
        self.current_state = target_state
        
        # Record transition
        transition_record = {
            "from": previous_state.value,
            "to": target_state.value,
            "timestamp": datetime.utcnow()
        }
        self.transition_history.append(transition_record)
        
        # Enter new state
        self.enter_state(target_state)
        
        logger.debug(
            f"State transition: {previous_state.value} → {target_state.value}"
        )
        return True
    
    def enter_state(self, state: InterviewState):
        """
        Enter a state (record entry time)
        
        Args:
            state: State being entered
        """
        self.state_entry_times[state] = datetime.utcnow()
    
    def get_time_in_state(self, state: InterviewState) -> Optional[float]:
        """
        Get time spent in a state (seconds)
        
        Args:
            state: State to check
            
        Returns:
            Time in seconds, or None if state not entered
        """
        if state not in self.state_entry_times:
            return None
        
        entry_time = self.state_entry_times[state]
        return (datetime.utcnow() - entry_time).total_seconds()
    
    def get_current_state(self) -> InterviewState:
        """Get current state"""
        return self.current_state
    
    def get_transition_history(self) -> List[Dict]:
        """Get transition history"""
        return self.transition_history.copy()
    
    def reset(self, new_state: InterviewState = InterviewState.SETUP):
        """
        Reset state machine to initial state
        
        Args:
            new_state: State to reset to
        """
        self.current_state = new_state
        self.transition_history = []
        self.state_entry_times = {}
        self.enter_state(new_state)
        logger.info(f"State machine reset to {new_state.value}")
    
    def is_terminal_state(self) -> bool:
        """
        Check if current state is terminal (no more transitions)
        
        Returns:
            True if in terminal state
        """
        return self.current_state in [InterviewState.COMPLETED, InterviewState.ERROR]
    
    def validate_state(self, state: InterviewState) -> bool:
        """
        Validate that a state is valid
        
        Args:
            state: State to validate
            
        Returns:
            True if state is valid
        """
        return state in InterviewState
