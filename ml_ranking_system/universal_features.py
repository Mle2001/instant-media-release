"""
Universal Structure Extractor
Trích xuất features từ universal structures có trong mọi campaign/content/conversation
"""

import os
import re
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
import asyncio
from collections import Counter
import math

from loguru import logger
from sentence_transformers import SentenceTransformer
import yaml

# Local model definitions to avoid circular imports
from pydantic import BaseModel
from typing import Dict, List, Any, Optional

class ContentAnalysis(BaseModel):
    """Local content analysis model"""
    topic: Optional[str] = None
    industry: Optional[str] = None
    content_type: Optional[str] = None
    urgency: Optional[str] = None
    target_audience: Optional[List[str]] = None

class ConversationContext(BaseModel):
    """Local conversation context model"""
    messages: Optional[List[Dict]] = None
    user_preferences: Optional[Dict] = None
    session_data: Optional[Dict] = None


@dataclass
class UniversalFeatures:
    """Container cho tất cả universal features"""
    
    # Content Structure Features
    content_features: Dict[str, float] = field(default_factory=dict)
    
    # Audience Signal Features  
    audience_features: Dict[str, float] = field(default_factory=dict)
    
    # Business Context Features
    business_features: Dict[str, float] = field(default_factory=dict)
    
    # Market Timing Features
    timing_features: Dict[str, float] = field(default_factory=dict)
    
    # Competitive Landscape Features
    competitive_features: Dict[str, float] = field(default_factory=dict)
    
    # Meta information
    extraction_timestamp: datetime = field(default_factory=datetime.now)
    feature_version: str = "1.0.0"
    
    def to_vector(self) -> np.ndarray:
        """Convert all features to single numpy vector"""
        all_features = []
        
        # Combine all feature dictionaries in consistent order
        for feature_dict in [
            self.content_features,
            self.audience_features, 
            self.business_features,
            self.timing_features,
            self.competitive_features
        ]:
            # Sort keys for consistent ordering
            sorted_keys = sorted(feature_dict.keys())
            values = [feature_dict[key] for key in sorted_keys]
            all_features.extend(values)
        
        return np.array(all_features, dtype=np.float32)
    
    def get_feature_names(self) -> List[str]:
        """Get ordered list of all feature names"""
        all_names = []
        
        for prefix, feature_dict in [
            ("content", self.content_features),
            ("audience", self.audience_features),
            ("business", self.business_features), 
            ("timing", self.timing_features),
            ("competitive", self.competitive_features)
        ]:
            sorted_keys = sorted(feature_dict.keys())
            names = [f"{prefix}_{key}" for key in sorted_keys]
            all_names.extend(names)
            
        return all_names


class UniversalStructureExtractor:
    """
    Trích xuất universal features từ campaign data
    
    RATIONALE: Thay vì dựa vào conversation success, tập trung vào 
    universal patterns có trong mọi successful campaign
    """
    
    def __init__(self, config_path: str = "./config/ml_config.yaml"):
        """Initialize with configuration"""
        
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Initialize embedding model for semantic analysis
        try:
            self.embedding_model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
            logger.info("✅ Embedding model loaded successfully")
        except Exception as e:
            logger.error(f"❌ Failed to load embedding model: {e}")
            self.embedding_model = None
        
        # Vietnamese industry keywords for classification
        self.industry_keywords = {
            'tech': ['công nghệ', 'phần mềm', 'app', 'digital', 'ai', 'blockchain', 'fintech'],
            'finance': ['tài chính', 'ngân hàng', 'đầu tư', 'bảo hiểm', 'cho vay', 'thanh toán'],
            'health': ['y tế', 'sức khỏe', 'bệnh viện', 'thuốc', 'chăm sóc', 'điều trị'],
            'education': ['giáo dục', 'đào tạo', 'học tập', 'trường', 'sinh viên', 'khóa học'],
            'retail': ['bán lẻ', 'thương mại', 'mua sắm', 'sản phẩm', 'khách hàng'],
            'manufacturing': ['sản xuất', 'nhà máy', 'chế tạo', 'công nghiệp', 'xuất khẩu'],
            'tourism': ['du lịch', 'khách sạn', 'tour', 'nghỉ dưỡng', 'điểm đến']
        }
        
        # Emotional keywords for content analysis
        self.emotion_keywords = {
            'excitement': ['heyén động', 'thú vị', 'tuyệt vời', 'đột phá', 'cách mạng'],
            'trust': ['tin cậy', 'uy tín', 'chất lượng', 'an toàn', 'bảo đảm'],
            'urgency': ['ngay lập tức', 'khẩn cấp', 'nhanh chóng', 'giới hạn', 'cuối cùng'],
            'innovation': ['đổi mới', 'sáng tạo', 'tiên phong', 'độc đáo', 'mới lạ']
        }
        
        # Competitive intensity indicators
        self.competition_keywords = {
            'high': ['cạnh tranh', 'thị trường bão hòa', 'nhiều đối thủ', 'giá cả'],
            'medium': ['tăng trưởng', 'mở rộng', 'phát triển', 'cơ hội'],
            'low': ['thị trường mới', 'ít cạnh tranh', 'dẫn đầu', 'độc quyền']
        }
        
        logger.info("✅ UniversalStructureExtractor initialized")
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            return config.get('data', {}).get('feature_extraction', {})
        except Exception as e:
            logger.warning(f"Could not load config from {config_path}: {e}")
            return {
                'content_max_length': 512,
                'keyword_max_count': 10,
                'topic_max_count': 5
            }
    
    async def extract_universal_features(
        self,
        content_analysis: Union[ContentAnalysis, Dict],
        conversation_context: Optional[Union[ConversationContext, Dict]] = None,
        additional_context: Optional[Dict] = None
    ) -> UniversalFeatures:
        """
        Main method to extract all universal features
        
        Args:
            content_analysis: Analysis of the content/campaign
            conversation_context: Optional conversation context
            additional_context: Additional context data
        
        Returns:
            UniversalFeatures: Complete feature set
        """
        
        logger.info("🔍 Extracting universal features...")
        
        # Convert to dict if needed for consistent access
        if hasattr(content_analysis, 'model_dump'):
            content_data = content_analysis.model_dump()
        elif hasattr(content_analysis, '__dict__'):
            content_data = content_analysis.__dict__
        else:
            content_data = content_analysis
        
        # Extract features in parallel for efficiency
        feature_tasks = [
            self._extract_content_features(content_data),
            self._extract_audience_features(content_data, conversation_context),
            self._extract_business_features(content_data, additional_context),
            self._extract_timing_features(content_data, additional_context),
            self._extract_competitive_features(content_data, additional_context)
        ]
        
        results = await asyncio.gather(*feature_tasks, return_exceptions=True)
        
        # Handle any extraction errors
        content_features, audience_features, business_features, timing_features, competitive_features = results
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Feature extraction error in task {i}: {result}")
                results[i] = {}
        
        universal_features = UniversalFeatures(
            content_features=content_features or {},
            audience_features=audience_features or {},
            business_features=business_features or {},
            timing_features=timing_features or {},
            competitive_features=competitive_features or {}
        )
        
        logger.info(f"✅ Extracted {len(universal_features.to_vector())} universal features")
        
        return universal_features
    
    async def _extract_content_features(self, content_data: Dict) -> Dict[str, float]:
        """
        Extract content structure features
        
        WHY: Content structure correlates với media success
        - Complex content → tier-1 media preference
        - Emotional content → higher engagement
        - Factual content → business media preference
        """
        
        content_text = content_data.get('content', '') or content_data.get('user_input', '') or ''
        keywords = content_data.get('keywords', []) or content_data.get('primary_topics', []) or []
        
        if not content_text:
            logger.warning("No content text found for feature extraction")
            return {}
        
        # Tokenize content for analysis
        words = content_text.lower().split()
        sentences = content_text.split('.')
        
        features = {}
        
        # 1. Linguistic Complexity Features
        features['lexical_diversity'] = len(set(words)) / max(len(words), 1)
        features['avg_sentence_length'] = np.mean([len(s.split()) for s in sentences if s.strip()])
        features['content_length_normalized'] = np.log1p(len(content_text)) / 10
        
        # 2. Technical Term Density
        technical_terms = self._count_technical_terms(content_text)
        features['technical_term_density'] = technical_terms / max(len(words), 1)
        
        # 3. Emotional Appeal Analysis
        emotion_scores = self._analyze_emotional_content(content_text)
        features.update(emotion_scores)
        
        # 4. Information Architecture
        features['fact_to_opinion_ratio'] = self._compute_fact_opinion_ratio(content_text)
        features['data_point_density'] = self._count_data_points(content_text) / max(len(words), 1)
        features['quote_presence'] = float(self._has_quotes(content_text))
        
        # 5. Newsworthiness Signals
        features['novelty_score'] = self._compute_novelty_score(content_text)
        features['impact_scale'] = self._analyze_impact_scope(content_text)
        features['timeliness_score'] = self._analyze_timeliness(content_text)
        
        # 6. Keyword Analysis
        if keywords:
            features['keyword_density'] = len(keywords) / max(len(words), 1)
            features['keyword_diversity'] = len(set([kw.lower() for kw in keywords])) / max(len(keywords), 1)
        else:
            features['keyword_density'] = 0.0
            features['keyword_diversity'] = 0.0
        
        # 7. Industry Classification Score
        industry_scores = self._classify_industry_content(content_text)
        features.update(industry_scores)
        
        return features
    
    async def _extract_audience_features(self, content_data: Dict, context: Optional[Dict]) -> Dict[str, float]:
        """
        Extract audience signal features
        
        WHY: Audience clarity correlates với media matching accuracy
        - Specific audiences → better media targeting
        - B2B vs B2C affects media choice
        - Geographic scope impacts regional media
        """
        
        target_audiences = content_data.get('target_audiences', []) or []
        audience_info = content_data.get('audience_info', '') or ''
        
        features = {}
        
        # 1. Audience Specificity
        if target_audiences:
            features['audience_count'] = min(len(target_audiences), 10) / 10  # Normalize to 0-1
            features['audience_specificity'] = self._measure_audience_specificity(target_audiences)
        else:
            features['audience_count'] = 0.0
            features['audience_specificity'] = 0.0
        
        # 2. B2B vs B2C Classification
        b2b_score, b2c_score = self._classify_audience_type(target_audiences, audience_info)
        features['b2b_score'] = b2b_score
        features['b2c_score'] = b2c_score
        
        # 3. Geographic Scope
        geo_signals = self._analyze_geographic_scope(content_data.get('geographic_scope', '') or audience_info)
        features.update(geo_signals)
        
        # 4. Demographic Indicators
        demo_signals = self._extract_demographic_signals(audience_info)
        features.update(demo_signals)
        
        # 5. Purchase Intent Signals
        features['purchase_intent_score'] = self._analyze_purchase_intent(audience_info, content_data)
        
        return features
    
    async def _extract_business_features(self, content_data: Dict, additional_context: Optional[Dict]) -> Dict[str, float]:
        """
        Extract business context features
        
        WHY: Business maturity predicts media strategy effectiveness
        - Startups → tech/business media focus
        - Established companies → mainstream media
        - Growth stage → investment/expansion coverage
        """
        
        features = {}
        
        # Get business context
        business_info = additional_context.get('business_context', {}) if additional_context else {}
        industry = content_data.get('industry_sector', '') or content_data.get('industry', '')
        
        # 1. Industry Classification
        industry_encoding = self._encode_industry(industry)
        features.update(industry_encoding)
        
        # 2. Business Stage Indicators
        stage_signals = self._infer_business_stage(content_data, business_info)
        features.update(stage_signals)
        
        # 3. Growth Indicators
        growth_signals = self._analyze_growth_signals(content_data)
        features.update(growth_signals)
        
        # 4. Market Position
        features['market_position_score'] = self._estimate_market_position(content_data, business_info)
        
        # 5. Innovation Index
        features['innovation_score'] = self._compute_innovation_index(content_data)
        
        # 6. Brand Recognition Proxy
        features['brand_recognition_proxy'] = self._estimate_brand_strength(business_info)
        
        return features
    
    async def _extract_timing_features(self, content_data: Dict, additional_context: Optional[Dict]) -> Dict[str, float]:
        """
        Extract market timing features
        
        WHY: Timing affects media receptivity
        - Q4 → holiday/year-end coverage
        - Industry events → increased coverage
        - Economic cycles → media focus shifts
        """
        
        features = {}
        current_time = datetime.now()
        
        # 1. Seasonal Alignment
        features['seasonal_score'] = self._compute_seasonal_relevance(current_time)
        
        # 2. News Cycle Position
        features['news_cycle_score'] = self._assess_news_cycle_timing(current_time)
        
        # 3. Economic Context
        features['economic_timing_score'] = self._analyze_economic_timing(current_time)
        
        # 4. Industry Cycle
        industry = content_data.get('industry_sector', '')
        features['industry_cycle_score'] = self._assess_industry_timing(industry, current_time)
        
        # 5. Holiday/Event Proximity
        features['holiday_proximity_score'] = self._compute_holiday_proximity(current_time)
        
        # 6. Fiscal Calendar Alignment
        features['fiscal_timing_score'] = self._assess_fiscal_timing(current_time)
        
        return features
    
    async def _extract_competitive_features(self, content_data: Dict, additional_context: Optional[Dict]) -> Dict[str, float]:
        """
        Extract competitive landscape features
        
        WHY: Competition level determines media strategy
        - High competition → differentiation focus
        - Low competition → market education
        - Industry maturity → coverage type
        """
        
        features = {}
        industry = content_data.get('industry_sector', '') or content_data.get('industry', '')
        content_text = content_data.get('content', '') or ''
        
        # 1. Competition Intensity
        features['competition_intensity'] = self._assess_competition_intensity(industry, content_text)
        
        # 2. Market Saturation
        features['market_saturation'] = self._estimate_market_saturation(industry)
        
        # 3. Differentiation Difficulty
        features['differentiation_score'] = self._assess_differentiation_challenge(content_text)
        
        # 4. Industry Media Friendliness
        features['media_friendliness'] = self._rate_media_coverage_tendency(industry)
        
        # 5. Regulatory Complexity
        features['regulatory_complexity'] = self._assess_regulatory_environment(industry)
        
        # 6. Innovation Cycle Stage
        features['innovation_cycle_stage'] = self._determine_innovation_maturity(industry)
        
        return features
    
    # =================== HELPER METHODS ===================
    
    def _count_technical_terms(self, text: str) -> int:
        """Count technical/specialized terms in text"""
        technical_patterns = [
            r'\b[A-Z]{2,}\b',  # Acronyms
            r'\b\d+%\b',       # Percentages  
            r'\b\d+[.,]\d+\b', # Numbers with decimals
            r'API|SDK|SaaS|B2B|B2C|AI|ML|IoT', # Tech terms
        ]
        
        count = 0
        for pattern in technical_patterns:
            count += len(re.findall(pattern, text, re.IGNORECASE))
        
        return count
    
    def _analyze_emotional_content(self, text: str) -> Dict[str, float]:
        """Analyze emotional appeal in content"""
        emotion_scores = {}
        
        for emotion, keywords in self.emotion_keywords.items():
            score = 0
            for keyword in keywords:
                score += text.lower().count(keyword)
            
            # Normalize by text length
            emotion_scores[f'{emotion}_score'] = score / max(len(text.split()), 1)
        
        return emotion_scores
    
    def _compute_fact_opinion_ratio(self, text: str) -> float:
        """Compute ratio of factual vs opinion content"""
        fact_indicators = ['theo', 'dữ liệu', 'nghiên cứu', 'báo cáo', 'thống kê', 'số liệu']
        opinion_indicators = ['tôi nghĩ', 'theo ý kiến', 'có thể', 'dự đoán', 'hy vọng']
        
        fact_count = sum(text.lower().count(indicator) for indicator in fact_indicators)
        opinion_count = sum(text.lower().count(indicator) for indicator in opinion_indicators)
        
        if opinion_count == 0:
            return 1.0 if fact_count > 0 else 0.5
        
        return fact_count / (fact_count + opinion_count)
    
    def _count_data_points(self, text: str) -> int:
        """Count data points, statistics, numbers"""
        patterns = [
            r'\b\d+%',           # Percentages
            r'\b\d+[.,]\d+\b',   # Decimal numbers
            r'\b\d+\s*(triệu|tỷ|nghìn)', # Vietnamese number units
            r'\$\d+',            # Dollar amounts
        ]
        
        count = 0
        for pattern in patterns:
            count += len(re.findall(pattern, text))
        
        return count
    
    def _has_quotes(self, text: str) -> bool:
        """Check for presence of quotes or testimonials"""
        quote_indicators = ['"', "'", '"', '"', 'theo lời', 'chia sẻ rằng', 'cho biết']
        return any(indicator in text for indicator in quote_indicators)
    
    def _compute_novelty_score(self, text: str) -> float:
        """Compute novelty/innovation score"""
        novelty_keywords = ['mới', 'đầu tiên', 'chưa từng', 'độc đáo', 'cách mạng', 'đột phá', 'tiên phong']
        score = sum(text.lower().count(keyword) for keyword in novelty_keywords)
        return min(score / max(len(text.split()), 1), 1.0)
    
    def _analyze_impact_scope(self, text: str) -> float:
        """Analyze scope of impact mentioned"""
        scope_keywords = {
            'local': ['địa phương', 'khu vực', 'thành phố'],
            'national': ['toàn quốc', 'Việt Nam', 'cả nước'],
            'international': ['quốc tế', 'toàn cầu', 'thế giới', 'châu Á']
        }
        
        scores = {'local': 0.3, 'national': 0.7, 'international': 1.0}
        
        for scope, keywords in scope_keywords.items():
            if any(keyword in text.lower() for keyword in keywords):
                return scores[scope]
        
        return 0.5  # Default medium scope
    
    def _analyze_timeliness(self, text: str) -> float:
        """Analyze timeliness/urgency of content"""
        time_keywords = ['ngay hôm nay', 'tuần này', 'tháng này', 'sắp tới', 'mới đây', 'vừa qua']
        score = sum(text.lower().count(keyword) for keyword in time_keywords)
        return min(score / max(len(text.split()), 1), 1.0)
    
    def _classify_industry_content(self, text: str) -> Dict[str, float]:
        """Classify industry based on content"""
        industry_scores = {}
        
        for industry, keywords in self.industry_keywords.items():
            score = sum(text.lower().count(keyword) for keyword in keywords)
            industry_scores[f'industry_{industry}_score'] = score / max(len(text.split()), 1)
        
        return industry_scores
    
    def _measure_audience_specificity(self, audiences: List[str]) -> float:
        """Measure how specific the audience targeting is"""
        if not audiences:
            return 0.0
        
        # More specific audiences have longer descriptions
        avg_length = np.mean([len(aud.split()) for aud in audiences])
        specificity = min(avg_length / 5, 1.0)  # Normalize to max 5 words
        
        return specificity
    
    def _classify_audience_type(self, audiences: List[str], audience_info: str) -> tuple:
        """Classify as B2B vs B2C"""
        b2b_keywords = ['doanh nghiệp', 'công ty', 'SME', 'startup', 'nhà đầu tư', 'quản lý']
        b2c_keywords = ['khách hàng', 'người dùng', 'cá nhân', 'gia đình', 'sinh viên']
        
        text = ' '.join(audiences) + ' ' + audience_info
        text = text.lower()
        
        b2b_score = sum(text.count(keyword) for keyword in b2b_keywords)
        b2c_score = sum(text.count(keyword) for keyword in b2c_keywords)
        
        total = b2b_score + b2c_score + 1  # Add 1 to avoid division by zero
        
        return b2b_score / total, b2c_score / total
    
    def _analyze_geographic_scope(self, geo_text: str) -> Dict[str, float]:
        """Analyze geographic scope indicators"""
        regions = {
            'north_vietnam': ['hà nội', 'miền bắc', 'bắc bộ', 'thủ đô'],
            'central_vietnam': ['huế', 'đà nẵng', 'miền trung', 'trung bộ'], 
            'south_vietnam': ['hồ chí minh', 'sài gòn', 'miền nam', 'nam bộ'],
            'national': ['toàn quốc', 'việt nam', 'cả nước'],
            'international': ['quốc tế', 'toàn cầu', 'châu á', 'asean']
        }
        
        geo_features = {}
        text = geo_text.lower()
        
        for region, keywords in regions.items():
            score = sum(text.count(keyword) for keyword in keywords)
            geo_features[f'geo_{region}_score'] = min(score, 1.0)
        
        return geo_features
    
    def _extract_demographic_signals(self, audience_info: str) -> Dict[str, float]:
        """Extract demographic targeting signals"""
        demographics = {
            'young': ['trẻ', 'gen z', 'millennials', '18-25', '20-30'],
            'professional': ['chuyên nghiệp', 'văn phòng', 'manager', 'giám đốc'],
            'tech_savvy': ['công nghệ', 'digital', 'online', 'app', 'internet'],
            'affluent': ['cao cấp', 'premium', 'luxury', 'thu nhập cao']
        }
        
        demo_features = {}
        text = audience_info.lower()
        
        for demo, keywords in demographics.items():
            score = sum(text.count(keyword) for keyword in keywords)
            demo_features[f'demo_{demo}_score'] = min(score / max(len(text.split()), 1), 1.0)
        
        return demo_features
    
    def _analyze_purchase_intent(self, audience_info: str, content_data: Dict) -> float:
        """Analyze purchase intent signals"""
        intent_keywords = ['mua', 'đầu tư', 'quyết định', 'lựa chọn', 'so sánh', 'tìm kiếm']
        
        text = audience_info + ' ' + content_data.get('content', '')
        text = text.lower()
        
        intent_score = sum(text.count(keyword) for keyword in intent_keywords)
        return min(intent_score / max(len(text.split()), 1), 1.0)
    
    def _encode_industry(self, industry: str) -> Dict[str, float]:
        """One-hot encode industry with confidence scores"""
        industry_mapping = {
            'technology': 'tech',
            'finance': 'finance', 
            'healthcare': 'health',
            'education': 'education',
            'retail': 'retail',
            'manufacturing': 'manufacturing',
            'tourism': 'tourism'
        }
        
        industry_features = {}
        industry_lower = industry.lower()
        
        # Check exact matches first
        for key, value in industry_mapping.items():
            if key in industry_lower or value in industry_lower:
                industry_features[f'industry_is_{value}'] = 1.0
            else:
                industry_features[f'industry_is_{value}'] = 0.0
        
        return industry_features
    
    def _infer_business_stage(self, content_data: Dict, business_info: Dict) -> Dict[str, float]:
        """Infer business stage from content signals"""
        stages = {
            'startup': ['startup', 'khởi nghiệp', 'mới thành lập', 'vòng gọi vốn'],
            'growth': ['tăng trưởng', 'mở rộng', 'phát triển', 'scale up'],
            'mature': ['thành lập', 'kinh nghiệm', 'dẫn đầu', 'ổn định']
        }
        
        content_text = content_data.get('content', '') + ' ' + str(business_info)
        content_text = content_text.lower()
        
        stage_features = {}
        for stage, keywords in stages.items():
            score = sum(content_text.count(keyword) for keyword in keywords)
            stage_features[f'business_stage_{stage}'] = min(score / max(len(content_text.split()), 1), 1.0)
        
        return stage_features
    
    def _analyze_growth_signals(self, content_data: Dict) -> Dict[str, float]:
        """Analyze growth trajectory signals"""
        growth_keywords = ['tăng trưởng', 'mở rộng', 'phát triển', 'gia tăng', 'nâng cao']
        expansion_keywords = ['chi nhánh', 'thị trường mới', 'sản phẩm mới', 'dịch vụ mới']
        
        content_text = content_data.get('content', '').lower()
        
        growth_score = sum(content_text.count(keyword) for keyword in growth_keywords)
        expansion_score = sum(content_text.count(keyword) for keyword in expansion_keywords)
        
        return {
            'growth_signals': min(growth_score / max(len(content_text.split()), 1), 1.0),
            'expansion_signals': min(expansion_score / max(len(content_text.split()), 1), 1.0)
        }
    
    def _estimate_market_position(self, content_data: Dict, business_info: Dict) -> float:
        """Estimate market position strength"""
        position_keywords = ['dẫn đầu', 'hàng đầu', 'số 1', 'top', 'uy tín', 'thương hiệu']
        
        text = content_data.get('content', '') + ' ' + str(business_info)
        text = text.lower()
        
        position_score = sum(text.count(keyword) for keyword in position_keywords)
        return min(position_score / max(len(text.split()), 1), 1.0)
    
    def _compute_innovation_index(self, content_data: Dict) -> float:
        """Compute innovation score"""
        innovation_keywords = ['đổi mới', 'sáng tạo', 'cải tiến', 'phát minh', 'nghiên cứu']
        
        content_text = content_data.get('content', '').lower()
        innovation_score = sum(content_text.count(keyword) for keyword in innovation_keywords)
        
        return min(innovation_score / max(len(content_text.split()), 1), 1.0)
    
    def _estimate_brand_strength(self, business_info: Dict) -> float:
        """Estimate brand recognition strength"""
        # This would ideally use external data, but we'll use proxy indicators
        strength_indicators = ['thương hiệu', 'nổi tiếng', 'uy tín', 'biết đến']
        
        text = str(business_info).lower()
        strength_score = sum(text.count(indicator) for indicator in strength_indicators)
        
        return min(strength_score / max(len(text.split()), 1), 1.0)
    
    # Timing feature helpers
    def _compute_seasonal_relevance(self, current_time: datetime) -> float:
        """Compute seasonal timing relevance"""
        month = current_time.month
        
        # Vietnamese business seasons
        if month in [1, 2]:  # Tết season
            return 0.9
        elif month in [3, 4, 5]:  # Spring business season
            return 0.8
        elif month in [9, 10, 11]:  # Fall business peak
            return 0.8
        elif month in [6, 7, 8]:  # Summer slower period
            return 0.6
        else:  # Q4 year-end push
            return 0.9
    
    def _assess_news_cycle_timing(self, current_time: datetime) -> float:
        """Assess news cycle timing favorability"""
        # Simplified: weekdays are better than weekends
        weekday = current_time.weekday()
        if weekday in [0, 1, 2, 3]:  # Mon-Thu
            return 0.8
        elif weekday == 4:  # Friday
            return 0.6
        else:  # Weekend
            return 0.4
    
    def _analyze_economic_timing(self, current_time: datetime) -> float:
        """Analyze economic timing context"""
        # This would ideally integrate with economic indicators
        # For now, return moderate score
        return 0.7
    
    def _assess_industry_timing(self, industry: str, current_time: datetime) -> float:
        """Assess industry-specific timing"""
        month = current_time.month
        
        industry_seasons = {
            'tech': {1: 0.9, 4: 0.8, 9: 0.9, 12: 0.7},  # CES, events
            'finance': {1: 0.9, 4: 0.8, 7: 0.6, 10: 0.8}, # Quarterly reports
            'retail': {3: 0.7, 6: 0.6, 9: 0.8, 11: 0.9},  # Shopping seasons
            'education': {8: 0.9, 9: 0.9, 1: 0.8, 6: 0.6} # School cycles
        }
        
        for ind_key, seasons in industry_seasons.items():
            if ind_key in industry.lower():
                return seasons.get(month, 0.7)
        
        return 0.7  # Default moderate timing
    
    def _compute_holiday_proximity(self, current_time: datetime) -> float:
        """Compute proximity to major Vietnamese holidays"""
        # Major Vietnamese holidays (approximate dates)
        holidays = [
            (1, 1),   # New Year
            (4, 30),  # Liberation Day  
            (5, 1),   # Labor Day
            (9, 2),   # National Day
        ]
        
        current_date = (current_time.month, current_time.day)
        
        min_distance = float('inf')
        for holiday in holidays:
            # Simple distance calculation
            distance = abs(current_date[0] - holiday[0]) * 30 + abs(current_date[1] - holiday[1])
            min_distance = min(min_distance, distance)
        
        # Convert to 0-1 score (closer to holiday = higher score)
        return max(0, 1 - min_distance / 365)
    
    def _assess_fiscal_timing(self, current_time: datetime) -> float:
        """Assess fiscal calendar timing"""
        month = current_time.month
        
        # Q1: Jan-Mar, Q2: Apr-Jun, Q3: Jul-Sep, Q4: Oct-Dec
        quarter_scores = {
            1: 0.9, 2: 0.8, 3: 0.8,  # Q1 - planning season
            4: 0.8, 5: 0.7, 6: 0.6,  # Q2 - execution
            7: 0.6, 8: 0.6, 9: 0.7,  # Q3 - mid-year
            10: 0.8, 11: 0.9, 12: 0.9 # Q4 - year-end push
        }
        
        return quarter_scores.get(month, 0.7)
    
    # Competitive feature helpers
    def _assess_competition_intensity(self, industry: str, content_text: str) -> float:
        """Assess competition intensity in industry"""
        high_competition_industries = ['tech', 'finance', 'retail', 'food']
        medium_competition_industries = ['health', 'education', 'manufacturing']
        low_competition_industries = ['government', 'utilities', 'specialized']
        
        industry_lower = industry.lower()
        
        for ind in high_competition_industries:
            if ind in industry_lower:
                return 0.8
        
        for ind in medium_competition_industries:
            if ind in industry_lower:
                return 0.6
                
        for ind in low_competition_industries:
            if ind in industry_lower:
                return 0.4
        
        # Check content for competition signals
        competition_signals = sum(content_text.lower().count(keyword) for keyword in self.competition_keywords['high'])
        if competition_signals > 0:
            return min(0.8, 0.5 + competition_signals / 10)
        
        return 0.6  # Default medium competition
    
    def _estimate_market_saturation(self, industry: str) -> float:
        """Estimate market saturation level"""
        # Simplified industry saturation mapping
        saturation_map = {
            'tech': 0.7,
            'finance': 0.8,
            'retail': 0.9,
            'health': 0.6,
            'education': 0.5,
            'manufacturing': 0.7,
            'tourism': 0.6
        }
        
        industry_lower = industry.lower()
        for key, value in saturation_map.items():
            if key in industry_lower:
                return value
        
        return 0.6  # Default moderate saturation
    
    def _assess_differentiation_challenge(self, content_text: str) -> float:
        """Assess how challenging differentiation is"""
        differentiation_keywords = ['độc đáo', 'khác biệt', 'đặc biệt', 'riêng', 'duy nhất']
        commodity_keywords = ['chuẩn', 'thông thường', 'phổ biến', 'giống', 'tương tự']
        
        diff_score = sum(content_text.lower().count(keyword) for keyword in differentiation_keywords)
        commodity_score = sum(content_text.lower().count(keyword) for keyword in commodity_keywords)
        
        if diff_score > commodity_score:
            return 0.3  # Easy to differentiate
        elif commodity_score > diff_score:
            return 0.8  # Hard to differentiate
        else:
            return 0.6  # Moderate difficulty
    
    def _rate_media_coverage_tendency(self, industry: str) -> float:
        """Rate how media-friendly an industry is"""
        media_friendly = ['tech', 'finance', 'startup', 'innovation']
        moderately_friendly = ['health', 'education', 'retail']
        less_friendly = ['manufacturing', 'logistics', 'utilities']
        
        industry_lower = industry.lower()
        
        for ind in media_friendly:
            if ind in industry_lower:
                return 0.8
        
        for ind in moderately_friendly:
            if ind in industry_lower:
                return 0.6
                
        for ind in less_friendly:
            if ind in industry_lower:
                return 0.4
        
        return 0.6  # Default moderate
    
    def _assess_regulatory_environment(self, industry: str) -> float:
        """Assess regulatory complexity"""
        highly_regulated = ['finance', 'health', 'pharma', 'banking', 'insurance']
        moderately_regulated = ['education', 'food', 'transportation']
        less_regulated = ['tech', 'retail', 'consulting', 'media']
        
        industry_lower = industry.lower()
        
        for ind in highly_regulated:
            if ind in industry_lower:
                return 0.9
        
        for ind in moderately_regulated:
            if ind in industry_lower:
                return 0.6
                
        for ind in less_regulated:
            if ind in industry_lower:
                return 0.3
        
        return 0.6  # Default moderate
    
    def _determine_innovation_maturity(self, industry: str) -> float:
        """Determine where industry is in innovation cycle"""
        emerging_industries = ['ai', 'blockchain', 'vr', 'iot', 'fintech']
        growth_industries = ['ecommerce', 'saas', 'digital', 'mobile']
        mature_industries = ['banking', 'manufacturing', 'retail', 'insurance']
        
        industry_lower = industry.lower()
        
        for ind in emerging_industries:
            if ind in industry_lower:
                return 0.9  # High innovation
        
        for ind in growth_industries:
            if ind in industry_lower:
                return 0.7  # Moderate innovation
                
        for ind in mature_industries:
            if ind in industry_lower:
                return 0.4  # Lower innovation
        
        return 0.6  # Default moderate innovation