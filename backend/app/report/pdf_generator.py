"""
PDF Report Generator
Generate comprehensive interview reports using ReportLab
"""
import logging
from io import BytesIO
from datetime import datetime
from typing import Dict, List, Optional
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

from app.models.interview import InterviewSession, FinalEvaluation

logger = logging.getLogger(__name__)


class PDFReportGenerator:
    """
    Generate PDF reports for interview sessions
    """
    
    def __init__(self):
        """Initialize PDF generator"""
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a73e8'),
            spaceAfter=30,
            alignment=TA_CENTER
        ))
        
        # Heading style
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#202124'),
            spaceAfter=12,
            spaceBefore=12
        ))
        
        # Body style
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#3c4043'),
            spaceAfter=12,
            alignment=TA_JUSTIFY
        ))
        
        # Verdict style
        self.styles.add(ParagraphStyle(
            name='Verdict',
            parent=self.styles['Heading2'],
            fontSize=18,
            textColor=colors.HexColor('#34a853'),
            spaceAfter=20,
            alignment=TA_CENTER
        ))
    
    def generate_pdf(self, session: InterviewSession) -> BytesIO:
        """
        Generate PDF report for interview session
        
        Args:
            session: Interview session with evaluation data
            
        Returns:
            BytesIO buffer containing PDF
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        story = []
        
        # Build PDF content
        story.extend(self._build_header(session))
        story.append(Spacer(1, 0.2 * inch))
        
        story.extend(self._build_executive_summary(session))
        story.append(PageBreak())
        
        story.extend(self._build_score_breakdown(session))
        story.append(Spacer(1, 0.2 * inch))
        
        story.extend(self._build_strengths_weaknesses(session))
        story.append(Spacer(1, 0.2 * inch))
        
        story.extend(self._build_improvement_suggestions(session))
        story.append(PageBreak())
        
        story.extend(self._build_qa_summary(session))
        story.append(Spacer(1, 0.2 * inch))
        
        story.extend(self._build_recommendations(session))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        
        logger.info(f"Generated PDF report for session {session.session_id}")
        return buffer
    
    def _build_header(self, session: InterviewSession) -> List:
        """Build PDF header"""
        elements = []
        
        # Title
        elements.append(Paragraph("Qrow IQ - Interview Report", self.styles['CustomTitle']))
        elements.append(Spacer(1, 0.1 * inch))
        
        # Interview details
        details_data = [
            ['Job Role:', session.job_role],
            ['Session ID:', session.session_id],
            ['Date:', session.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')],
            ['Total Questions:', str(session.question_count)],
            ['Questions Answered:', str(len(session.answers))]
        ]
        
        details_table = Table(details_data, colWidths=[2 * inch, 4 * inch])
        details_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8f9fa')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#202124')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dadce0')),
        ]))
        
        elements.append(details_table)
        return elements
    
    def _build_executive_summary(self, session: InterviewSession) -> List:
        """Build executive summary section"""
        elements = []
        
        elements.append(Paragraph("Executive Summary", self.styles['CustomHeading']))
        
        if session.final_evaluation:
            eval = session.final_evaluation
            overall_score = eval.overall_score
            verdict = eval.verdict
            
            # Verdict
            verdict_color = colors.HexColor('#34a853') if verdict == "Hire" else \
                          colors.HexColor('#fbbc04') if verdict == "Borderline" else \
                          colors.HexColor('#ea4335')
            
            verdict_style = ParagraphStyle(
                name='VerdictStyle',
                parent=self.styles['Heading2'],
                fontSize=20,
                textColor=verdict_color,
                spaceAfter=15,
                alignment=TA_CENTER
            )
            
            elements.append(Paragraph(f"Verdict: {verdict}", verdict_style))
            elements.append(Paragraph(f"Overall Score: {overall_score:.1f}/10", self.styles['CustomBody']))
            elements.append(Spacer(1, 0.1 * inch))
            
            # Key insights
            if eval.insights:
                insights_text = f"""
                <b>Key Insights:</b><br/>
                • Strongest Area: {eval.insights.get('strongest_metric', 'N/A').replace('_', ' ').title()}<br/>
                • Weakest Area: {eval.insights.get('weakest_metric', 'N/A').replace('_', ' ').title()}<br/>
                • Average Score: {eval.insights.get('average_score', 0):.1f}/10<br/>
                • Total Answers Evaluated: {eval.insights.get('total_answers', 0)}
                """
                elements.append(Paragraph(insights_text, self.styles['CustomBody']))
        else:
            elements.append(Paragraph("Evaluation data not available.", self.styles['CustomBody']))
        
        return elements
    
    def _build_score_breakdown(self, session: InterviewSession) -> List:
        """Build score breakdown section"""
        elements = []
        
        elements.append(Paragraph("Score Breakdown", self.styles['CustomHeading']))
        
        if session.final_evaluation:
            eval = session.final_evaluation
            metrics = eval.aggregated_metrics
            
            # Create metrics table
            metrics_data = [
                ['Metric', 'Score', 'Rating'],
                ['Technical Depth', f"{metrics.technical_depth:.1f}/10", self._get_rating(metrics.technical_depth)],
                ['Communication', f"{metrics.communication:.1f}/10", self._get_rating(metrics.communication)],
                ['Confidence', f"{metrics.confidence:.1f}/10", self._get_rating(metrics.confidence)],
                ['Logical Thinking', f"{metrics.logical_thinking:.1f}/10", self._get_rating(metrics.logical_thinking)],
                ['Problem Solving', f"{metrics.problem_solving:.1f}/10", self._get_rating(metrics.problem_solving)],
                ['Culture Fit', f"{metrics.culture_fit:.1f}/10", self._get_rating(metrics.culture_fit)],
            ]
            
            metrics_table = Table(metrics_data, colWidths=[2.5 * inch, 1.5 * inch, 2 * inch])
            metrics_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a73e8')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dadce0')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
            ]))
            
            elements.append(metrics_table)
        else:
            elements.append(Paragraph("Score data not available.", self.styles['CustomBody']))
        
        return elements
    
    def _build_strengths_weaknesses(self, session: InterviewSession) -> List:
        """Build strengths and weaknesses section"""
        elements = []
        
        elements.append(Paragraph("Strengths & Weaknesses", self.styles['CustomHeading']))
        
        if session.final_evaluation and session.final_evaluation.insights:
            insights = session.final_evaluation.insights
            
            # Strengths
            elements.append(Paragraph("<b>Strengths:</b>", self.styles['CustomBody']))
            strengths = insights.get('common_strengths', [])
            if strengths:
                strengths_text = "• " + "<br/>• ".join(strengths[:5])
                elements.append(Paragraph(strengths_text, self.styles['CustomBody']))
            else:
                elements.append(Paragraph("No specific strengths identified.", self.styles['CustomBody']))
            
            elements.append(Spacer(1, 0.1 * inch))
            
            # Weaknesses
            elements.append(Paragraph("<b>Areas for Improvement:</b>", self.styles['CustomBody']))
            weaknesses = insights.get('common_weaknesses', [])
            if weaknesses:
                weaknesses_text = "• " + "<br/>• ".join(weaknesses[:5])
                elements.append(Paragraph(weaknesses_text, self.styles['CustomBody']))
            else:
                elements.append(Paragraph("No specific weaknesses identified.", self.styles['CustomBody']))
        else:
            elements.append(Paragraph("Evaluation insights not available.", self.styles['CustomBody']))
        
        return elements
    
    def _build_improvement_suggestions(self, session: InterviewSession) -> List:
        """Build improvement suggestions section"""
        elements = []
        
        elements.append(Paragraph("Improvement Suggestions", self.styles['CustomHeading']))
        
        suggestions = self._generate_suggestions(session)
        if suggestions:
            suggestions_text = "<br/>".join([f"• {s}" for s in suggestions])
            elements.append(Paragraph(suggestions_text, self.styles['CustomBody']))
        else:
            elements.append(Paragraph("Continue practicing interview skills and technical knowledge.", self.styles['CustomBody']))
        
        return elements
    
    def _build_qa_summary(self, session: InterviewSession) -> List:
        """Build question-answer summary"""
        elements = []
        
        elements.append(Paragraph("Question & Answer Summary", self.styles['CustomHeading']))
        
        if session.questions and session.answers:
            for i, (question, answer) in enumerate(zip(session.questions, session.answers), 1):
                elements.append(Paragraph(f"<b>Question {i}:</b> {question}", self.styles['CustomBody']))
                elements.append(Paragraph(f"<b>Answer:</b> {answer}", self.styles['CustomBody']))
                elements.append(Spacer(1, 0.1 * inch))
        else:
            elements.append(Paragraph("No Q&A data available.", self.styles['CustomBody']))
        
        return elements
    
    def _build_recommendations(self, session: InterviewSession) -> List:
        """Build final recommendations section"""
        elements = []
        
        elements.append(Paragraph("Final Recommendations", self.styles['CustomHeading']))
        
        if session.final_evaluation:
            verdict = session.final_evaluation.verdict
            overall_score = session.final_evaluation.overall_score
            
            if verdict == "Hire":
                recommendation = f"""
                Based on the comprehensive evaluation, this candidate demonstrates strong qualifications 
                with an overall score of {overall_score:.1f}/10. The candidate shows proficiency across 
                multiple evaluation metrics and is recommended for hiring consideration.
                """
            elif verdict == "Borderline":
                recommendation = f"""
                The candidate shows potential with an overall score of {overall_score:.1f}/10, but there 
                are areas that need improvement. Consider additional assessment or a follow-up interview 
                to better evaluate fit for the role.
                """
            else:
                recommendation = f"""
                The candidate's overall score of {overall_score:.1f}/10 indicates significant gaps in 
                required competencies. Further development is recommended before considering for this position.
                """
            
            elements.append(Paragraph(recommendation, self.styles['CustomBody']))
        else:
            elements.append(Paragraph("Recommendation data not available.", self.styles['CustomBody']))
        
        return elements
    
    def _get_rating(self, score: float) -> str:
        """Get rating text based on score"""
        if score >= 8.0:
            return "Excellent"
        elif score >= 6.5:
            return "Good"
        elif score >= 5.0:
            return "Average"
        elif score >= 3.5:
            return "Below Average"
        else:
            return "Needs Improvement"
    
    def _generate_suggestions(self, session: InterviewSession) -> List[str]:
        """Generate improvement suggestions based on evaluation"""
        suggestions = []
        
        if not session.final_evaluation:
            return suggestions
        
        eval = session.final_evaluation
        metrics = eval.aggregated_metrics
        
        # Generate suggestions based on weakest areas
        if metrics.technical_depth < 6.0:
            suggestions.append("Focus on deepening technical knowledge and understanding of core concepts relevant to the role.")
        
        if metrics.communication < 6.0:
            suggestions.append("Practice articulating thoughts clearly and structuring responses using the STAR method (Situation, Task, Action, Result).")
        
        if metrics.confidence < 6.0:
            suggestions.append("Work on building confidence through practice interviews and preparation. Maintain professional presence.")
        
        if metrics.logical_thinking < 6.0:
            suggestions.append("Develop logical reasoning skills by practicing problem-solving exercises and explaining thought processes.")
        
        if metrics.problem_solving < 6.0:
            suggestions.append("Practice breaking down complex problems into smaller components and demonstrating analytical thinking.")
        
        if metrics.culture_fit < 6.0:
            suggestions.append("Research company values and culture. Prepare examples that demonstrate alignment with team collaboration and company mission.")
        
        # General suggestions
        if not suggestions:
            suggestions.append("Continue practicing interview skills and maintaining strong performance across all areas.")
        
        return suggestions[:6]  # Limit to 6 suggestions


# Global PDF generator instance
pdf_generator = PDFReportGenerator()
