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
from typing import Optional, Dict

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
from agents import ConversationContext # Import ConversationContext

# ==============================================================================
# SECTION 1: CONFIGURATION
# ==============================================================================
REPORT_DIR = "generated_reports"
os.makedirs(REPORT_DIR, exist_ok=True)
SUCCESS_CRITERIA_ROI = float(os.getenv("SUCCESS_CRITERIA_ROI", "50.0"))

FONT_PATH = 'Roboto-Regular.ttf'
if os.path.exists(FONT_PATH):
    pdfmetrics.registerFont(TTFont('VietnameseFont', FONT_PATH))
    logger.info(f"✅ Vietnamese font '{FONT_PATH}' successfully registered.")
else:
    logger.warning(f"Font '{FONT_PATH}' not found. PDF reports may not display Vietnamese. Using Helvetica as fallback.")
    pdfmetrics.registerFont(TTFont('VietnameseFont', 'Helvetica'))

# ==============================================================================
# SECTION 2: REPORTING SERVICE
# ==============================================================================

class ReportingService:
    """A service dedicated to generating performance reports for completed campaigns."""
    def __init__(self, db_session: Session):
        self.db = db_session

    async def generate_performance_report(self, session_id: str) -> Optional[PerformanceReport]:
        """Generates a PDF performance report and saves the report data to the database."""
        logger.info(f"📊 Starting performance report generation for session_id: {session_id}")
        user_request = self.db.query(UserRequest).filter(UserRequest.session_id == session_id).first()

        if not user_request or not user_request.executive_report_json:
            logger.error(f"❌ Cannot generate report. No agent results found for session: {session_id}")
            return None

        agent_result = json.loads(user_request.executive_report_json)
        performance_data = self._simulate_performance_metrics(agent_result)
        pdf_path = self._create_pdf_report(agent_result, performance_data)
        
        report = self.db.query(PerformanceReport).filter(PerformanceReport.user_request_id == user_request.id).first()
        if not report:
            report = PerformanceReport(user_request_id=user_request.id)
            self.db.add(report)

        report.total_reach = performance_data["total_reach"]
        report.engagement_rate = performance_data["engagement_rate"]
        report.mentions_count = len(performance_data["mentions"])
        report.roi = performance_data["roi"]
        report.report_url = os.path.basename(pdf_path)
        report.generated_at = datetime.utcnow()
        
        user_request.status = 'reported'
        self.db.commit()
        self.db.refresh(report)
        logger.info(f"✅ Successfully created/updated performance report: {pdf_path}")
        return report
    
    def _simulate_performance_metrics(self, agent_result: dict) -> dict:
        """This is a placeholder method to simulate the collection of real-world performance data."""
        logger.info("📈 Simulating the collection of post-campaign performance metrics...")
        recommendations = agent_result.get("media_recommendations", [])
        pricing = agent_result.get("pricing_analysis", {})
        
        estimated_reach = sum(rec.get('estimated_reach', 0) for rec in recommendations)
        actual_reach = int(estimated_reach * random.uniform(0.85, 1.3))
        cost = pricing.get("total_cost_vnd", 1) or 1
        profit_per_reach = random.randint(8, 15)
        total_profit = actual_reach * profit_per_reach
        roi = ((total_profit - cost) / cost) * 100
        
        return {
            "total_reach": actual_reach,
            "engagement_rate": round(random.uniform(0.5, 2.5), 2),
            "mentions": [f"Article on {rec.get('media_name')} was shared {random.randint(50, 500)} times." for rec in recommendations],
            "roi": round(roi, 2)
        }

    def _create_pdf_report(self, agent_result: dict, performance_data: dict) -> str:
        """Creates the physical PDF report file using reportlab."""
        session_id = agent_result.get("session_id", "unknown")
        file_path = os.path.join(REPORT_DIR, f"report_{session_id}.pdf")
        c = canvas.Canvas(file_path, pagesize=letter)
        width, height = letter

        c.setFont('VietnameseFont', 20)
        c.drawCentredString(width / 2.0, height - inch, "Báo Cáo Hiệu Suất Chiến Dịch")

        c.setFont('VietnameseFont', 12)
        pricing = agent_result.get("pricing_analysis", {})
        c.drawString(inch, height - 1.5*inch, f"Mã chiến dịch (Session ID): {session_id}")
        c.drawString(inch, height - 1.7*inch, f"Gói dịch vụ: {pricing.get('recommended_package', 'N/A')}")
        c.drawString(inch, height - 1.9*inch, f"Tổng chi phí: {pricing.get('total_cost_vnd', 0):,.0f} VND")
        
        y_pos = height - 2.5*inch
        c.setFont('VietnameseFont', 16)
        c.drawString(inch, y_pos, "Kết Quả Kinh Doanh Chính (KPIs)")
        y_pos -= 0.4*inch
        c.setFont('VietnameseFont', 12)
        c.drawString(1.2*inch, y_pos, f"• Tổng lượt tiếp cận: {performance_data['total_reach']:,}")
        c.drawString(1.2*inch, y_pos - 0.3*inch, f"• Tỉ lệ tương tác: {performance_data['engagement_rate']}%")
        c.drawString(1.2*inch, y_pos - 0.6*inch, f"• Số lượt đề cập: {len(performance_data['mentions'])}")
        c.setFont('VietnameseFont', 14)
        c.drawString(1.2*inch, y_pos - 1.0*inch, f"• Hoàn vốn đầu tư (ROI): {performance_data['roi']:.2f}%")
        
        c.save()
        return file_path

# ==============================================================================
# SECTION 3: STRATEGY OPTIMIZER SERVICE (FEW-SHOT LEARNING)
# ==============================================================================

class StrategyOptimizerService:
    """A service that implements the few-shot learning feedback loop."""
    def __init__(self, db_session: Session):
        self.db = db_session

    def get_budget_range(self, budget: float) -> str:
        """Categorizes a budget into a searchable range."""
        if not isinstance(budget, (int, float)) or budget <= 0:
            return "low"
        if budget < 15_000_000: return "low"
        if budget <= 35_000_000: return "medium"
        if budget <= 60_000_000: return "high"
        return "enterprise"

    async def archive_successful_strategy(self, report: PerformanceReport):
        """Checks if a completed campaign was successful and archives its strategy."""
        if report.roi < SUCCESS_CRITERIA_ROI:
            logger.info(f"📉 Campaign {report.user_request.session_id} did not meet success criteria (ROI: {report.roi}%), skipping archival.")
            return

        logger.info(f"🏆 Campaign {report.user_request.session_id} was a success! (ROI: {report.roi}%) -> Archiving for future learning...")
        
        if self.db.query(SuccessfulStrategy).filter(SuccessfulStrategy.source_request_id == report.user_request_id).first():
            logger.info("-> This strategy has already been archived.")
            return

        user_request = report.user_request
        agent_result = json.loads(user_request.executive_report_json)
        pricing = agent_result.get("pricing_analysis", {})
        summary = agent_result.get("summary", {})
        
        few_shot_prompt = (
            f"- Input: Budget of ~{user_request.budget or 0:,.0f} VND for the '{user_request.industry_sector}' industry.\n"
            f"- Strategy: Selected the '{pricing.get('recommended_package')}' package with {summary.get('media_count', 0)} outlets.\n"
            f"- Outcome: Achieved an impressive {report.roi:.2f}% ROI."
        )
        
        new_strategy = SuccessfulStrategy(
            source_request_id=user_request.id,
            achieved_roi=report.roi,
            industry_sector=user_request.industry_sector,
            budget_range=self.get_budget_range(user_request.budget or 0),
            few_shot_prompt_example=few_shot_prompt.strip(),
            full_strategy_json=user_request.executive_report_json
        )
        self.db.add(new_strategy)
        self.db.commit()
        logger.info(f"✅ Successfully archived successful strategy to the learning database.")

    async def get_few_shot_examples(self, context: ConversationContext) -> str:
        """Retrieves the most relevant successful past campaigns to be used as learning examples."""
        # Safely get industry and budget from context
        current_industry = "General"
        if context.content_analysis and isinstance(context.content_analysis, dict):
             current_industry = context.content_analysis.get("industry_sector", "General")
        elif context.requirements:
             current_industry = context.requirements.get("industry", "General")
        
        current_budget = context.budget or 0
        budget_range = self.get_budget_range(current_budget)
        
        examples = self.db.query(SuccessfulStrategy).filter(
            SuccessfulStrategy.industry_sector == current_industry,
            SuccessfulStrategy.budget_range == budget_range
        ).order_by(desc(SuccessfulStrategy.achieved_roi)).limit(2).all()

        if not examples:
            examples = self.db.query(SuccessfulStrategy).order_by(desc(SuccessfulStrategy.achieved_roi)).limit(1).all()

        if not examples:
            return "No past successful examples are available for learning yet."

        formatted_examples = "\n\n**REFERENCE: EXAMPLES OF PAST SUCCESSFUL STRATEGIES**\n"
        for i, ex in enumerate(examples):
            formatted_examples += f"\n--- Example Case {i+1} ---\n{ex.few_shot_prompt_example}\n"
        
        logger.info(f"📚 Found {len(examples)} relevant learning examples for the current request.")
        return formatted_examples
