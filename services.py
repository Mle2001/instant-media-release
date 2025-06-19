"""
Instant Media Release - Business Logic Services
================================================
This new module contains business logic services that are decoupled from the main
FastAPI server and agent definitions. This follows the principle of Separation of
Concerns, making the codebase cleaner and more maintainable.

Services included:
1.  ReportingService: Handles the generation of client-facing PDF reports.
2.  StrategyOptimizerService: Manages the few-shot learning loop by archiving
    successful strategies and providing them as examples for future agent runs.
"""

import os
import json
import random
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import desc
from loguru import logger
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

# Import project-specific models
from database import UserRequest, PerformanceReport, SuccessfulStrategy

# ==============================================================================
# SECTION 1: CONFIGURATION
# ==============================================================================

# Directory to store generated PDF reports
REPORT_DIR = "generated_reports"
os.makedirs(REPORT_DIR, exist_ok=True)

# The ROI threshold to consider a campaign "successful" and worth learning from
SUCCESS_CRITERIA_ROI = float(os.getenv("SUCCESS_CRITERIA_ROI", "50.0"))

# Font setup for PDF generation to support Vietnamese characters.
# IMPORTANT: Place a Vietnamese-compatible .ttf font file (e.g., 'Roboto-Regular.ttf')
# in the project's root directory.
try:
    FONT_PATH = 'Roboto-Regular.ttf'
    pdfmetrics.registerFont(TTFont('VietnameseFont', FONT_PATH))
    logger.info(f"✅ Vietnamese font '{FONT_PATH}' successfully registered for PDF generation.")
except Exception:
    logger.warning(
        f"Font '{FONT_PATH}' not found. PDF reports may not display Vietnamese characters correctly. "
        "Falling back to Helvetica. Please download a compatible font from Google Fonts."
    )
    # Fallback to a default font if the custom one is not found
    pdfmetrics.registerFont(TTFont('VietnameseFont', 'Helvetica'))

# ==============================================================================
# SECTION 2: REPORTING SERVICE
# ==============================================================================

class ReportingService:
    """
    A service dedicated to generating performance reports for completed campaigns.
    """
    def __init__(self, db_session: Session):
        """Initializes the service with a database session."""
        self.db = db_session

    async def generate_performance_report(self, session_id: str) -> Optional[PerformanceReport]:
        """
        Generates a PDF performance report and saves the report data to the database.
        
        Args:
            session_id: The unique ID of the session to generate a report for.

        Returns:
            The PerformanceReport database object if successful, otherwise None.
        """
        logger.info(f"📊 Starting performance report generation for session_id: {session_id}")
        user_request = self.db.query(UserRequest).filter(UserRequest.session_id == session_id).first()

        if not user_request or not user_request.final_report_json:
            logger.error(f"❌ Cannot generate report. No data found for session: {session_id}")
            return None

        # Load the final results from the agent process
        agent_result = json.loads(user_request.final_report_json)
        
        # Simulate collecting post-campaign performance metrics
        performance_data = self._simulate_performance_metrics(agent_result)
        
        # Create the physical PDF file
        pdf_path = self._create_pdf_report(agent_result, performance_data)
        
        # Check if a report entry already exists to avoid duplicates
        report = self.db.query(PerformanceReport).filter(PerformanceReport.user_request_id == user_request.id).first()
        if not report:
            report = PerformanceReport(user_request_id=user_request.id)
            self.db.add(report)

        # Update the report object with the new performance data
        report.total_reach = performance_data["total_reach"]
        report.engagement_rate = performance_data["engagement_rate"]
        report.mentions_count = len(performance_data["mentions"])
        report.roi = performance_data["roi"]
        report.report_url = os.path.basename(pdf_path) # Store only the filename
        report.generated_at = datetime.utcnow()
        
        # Update the original user request status
        user_request.status = 'reported'
        
        self.db.commit()
        self.db.refresh(report)
        logger.info(f"✅ Successfully created/updated performance report: {pdf_path}")
        return report
    
    def _simulate_performance_metrics(self, agent_result: dict) -> dict:
        """
        This is a placeholder method to simulate the collection of real-world
        performance data after a campaign has run. In a real application, this
        would involve integrating with media monitoring tools.
        """
        logger.info("📈 Simulating the collection of post-campaign performance metrics...")
        recommendations = agent_result.get("media_recommendations", [])
        pricing = agent_result.get("pricing_analysis", {})
        
        # Simulate actual reach based on agent's estimate, with some variance
        estimated_reach = sum(rec.get('estimated_reach', 0) for rec in recommendations)
        actual_reach = int(estimated_reach * random.uniform(0.85, 1.3)) # 85% to 130% of estimate
        
        cost = pricing.get("total_cost_vnd", 1) or 1 # Avoid division by zero
        
        # Simulate profit based on reach. Assume each person reached generates a certain value.
        profit_per_reach = random.randint(8, 15) # Assume each reach is worth 8-15 VND in brand value
        total_profit = actual_reach * profit_per_reach
        roi = ((total_profit - cost) / cost) * 100
        
        return {
            "total_reach": actual_reach,
            "engagement_rate": round(random.uniform(0.5, 2.5), 2),
            "mentions": [
                f"Article on {rec.get('media_name')} was shared {random.randint(50, 500)} times." 
                for rec in recommendations
            ],
            "roi": round(roi, 2)
        }

    def _create_pdf_report(self, agent_result: dict, performance_data: dict) -> str:
        """Creates the physical PDF report file using reportlab."""
        session_id = agent_result.get("session_id", "unknown_session")
        file_path = os.path.join(REPORT_DIR, f"report_{session_id}.pdf")
        c = canvas.Canvas(file_path, pagesize=letter)
        width, height = letter

        # Draw Header
        c.setFont('VietnameseFont', 20)
        c.drawCentredString(width / 2.0, height - inch, "Báo Cáo Hiệu Suất Chiến Dịch Truyền Thông")

        # Draw Campaign Info
        c.setFont('VietnameseFont', 12)
        pricing = agent_result.get("pricing_analysis", {})
        c.drawString(inch, height - 1.5*inch, f"Mã chiến dịch (Session ID): {session_id}")
        c.drawString(inch, height - 1.7*inch, f"Gói dịch vụ được chọn: {pricing.get('recommended_package', 'N/A')}")
        c.drawString(inch, height - 1.9*inch, f"Tổng chi phí thực tế: {pricing.get('total_cost_vnd', 0):,.0f} VND")
        
        # Draw Performance KPIs
        y_pos = height - 2.5*inch
        c.setFont('VietnameseFont', 16)
        c.drawString(inch, y_pos, "Kết Quả Kinh Doanh Chính (KPIs)")
        y_pos -= 0.4*inch
        c.setFont('VietnameseFont', 12)
        c.drawString(1.2*inch, y_pos, f"• Tổng lượt tiếp cận (Total Reach): {performance_data['total_reach']:,}")
        c.drawString(1.2*inch, y_pos - 0.3*inch, f"• Tỉ lệ tương tác (Engagement Rate): {performance_data['engagement_rate']}%")
        c.drawString(1.2*inch, y_pos - 0.6*inch, f"• Số lượt đề cập (Mentions): {len(performance_data['mentions'])}")
        c.setFont('VietnameseFont', 14)
        c.drawString(1.2*inch, y_pos - 1.0*inch, f"• Hoàn vốn đầu tư (ROI): {performance_data['roi']:.2f}%")
        
        c.save()
        return file_path

# ==============================================================================
# SECTION 3: STRATEGY OPTIMIZER SERVICE (FEW-SHOT LEARNING)
# ==============================================================================

class StrategyOptimizerService:
    """
    A service that implements the few-shot learning feedback loop. It analyzes
    successful campaigns and archives them to be used as examples for future AI runs.
    """
    def __init__(self, db_session: Session):
        """Initializes the service with a database session."""
        self.db = db_session

    def get_budget_range(self, budget: float) -> str:
        """Categorizes a budget into a searchable range."""
        if budget < 15_000_000: return "low"
        if budget <= 35_000_000: return "medium"
        if budget <= 60_000_000: return "high"
        return "enterprise"

    async def archive_successful_strategy(self, report: PerformanceReport):
        """
        Checks if a completed campaign was successful based on its ROI and,
        if so, archives a summary of its strategy for future learning.
        """
        if report.roi < SUCCESS_CRITERIA_ROI:
            logger.info(f"📉 Campaign {report.user_request.session_id} did not meet success criteria (ROI: {report.roi}%), skipping archival.")
            return

        logger.info(f"🏆 Campaign {report.user_request.session_id} was a success! (ROI: {report.roi}%) -> Archiving for future learning...")
        
        if self.db.query(SuccessfulStrategy).filter(SuccessfulStrategy.source_request_id == report.user_request_id).first():
            logger.info("-> This strategy has already been archived.")
            return

        user_request = report.user_request
        agent_result = json.loads(user_request.final_report_json)
        pricing = agent_result.get("pricing_analysis", {})
        summary = agent_result.get("summary", {})
        
        # Create a concise summary of the successful strategy for the AI prompt
        few_shot_prompt = (
            f"- Input: Budget of ~{user_request.budget:,.0f} VND for the '{user_request.industry_sector}' industry.\n"
            f"- Strategy: Selected the '{pricing.get('recommended_package')}' package with {summary.get('media_count', 0)} outlets.\n"
            f"- Outcome: Achieved an impressive {report.roi:.2f}% ROI."
        )
        
        new_strategy = SuccessfulStrategy(
            source_request_id=user_request.id,
            achieved_roi=report.roi,
            industry_sector=user_request.industry_sector,
            budget_range=self.get_budget_range(user_request.budget),
            few_shot_prompt_example=few_shot_prompt.strip(),
            full_strategy_json=user_request.final_report_json
        )
        self.db.add(new_strategy)
        self.db.commit()
        logger.info(f"✅ Successfully archived successful strategy to the learning database.")

    async def get_few_shot_examples(self, current_industry: str, current_budget: float, limit: int = 2) -> str:
        """
        Retrieves the most relevant successful past campaigns to be used as
        few-shot learning examples for the current AI run.
        """
        budget_range = self.get_budget_range(current_budget)
        
        # Find the most relevant examples based on industry and budget
        examples = self.db.query(SuccessfulStrategy).filter(
            SuccessfulStrategy.industry_sector == current_industry,
            SuccessfulStrategy.budget_range == budget_range
        ).order_by(desc(SuccessfulStrategy.achieved_roi)).limit(limit).all()

        # If no specific matches, find the best overall examples
        if not examples:
            examples = self.db.query(SuccessfulStrategy).order_by(desc(SuccessfulStrategy.achieved_roi)).limit(1).all()

        if not examples:
            return "No past successful examples are available for learning yet."

        # Format the examples into a string to be injected into the agent's prompt
        formatted_examples = "\n\n**REFERENCE: EXAMPLES OF PAST SUCCESSFUL STRATEGIES**\n"
        for i, ex in enumerate(examples):
            formatted_examples += f"\n--- Example Case {i+1} ---\n{ex.few_shot_prompt_example}\n"
        
        logger.info(f"📚 Found {len(examples)} relevant learning examples for the current request.")
        return formatted_examples
