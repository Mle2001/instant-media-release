"""
Basic functionality tests to verify all ML modules work correctly
"""

import pytest
import numpy as np
from datetime import datetime
import asyncio

def test_basic_imports():
    """Test that all ML modules can be imported"""
    try:
        from ml_ranking_system.universal_features import UniversalStructureExtractor
        from ml_ranking_system.ground_truth_collector import GroundTruthKPICollector
        assert True, "Basic imports successful"
    except ImportError as e:
        pytest.fail(f"Import failed: {e}")

def test_universal_extractor_basic():
    """Test basic Universal Structure Extractor functionality"""
    from ml_ranking_system.universal_features import UniversalStructureExtractor
    
    extractor = UniversalStructureExtractor()
    assert extractor is not None
    assert hasattr(extractor, 'industry_keywords')
    assert hasattr(extractor, 'emotion_keywords')
    assert len(extractor.industry_keywords) > 0

def test_ground_truth_collector_basic():
    """Test basic Ground Truth Collector functionality"""
    from ml_ranking_system.ground_truth_collector import GroundTruthKPICollector
    
    collector = GroundTruthKPICollector()
    assert collector is not None
    assert hasattr(collector, 'kpi_weights')
    assert abs(sum(collector.kpi_weights.values()) - 1.0) < 0.001  # Allow for floating point precision

@pytest.mark.asyncio
async def test_feature_extraction_basic():
    """Test basic feature extraction"""
    from ml_ranking_system.universal_features import UniversalStructureExtractor
    
    extractor = UniversalStructureExtractor()
    
    # Create a mock ContentAnalysis object
    class MockContentAnalysis:
        def __init__(self):
            self.title = "Test title"
            self.content_preview = "Test content about technology and innovation"
            self.content = "Test content about technology and innovation. This is a longer text for feature extraction."
            self.industry_sector = "technology"
            self.primary_topics = ["tech", "innovation"]
            self.target_audiences = ["businesses"]
            self.campaign_type = "product_launch"
            self.language = "vietnamese"
            self.sentiment_score = 0.7
    
    content_analysis = MockContentAnalysis()
    
    # Create conversation context
    conversation_context = {
        "budget": 10000000,
        "target_media_types": ["technology"],
        "campaign_duration_days": 30
    }
    
    additional_context = {
        "competitor_campaigns": [],
        "market_events": [],
        "industry_trends": ["digital_transformation"]
    }
    
    features = await extractor.extract_universal_features(
        content_analysis=content_analysis,
        conversation_context=conversation_context,
        additional_context=additional_context
    )
    
    assert features is not None
    vector = features.to_vector()
    assert isinstance(vector, np.ndarray)
    assert len(vector) > 30  # At least 30 features, exact number may vary
    assert not np.isnan(vector).any()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])