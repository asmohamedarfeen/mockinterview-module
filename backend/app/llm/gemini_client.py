"""
Google Gemini 2.0 Flash API Client
Strict FAANG-style HR interviewer persona
"""
import os
import logging
from typing import Dict, List, Optional, Tuple
from google import genai
from google.genai import types

from app.core.config import settings

logger = logging.getLogger(__name__)


class GeminiClient:
    """
    Client for interacting with Google Gemini 2.0 Flash
    Configured as a strict FAANG HR interviewer
    """
    
    def __init__(self):
        """Initialize Gemini client with API key"""
        api_key = settings.gemini_api_key
        if not api_key:
            logger.warning("GEMINI_API_KEY not set - Gemini features will be disabled")
            self.client = None
            self.model_name = None
            return
        
        try:
            self.client = genai.Client(api_key=api_key)
            self.model_name = "gemini-2.0-flash"
            
            logger.info(f"Gemini client initialized with model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            self.client = None
            self.model_name = None
    
    def _get_system_prompt(self, job_role: str, job_description: str) -> str:
        """
        Generate system prompt for strict FAANG HR interviewer
        """
        return f"""You are a strict FAANG-style female HR interviewer conducting a mock interview.

Your role:
- Ask concise, deep, job-relevant questions
- Probe weaknesses in answers
- Maintain professional corporate tone
- Follow STAR method (Situation, Task, Action, Result) when appropriate
- Assess: technical depth, communication, confidence, logical thinking, problem-solving, culture fit

Job Role: {job_role}
Job Description: {job_description}

Guidelines:
1. Start with a welcoming but professional tone
2. Ask questions that test specific job requirements
3. If an answer is vague, incomplete, or off-topic, ask a follow-up to probe deeper
4. Maintain interview flow and avoid repetitive questions
5. Keep questions concise (1-2 sentences max)
6. Be direct and professional, not overly friendly

Generate questions that:
- Build on previous answers
- Probe deeper if answer was weak
- Test specific job requirements
- Maintain professional interview flow"""
    
    async def generate_first_question(
        self, 
        job_role: str, 
        job_description: str
    ) -> Dict[str, str]:
        """
        Generate the first interview question
        
        Args:
            job_role: The job role being interviewed for
            job_description: Job description text
            
        Returns:
            Dict with 'text' and 'topic'
        """
        if not self.client:
            raise RuntimeError(
                "Gemini client is not initialized. Please ensure GEMINI_API_KEY is set in environment variables."
            )
        
        prompt = f"""Generate the first interview question for a {job_role} position.

Job Description: {job_description}

Generate a concise, professional opening question (1-2 sentences).

OUTPUT FORMAT:
TOPIC: [Short 2-3 word title, e.g. "Introduction"]
QUESTION: [The question text]"""
        
        
        config = types.GenerateContentConfig(
            temperature=0.7,
            top_p=0.95,
            top_k=40,
            max_output_tokens=8192,
        )

        response = await self.client.aio.models.generate_content(
            model=self.model_name,
            contents=[
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=prompt)]
                )
            ],
            config=config
        )
        text = response.text.strip()
        
        topic = "Introduction"
        question_text = text
        
        lines = text.split('\n')
        for line in lines:
            if line.startswith("TOPIC:"):
                topic = line.split(":", 1)[1].strip()
            elif line.startswith("QUESTION:"):
                question_text = line.split(":", 1)[1].strip()
                
        if "QUESTION:" not in text and "TOPIC:" not in text:
             question_text = text
        
        # Clean up
        question_text = question_text.replace("**", "").strip()
        if question_text.startswith('"') and question_text.endswith('"'):
            question_text = question_text[1:-1]
        
        logger.info(f"Generated first question: {question_text[:50]}...")
        return {
            "text": question_text,
            "topic": topic
        }
    
    async def generate_next_question(
        self,
        job_role: str,
        job_description: str,
        conversation_history: List[Tuple[str, str]],  # List of (question, answer) tuples
        current_question_number: int,
        total_questions: int
    ) -> Dict[str, str]:
        """
        Generate next question based on conversation history
        
        Args:
            job_role: The job role
            job_description: Job description
            conversation_history: List of (question, answer) tuples
            current_question_number: Current question number (0-indexed)
            total_questions: Total number of questions
            
        Returns:
            Dict with 'text' and 'topic' of the question
        """
        if not self.client:
            raise RuntimeError(
                "Gemini client is not initialized. Please ensure GEMINI_API_KEY is set in environment variables."
            )
        
        # Format conversation history
        history_text = ""
        for i, (q, a) in enumerate(conversation_history[-3:], 1):  # Last 3 Q&A pairs
            history_text += f"\nQ{i}: {q}\nA{i}: {a}\n"
        
        prompt = f"""You are conducting a strict, dynamic mock interview for a {job_role} position.

Job Description: {job_description}

Previous conversation:
{history_text}

Current progress: Question {current_question_number + 1} of {total_questions}

INSTRUCTIONS:
1. You MUST reference a specific technical concept, tool, or claim mentioned in the candidate's LAST answer (A{len(conversation_history)}).
2. Do NOT ask generic "standard" questions (e.g., "Tell me about a challenge") unless they are directly related to the specific context the candidate just provided.
3. Be reactive. drill down. If they mentioned "Redis", ask about Redis strategies. If they mentioned "Leadership", ask about a specific leadership scenario they implied.
4. Keep the question concise (1-2 sentences).

OUTPUT FORMAT:
Generate the response in the following format:
TOPIC: [Short 2-3 word title of the topic being asked, e.g. "API Scalability", "Conflict Resolution"]
QUESTION: [The interview question text]"""
        
        config = types.GenerateContentConfig(
            temperature=0.7,
            top_p=0.95,
            top_k=40,
            max_output_tokens=8192,
        )
        
        response = await self.client.aio.models.generate_content(
            model=self.model_name,
            contents=[
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=prompt)]
                )
            ],
            config=config
        )
        text = response.text.strip()
        
        topic = "General"
        question_text = text
        
        # Simple parsing
        lines = text.split('\n')
        for line in lines:
            if line.startswith("TOPIC:"):
                topic = line.split(":", 1)[1].strip()
            elif line.startswith("QUESTION:"):
                question_text = line.split(":", 1)[1].strip()
        
        # Fallback if parsing failed but text exists
        if "QUESTION:" not in text and "TOPIC:" not in text:
             question_text = text

        # Cleanup
        question_text = question_text.replace("**", "").strip()
        if question_text.startswith('"') and question_text.endswith('"'):
            question_text = question_text[1:-1]
        
        logger.info(f"Generated question {current_question_number + 1}: {question_text[:50]}... Topic: {topic}")
        return {
            "text": question_text,
            "topic": topic
        }
    
    async def evaluate_answer(
        self,
        question: str,
        answer: str,
        job_role: str,
        job_description: str
    ) -> Dict[str, any]:
        """
        Evaluate an answer and determine if follow-up is needed
        
        Args:
            question: The question that was asked
            answer: The candidate's answer
            job_role: Job role
            job_description: Job description
            
        Returns:
            Dictionary with:
            - quality_score: float (0-10)
            - needs_followup: bool
            - weaknesses: List[str]
            - strengths: List[str]
        """
        if not self.client:
            raise RuntimeError(
                "Gemini client is not initialized. Please ensure GEMINI_API_KEY is set in environment variables."
            )
        
        prompt = f"""Evaluate this interview answer for a {job_role} position.

Job Description: {job_description}

Question: {question}
Answer: {answer}

Evaluate the answer and provide:
1. Quality score (0-10): How well did they answer?
2. Needs follow-up (yes/no): Is the answer vague, incomplete, or off-topic?
3. Weaknesses: List specific weaknesses (e.g., "too vague", "lacks examples", "off-topic")
4. Strengths: List specific strengths (e.g., "clear examples", "relevant experience", "good structure")

Format your response as:
QUALITY_SCORE: [number]
NEEDS_FOLLOWUP: [yes/no]
WEAKNESSES: [comma-separated list]
STRENGTHS: [comma-separated list]"""
        
        config = types.GenerateContentConfig(
            temperature=0.2, # Lower temperature for evaluation
            top_p=0.95,
            top_k=40,
            max_output_tokens=8192,
        )

        response = await self.client.aio.models.generate_content(
            model=self.model_name,
            contents=[
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=prompt)]
                )
            ],
            config=config
        )
        text = response.text.strip()
        
        # Parse response
        quality_score = 5.0
        needs_followup = False
        weaknesses = []
        strengths = []
        
        for line in text.split('\n'):
            line = line.strip()
            if line.startswith('QUALITY_SCORE:'):
                try:
                    quality_score = float(line.split(':', 1)[1].strip())
                except:
                    pass
            elif line.startswith('NEEDS_FOLLOWUP:'):
                needs_followup = line.split(':', 1)[1].strip().lower() == 'yes'
            elif line.startswith('WEAKNESSES:'):
                weaknesses_text = line.split(':', 1)[1].strip()
                weaknesses = [w.strip() for w in weaknesses_text.split(',') if w.strip()]
            elif line.startswith('STRENGTHS:'):
                strengths_text = line.split(':', 1)[1].strip()
                strengths = [s.strip() for s in strengths_text.split(',') if s.strip()]
        
        logger.info(f"Answer evaluation - Score: {quality_score}, Follow-up: {needs_followup}")
        
        return {
            "quality_score": max(0, min(10, quality_score)),
            "needs_followup": needs_followup,
            "weaknesses": weaknesses,
            "strengths": strengths
        }
    
    async def evaluate_answer_detailed(
        self,
        question: str,
        answer: str,
        job_role: str,
        job_description: str
    ) -> Dict[str, any]:
        """
        Evaluate answer with all 6 metrics using detailed scoring
        
        Args:
            question: The question asked
            answer: The candidate's answer
            job_role: Job role
            job_description: Job description
            
        Returns:
            Dictionary with:
            - technical_depth: float (0-10)
            - communication: float (0-10)
            - confidence: float (0-10)
            - logical_thinking: float (0-10)
            - problem_solving: float (0-10)
            - culture_fit: float (0-10)
            - needs_followup: bool
            - weaknesses: List[str]
            - strengths: List[str]
            - reasoning: str
        """
        if not self.client:
            raise RuntimeError(
                "Gemini client is not initialized. Please ensure GEMINI_API_KEY is set in environment variables."
            )
        
        prompt = f"""Evaluate this interview answer for a {job_role} position across 6 specific metrics.

Job Description: {job_description}

Question: {question}
Answer: {answer}

Evaluate the answer and provide scores (0-10) for each metric:

1. TECHNICAL_DEPTH (0-10): Understanding of technical concepts, depth of knowledge, technical accuracy
2. COMMUNICATION (0-10): Clarity, articulation, ability to explain ideas clearly, structure of response
3. CONFIDENCE (0-10): Self-assurance, poise, professional presence, conviction in answers
4. LOGICAL_THINKING (0-10): Problem-solving approach, reasoning ability, logical flow of thoughts
5. PROBLEM_SOLVING (0-10): Ability to break down problems, find solutions, analytical thinking
6. CULTURE_FIT (0-10): Alignment with company values, team collaboration, cultural fit

Also provide:
- NEEDS_FOLLOWUP: yes/no (Is the answer vague, incomplete, or off-topic?)
- WEAKNESSES: List specific weaknesses
- STRENGTHS: List specific strengths
- REASONING: Brief explanation of the evaluation

Format your response EXACTLY as:
TECHNICAL_DEPTH: [number]
COMMUNICATION: [number]
CONFIDENCE: [number]
LOGICAL_THINKING: [number]
PROBLEM_SOLVING: [number]
CULTURE_FIT: [number]
NEEDS_FOLLOWUP: [yes/no]
WEAKNESSES: [comma-separated list]
STRENGTHS: [comma-separated list]
REASONING: [brief explanation]"""
        
        config = types.GenerateContentConfig(
            temperature=0.2, # Lower temperature for evaluation
            top_p=0.95,
            top_k=40,
            max_output_tokens=8192,
        )
        
        response = await self.client.aio.models.generate_content(
            model=self.model_name,
            contents=[
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=prompt)]
                )
            ],
            config=config
        )
        text = response.text.strip()
        
        # Parse response
        scores = {
            "technical_depth": 5.0,
            "communication": 5.0,
            "confidence": 5.0,
            "logical_thinking": 5.0,
            "problem_solving": 5.0,
            "culture_fit": 5.0,
        }
        needs_followup = False
        weaknesses = []
        strengths = []
        reasoning = ""
        
        current_section = None
        for line in text.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            # Parse metric scores
            for metric in scores.keys():
                if line.upper().startswith(metric.upper().replace('_', '_') + ':'):
                    try:
                        score = float(line.split(':', 1)[1].strip())
                        scores[metric] = max(0.0, min(10.0, score))
                    except:
                        pass
                    break
            
            # Parse other fields
            if line.upper().startswith('NEEDS_FOLLOWUP:'):
                needs_followup = line.split(':', 1)[1].strip().lower() == 'yes'
            elif line.upper().startswith('WEAKNESSES:'):
                weaknesses_text = line.split(':', 1)[1].strip()
                weaknesses = [w.strip() for w in weaknesses_text.split(',') if w.strip()]
            elif line.upper().startswith('STRENGTHS:'):
                strengths_text = line.split(':', 1)[1].strip()
                strengths = [s.strip() for s in strengths_text.split(',') if s.strip()]
            elif line.upper().startswith('REASONING:'):
                reasoning = line.split(':', 1)[1].strip()
        
        result = {
            **scores,
            "needs_followup": needs_followup,
            "weaknesses": weaknesses,
            "strengths": strengths,
            "reasoning": reasoning
        }
        
        logger.info(
            f"Detailed evaluation - "
            f"Tech: {scores['technical_depth']:.1f}, "
            f"Comm: {scores['communication']:.1f}, "
            f"Conf: {scores['confidence']:.1f}"
        )
        
        return result
    
    async def generate_followup_question(
        self,
        original_question: str,
        answer: str,
        weaknesses: List[str],
        job_role: str
    ) -> Dict[str, str]:
        """
        Generate a follow-up question to probe deeper
        
        Returns:
            Dict with 'text' and 'topic'
        """
        if not self.client:
            raise RuntimeError(
                "Gemini client is not initialized. Please ensure GEMINI_API_KEY is set in environment variables."
            )
        
        weaknesses_text = ", ".join(weaknesses) if weaknesses else "answer was vague or incomplete"
        
        prompt = f"""The candidate was asked: "{original_question}"
They answered: "{answer}"

Weaknesses identified: {weaknesses_text}

Generate a concise follow-up question (1-2 sentences) that drills deeper into the specific concepts mentioned (or missed).

OUTPUT FORMAT:
TOPIC: [Short 2-3 word title, e.g. "Security Implementation", "Clarification"]
QUESTION: [The question text]"""
        
        config = types.GenerateContentConfig(
            temperature=0.7,
            top_p=0.95,
            top_k=40,
            max_output_tokens=8192,
        )
        
        response = await self.client.aio.models.generate_content(
            model=self.model_name,
            contents=[
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=prompt)]
                )
            ],
            config=config
        )
        text = response.text.strip()
        
        topic = "Deep Dive"
        question_text = text
        
        lines = text.split('\n')
        for line in lines:
            if line.startswith("TOPIC:"):
                topic = line.split(":", 1)[1].strip()
            elif line.startswith("QUESTION:"):
                question_text = line.split(":", 1)[1].strip()
        
            # Fallback
        if "QUESTION:" not in text and "TOPIC:" not in text:
                question_text = text
        
        # Clean up formatting
        question_text = question_text.replace("**", "").strip()
        if question_text.startswith('"') and question_text.endswith('"'):
            question_text = question_text[1:-1]
        
        logger.info(f"Generated follow-up question: {question_text[:50]}...")
        return {
            "text": question_text,
            "topic": topic
        }


# Global Gemini client instance
gemini_client = GeminiClient()
