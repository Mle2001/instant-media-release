"""
AI Content Generation Module
Press release and email marketing content generation with Vietnamese context
Template-based content generation with SEO and style optimization
Designed for integration with EnhancedMediaReleaseTeamSystem
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from loguru import logger
import asyncio
import random

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.storage.agent.sqlite import SqliteAgentStorage

# =================== CONFIGURATION ===================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CONTENT_MODEL = os.getenv("CONTENT_MODEL", "gpt-4o")
CONTENT_TEMPERATURE = float(os.getenv("CONTENT_TEMPERATURE", "0.5"))
CONTENT_MAX_TOKENS = int(os.getenv("CONTENT_MAX_TOKENS", "3000"))

# SEO Configuration
SEO_KEYWORD_DENSITY = float(
    os.getenv("SEO_KEYWORD_DENSITY", "0.02")
)  # 2% keyword density
MAX_KEYWORDS = int(os.getenv("MAX_KEYWORDS", "5"))

# Style Configuration
DEFAULT_TONE = os.getenv("CONTENT_TONE", "Professional")
DEFAULT_LANGUAGE = "Vietnamese"

# Template Directory
TEMPLATE_DIR = os.getenv("TEMPLATE_DIR", "./templates/press_release")

# =================== DATA MODELS ===================


class ContentRequest(BaseModel):
    """Structured input for content generation request"""

    session_id: str = Field(description="Unique session identifier")
    project_description: str = Field(description="Main project or product description")
    industry: str = Field(description="Industry sector: Tech/Finance/Healthcare/etc")
    target_audience: List[str] = Field(description="Target audiences", default=[])
    keywords: List[str] = Field(description="SEO keywords", default=[])
    tone: str = Field(
        description="Content tone: Professional/Casual/Formal", default=DEFAULT_TONE
    )
    language: str = Field(
        description="Language: Vietnamese/English/Both", default=DEFAULT_LANGUAGE
    )
    press_release_type: str = Field(
        description="Type: Product Launch/Partnership/Funding/Event/Other"
    )
    word_count: int = Field(
        description="Target word count", default=500, ge=200, le=1000
    )
    additional_info: Optional[Dict] = Field(
        description="Extra context or requirements", default=None
    )


class ContentOutput(BaseModel):
    """Structured output for generated content"""

    content: str = Field(description="Generated press release content")
    title: str = Field(description="Press release title")
    meta_description: str = Field(description="SEO meta description, 120-160 chars")
    keywords_used: List[str] = Field(description="Keywords integrated in content")
    word_count: int = Field(description="Actual word count")
    seo_score: float = Field(description="SEO optimization score 0-1", ge=0, le=1)
    tone_score: float = Field(description="Tone consistency score 0-1", ge=0, le=1)
    template_id: str = Field(description="Template used for generation")
    generation_time: float = Field(description="Time taken in seconds", ge=0)
    confidence_score: float = Field(description="Generation confidence 0-1", ge=0, le=1)


# =================== TEMPLATE MANAGEMENT ===================


class TemplateManager:
    """Manage press release templates for Vietnamese context"""

    def __init__(self, template_dir: str = TEMPLATE_DIR):
        self.template_dir = template_dir
        self.templates: Dict[str, Dict] = {}
        self._load_templates()

    def _load_templates(self):
        """Load templates from directory or use default if not found"""
        try:
            if os.path.exists(self.template_dir):
                for filename in os.listdir(self.template_dir):
                    if filename.endswith(".json"):
                        with open(
                            os.path.join(self.template_dir, filename),
                            "r",
                            encoding="utf-8",
                        ) as f:
                            template = json.load(f)
                            template_id = filename.replace(".json", "")
                            self.templates[template_id] = template
                            logger.info(f"Loaded template: {template_id}")
            else:
                # Default templates for Vietnamese PR
                self.templates = {
                    "product_launch_vn": {
                        "id": "product_launch_vn",
                        "type": "Product Launch",
                        "language": "Vietnamese",
                        "structure": {
                            "title": "[Tên Công Ty] Ra Mắt [Tên Sản Phẩm]: [Điểm Nổi Bật]",
                            "intro": "TP. Hồ Chí Minh, [Ngày] - [Tên Công Ty], [Mô Tả Ngắn Công Ty], chính thức ra mắt [Tên Sản Phẩm], [Mô Tả Ngắn Sản Phẩm].",
                            "body": [
                                {
                                    "section": "Giới thiệu sản phẩm",
                                    "content": "[Tên Sản Phẩm] là [Mô Tả Chi Tiết]. Với [Đặc Điểm Nổi Bật], sản phẩm mang đến [Lợi Ích Chính].",
                                },
                                {
                                    "section": "Tầm nhìn và giá trị",
                                    "content": '"[Trích Dẫn từ CEO hoặc đại diện công ty về tầm nhìn, sứ mệnh, hoặc giá trị cốt lõi]", theo lời chia sẻ của [Tên], [Chức vụ].',
                                },
                                {
                                    "section": "Thông tin bổ sung",
                                    "content": "[Thông Tin Thêm về Công Ty hoặc Sản Phẩm].",
                                },
                            ],
                            "closing": "Để biết thêm thông tin, vui lòng liên hệ: [Thông Tin Liên Hệ].",
                        },
                    },
                    "partnership_vn": {
                        "id": "partnership_vn",
                        "type": "Partnership",
                        "language": "Vietnamese",
                        "structure": {
                            "title": "[Công Ty A] và [Công Ty B] Công Bố Hợp Tác Chiến Lược",
                            "intro": "Hà Nội, [Ngày] - [Công Ty A], [Mô Tả Ngắn], và [Công Ty B], [Mô Tả Ngắn], công bố hợp tác chiến lược nhằm [Mục Tiêu Hợp Tác].",
                            "body": [
                                {
                                    "section": "Chi tiết hợp tác",
                                    "content": "Quan hệ đối tác này sẽ [Mô Tả Hợp Tác]. [Lợi Ích Dự Kiến].",
                                },
                                {
                                    "section": "Ý kiến lãnh đạo",
                                    "content": "“[Trích Dẫn từ Đại Diện Công Ty A]”, [Tên và Chức Vụ] cho biết.",
                                },
                            ],
                            "closing": "Liên hệ: [Thông Tin Liên Hệ].",
                        },
                    },
                }
                logger.info(f"Loaded {len(self.templates)} default templates")
        except Exception as e:
            logger.error(f"Failed to load templates: {e}")

    def get_template(
        self, press_release_type: str, language: str = "Vietnamese"
    ) -> Optional[Dict]:
        """Select appropriate template based on type and language"""
        for template_id, template in self.templates.items():
            if (
                template["type"].lower() == press_release_type.lower()
                and template["language"].lower() == language.lower()
            ):
                return template
        logger.warning(
            f"No template found for type: {press_release_type}, language: {language}"
        )
        return self.templates.get("product_launch_vn")  # Fallback to default


# =================== CONTENT GENERATOR ===================


class AIContentGenerator:
    """AI-powered content generator for Vietnamese press releases"""

    def __init__(self):
        """Initialize content generator with OpenAI model and template manager"""
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY environment variable is required")

        self.llm = OpenAIChat(
            id=CONTENT_MODEL,
            api_key=OPENAI_API_KEY,
            temperature=CONTENT_TEMPERATURE,
            max_tokens=CONTENT_MAX_TOKENS,
            timeout=60,
        )

        self.storage = SqliteAgentStorage(
            table_name="content_generator", db_file="./content_memory.db"
        )

        self.template_manager = TemplateManager()

        self.content_agent = Agent(
            name="ContentGenerationAgent",
            role="Vietnamese PR content generation specialist",
            model=self.llm,
            instructions=[
                "Generate high-quality press release content for Vietnamese market",
                "Follow provided template structure strictly",
                "Integrate SEO keywords naturally (2% density)",
                "Maintain specified tone and language",
                "Include compelling quotes and statistics when relevant",
                "Optimize for readability and media appeal",
                "Return JSON matching ContentOutput schema",
                "Handle Vietnamese cultural nuances and business context",
            ],
            response_model=ContentOutput,
            storage=self.storage,
            show_tool_calls=False,
            markdown=False,
        )

        logger.info("✅ AI Content Generator initialized")

    async def generate_content(self, request: ContentRequest) -> ContentOutput:
        """Generate press release content based on request"""
        start_time = datetime.utcnow()
        try:
            # Select template
            template = self.template_manager.get_template(
                request.press_release_type, request.language
            )
            if not template:
                raise ValueError(
                    f"No suitable template for {request.press_release_type}"
                )

            # Prepare keywords
            keywords = request.keywords[:MAX_KEYWORDS]
            if not keywords:
                keywords = self._extract_keywords(
                    request.project_description, request.industry
                )

            # Build prompt
            prompt = self._build_content_prompt(request, template, keywords)

            # Generate content
            result = await self.content_agent.arun(prompt)

            # Parse and validate output
            content_output = self._parse_content_output(
                result, template["id"], keywords, request
            )

            # Calculate generation time
            generation_time = (datetime.utcnow() - start_time).total_seconds()
            content_output.generation_time = generation_time

            # Log success
            logger.info(
                f"✅ Generated content for session {request.session_id} "
                f"- Template: {template['id']}, "
                f"Time: {generation_time:.2f}s, "
                f"SEO Score: {content_output.seo_score:.2f}"
            )

            return content_output

        except Exception as e:
            logger.error(f"❌ Content generation failed: {e}")
            return ContentOutput(
                content=f"Lỗi: Không thể tạo nội dung. Vui lòng thử lại. ({str(e)})",
                title="Thông Cáo Báo Chí",
                meta_description="Thông cáo báo chí không thể tạo do lỗi hệ thống.",
                keywords_used=[],
                word_count=0,
                seo_score=0.0,
                tone_score=0.0,
                template_id="error",
                generation_time=(datetime.utcnow() - start_time).total_seconds(),
                confidence_score=0.0,
            )

    def _build_content_prompt(
        self, request: ContentRequest, template: Dict, keywords: List[str]
    ) -> str:
        """Build a detailed and optimized prompt for generating high-quality press release content"""
        structure = template["structure"]

        prompt = f"""
        Generate a compelling press release tailored for the Vietnamese market based on the following details:

        PROJECT DESCRIPTION: {request.project_description}
        INDUSTRY: {request.industry}
        TARGET AUDIENCE: {', '.join(request.target_audience) if request.target_audience else 'General Public'}
        KEYWORDS (integrate naturally with {SEO_KEYWORD_DENSITY*100}% density): {', '.join(keywords)}
        TONE: {request.tone}
        LANGUAGE: {request.language}
        PRESS RELEASE TYPE: {request.press_release_type}
        TARGET WORD COUNT: {request.word_count}
        ADDITIONAL INFO: {json.dumps(request.additional_info, ensure_ascii=False) if request.additional_info else 'None'}

        TEMPLATE STRUCTURE:
        - Title: {structure['title']}
        - Intro: {structure['intro']}
        - Body Sections:
        {[f"{sec['section']}: {sec['content']}" for sec in structure['body']]}
        - Closing: {structure['closing']}

        INSTRUCTIONS:
        1. Adhere strictly to the template structure, ensuring all sections (Title, Intro, Body Sections, Closing) are included and complete. Missing sections render the output invalid.
        2. Replace placeholders with relevant, engaging content that reflects Vietnamese cultural nuances and business context.
        3. Seamlessly integrate keywords to achieve the specified density, placing them naturally within sentences for SEO optimization.
        4. Maintain the specified tone consistently throughout, enhancing readability and professionalism.
        5. Include a compelling, fictional quote from an executive (e.g., CEO or spokesperson) that aligns with the project and resonates with the target audience.
        6. Incorporate relevant statistics, trends, or a short success story (if applicable) to boost credibility and media appeal.
        7. Structure body sections with clear, bolded titles (e.g., "Vision and Core Values", "Product Introduction") to improve readability and navigation.
        8. Optimize for Vietnamese media by using local references (e.g., cities like Hanoi or Ho Chi Minh City) and appealing to local values (e.g., community impact, innovation).
        9. Craft an SEO-optimized title (50-60 characters) and a meta description (120-160 characters) that summarize the key points and include primary keywords.
        10. Return a JSON object in the ContentOutput format with the following fields:
            - content: The full press release text
            - title: SEO-optimized title
            - meta_description: SEO-optimized meta description
            - keywords_used: List of integrated keywords
            - word_count: Total word count
            - seo_score: Score (0-1) based on keyword integration
            - tone_score: Score (0-1) for tone consistency
            - template_id: ID of the used template
            - confidence_score: Overall confidence score (0-1)
        11. End with a strong call-to-action in the closing section, encouraging readers to visit a website, contact for more info, or follow updates.
        """

        return prompt

    def _parse_content_output(
        self,
        result: any,
        template_id: str,
        keywords: List[str],
        request: ContentRequest,
    ) -> ContentOutput:
        """Parse and validate content generation output"""
        try:
            if hasattr(result, "content"):
                raw_result = result.content
            elif hasattr(result, "output"):
                raw_result = result.output
            else:
                raw_result = result

            if isinstance(raw_result, ContentOutput):
                output = raw_result
            elif isinstance(result, dict):
                output = ContentOutput(**raw_result)
            elif isinstance(raw_result, str):
                output = ContentOutput(**json.loads(raw_result))
            else:
                raise ValueError(f"Invalid result type: {type(raw_result)}")

            # Validate and enhance output
            output.template_id = template_id
            output.keywords_used = self._validate_keywords(output.content, keywords)
            output.word_count = len(output.content.split())
            output.seo_score = self._calculate_seo_score(
                output.content, output.keywords_used, output.word_count
            )
            output.tone_score = self._calculate_tone_score(output.content, request.tone)
            output.confidence_score = min(output.seo_score, output.tone_score, 0.9)

            # Ensure meta description length
            if len(output.meta_description) < 120 or len(output.meta_description) > 160:
                output.meta_description = self._generate_meta_description(
                    output.content, output.keywords_used
                )

            # Ensure title length
            if len(output.title) < 50 or len(output.title) > 60:
                output.title = self._generate_title(output.content, request)

            return output

        except Exception as e:
            logger.warning(f"Failed to parse content output: {e}")
            return ContentOutput(
                content="Nội dung mẫu cho thông cáo báo chí.",
                title=f"Thông Cáo Báo Chí {request.industry}",
                meta_description="Thông cáo báo chí không thể tạo do lỗi xử lý.",
                keywords_used=keywords,
                word_count=0,
                seo_score=0.5,
                tone_score=0.5,
                template_id=template_id,
                generation_time=0.0,
                confidence_score=0.5,
            )

    def _extract_keywords(self, description: str, industry: str) -> List[str]:
        """Extract default keywords if none provided"""
        words = description.lower().split()
        industry_keywords = {
            "technology": ["công nghệ", "ứng dụng", "phần mềm", "số hóa"],
            "finance": ["tài chính", "ngân hàng", "thanh toán", "fintech"],
            "healthcare": ["y tế", "sức khỏe", "bệnh viện", "chăm sóc"],
            "education": ["giáo dục", "đào tạo", "học tập", "trường học"],
        }

        keywords = industry_keywords.get(industry.lower(), ["thông cáo", "báo chí"])
        for word in words:
            if len(word) > 5 and word not in keywords and len(keywords) < MAX_KEYWORDS:
                keywords.append(word)

        return keywords[:MAX_KEYWORDS]

    def _validate_keywords(self, content: str, keywords: List[str]) -> List[str]:
        """Validate which keywords were used in content"""
        content_lower = content.lower()
        used_keywords = [kw for kw in keywords if kw.lower() in content_lower]
        return used_keywords

    def _calculate_seo_score(
        self, content: str, keywords: List[str], word_count: int
    ) -> float:
        """Calculate SEO score based on keyword density and distribution"""
        if not keywords or word_count == 0:
            return 0.5

        content_lower = content.lower()
        keyword_count = sum(content_lower.count(kw.lower()) for kw in keywords)
        actual_density = keyword_count / word_count

        # Ideal density is SEO_KEYWORD_DENSITY (2%)
        density_score = min(
            1.0, 1 - abs(actual_density - SEO_KEYWORD_DENSITY) / SEO_KEYWORD_DENSITY
        )

        # Check distribution
        sections = content.split("\n\n")
        keyword_coverage = sum(
            1
            for section in sections
            if any(kw.lower() in section.lower() for kw in keywords)
        )
        distribution_score = keyword_coverage / max(len(sections), 1)

        return density_score * 0.6 + distribution_score * 0.4

    def _calculate_tone_score(self, content: str, target_tone: str) -> float:
        """Calculate tone consistency score"""
        tone_indicators = {
            "Professional": ["chính thức", "chiến lược", "công bố", "phát triển"],
            "Casual": ["thân thiện", "gần gũi", "dễ dàng", "vui vẻ"],
            "Formal": ["kính gửi", "trân trọng", "tôn trọng", "nghiêm túc"],
        }

        indicators = tone_indicators.get(target_tone, [])
        if not indicators:
            return 0.8

        content_lower = content.lower()
        indicator_count = sum(content_lower.count(ind.lower()) for ind in indicators)
        return min(1.0, 0.5 + (indicator_count / max(len(content.split()), 1)) * 5)

    def _generate_meta_description(self, content: str, keywords: List[str]) -> str:
        """Generate SEO-friendly meta description"""
        sentences = content.split(".")
        first_sentence = sentences[0].strip() if sentences else ""
        keyword_str = ", ".join(keywords[:2]) if keywords else ""

        meta = f"{first_sentence} {keyword_str}.".strip()
        if len(meta) > 160:
            meta = meta[:157] + "..."
        elif len(meta) < 120:
            meta += " Tìm hiểu thêm về thông cáo báo chí này."

        return meta[:160]

    def _generate_title(self, content: str, request: ContentRequest) -> str:
        """Generate SEO-friendly title"""
        industry = request.industry
        project_name = request.project_description[:20]
        title_templates = [
            f"{project_name}: Thông Cáo Báo Chí {industry}",
            f"Ra Mắt {project_name} Trong Ngành {industry}",
            f"{industry}: {project_name} Công Bố Chiến Lược Mới",
        ]

        title = random.choice(title_templates)
        return title[:60]


# =================== INTEGRATION WITH AGENT SYSTEM ===================


def get_content_generator() -> AIContentGenerator:
    """Factory function for integration with EnhancedMediaReleaseTeamSystem"""
    try:
        return AIContentGenerator()
    except Exception as e:
        logger.error(f"Failed to initialize Content Generator: {e}")
        return None


# =================== TESTING ===================


async def test_content_generator():
    """Test content generator functionality"""
    logger.info("🧪 Testing AI Content Generator...")

    content_generator = get_content_generator()
    if not content_generator:
        logger.error("❌ Content Generator initialization failed")
        return False

    try:
        # Test content generation
        request = ContentRequest(
            session_id="test_content_001",
            project_description="VietFinance ra mắt ứng dụng vay vốn SME mới với lãi suất thấp.",
            industry="Finance",
            target_audience=["SMEs", "Business Owners"],
            keywords=["vay vốn", "SME", "fintech", "lãi suất"],
            tone="Professional",
            language="Vietnamese",
            press_release_type="Product Launch",
            word_count=400,
            additional_info={
                "company_name": "VietFinance",
                "contact": "info@vietfinance.vn",
            },
        )

        output = await content_generator.generate_content(request)

        logger.info(f"✅ Content Generation Test:")
        logger.info(f"  - Title: {output.title}")
        logger.info(f"  - Word Count: {output.word_count}")
        logger.info(f"📝 Content:\n{output.content[:800]}...\n")
        logger.info(f"  - SEO Score: {output.seo_score:.2f}")
        logger.info(f"  - Tone Score: {output.tone_score:.2f}")
        logger.info(f"  - Keywords: {', '.join(output.keywords_used)}")
        logger.info(f"  - Template: {output.template_id}")
        logger.info(f"  - Time: {output.generation_time:.2f}s")

        # Validate output
        if (
            output.word_count >= 300
            and output.seo_score >= 0.7
            and output.tone_score >= 0.7
            and len(output.keywords_used) >= 2
        ):
            logger.info("✅ Content generation test passed")
            return True
        else:
            logger.error("❌ Content generation test failed validation")
            return False

    except Exception as e:
        logger.error(f"❌ Content generation test failed: {e}")
        return False


if __name__ == "__main__":
    asyncio.run(test_content_generator())
