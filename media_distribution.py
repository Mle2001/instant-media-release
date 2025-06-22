"""
Media Distribution System - Email automation, press release delivery, response tracking
Tích hợp với Agno Email Tools và Gmail để tự động gửi press release tới media contacts
"""

import asyncio
import json
import logging
import sqlite3
import smtplib
import uuid
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, List, Optional, Any
from enum import Enum
from pydantic import BaseModel
import httpx

# Agno imports
from agno.tools.email import EmailTools
from agno.tools.gmail import GmailTools
from agno.tools import Toolkit
from agno.agent import Agent
from agno.models.openai import OpenAI

logger = logging.getLogger(__name__)

class DistributionStatus(Enum):
    PENDING = "pending"
    SCHEDULED = "scheduled"
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"
    REPLIED = "replied"
    BOUNCED = "bounced"
    FAILED = "failed"

class MediaContact(BaseModel):
    contact_id: str
    name: str
    email: str
    media_outlet: str
    position: str
    phone: Optional[str] = None
    categories: List[str]
    tier: int
    preferred_language: str = "Vietnamese"
    last_contacted: Optional[datetime] = None
    response_rate: float = 0.0
    is_active: bool = True

class PressRelease(BaseModel):
    release_id: str
    order_id: str
    title: str
    content: str
    summary: str
    category: str
    target_audience: str
    language: str = "Vietnamese"
    attachments: List[str] = []
    created_at: datetime
    scheduled_at: Optional[datetime] = None

class DistributionCampaign(BaseModel):
    campaign_id: str
    order_id: str
    press_release_id: str
    target_contacts: List[str]  # List of contact_ids
    subject_line: str
    personalized_message: str
    scheduled_at: datetime
    status: DistributionStatus
    created_at: datetime
    sent_count: int = 0
    delivered_count: int = 0
    opened_count: int = 0
    replied_count: int = 0

class EmailTemplate(BaseModel):
    template_id: str
    name: str
    subject_template: str
    body_template: str
    category: str
    language: str = "Vietnamese"
    variables: List[str] = []

class MediaDistributionToolkit(Toolkit):
    """Custom toolkit cho media distribution và email automation"""
    
    def __init__(self, smtp_config: Dict = None, gmail_config: Dict = None):
        self.smtp_config = smtp_config or {}
        self.gmail_config = gmail_config or {}
        self.email_tools = EmailTools() if not gmail_config else None
        self.gmail_tools = GmailTools() if gmail_config else None
        
        super().__init__(
            name="media_distribution_toolkit",
            tools=[
                self.send_press_release,
                self.schedule_distribution,
                self.track_email_status,
                self.get_contact_list,
                self.personalize_email,
                self.generate_email_template
            ]
        )
    
    def send_press_release(self, campaign_id: str, contact_id: str, 
                          press_release: PressRelease) -> bool:
        """Gửi press release tới một media contact"""
        try:
            contact = self._get_media_contact(contact_id)
            if not contact or not contact.is_active:
                return False
            
            # Personalize email content
            personalized_content = self._personalize_content(press_release, contact)
            
            # Send via Gmail or SMTP
            if self.gmail_tools:
                return self._send_via_gmail(contact, personalized_content)
            else:
                return self._send_via_smtp(contact, personalized_content)
                
        except Exception as e:
            logger.error(f"Send press release failed: {e}")
            return False
    
    def schedule_distribution(self, campaign: DistributionCampaign) -> bool:
        """Lên lịch distribution campaign"""
        try:
            # Save campaign to database
            self._save_distribution_campaign(campaign)
            
            # Schedule execution
            if campaign.scheduled_at <= datetime.now():
                # Execute immediately
                return self._execute_distribution(campaign)
            else:
                # Schedule for later (would use celery/background tasks in production)
                logger.info(f"Campaign {campaign.campaign_id} scheduled for {campaign.scheduled_at}")
                return True
                
        except Exception as e:
            logger.error(f"Schedule distribution failed: {e}")
            return False
    
    def track_email_status(self, campaign_id: str) -> Dict[str, Any]:
        """Theo dõi trạng thái email campaign"""
        try:
            conn = sqlite3.connect('media_release.db')
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT sent_count, delivered_count, opened_count, replied_count, status
                FROM distribution_campaigns WHERE campaign_id = ?
            """, (campaign_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    "campaign_id": campaign_id,
                    "sent_count": result[0],
                    "delivered_count": result[1],
                    "opened_count": result[2],
                    "replied_count": result[3],
                    "status": result[4],
                    "open_rate": result[2] / result[1] if result[1] > 0 else 0,
                    "response_rate": result[3] / result[1] if result[1] > 0 else 0
                }
            return {}
            
        except Exception as e:
            logger.error(f"Track email status failed: {e}")
            return {}
    
    def get_contact_list(self, category: str = None, tier: int = None) -> List[MediaContact]:
        """Lấy danh sách media contacts theo filter"""
        try:
            conn = sqlite3.connect('media_release.db')
            cursor = conn.cursor()
            
            query = "SELECT * FROM media_contacts WHERE is_active = 1"
            params = []
            
            if category:
                query += " AND categories LIKE ?"
                params.append(f"%{category}%")
            
            if tier:
                query += " AND tier = ?"
                params.append(tier)
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            conn.close()
            
            contacts = []
            for row in results:
                contacts.append(MediaContact(
                    contact_id=row[0],
                    name=row[1],
                    email=row[2],
                    media_outlet=row[3],
                    position=row[4],
                    phone=row[5],
                    categories=json.loads(row[6]),
                    tier=row[7],
                    preferred_language=row[8],
                    last_contacted=datetime.fromisoformat(row[9]) if row[9] else None,
                    response_rate=row[10],
                    is_active=bool(row[11])
                ))
            
            return contacts
            
        except Exception as e:
            logger.error(f"Get contact list failed: {e}")
            return []
    
    def personalize_email(self, template: EmailTemplate, contact: MediaContact, 
                         press_release: PressRelease) -> Dict[str, str]:
        """Cá nhân hóa email content cho từng contact"""
        variables = {
            "contact_name": contact.name,
            "media_outlet": contact.media_outlet,
            "position": contact.position,
            "release_title": press_release.title,
            "release_summary": press_release.summary,
            "category": press_release.category,
            "current_date": datetime.now().strftime("%d/%m/%Y")
        }
        
        personalized_subject = template.subject_template
        personalized_body = template.body_template
        
        for var, value in variables.items():
            personalized_subject = personalized_subject.replace(f"{{{var}}}", str(value))
            personalized_body = personalized_body.replace(f"{{{var}}}", str(value))
        
        return {
            "subject": personalized_subject,
            "body": personalized_body,
            "variables": variables
        }
    
    def generate_email_template(self, category: str, tone: str = "professional") -> EmailTemplate:
        """Tạo email template tự động cho category"""
        template_id = str(uuid.uuid4())
        
        templates = {
            "TECHNOLOGY": {
                "subject": "🚀 [Độc quyền] {release_title} - Thông tin từ {media_outlet}",
                "body": """Kính chào {contact_name},

Tôi hy vọng email này đến với bạn trong tình trạng tốt nhất. Tôi là đại diện của Instant Media Release, chuyên cung cấp thông tin báo chí chất lượng cao.

📋 THÔNG TIN ĐỘC QUYỀN:
{release_title}

📊 TÓM TẮT NHANH:
{release_summary}

🎯 TẠI SAO THÔNG TIN NÀY PHÙ HỢP VỚI {media_outlet}:
- Thuộc lĩnh vực {category} - chuyên môn của {media_outlet}
- Có tiềm năng viral cao trong cộng đồng công nghệ
- Cung cấp góc nhìn mới về xu hướng technology tại Việt Nam

📎 Thông tin chi tiết được đính kèm trong email này.

Tôi sẵn sàng cung cấp thêm thông tin hoặc sắp xếp cuộc phỏng vấn độc quyền nếu {contact_name} quan tâm.

Xin cảm ơn thời gian quý báu của bạn!

Trân trọng,
Instant Media Release Team
📧 contact@instantmediarelease.vn
📞 +84 xxx xxx xxxx"""
            },
            "BUSINESS": {
                "subject": "💼 [Doanh nghiệp] {release_title} - Cơ hội độc quyền cho {media_outlet}",
                "body": """Kính chào {contact_name},

Chúng tôi trân trọng gửi đến {media_outlet} thông tin báo chí độc quyền về một phát triển quan trọng trong lĩnh vực kinh doanh.

📈 THÔNG TIN KINH DOANH MỚI:
{release_title}

💡 ĐIỂM NỔI BẬT:
{release_summary}

🏢 GIÁ TRỊ THÔNG TIN CHO {media_outlet}:
- Phù hợp với định hướng nội dung business của {media_outlet}
- Ảnh hưởng trực tiếp đến cộng đồng doanh nghiệp Việt Nam
- Tiềm năng tạo engagement cao với độc giả quan tâm đến {category}

Chúng tôi tin rằng thông tin này sẽ mang lại giá trị cho độc giả của {media_outlet}.

Sẵn sàng hỗ trợ thêm thông tin hoặc sắp xếp interview nếu cần.

Trân trọng,
Instant Media Release Team"""
            }
        }
        
        template_data = templates.get(category.upper(), templates["BUSINESS"])
        
        return EmailTemplate(
            template_id=template_id,
            name=f"{category} Press Release Template",
            subject_template=template_data["subject"],
            body_template=template_data["body"],
            category=category,
            language="Vietnamese",
            variables=["contact_name", "media_outlet", "position", "release_title", "release_summary", "category"]
        )
    
    def _send_via_gmail(self, contact: MediaContact, content: Dict[str, str]) -> bool:
        """Gửi email qua Gmail API"""
        try:
            if not self.gmail_tools:
                return False
            
            # Use Gmail tools to send email
            result = self.gmail_tools.send_email(
                to=contact.email,
                subject=content["subject"],
                body=content["body"]
            )
            
            return result.get("success", False)
            
        except Exception as e:
            logger.error(f"Gmail send failed: {e}")
            return False
    
    def _send_via_smtp(self, contact: MediaContact, content: Dict[str, str]) -> bool:
        """Gửi email qua SMTP"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.smtp_config.get('from_email', 'noreply@instantmediarelease.vn')
            msg['To'] = contact.email
            msg['Subject'] = content["subject"]
            
            msg.attach(MIMEText(content["body"], 'plain', 'utf-8'))
            
            # SMTP connection
            server = smtplib.SMTP(
                self.smtp_config.get('smtp_server', 'smtp.gmail.com'),
                self.smtp_config.get('smtp_port', 587)
            )
            server.starttls()
            server.login(
                self.smtp_config.get('username', ''),
                self.smtp_config.get('password', '')
            )
            
            text = msg.as_string()
            server.sendmail(msg['From'], contact.email, text)
            server.quit()
            
            return True
            
        except Exception as e:
            logger.error(f"SMTP send failed: {e}")
            return False
    
    def _get_media_contact(self, contact_id: str) -> Optional[MediaContact]:
        """Lấy media contact từ database"""
        try:
            conn = sqlite3.connect('media_release.db')
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM media_contacts WHERE contact_id = ?", (contact_id,))
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return MediaContact(
                    contact_id=result[0],
                    name=result[1],
                    email=result[2],
                    media_outlet=result[3],
                    position=result[4],
                    phone=result[5],
                    categories=json.loads(result[6]),
                    tier=result[7],
                    preferred_language=result[8],
                    last_contacted=datetime.fromisoformat(result[9]) if result[9] else None,
                    response_rate=result[10],
                    is_active=bool(result[11])
                )
            return None
            
        except Exception as e:
            logger.error(f"Get media contact failed: {e}")
            return None
    
    def _personalize_content(self, press_release: PressRelease, contact: MediaContact) -> Dict[str, str]:
        """Cá nhân hóa nội dung cho contact"""
        template = self.generate_email_template(press_release.category)
        return self.personalize_email(template, contact, press_release)
    
    def _save_distribution_campaign(self, campaign: DistributionCampaign):
        """Lưu distribution campaign vào database"""
        try:
            conn = sqlite3.connect('media_release.db')
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO distribution_campaigns
                (campaign_id, order_id, press_release_id, target_contacts, subject_line,
                 personalized_message, scheduled_at, status, created_at, sent_count,
                 delivered_count, opened_count, replied_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                campaign.campaign_id, campaign.order_id, campaign.press_release_id,
                json.dumps(campaign.target_contacts), campaign.subject_line,
                campaign.personalized_message, campaign.scheduled_at.isoformat(),
                campaign.status.value, campaign.created_at.isoformat(),
                campaign.sent_count, campaign.delivered_count, 
                campaign.opened_count, campaign.replied_count
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Save distribution campaign failed: {e}")
    
    def _execute_distribution(self, campaign: DistributionCampaign) -> bool:
        """Thực thi distribution campaign"""
        try:
            press_release = self._get_press_release(campaign.press_release_id)
            if not press_release:
                return False
            
            success_count = 0
            for contact_id in campaign.target_contacts:
                if self.send_press_release(campaign.campaign_id, contact_id, press_release):
                    success_count += 1
            
            # Update campaign status
            campaign.sent_count = success_count
            campaign.status = DistributionStatus.SENT
            self._save_distribution_campaign(campaign)
            
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Execute distribution failed: {e}")
            return False
    
    def _get_press_release(self, release_id: str) -> Optional[PressRelease]:
        """Lấy press release từ database"""
        try:
            conn = sqlite3.connect('media_release.db')
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM press_releases WHERE release_id = ?", (release_id,))
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return PressRelease(
                    release_id=result[0],
                    order_id=result[1],
                    title=result[2],
                    content=result[3],
                    summary=result[4],
                    category=result[5],
                    target_audience=result[6],
                    language=result[7],
                    attachments=json.loads(result[8]),
                    created_at=datetime.fromisoformat(result[9]),
                    scheduled_at=datetime.fromisoformat(result[10]) if result[10] else None
                )
            return None
            
        except Exception as e:
            logger.error(f"Get press release failed: {e}")
            return None

class MediaDistributionAgent(Agent):
    """AI Agent chuyên xử lý media distribution và email automation"""
    
    def __init__(self, smtp_config: Dict = None, gmail_config: Dict = None):
        self.distribution_toolkit = MediaDistributionToolkit(smtp_config, gmail_config)
        self._init_database()
        
        super().__init__(
            model=OpenAI(id="gpt-4"),
            tools=[self.distribution_toolkit],
            instructions=[
                "Bạn là Media Distribution Agent chuyên phân phối press release tới media contacts",
                "Tự động cá nhân hóa email cho từng media outlet",
                "Theo dõi delivery rate, open rate và response rate",
                "Tối ưu hóa timing và content cho highest engagement",
                "Luôn đảm bảo professional tone trong communication"
            ],
            description="AI Agent quản lý distribution và email automation cho media outreach"
        )
    
    def _init_database(self):
        """Khởi tạo database tables cho distribution system"""
        conn = sqlite3.connect('media_release.db')
        cursor = conn.cursor()
        
        # Media contacts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS media_contacts (
                contact_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                media_outlet TEXT NOT NULL,
                position TEXT,
                phone TEXT,
                categories TEXT,
                tier INTEGER,
                preferred_language TEXT DEFAULT 'Vietnamese',
                last_contacted TEXT,
                response_rate REAL DEFAULT 0.0,
                is_active BOOLEAN DEFAULT 1
            )
        """)
        
        # Press releases table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS press_releases (
                release_id TEXT PRIMARY KEY,
                order_id TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                summary TEXT,
                category TEXT,
                target_audience TEXT,
                language TEXT DEFAULT 'Vietnamese',
                attachments TEXT DEFAULT '[]',
                created_at TEXT NOT NULL,
                scheduled_at TEXT,
                FOREIGN KEY (order_id) REFERENCES orders (order_id)
            )
        """)
        
        # Distribution campaigns table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS distribution_campaigns (
                campaign_id TEXT PRIMARY KEY,
                order_id TEXT NOT NULL,
                press_release_id TEXT NOT NULL,
                target_contacts TEXT NOT NULL,
                subject_line TEXT,
                personalized_message TEXT,
                scheduled_at TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                sent_count INTEGER DEFAULT 0,
                delivered_count INTEGER DEFAULT 0,
                opened_count INTEGER DEFAULT 0,
                replied_count INTEGER DEFAULT 0,
                FOREIGN KEY (order_id) REFERENCES orders (order_id),
                FOREIGN KEY (press_release_id) REFERENCES press_releases (release_id)
            )
        """)
        
        # Email tracking table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS email_tracking (
                tracking_id TEXT PRIMARY KEY,
                campaign_id TEXT NOT NULL,
                contact_id TEXT NOT NULL,
                email_address TEXT NOT NULL,
                subject TEXT,
                sent_at TEXT,
                delivered_at TEXT,
                opened_at TEXT,
                clicked_at TEXT,
                replied_at TEXT,
                bounce_reason TEXT,
                status TEXT NOT NULL,
                FOREIGN KEY (campaign_id) REFERENCES distribution_campaigns (campaign_id),
                FOREIGN KEY (contact_id) REFERENCES media_contacts (contact_id)
            )
        """)
        
        conn.commit()
        conn.close()
        
        # Seed sample media contacts
        self._seed_media_contacts()
    
    def _seed_media_contacts(self):
        """Tạo sample media contacts từ database có sẵn"""
        try:
            conn = sqlite3.connect('media_release.db')
            cursor = conn.cursor()
            
            # Check if contacts already exist
            cursor.execute("SELECT COUNT(*) FROM media_contacts")
            count = cursor.fetchone()[0]
            
            if count > 0:
                conn.close()
                return
            
            # Sample contacts based on existing media outlets
            sample_contacts = [
                {
                    "contact_id": "vnexpress-tech",
                    "name": "Nguyễn Văn Tech",
                    "email": "tech@vnexpress.net",
                    "media_outlet": "VnExpress",
                    "position": "Editor Technology",
                    "categories": ["TECHNOLOGY", "BUSINESS"],
                    "tier": 1
                },
                {
                    "contact_id": "cafef-business",
                    "name": "Trần Thị Finance",
                    "email": "news@cafef.vn",
                    "media_outlet": "CafeF",
                    "position": "Business Reporter",
                    "categories": ["BUSINESS", "FINTECH"],
                    "tier": 1
                },
                {
                    "contact_id": "dantri-startup",
                    "name": "Lê Văn Startup",
                    "email": "startup@dantri.com.vn",
                    "media_outlet": "Dân trí",
                    "position": "Startup Editor",
                    "categories": ["TECHNOLOGY", "STARTUP"],
                    "tier": 1
                }
            ]
            
            for contact in sample_contacts:
                cursor.execute("""
                    INSERT INTO media_contacts
                    (contact_id, name, email, media_outlet, position, categories, tier)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    contact["contact_id"], contact["name"], contact["email"],
                    contact["media_outlet"], contact["position"],
                    json.dumps(contact["categories"]), contact["tier"]
                ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Seed media contacts failed: {e}")
    
    def create_distribution_campaign(self, order_id: str, press_release: PressRelease,
                                   target_media_types: List[str] = None,
                                   scheduled_at: datetime = None) -> DistributionCampaign:
        """Tạo distribution campaign tự động"""
        
        # Get appropriate contacts
        target_contacts = []
        for media_type in (target_media_types or [press_release.category]):
            contacts = self.distribution_toolkit.get_contact_list(category=media_type)
            target_contacts.extend([c.contact_id for c in contacts])
        
        # Remove duplicates
        target_contacts = list(set(target_contacts))
        
        campaign = DistributionCampaign(
            campaign_id=str(uuid.uuid4()),
            order_id=order_id,
            press_release_id=press_release.release_id,
            target_contacts=target_contacts,
            subject_line=f"[Thông tin báo chí] {press_release.title}",
            personalized_message="Tự động tạo nội dung cá nhân hóa cho từng contact",
            scheduled_at=scheduled_at or datetime.now(),
            status=DistributionStatus.PENDING,
            created_at=datetime.now()
        )
        
        # Save và schedule campaign
        self.distribution_toolkit.schedule_distribution(campaign)
        
        return campaign
    
    def get_distribution_analytics(self, order_id: str) -> Dict[str, Any]:
        """Lấy analytics cho distribution campaigns của order"""
        try:
            conn = sqlite3.connect('media_release.db')
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT campaign_id, sent_count, delivered_count, opened_count, replied_count, status
                FROM distribution_campaigns WHERE order_id = ?
            """, (order_id,))
            
            campaigns = cursor.fetchall()
            conn.close()
            
            total_sent = sum(c[1] for c in campaigns)
            total_delivered = sum(c[2] for c in campaigns)
            total_opened = sum(c[3] for c in campaigns)
            total_replied = sum(c[4] for c in campaigns)
            
            return {
                "order_id": order_id,
                "campaigns_count": len(campaigns),
                "total_sent": total_sent,
                "total_delivered": total_delivered,
                "total_opened": total_opened,
                "total_replied": total_replied,
                "delivery_rate": total_delivered / total_sent if total_sent > 0 else 0,
                "open_rate": total_opened / total_delivered if total_delivered > 0 else 0,
                "response_rate": total_replied / total_delivered if total_delivered > 0 else 0,
                "campaigns": [
                    {
                        "campaign_id": c[0],
                        "sent": c[1],
                        "delivered": c[2],
                        "opened": c[3],
                        "replied": c[4],
                        "status": c[5]
                    } for c in campaigns
                ]
            }
            
        except Exception as e:
            logger.error(f"Get distribution analytics failed: {e}")
            return {}

if __name__ == "__main__":
    # Test distribution system
    distribution_agent = MediaDistributionAgent()
    
    # Test press release
    test_release = PressRelease(
        release_id="test-release-1",
        order_id="test-order-1",
        title="VietPay Ra Mắt Giải Pháp Thanh Toán Mới Cho SME",
        content="Nội dung chi tiết press release...",
        summary="VietPay công bố ứng dụng thanh toán mới nhắm vào thị trường SME Việt Nam",
        category="TECHNOLOGY",
        target_audience="SME",
        created_at=datetime.now()
    )
    
    # Test create campaign
    campaign = distribution_agent.create_distribution_campaign(
        order_id="test-order-1",
        press_release=test_release,
        target_media_types=["TECHNOLOGY", "BUSINESS"]
    )
    
    print(f"✅ Distribution campaign created: {campaign.campaign_id}")
    print(f"📧 Target contacts: {len(campaign.target_contacts)}")
    
    # Test analytics
    analytics = distribution_agent.get_distribution_analytics("test-order-1")
    print(f"📊 Analytics: {analytics}")