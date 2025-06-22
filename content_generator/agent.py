"""
AI Content Generator - Press release writing với Vietnamese context
Template-based content generation, SEO optimization và style enhancement
"""

import json
import logging
import re
import sqlite3
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
from pydantic import BaseModel

# Agno imports
from agno.tools import Toolkit
from agno.agent import Agent
from agno.models.openai import OpenAI

logger = logging.getLogger(__name__)


class ContentType(Enum):
    PRESS_RELEASE = "press_release"
    NEWS_ARTICLE = "news_article"
    FEATURE_STORY = "feature_story"
    INTERVIEW = "interview"
    PRODUCT_ANNOUNCEMENT = "product_announcement"
    COMPANY_NEWS = "company_news"


class ContentTone(Enum):
    PROFESSIONAL = "professional"
    FRIENDLY = "friendly"
    FORMAL = "formal"
    CREATIVE = "creative"
    TECHNICAL = "technical"
    CASUAL = "casual"


class ContentLength(Enum):
    SHORT = "short"  # 300-500 words
    MEDIUM = "medium"  # 500-800 words
    LONG = "long"  # 800-1200 words
    EXTENDED = "extended"  # 1200+ words


class ContentRequest(BaseModel):
    request_id: str
    order_id: str
    content_type: ContentType
    industry: str
    company_name: str
    company_description: str
    announcement_details: Dict[str, Any]
    target_audience: str
    tone: ContentTone = ContentTone.PROFESSIONAL
    length: ContentLength = ContentLength.MEDIUM
    key_messages: List[str] = []
    seo_keywords: List[str] = []
    include_quotes: bool = True
    include_statistics: bool = False
    language: str = "Vietnamese"
    created_at: datetime = datetime.now()


class GeneratedContent(BaseModel):
    content_id: str
    request_id: str
    order_id: str
    title: str
    subtitle: Optional[str] = None
    content: str
    summary: str
    meta_description: str
    tags: List[str] = []
    word_count: int
    seo_score: float
    readability_score: float
    created_at: datetime
    version: int = 1


class ContentTemplate(BaseModel):
    template_id: str
    name: str
    content_type: ContentType
    industry: str
    structure: List[str]  # List of sections
    sample_content: Dict[str, str]  # Section -> sample content
    required_fields: List[str]
    optional_fields: List[str] = []
    tone_guidelines: Dict[str, str] = {}


class ContentGeneratorToolkit(Toolkit):
    """Custom toolkit cho AI content generation"""

    def __init__(self):
        super().__init__(
            name="content_generator_toolkit",
            tools=[
                self.generate_press_release,
                self.enhance_content,
                self.optimize_seo,
                self.check_readability,
                self.create_content_variations,
                self.extract_key_points,
                self.generate_headlines,
                self.create_summary,
            ],
        )

    def generate_press_release(self, request: ContentRequest) -> GeneratedContent:
        """Tạo press release hoàn chỉnh từ content request"""
        try:
            # Get appropriate template
            template = self._get_content_template(
                request.content_type, request.industry
            )

            # Generate content structure
            content_structure = self._create_content_structure(request, template)

            # Generate each section
            sections = {}
            for section in content_structure:
                sections[section] = self._generate_section_content(
                    section, request, template
                )

            # Combine sections into full content
            full_content = self._combine_sections(sections, request)

            # Generate title and metadata
            title = self._generate_title(request)
            summary = self._generate_summary(full_content, request)
            meta_description = self._generate_meta_description(summary)

            # Calculate metrics
            word_count = len(full_content.split())
            seo_score = self._calculate_seo_score(full_content, request.seo_keywords)
            readability_score = self._calculate_readability_score(full_content)

            content = GeneratedContent(
                content_id=str(uuid.uuid4()),
                request_id=request.request_id,
                order_id=request.order_id,
                title=title,
                content=full_content,
                summary=summary,
                meta_description=meta_description,
                tags=self._extract_tags(full_content, request),
                word_count=word_count,
                seo_score=seo_score,
                readability_score=readability_score,
                created_at=datetime.now(),
            )

            # Save to database
            self._save_generated_content(content)

            return content

        except Exception as e:
            logger.error(f"Generate press release failed: {e}")
            raise

    def enhance_content(self, content: str, enhancement_type: str) -> str:
        """Cải thiện content với các enhancement khác nhau"""
        enhancements = {
            "clarity": self._enhance_clarity,
            "engagement": self._enhance_engagement,
            "professional": self._enhance_professional_tone,
            "seo": self._enhance_seo,
            "readability": self._enhance_readability,
        }

        if enhancement_type in enhancements:
            return enhancements[enhancement_type](content)

        return content

    def optimize_seo(self, content: str, keywords: List[str]) -> str:
        """Tối ưu SEO cho content"""
        optimized_content = content

        # Keyword density optimization
        for keyword in keywords:
            # Add keywords naturally if not present enough
            keyword_count = optimized_content.lower().count(keyword.lower())
            target_density = max(
                2, len(optimized_content.split()) // 100
            )  # 1-2% density

            if keyword_count < target_density:
                # Add keyword in natural context
                optimized_content = self._add_keyword_naturally(
                    optimized_content, keyword
                )

        # Add semantic variations
        optimized_content = self._add_semantic_keywords(optimized_content, keywords)

        return optimized_content

    def check_readability(self, content: str) -> Dict[str, Any]:
        """Kiểm tra readability của content"""
        sentences = re.split(r"[.!?]+", content)
        words = content.split()

        avg_sentence_length = len(words) / len(sentences) if sentences else 0
        complex_words = self._count_complex_words(words)

        # Simplified readability score for Vietnamese
        readability_score = (
            100
            - (avg_sentence_length * 1.015)
            - (complex_words * 84.6 / len(words) * 100)
        )

        return {
            "score": max(0, min(100, readability_score)),
            "grade_level": self._get_grade_level(readability_score),
            "avg_sentence_length": avg_sentence_length,
            "complex_word_percentage": complex_words / len(words) * 100 if words else 0,
            "total_words": len(words),
            "total_sentences": len(sentences),
            "recommendations": self._get_readability_recommendations(readability_score),
        }

    def create_content_variations(
        self, base_content: str, variations: int = 3
    ) -> List[str]:
        """Tạo nhiều variations của content"""
        variations_list = []

        for i in range(variations):
            variation = self._create_variation(
                base_content, variation_type=f"style_{i+1}"
            )
            variations_list.append(variation)

        return variations_list

    def extract_key_points(self, content: str) -> List[str]:
        """Trích xuất key points từ content"""
        sentences = re.split(r"[.!?]+", content)

        # Simple key point extraction (in production, use NLP)
        key_points = []
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 50:  # Meaningful sentences
                # Check for important indicators
                if any(
                    indicator in sentence.lower()
                    for indicator in [
                        "thông báo",
                        "ra mắt",
                        "phát triển",
                        "tăng",
                        "cải thiện",
                        "mới",
                    ]
                ):
                    key_points.append(sentence)

        return key_points[:5]  # Top 5 key points

    def generate_headlines(self, content: str, count: int = 5) -> List[str]:
        """Tạo multiple headlines cho content"""
        headlines = []

        # Extract key elements
        key_points = self.extract_key_points(content)
        if not key_points:
            return ["Thông báo báo chí mới"]

        # Generate different headline styles
        for i, point in enumerate(key_points[:count]):
            if i == 0:
                headline = f"🚀 {point[:60]}..."
            elif i == 1:
                headline = f"[Độc quyền] {point[:50]}..."
            elif i == 2:
                headline = f"NÓNG: {point[:55]}..."
            else:
                headline = f"{point[:65]}..."

            headlines.append(headline)

        return headlines

    def create_summary(self, content: str, max_length: int = 200) -> str:
        """Tạo summary từ content"""
        sentences = re.split(r"[.!?]+", content)

        # Select most important sentences
        important_sentences = []
        for sentence in sentences[:3]:  # First 3 sentences usually most important
            sentence = sentence.strip()
            if sentence and len(sentence) > 20:
                important_sentences.append(sentence)

        summary = ". ".join(important_sentences)

        # Truncate if too long
        if len(summary) > max_length:
            summary = summary[: max_length - 3] + "..."

        return summary

    def _get_content_template(
        self, content_type: ContentType, industry: str
    ) -> ContentTemplate:
        """Lấy template phù hợp cho content type và industry"""

        # Define templates for different industries
        templates = {
            "TECHNOLOGY": ContentTemplate(
                template_id="tech_press_release",
                name="Technology Press Release",
                content_type=content_type,
                industry=industry,
                structure=[
                    "headline",
                    "dateline",
                    "lead_paragraph",
                    "body_paragraph_1",
                    "quote_1",
                    "body_paragraph_2",
                    "quote_2",
                    "company_info",
                    "contact_info",
                ],
                sample_content={
                    "headline": "[Company] ra mắt [product/service] mang tính đột phá cho thị trường [target_market]",
                    "lead_paragraph": "Công ty [Company] hôm nay chính thức công bố [announcement] nhằm [benefit/goal].",
                    "quote_1": '"[Key message about innovation]" - [Executive Name], [Title] của [Company]',
                },
                required_fields=[
                    "company_name",
                    "announcement_details",
                    "target_audience",
                ],
                optional_fields=["statistics", "quotes", "contact_info"],
            ),
            "BUSINESS": ContentTemplate(
                template_id="business_press_release",
                name="Business Press Release",
                content_type=content_type,
                industry=industry,
                structure=[
                    "headline",
                    "dateline",
                    "lead_paragraph",
                    "business_impact",
                    "executive_quote",
                    "market_context",
                    "financial_details",
                    "future_outlook",
                    "company_info",
                ],
                sample_content={
                    "headline": "[Company] thông báo [business_news] tạo đột phá trong lĩnh vực [industry]",
                    "business_impact": "Động thái này dự kiến sẽ [expected_impact] và mang lại [benefits].",
                },
                required_fields=[
                    "company_name",
                    "business_announcement",
                    "market_impact",
                ],
                optional_fields=["financial_data", "growth_metrics"],
            ),
        }

        return templates.get(industry.upper(), templates["BUSINESS"])

    def _create_content_structure(
        self, request: ContentRequest, template: ContentTemplate
    ) -> List[str]:
        """Tạo cấu trúc content dựa trên template và yêu cầu"""
        structure = template.structure.copy()

        # Modify structure based on content length
        if request.length == ContentLength.SHORT:
            # Remove optional sections for short content
            structure = [
                s
                for s in structure
                if s
                in ["headline", "lead_paragraph", "body_paragraph_1", "company_info"]
            ]
        elif request.length == ContentLength.EXTENDED:
            # Add more sections for extended content
            structure.extend(
                ["additional_details", "market_analysis", "technical_specs"]
            )

        return structure

    def _generate_section_content(
        self, section: str, request: ContentRequest, template: ContentTemplate
    ) -> str:
        """Tạo content cho một section cụ thể"""

        # Section generators
        generators = {
            "headline": self._generate_headline,
            "dateline": self._generate_dateline,
            "lead_paragraph": self._generate_lead_paragraph,
            "body_paragraph_1": self._generate_body_paragraph,
            "quote_1": self._generate_quote,
            "company_info": self._generate_company_info,
            "contact_info": self._generate_contact_info,
        }

        generator = generators.get(section, self._generate_generic_section)
        return generator(section, request, template)

    def _generate_headline(
        self, section: str, request: ContentRequest, template: ContentTemplate
    ) -> str:
        """Tạo headline"""
        company = request.company_name
        announcement = request.announcement_details.get("title", "thông báo mới")

        headlines = [
            f"{company} ra mắt {announcement} tạo đột phá cho thị trường {request.target_audience}",
            f"[Độc quyền] {company} công bố {announcement} mang tính cách mạng",
            f"🚀 {company} giới thiệu {announcement} - Bước tiến mới trong ngành {request.industry}",
            f"NÓNG: {company} chính thức phát hành {announcement} cho {request.target_audience}",
        ]

        # Select based on tone
        if request.tone == ContentTone.PROFESSIONAL:
            return headlines[0]
        elif request.tone == ContentTone.CREATIVE:
            return headlines[2]
        else:
            return headlines[1]

    def _generate_dateline(
        self, section: str, request: ContentRequest, template: ContentTemplate
    ) -> str:
        """Tạo dateline"""
        return f"TP. Hồ Chí Minh, {datetime.now().strftime('%d/%m/%Y')}"

    def _generate_lead_paragraph(
        self, section: str, request: ContentRequest, template: ContentTemplate
    ) -> str:
        """Tạo lead paragraph"""
        company = request.company_name
        announcement = request.announcement_details.get("description", "phát triển mới")
        benefit = request.announcement_details.get(
            "benefit", "mang lại giá trị cho khách hàng"
        )

        return f"Công ty {company} hôm nay chính thức thông báo {announcement} nhằm {benefit}. Đây được xem là một bước tiến quan trọng trong chiến lược phát triển của {company} tại thị trường Việt Nam."

    def _generate_body_paragraph(
        self, section: str, request: ContentRequest, template: ContentTemplate
    ) -> str:
        """Tạo body paragraph"""
        details = request.announcement_details

        features = details.get(
            "features", ["tính năng tiên tiến", "giao diện thân thiện", "bảo mật cao"]
        )
        target = request.target_audience

        paragraph = f"Với {', '.join(features[:3])}, sản phẩm/dịch vụ này được thiết kế đặc biệt cho {target}. "

        if request.include_statistics and details.get("statistics"):
            stats = details["statistics"]
            paragraph += f"Theo nghiên cứu, {stats}. "

        paragraph += f"Điều này thể hiện cam kết của {request.company_name} trong việc đáp ứng nhu cầu ngày càng cao của thị trường."

        return paragraph

    def _generate_quote(
        self, section: str, request: ContentRequest, template: ContentTemplate
    ) -> str:
        """Tạo quote"""
        if not request.include_quotes:
            return ""

        executive = request.announcement_details.get("executive", "CEO")
        key_message = (
            request.key_messages[0]
            if request.key_messages
            else "Đây là một cột mốc quan trọng cho chúng tôi"
        )

        return f'"{key_message}," chia sẻ {executive} của {request.company_name}. "Chúng tôi tin rằng điều này sẽ mang lại giá trị thiết thực cho {request.target_audience} và góp phần thúc đẩy sự phát triển của ngành {request.industry}."'

    def _generate_company_info(
        self, section: str, request: ContentRequest, template: ContentTemplate
    ) -> str:
        """Tạo company info"""
        return f"Về {request.company_name}: {request.company_description}"

    def _generate_contact_info(
        self, section: str, request: ContentRequest, template: ContentTemplate
    ) -> str:
        """Tạo contact info"""
        return """Thông tin liên hệ:
Email: contact@instantmediarelease.vn
Website: www.instantmediarelease.vn
Điện thoại: +84 xxx xxx xxxx"""

    def _generate_generic_section(
        self, section: str, request: ContentRequest, template: ContentTemplate
    ) -> str:
        """Generic section generator"""
        return f"[Nội dung cho section: {section}]"

    def _combine_sections(
        self, sections: Dict[str, str], request: ContentRequest
    ) -> str:
        """Kết hợp các sections thành content hoàn chỉnh"""
        content_parts = []

        for section_name, section_content in sections.items():
            if section_content and section_content.strip():
                if section_name == "headline":
                    content_parts.append(f"# {section_content}\n")
                elif section_name == "dateline":
                    content_parts.append(f"*{section_content}*\n")
                elif "quote" in section_name:
                    content_parts.append(f"> {section_content}\n")
                else:
                    content_parts.append(f"{section_content}\n")

        return "\n".join(content_parts)

    def _generate_title(self, request: ContentRequest) -> str:
        """Tạo title cho content"""
        return self._generate_headline("headline", request, None)

    def _generate_summary(self, content: str, request: ContentRequest) -> str:
        """Tạo summary cho content"""
        return self.create_summary(content, max_length=150)

    def _generate_meta_description(self, summary: str) -> str:
        """Tạo meta description cho SEO"""
        if len(summary) <= 160:
            return summary
        return summary[:157] + "..."

    def _extract_tags(self, content: str, request: ContentRequest) -> List[str]:
        """Trích xuất tags từ content"""
        tags = [request.industry, request.target_audience, request.company_name]

        # Add keyword-based tags
        for keyword in request.seo_keywords:
            if keyword.lower() in content.lower():
                tags.append(keyword)

        return list(set(tags))

    def _calculate_seo_score(self, content: str, keywords: List[str]) -> float:
        """Tính SEO score"""
        if not keywords:
            return 0.5

        total_score = 0
        content_lower = content.lower()

        for keyword in keywords:
            keyword_count = content_lower.count(keyword.lower())
            keyword_density = keyword_count / len(content.split()) * 100

            # Optimal density is 1-3%
            if 1 <= keyword_density <= 3:
                score = 1.0
            elif keyword_density < 1:
                score = keyword_density
            else:
                score = max(0.5, 3 / keyword_density)

            total_score += score

        return min(1.0, total_score / len(keywords))

    def _calculate_readability_score(self, content: str) -> float:
        """Tính readability score"""
        return self.check_readability(content)["score"] / 100

    def _enhance_clarity(self, content: str) -> str:
        """Cải thiện clarity của content"""
        # Replace complex phrases with simpler ones
        replacements = {
            "thực hiện": "làm",
            "khả năng": "có thể",
            "tối ưu hóa": "cải thiện",
            "hiệu quả": "tốt",
        }

        enhanced = content
        for complex_word, simple_word in replacements.items():
            enhanced = enhanced.replace(complex_word, simple_word)

        return enhanced

    def _enhance_engagement(self, content: str) -> str:
        """Cải thiện engagement của content"""
        # Add engaging elements
        enhanced = content

        # Add action words at the beginning of paragraphs
        paragraphs = enhanced.split("\n\n")
        for i, paragraph in enumerate(paragraphs):
            if i == 0:  # First paragraph
                if not paragraph.startswith(("🚀", "NÓNG:", "[Độc quyền]")):
                    paragraphs[i] = f"🚀 {paragraph}"

        return "\n\n".join(paragraphs)

    def _enhance_professional_tone(self, content: str) -> str:
        """Cải thiện professional tone"""
        # Replace casual language with professional alternatives
        professional_replacements = {
            "rất tốt": "xuất sắc",
            "khá hay": "ấn tượng",
            "ok": "phù hợp",
            "cool": "tiến tiến",
        }

        enhanced = content
        for casual, professional in professional_replacements.items():
            enhanced = enhanced.replace(casual, professional)

        return enhanced

    def _enhance_seo(self, content: str) -> str:
        """Cải thiện SEO của content"""
        # Add SEO-friendly elements
        enhanced = content

        # Ensure proper heading structure
        if "# " not in enhanced:
            lines = enhanced.split("\n")
            if lines:
                lines[0] = f"# {lines[0]}"
                enhanced = "\n".join(lines)

        return enhanced

    def _enhance_readability(self, content: str) -> str:
        """Cải thiện readability"""
        # Break long sentences
        sentences = re.split(r"[.!?]+", content)
        improved_sentences = []

        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence.split()) > 25:  # Long sentence
                # Try to break at conjunctions
                parts = re.split(r"\s+(và|nhưng|tuy nhiên|do đó|vì vậy)\s+", sentence)
                if len(parts) > 1:
                    improved_sentences.extend(parts)
                else:
                    improved_sentences.append(sentence)
            else:
                improved_sentences.append(sentence)

        return ". ".join([s for s in improved_sentences if s.strip()])

    def _add_keyword_naturally(self, content: str, keyword: str) -> str:
        """Thêm keyword một cách tự nhiên"""
        # Find appropriate places to add keyword
        sentences = content.split(". ")

        # Add to the second paragraph if possible
        if len(sentences) > 3:
            sentences[2] = sentences[2].replace("nó", keyword, 1)

        return ". ".join(sentences)

    def _add_semantic_keywords(self, content: str, keywords: List[str]) -> str:
        """Thêm semantic keywords"""
        # Define semantic variations for common keywords
        semantic_map = {
            "công nghệ": ["technology", "kỹ thuật", "công nghệ thông tin"],
            "doanh nghiệp": ["business", "công ty", "tổ chức"],
            "phát triển": ["development", "tăng trưởng", "mở rộng"],
        }

        enhanced = content
        for keyword in keywords:
            if keyword in semantic_map:
                variations = semantic_map[keyword]
                # Add one variation naturally
                if variations and len(enhanced.split()) > 100:
                    enhanced = enhanced.replace("nó", variations[0], 1)

        return enhanced

    def _count_complex_words(self, words: List[str]) -> int:
        """Đếm số từ phức tạp (>3 syllables for Vietnamese)"""
        complex_count = 0
        for word in words:
            # Simple heuristic: words longer than 8 characters are complex
            if len(word) > 8:
                complex_count += 1
        return complex_count

    def _get_grade_level(self, score: float) -> str:
        """Lấy grade level từ readability score"""
        if score >= 90:
            return "Very Easy"
        elif score >= 80:
            return "Easy"
        elif score >= 70:
            return "Fairly Easy"
        elif score >= 60:
            return "Standard"
        elif score >= 50:
            return "Fairly Difficult"
        elif score >= 30:
            return "Difficult"
        else:
            return "Very Difficult"

    def _get_readability_recommendations(self, score: float) -> List[str]:
        """Lấy recommendations để cải thiện readability"""
        recommendations = []

        if score < 50:
            recommendations.extend(
                [
                    "Sử dụng câu ngắn hơn (dưới 20 từ)",
                    "Thay thế từ phức tạp bằng từ đơn giản",
                    "Chia đoạn văn dài thành đoạn ngắn hơn",
                ]
            )
        elif score < 70:
            recommendations.extend(
                ["Giảm số lượng từ phức tạp", "Sử dụng cấu trúc câu đa dạng"]
            )
        else:
            recommendations.append("Readability tốt! Tiếp tục maintain chất lượng.")

        return recommendations

    def _create_variation(self, base_content: str, variation_type: str) -> str:
        """Tạo variation của content"""
        variations = {
            "style_1": self._create_formal_variation,
            "style_2": self._create_creative_variation,
            "style_3": self._create_technical_variation,
        }

        creator = variations.get(variation_type, lambda x: x)
        return creator(base_content)

    def _create_formal_variation(self, content: str) -> str:
        """Tạo formal variation"""
        # Make content more formal
        formal_replacements = {
            "chúng tôi": "công ty chúng tôi",
            "sản phẩm": "giải pháp",
            "app": "ứng dụng",
        }

        formal_content = content
        for casual, formal in formal_replacements.items():
            formal_content = formal_content.replace(casual, formal)

        return formal_content

    def _create_creative_variation(self, content: str) -> str:
        """Tạo creative variation"""
        # Add creative elements
        creative = content

        # Add emojis and creative language
        if "công nghệ" in creative:
            creative = creative.replace("công nghệ", "công nghệ 🚀")
        if "ra mắt" in creative:
            creative = creative.replace("ra mắt", "chính thức ra mắt 🎉")

        return creative

    def _create_technical_variation(self, content: str) -> str:
        """Tạo technical variation"""
        # Add more technical details
        technical = content

        # Add technical terms
        technical_additions = {
            "ứng dụng": "ứng dụng với kiến trúc microservices",
            "bảo mật": "bảo mật end-to-end encryption",
            "hiệu suất": "hiệu suất với 99.9% uptime",
        }

        for term, technical_term in technical_additions.items():
            technical = technical.replace(term, technical_term, 1)

        return technical

    def _save_generated_content(self, content: GeneratedContent):
        """Lưu generated content vào database"""
        try:
            conn = sqlite3.connect("media_release.db")
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT OR REPLACE INTO generated_content
                (content_id, request_id, order_id, title, subtitle, content, summary, 
                 meta_description, tags, word_count, seo_score, readability_score, 
                 created_at, version)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    content.content_id,
                    content.request_id,
                    content.order_id,
                    content.title,
                    content.subtitle,
                    content.content,
                    content.summary,
                    content.meta_description,
                    json.dumps(content.tags),
                    content.word_count,
                    content.seo_score,
                    content.readability_score,
                    content.created_at.isoformat(),
                    content.version,
                ),
            )

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Save generated content failed: {e}")


class ContentGeneratorAgent(Agent):
    """AI Agent chuyên tạo content marketing và press releases"""

    def __init__(self):
        self.content_toolkit = ContentGeneratorToolkit()
        self._init_database()

        super().__init__(
            model=OpenAI(id="gpt-4"),
            tools=[self.content_toolkit],
            instructions=[
                "Bạn là Content Generator Agent chuyên tạo press release và content marketing",
                "Viết content chuyên nghiệp bằng tiếng Việt với tone phù hợp",
                "Tối ưu SEO và readability cho từng piece of content",
                "Đảm bảo accuracy và consistency trong thông tin",
                "Luôn include call-to-action và contact information",
            ],
            description="AI Agent tạo content chất lượng cao cho media outreach và marketing",
        )

    def _init_database(self):
        """Khởi tạo database tables cho content generation"""
        conn = sqlite3.connect("media_release.db")
        cursor = conn.cursor()

        # Content requests table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS content_requests (
                request_id TEXT PRIMARY KEY,
                order_id TEXT NOT NULL,
                content_type TEXT NOT NULL,
                industry TEXT NOT NULL,
                company_name TEXT NOT NULL,
                company_description TEXT NOT NULL,
                announcement_details TEXT NOT NULL,
                target_audience TEXT NOT NULL,
                tone TEXT DEFAULT 'professional',
                length TEXT DEFAULT 'medium',
                key_messages TEXT DEFAULT '[]',
                seo_keywords TEXT DEFAULT '[]',
                include_quotes BOOLEAN DEFAULT 1,
                include_statistics BOOLEAN DEFAULT 0,
                language TEXT DEFAULT 'Vietnamese',
                created_at TEXT NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders (order_id)
            )
        """
        )

        # Generated content table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS generated_content (
                content_id TEXT PRIMARY KEY,
                request_id TEXT NOT NULL,
                order_id TEXT NOT NULL,
                title TEXT NOT NULL,
                subtitle TEXT,
                content TEXT NOT NULL,
                summary TEXT NOT NULL,
                meta_description TEXT NOT NULL,
                tags TEXT DEFAULT '[]',
                word_count INTEGER NOT NULL,
                seo_score REAL NOT NULL,
                readability_score REAL NOT NULL,
                created_at TEXT NOT NULL,
                version INTEGER DEFAULT 1,
                FOREIGN KEY (request_id) REFERENCES content_requests (request_id),
                FOREIGN KEY (order_id) REFERENCES orders (order_id)
            )
        """
        )

        # Content templates table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS content_templates (
                template_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                content_type TEXT NOT NULL,
                industry TEXT NOT NULL,
                structure TEXT NOT NULL,
                sample_content TEXT NOT NULL,
                required_fields TEXT NOT NULL,
                optional_fields TEXT DEFAULT '[]',
                tone_guidelines TEXT DEFAULT '{}',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """
        )

        conn.commit()
        conn.close()

    def create_press_release(
        self,
        order_id: str,
        company_info: Dict[str, Any],
        announcement: Dict[str, Any],
        preferences: Dict[str, Any] = None,
    ) -> GeneratedContent:
        """Tạo press release hoàn chỉnh"""

        preferences = preferences or {}

        # Create content request
        request = ContentRequest(
            request_id=str(uuid.uuid4()),
            order_id=order_id,
            content_type=ContentType.PRESS_RELEASE,
            industry=company_info.get("industry", "BUSINESS"),
            company_name=company_info["name"],
            company_description=company_info.get("description", ""),
            announcement_details=announcement,
            target_audience=announcement.get("target_audience", "doanh nghiệp SME"),
            tone=ContentTone(preferences.get("tone", "professional")),
            length=ContentLength(preferences.get("length", "medium")),
            key_messages=preferences.get("key_messages", []),
            seo_keywords=preferences.get("seo_keywords", []),
            include_quotes=preferences.get("include_quotes", True),
            include_statistics=preferences.get("include_statistics", False),
        )

        # Save request
        self._save_content_request(request)

        # Generate content
        content = self.content_toolkit.generate_press_release(request)

        return content

    def enhance_existing_content(
        self, content_id: str, enhancement_types: List[str]
    ) -> GeneratedContent:
        """Cải thiện content đã có"""

        # Get existing content
        existing_content = self._get_generated_content(content_id)
        if not existing_content:
            raise ValueError(f"Content not found: {content_id}")

        # Apply enhancements
        enhanced_content = existing_content.content
        for enhancement_type in enhancement_types:
            enhanced_content = self.content_toolkit.enhance_content(
                enhanced_content, enhancement_type
            )

        # Recalculate metrics
        word_count = len(enhanced_content.split())
        seo_score = self.content_toolkit._calculate_seo_score(enhanced_content, [])
        readability_score = self.content_toolkit._calculate_readability_score(
            enhanced_content
        )

        # Create new version
        enhanced = GeneratedContent(
            content_id=str(uuid.uuid4()),
            request_id=existing_content.request_id,
            order_id=existing_content.order_id,
            title=existing_content.title,
            subtitle=existing_content.subtitle,
            content=enhanced_content,
            summary=self.content_toolkit.create_summary(enhanced_content),
            meta_description=existing_content.meta_description,
            tags=existing_content.tags,
            word_count=word_count,
            seo_score=seo_score,
            readability_score=readability_score,
            created_at=datetime.now(),
            version=existing_content.version + 1,
        )

        # Save enhanced version
        self.content_toolkit._save_generated_content(enhanced)

        return enhanced

    def get_content_analytics(self, order_id: str) -> Dict[str, Any]:
        """Lấy analytics cho content của order"""
        try:
            conn = sqlite3.connect("media_release.db")
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT content_id, title, word_count, seo_score, readability_score, created_at
                FROM generated_content WHERE order_id = ?
                ORDER BY created_at DESC
            """,
                (order_id,),
            )

            contents = cursor.fetchall()
            conn.close()

            if not contents:
                return {"order_id": order_id, "content_count": 0}

            # Calculate averages
            avg_seo = sum(c[3] for c in contents) / len(contents)
            avg_readability = sum(c[4] for c in contents) / len(contents)
            total_words = sum(c[2] for c in contents)

            return {
                "order_id": order_id,
                "content_count": len(contents),
                "total_words": total_words,
                "average_seo_score": round(avg_seo, 2),
                "average_readability_score": round(avg_readability, 2),
                "contents": [
                    {
                        "content_id": c[0],
                        "title": c[1],
                        "word_count": c[2],
                        "seo_score": c[3],
                        "readability_score": c[4],
                        "created_at": c[5],
                    }
                    for c in contents
                ],
            }

        except Exception as e:
            logger.error(f"Get content analytics failed: {e}")
            return {}

    def _save_content_request(self, request: ContentRequest):
        """Lưu content request vào database"""
        try:
            conn = sqlite3.connect("media_release.db")
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT OR REPLACE INTO content_requests
                (request_id, order_id, content_type, industry, company_name,
                 company_description, announcement_details, target_audience, tone,
                 length, key_messages, seo_keywords, include_quotes, include_statistics,
                 language, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    request.request_id,
                    request.order_id,
                    request.content_type.value,
                    request.industry,
                    request.company_name,
                    request.company_description,
                    json.dumps(request.announcement_details),
                    request.target_audience,
                    request.tone.value,
                    request.length.value,
                    json.dumps(request.key_messages),
                    json.dumps(request.seo_keywords),
                    request.include_quotes,
                    request.include_statistics,
                    request.language,
                    request.created_at.isoformat(),
                ),
            )

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Save content request failed: {e}")

    def _get_generated_content(self, content_id: str) -> Optional[GeneratedContent]:
        """Lấy generated content từ database"""
        try:
            conn = sqlite3.connect("media_release.db")
            cursor = conn.cursor()

            cursor.execute(
                "SELECT * FROM generated_content WHERE content_id = ?", (content_id,)
            )
            result = cursor.fetchone()
            conn.close()

            if result:
                return GeneratedContent(
                    content_id=result[0],
                    request_id=result[1],
                    order_id=result[2],
                    title=result[3],
                    subtitle=result[4],
                    content=result[5],
                    summary=result[6],
                    meta_description=result[7],
                    tags=json.loads(result[8]),
                    word_count=result[9],
                    seo_score=result[10],
                    readability_score=result[11],
                    created_at=datetime.fromisoformat(result[12]),
                    version=result[13],
                )
            return None

        except Exception as e:
            logger.error(f"Get generated content failed: {e}")
            return None


if __name__ == "__main__":
    # Test content generator
    content_agent = ContentGeneratorAgent()

    # Test press release generation
    company_info = {
        "name": "VietPay",
        "description": "Startup fintech phát triển giải pháp thanh toán cho SME",
        "industry": "TECHNOLOGY",
    }

    announcement = {
        "title": "Ứng dụng thanh toán VietPay cho SME",
        "description": "ra mắt ứng dụng thanh toán mới cho doanh nghiệp SME",
        "benefit": "giúp SME quản lý tài chính hiệu quả hơn",
        "features": ["thanh toán nhanh", "báo cáo tự động", "tích hợp ngân hàng"],
        "target_audience": "doanh nghiệp SME",
    }

    preferences = {
        "tone": "professional",
        "length": "medium",
        "seo_keywords": ["fintech", "SME", "thanh toán", "ứng dụng"],
        "include_quotes": True,
    }

    press_release = content_agent.create_press_release(
        order_id="test-order-content",
        company_info=company_info,
        announcement=announcement,
        preferences=preferences,
    )

    print(f"✅ Press release generated: {press_release.title}")
    print(f"📊 Word count: {press_release.word_count}")
    print(f"🎯 SEO score: {press_release.seo_score:.2f}")
    print(f"📖 Readability score: {press_release.readability_score:.2f}")
    print(f"🏷️ Tags: {', '.join(press_release.tags)}")
