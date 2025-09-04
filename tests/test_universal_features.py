"""
Comprehensive tests for Universal Structure Extractor
Testing all feature extraction capabilities and Vietnamese language support
"""

import pytest
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Import the module to test
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from ml_ranking_system.universal_features import (
    UniversalStructureExtractor,
    UniversalFeatures,
    ContentFeatures,
    AudienceFeatures,
    BusinessFeatures,
    TimingFeatures,
    CompetitiveFeatures
)


class TestUniversalStructureExtractor:
    """Test suite for Universal Structure Extractor"""

    @pytest.fixture
    def extractor(self):
        """Create extractor instance"""
        return UniversalStructureExtractor()

    @pytest.fixture
    def sample_content_vietnamese(self):
        """Sample Vietnamese content for testing"""
        return {
            "title": "Công ty Fintech VietPay ra mắt ứng dụng thanh toán mới cho SME",
            "content": """
            VietPay, một startup fintech hàng đầu tại Việt Nam, vừa chính thức ra mắt 
            ứng dụng thanh toán di động mới nhằm phục vụ các doanh nghiệp vừa và nhỏ (SME). 
            Ứng dụng này được thiết kế để giúp các SME quản lý tài chính hiệu quả hơn, 
            với các tính năng thanh toán không tiếp xúc, quản lý dòng tiền và báo cáo tài chính tự động.
            
            Theo ông Nguyễn Văn A, CEO của VietPay, "Chúng tôi tin rằng công nghệ fintech 
            sẽ thay đổi cách thức kinh doanh của các SME tại Việt Nam. Ứng dụng mới này 
            không chỉ giúp tiết kiệm thời gian mà còn giảm chi phí vận hành đáng kể."
            
            VietPay hiện đang phục vụ hơn 50,000 doanh nghiệp nhỏ trên khắp Việt Nam 
            và dự kiến mở rộng ra thị trường Đông Nam Á trong năm 2025.
            """,
            "industry": "fintech",
            "keywords": ["fintech", "thanh toán", "SME", "startup", "công nghệ"],
            "target_audience": ["doanh nghiệp nhỏ", "SME", "chủ doanh nghiệp"],
            "announcement_type": "product_launch"
        }

    @pytest.fixture
    def sample_content_english(self):
        """Sample English content for testing"""
        return {
            "title": "VietPay Fintech Company Launches New Payment App for SMEs",
            "content": """
            VietPay, a leading fintech startup in Vietnam, has officially launched 
            a new mobile payment application targeting small and medium enterprises (SMEs). 
            The app is designed to help SMEs manage their finances more efficiently, 
            featuring contactless payments, cash flow management, and automated financial reporting.
            
            According to Mr. Nguyen Van A, CEO of VietPay, "We believe that fintech technology 
            will change the way SMEs do business in Vietnam. This new app not only saves time 
            but also significantly reduces operational costs."
            
            VietPay currently serves over 50,000 small businesses across Vietnam 
            and plans to expand to Southeast Asian markets in 2025.
            """,
            "industry": "fintech",
            "keywords": ["fintech", "payment", "SME", "startup", "technology"],
            "target_audience": ["small businesses", "SME", "business owners"],
            "announcement_type": "product_launch"
        }

    @pytest.fixture
    def sample_media_context(self):
        """Sample media context data"""
        return {
            "budget": 30000000,  # 30 million VND
            "target_media_types": ["business", "technology", "mainstream"],
            "campaign_duration_days": 30,
            "desired_reach": 1000000,
            "geographic_focus": ["ho_chi_minh", "ha_noi"],
            "urgency_level": "high"
        }

    @pytest.fixture
    def sample_competitive_context(self):
        """Sample competitive landscape data"""
        return {
            "competitor_campaigns": [
                {
                    "company": "PayTech Vietnam",
                    "campaign_type": "product_launch",
                    "media_spend": 25000000,
                    "launch_date": "2024-01-15"
                },
                {
                    "company": "FinanceApp Pro",
                    "campaign_type": "feature_update",
                    "media_spend": 15000000,
                    "launch_date": "2024-02-01"
                }
            ],
            "market_events": [
                {
                    "event": "Vietnam Fintech Week",
                    "date": "2024-03-15",
                    "impact": "high"
                }
            ],
            "industry_trends": ["digital_transformation", "cashless_payments", "sme_focus"]
        }

    def test_extractor_initialization(self, extractor):
        """Test that extractor initializes properly"""
        assert extractor is not None
        assert hasattr(extractor, 'vietnamese_keywords')
        assert hasattr(extractor, 'industry_keywords')
        assert len(extractor.vietnamese_keywords) > 0
        assert len(extractor.industry_keywords) > 0

    def test_extract_universal_features_vietnamese(self, extractor, sample_content_vietnamese, 
                                                  sample_media_context, sample_competitive_context):
        """Test feature extraction with Vietnamese content"""
        features = extractor.extract_universal_features(
            content=sample_content_vietnamese,
            media_context=sample_media_context,
            competitive_context=sample_competitive_context
        )
        
        # Test return type
        assert isinstance(features, UniversalFeatures)
        
        # Test content features
        assert features.content.language_score > 0.5  # Should detect Vietnamese
        assert features.content.industry_relevance > 0.0
        assert len(features.content.key_topics) > 0
        assert features.content.sentiment_score is not None
        assert features.content.urgency_score > 0.0  # Should detect urgency keywords
        
        # Test audience features
        assert features.audience.demographic_match > 0.0
        assert features.audience.interest_alignment > 0.0
        assert len(features.audience.target_segments) > 0
        
        # Test business features
        assert features.business.budget_efficiency > 0.0
        assert features.business.roi_potential > 0.0
        assert features.business.market_opportunity > 0.0
        
        # Test timing features
        assert features.timing.market_readiness > 0.0
        assert features.timing.competitive_timing > 0.0
        assert features.timing.seasonal_relevance >= 0.0
        
        # Test competitive features
        assert features.competitive.differentiation_score > 0.0
        assert features.competitive.market_share_potential > 0.0
        assert features.competitive.competitive_advantage >= 0.0

    def test_extract_universal_features_english(self, extractor, sample_content_english,
                                               sample_media_context, sample_competitive_context):
        """Test feature extraction with English content"""
        features = extractor.extract_universal_features(
            content=sample_content_english,
            media_context=sample_media_context,
            competitive_context=sample_competitive_context
        )
        
        assert isinstance(features, UniversalFeatures)
        assert features.content.language_score >= 0.0  # Should handle English
        assert features.content.industry_relevance > 0.0
        assert len(features.content.key_topics) > 0

    def test_feature_vector_conversion(self, extractor, sample_content_vietnamese,
                                     sample_media_context, sample_competitive_context):
        """Test conversion to feature vector"""
        features = extractor.extract_universal_features(
            content=sample_content_vietnamese,
            media_context=sample_media_context,
            competitive_context=sample_competitive_context
        )
        
        vector = features.to_vector()
        
        # Test vector properties
        assert isinstance(vector, np.ndarray)
        assert vector.dtype == np.float32
        assert len(vector) == 50  # Expected feature dimension
        assert not np.isnan(vector).any()  # No NaN values
        assert np.isfinite(vector).all()  # All finite values
        assert (vector >= 0).all() and (vector <= 1).all()  # Normalized values

    def test_content_features_extraction(self, extractor):
        """Test content features extraction specifically"""
        content = {
            "title": "Khẩn cấp: Công ty công nghệ mới ra mắt sản phẩm AI đột phá",
            "content": "Đây là một sản phẩm AI rất tuyệt vời và cách mạng cho thị trường Việt Nam.",
            "industry": "technology",
            "keywords": ["AI", "công nghệ", "đột phá"],
            "announcement_type": "product_launch"
        }
        
        content_features = extractor._extract_content_features(content)
        
        assert isinstance(content_features, ContentFeatures)
        assert content_features.word_count > 0
        assert content_features.language_score > 0.5  # Vietnamese content
        assert content_features.urgency_score > 0.5  # "Khẩn cấp" keyword
        assert content_features.sentiment_score is not None
        assert content_features.industry_relevance > 0.0
        assert len(content_features.key_topics) > 0

    def test_audience_features_extraction(self, extractor, sample_media_context):
        """Test audience features extraction"""
        content = {
            "target_audience": ["doanh nghiệp nhỏ", "startup", "SME"],
            "industry": "fintech"
        }
        
        audience_features = extractor._extract_audience_features(content, sample_media_context)
        
        assert isinstance(audience_features, AudienceFeatures)
        assert audience_features.demographic_match > 0.0
        assert audience_features.interest_alignment > 0.0
        assert audience_features.geographic_relevance > 0.0
        assert len(audience_features.target_segments) > 0

    def test_business_features_extraction(self, extractor, sample_media_context):
        """Test business features extraction"""
        content = {"industry": "fintech", "announcement_type": "product_launch"}
        
        business_features = extractor._extract_business_features(content, sample_media_context)
        
        assert isinstance(business_features, BusinessFeatures)
        assert business_features.budget_efficiency > 0.0
        assert business_features.roi_potential > 0.0
        assert business_features.market_opportunity > 0.0
        assert business_features.urgency_level > 0.0

    def test_timing_features_extraction(self, extractor, sample_competitive_context):
        """Test timing features extraction"""
        timing_features = extractor._extract_timing_features(sample_competitive_context)
        
        assert isinstance(timing_features, TimingFeatures)
        assert timing_features.market_readiness >= 0.0
        assert timing_features.competitive_timing >= 0.0
        assert timing_features.seasonal_relevance >= 0.0
        assert timing_features.news_cycle_fit >= 0.0

    def test_competitive_features_extraction(self, extractor, sample_competitive_context):
        """Test competitive features extraction"""
        content = {"industry": "fintech", "keywords": ["AI", "fintech", "innovation"]}
        
        competitive_features = extractor._extract_competitive_features(content, sample_competitive_context)
        
        assert isinstance(competitive_features, CompetitiveFeatures)
        assert competitive_features.differentiation_score >= 0.0
        assert competitive_features.market_share_potential >= 0.0
        assert competitive_features.competitive_advantage >= 0.0

    def test_vietnamese_keyword_detection(self, extractor):
        """Test Vietnamese keyword detection"""
        content = "Công ty công nghệ khẩn cấp ra mắt sản phẩm AI đột phá tuyệt vời"
        
        # Test urgency detection
        urgency_score = extractor._calculate_urgency_score(content)
        assert urgency_score > 0.5  # Should detect "khẩn cấp"
        
        # Test positive sentiment keywords
        sentiment_keywords = extractor._extract_sentiment_keywords(content)
        assert len(sentiment_keywords) > 0

    def test_industry_relevance_calculation(self, extractor):
        """Test industry relevance calculation"""
        content = {
            "industry": "technology",
            "keywords": ["AI", "machine learning", "innovation"],
            "title": "AI breakthrough in fintech"
        }
        
        relevance = extractor._calculate_industry_relevance(content)
        assert 0.0 <= relevance <= 1.0
        assert relevance > 0.5  # Should have high relevance for tech content

    def test_error_handling_empty_content(self, extractor):
        """Test error handling with empty content"""
        empty_content = {"title": "", "content": "", "industry": ""}
        empty_context = {}
        
        features = extractor.extract_universal_features(
            content=empty_content,
            media_context=empty_context,
            competitive_context={}
        )
        
        # Should not crash and return valid features
        assert isinstance(features, UniversalFeatures)
        vector = features.to_vector()
        assert isinstance(vector, np.ndarray)
        assert not np.isnan(vector).any()

    def test_error_handling_missing_keys(self, extractor):
        """Test error handling with missing keys"""
        incomplete_content = {"title": "Test title"}
        
        features = extractor.extract_universal_features(
            content=incomplete_content,
            media_context={},
            competitive_context={}
        )
        
        # Should handle missing keys gracefully
        assert isinstance(features, UniversalFeatures)
        vector = features.to_vector()
        assert len(vector) == 50

    def test_feature_consistency(self, extractor, sample_content_vietnamese,
                                sample_media_context, sample_competitive_context):
        """Test that feature extraction is consistent across multiple calls"""
        features1 = extractor.extract_universal_features(
            content=sample_content_vietnamese,
            media_context=sample_media_context,
            competitive_context=sample_competitive_context
        )
        
        features2 = extractor.extract_universal_features(
            content=sample_content_vietnamese,
            media_context=sample_media_context,
            competitive_context=sample_competitive_context
        )
        
        vector1 = features1.to_vector()
        vector2 = features2.to_vector()
        
        # Features should be identical for same input
        np.testing.assert_array_almost_equal(vector1, vector2, decimal=6)

    def test_all_feature_categories_present(self, extractor, sample_content_vietnamese,
                                           sample_media_context, sample_competitive_context):
        """Test that all feature categories are properly extracted"""
        features = extractor.extract_universal_features(
            content=sample_content_vietnamese,
            media_context=sample_media_context,
            competitive_context=sample_competitive_context
        )
        
        # Verify all feature categories exist
        assert hasattr(features, 'content')
        assert hasattr(features, 'audience')
        assert hasattr(features, 'business')
        assert hasattr(features, 'timing')
        assert hasattr(features, 'competitive')
        
        # Verify each category has expected attributes
        content_attrs = ['word_count', 'language_score', 'industry_relevance', 
                        'sentiment_score', 'urgency_score', 'key_topics']
        for attr in content_attrs:
            assert hasattr(features.content, attr)

    @pytest.mark.parametrize("industry", ["technology", "fintech", "healthcare", "retail"])
    def test_different_industries(self, extractor, industry, sample_media_context, 
                                 sample_competitive_context):
        """Test feature extraction for different industries"""
        content = {
            "title": f"New {industry} product launch",
            "content": f"This is a revolutionary {industry} solution for businesses.",
            "industry": industry,
            "keywords": [industry, "innovation", "business"],
            "announcement_type": "product_launch"
        }
        
        features = extractor.extract_universal_features(
            content=content,
            media_context=sample_media_context,
            competitive_context=sample_competitive_context
        )
        
        assert isinstance(features, UniversalFeatures)
        assert features.content.industry_relevance > 0.0
        vector = features.to_vector()
        assert len(vector) == 50
        assert not np.isnan(vector).any()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])