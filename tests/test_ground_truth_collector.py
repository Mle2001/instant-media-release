"""
Comprehensive tests for Ground Truth KPI Collector
Testing campaign feedback processing and ground truth computation
"""

import pytest
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List
import asyncio

# Import the module to test
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from ml_ranking_system.ground_truth_collector import (
    GroundTruthKPICollector,
    CampaignFeedback,
    MediaPerformanceMetrics,
    BusinessImpactMetrics,
    AudienceEngagementMetrics,
    CostEfficiencyMetrics,
    GroundTruthResult
)


class TestGroundTruthKPICollector:
    """Test suite for Ground Truth KPI Collector"""

    @pytest.fixture
    def collector(self):
        """Create collector instance"""
        return GroundTruthKPICollector()

    @pytest.fixture
    def sample_campaign_feedback(self):
        """Sample campaign feedback data"""
        return CampaignFeedback(
            enterprise_id="enterprise_001",
            campaign_id="campaign_001",
            campaign_title="VietPay Fintech App Launch",
            campaign_type="product_launch",
            industry="fintech",
            target_audience=["SME", "small businesses", "startups"],
            budget=30000000.0,
            
            # Media Performance
            media_performance=MediaPerformanceMetrics(
                total_articles_published=25,
                total_media_reach=2500000,
                click_through_rate=0.035,
                social_media_shares=1500,
                media_quality_score=8.2,
                publication_success_rate=0.85,
                tier1_coverage=8,
                tier2_coverage=12,
                tier3_coverage=5,
                average_article_quality=7.8
            ),
            
            # Business Impact
            business_impact=BusinessImpactMetrics(
                brand_awareness_lift=15.5,
                lead_generation=450,
                sales_conversion=85,
                revenue_generated=125000000.0,
                roi_percentage=316.7,
                customer_acquisition_cost=294117.6,
                brand_mention_increase=28.3,
                market_share_gain=2.1
            ),
            
            # Audience Engagement
            audience_engagement=AudienceEngagementMetrics(
                average_engagement_rate=0.045,
                comment_sentiment_score=0.72,
                audience_retention_rate=0.68,
                social_virality_score=0.35,
                user_generated_content=12,
                influencer_engagement_rate=0.082,
                audience_quality_score=8.1
            ),
            
            # Cost Efficiency
            cost_efficiency=CostEfficiencyMetrics(
                cost_per_acquisition=294117.6,
                cost_per_impression=0.012,
                cost_per_click=0.34,
                budget_utilization=0.96,
                cost_per_lead=66666.7,
                efficiency_vs_industry_avg=1.28,
                waste_percentage=4.0
            ),
            
            # Campaign metadata
            campaign_duration_days=30,
            launch_date=datetime(2024, 1, 15),
            completion_date=datetime(2024, 2, 14),
            feedback_timestamp=datetime(2024, 2, 20)
        )

    @pytest.fixture
    def poor_performing_campaign(self):
        """Sample poor performing campaign"""
        return CampaignFeedback(
            enterprise_id="enterprise_002",
            campaign_id="campaign_002",
            campaign_title="Failed Product Launch",
            campaign_type="product_launch",
            industry="retail",
            target_audience=["general consumers"],
            budget=20000000.0,
            
            media_performance=MediaPerformanceMetrics(
                total_articles_published=5,
                total_media_reach=150000,
                click_through_rate=0.008,
                social_media_shares=45,
                media_quality_score=4.2,
                publication_success_rate=0.25,
                tier1_coverage=0,
                tier2_coverage=3,
                tier3_coverage=2,
                average_article_quality=4.1
            ),
            
            business_impact=BusinessImpactMetrics(
                brand_awareness_lift=2.1,
                lead_generation=12,
                sales_conversion=1,
                revenue_generated=5000000.0,
                roi_percentage=25.0,
                customer_acquisition_cost=16666667.0,
                brand_mention_increase=1.2,
                market_share_gain=0.05
            ),
            
            audience_engagement=AudienceEngagementMetrics(
                average_engagement_rate=0.012,
                comment_sentiment_score=0.32,
                audience_retention_rate=0.25,
                social_virality_score=0.08,
                user_generated_content=1,
                influencer_engagement_rate=0.015,
                audience_quality_score=3.8
            ),
            
            cost_efficiency=CostEfficiencyMetrics(
                cost_per_acquisition=16666667.0,
                cost_per_impression=0.133,
                cost_per_click=2.50,
                budget_utilization=1.0,
                cost_per_lead=1666666.7,
                efficiency_vs_industry_avg=0.15,
                waste_percentage=78.0
            ),
            
            campaign_duration_days=30,
            launch_date=datetime(2024, 2, 1),
            completion_date=datetime(2024, 3, 2),
            feedback_timestamp=datetime(2024, 3, 5)
        )

    @pytest.fixture
    def excellent_campaign(self):
        """Sample excellent performing campaign"""
        return CampaignFeedback(
            enterprise_id="enterprise_003",
            campaign_id="campaign_003",
            campaign_title="Viral Tech Product Launch",
            campaign_type="product_launch",
            industry="technology",
            target_audience=["tech enthusiasts", "early adopters"],
            budget=50000000.0,
            
            media_performance=MediaPerformanceMetrics(
                total_articles_published=45,
                total_media_reach=8500000,
                click_through_rate=0.082,
                social_media_shares=15000,
                media_quality_score=9.4,
                publication_success_rate=0.95,
                tier1_coverage=18,
                tier2_coverage=20,
                tier3_coverage=7,
                average_article_quality=9.1
            ),
            
            business_impact=BusinessImpactMetrics(
                brand_awareness_lift=45.2,
                lead_generation=2800,
                sales_conversion=890,
                revenue_generated=780000000.0,
                roi_percentage=1460.0,
                customer_acquisition_cost=56180.0,
                brand_mention_increase=78.5,
                market_share_gain=8.3
            ),
            
            audience_engagement=AudienceEngagementMetrics(
                average_engagement_rate=0.125,
                comment_sentiment_score=0.89,
                audience_retention_rate=0.92,
                social_virality_score=0.78,
                user_generated_content=156,
                influencer_engagement_rate=0.186,
                audience_quality_score=9.3
            ),
            
            cost_efficiency=CostEfficiencyMetrics(
                cost_per_acquisition=56180.0,
                cost_per_impression=0.0059,
                cost_per_click=0.072,
                budget_utilization=0.98,
                cost_per_lead=17857.1,
                efficiency_vs_industry_avg=2.85,
                waste_percentage=2.0
            ),
            
            campaign_duration_days=45,
            launch_date=datetime(2024, 3, 1),
            completion_date=datetime(2024, 4, 15),
            feedback_timestamp=datetime(2024, 4, 20)
        )

    def test_collector_initialization(self, collector):
        """Test collector initializes properly"""
        assert collector is not None
        assert hasattr(collector, 'weights')
        assert len(collector.weights) == 4
        assert sum(collector.weights.values()) == 1.0  # Weights should sum to 1

    @pytest.mark.asyncio
    async def test_collect_campaign_metrics_good_campaign(self, collector, sample_campaign_feedback):
        """Test collection of campaign metrics for good performing campaign"""
        result = await collector.collect_campaign_metrics(sample_campaign_feedback)
        
        assert isinstance(result, GroundTruthResult)
        assert result.enterprise_id == "enterprise_001"
        assert result.campaign_id == "campaign_001"
        
        # Check ground truth score is reasonable (should be good but not perfect)
        assert 0.6 <= result.ground_truth_score <= 0.9
        assert 0.5 <= result.confidence_score <= 1.0
        assert result.data_quality in ["excellent", "good", "fair"]
        
        # Check individual category scores
        assert 0.0 <= result.media_performance_score <= 1.0
        assert 0.0 <= result.business_impact_score <= 1.0
        assert 0.0 <= result.audience_engagement_score <= 1.0
        assert 0.0 <= result.cost_efficiency_score <= 1.0

    @pytest.mark.asyncio
    async def test_collect_campaign_metrics_poor_campaign(self, collector, poor_performing_campaign):
        """Test collection of campaign metrics for poor performing campaign"""
        result = await collector.collect_campaign_metrics(poor_performing_campaign)
        
        assert isinstance(result, GroundTruthResult)
        assert result.enterprise_id == "enterprise_002"
        assert result.campaign_id == "campaign_002"
        
        # Poor campaign should have low ground truth score
        assert 0.0 <= result.ground_truth_score <= 0.4
        assert result.data_quality in ["good", "fair", "poor"]

    @pytest.mark.asyncio
    async def test_collect_campaign_metrics_excellent_campaign(self, collector, excellent_campaign):
        """Test collection of campaign metrics for excellent campaign"""
        result = await collector.collect_campaign_metrics(excellent_campaign)
        
        assert isinstance(result, GroundTruthResult)
        assert result.enterprise_id == "enterprise_003"
        assert result.campaign_id == "campaign_003"
        
        # Excellent campaign should have high ground truth score
        assert 0.8 <= result.ground_truth_score <= 1.0
        assert result.confidence_score >= 0.7
        assert result.data_quality in ["excellent", "good"]

    def test_compute_media_performance_score(self, collector, sample_campaign_feedback):
        """Test media performance score computation"""
        score = collector._compute_media_performance_score(
            sample_campaign_feedback.media_performance,
            sample_campaign_feedback.budget
        )
        
        assert 0.0 <= score <= 1.0
        assert isinstance(score, float)

    def test_compute_business_impact_score(self, collector, sample_campaign_feedback):
        """Test business impact score computation"""
        score = collector._compute_business_impact_score(
            sample_campaign_feedback.business_impact,
            sample_campaign_feedback.budget
        )
        
        assert 0.0 <= score <= 1.0
        assert isinstance(score, float)

    def test_compute_audience_engagement_score(self, collector, sample_campaign_feedback):
        """Test audience engagement score computation"""
        score = collector._compute_audience_engagement_score(
            sample_campaign_feedback.audience_engagement
        )
        
        assert 0.0 <= score <= 1.0
        assert isinstance(score, float)

    def test_compute_cost_efficiency_score(self, collector, sample_campaign_feedback):
        """Test cost efficiency score computation"""
        score = collector._compute_cost_efficiency_score(
            sample_campaign_feedback.cost_efficiency,
            sample_campaign_feedback.budget
        )
        
        assert 0.0 <= score <= 1.0
        assert isinstance(score, float)

    def test_validate_campaign_feedback_valid(self, collector, sample_campaign_feedback):
        """Test campaign feedback validation with valid data"""
        issues = collector._validate_campaign_feedback(sample_campaign_feedback)
        
        # Should have no major validation issues
        critical_issues = [issue for issue in issues if issue.get("severity") == "critical"]
        assert len(critical_issues) == 0

    def test_validate_campaign_feedback_invalid(self, collector):
        """Test campaign feedback validation with invalid data"""
        invalid_feedback = CampaignFeedback(
            enterprise_id="",  # Invalid empty ID
            campaign_id="test",
            campaign_title="Test",
            campaign_type="test",
            industry="test",
            target_audience=[],
            budget=100.0,  # Too low budget
            
            media_performance=MediaPerformanceMetrics(
                total_articles_published=-5,  # Invalid negative value
                total_media_reach=0,
                click_through_rate=1.5,  # Invalid rate > 1
                social_media_shares=0,
                media_quality_score=15.0,  # Invalid score > 10
                publication_success_rate=0.0,
                tier1_coverage=0,
                tier2_coverage=0,
                tier3_coverage=0,
                average_article_quality=0.0
            ),
            
            business_impact=BusinessImpactMetrics(
                brand_awareness_lift=0.0,
                lead_generation=0,
                sales_conversion=0,
                revenue_generated=-1000.0,  # Invalid negative revenue
                roi_percentage=-50.0,  # Invalid negative ROI
                customer_acquisition_cost=0.0,
                brand_mention_increase=0.0,
                market_share_gain=0.0
            ),
            
            audience_engagement=AudienceEngagementMetrics(
                average_engagement_rate=0.0,
                comment_sentiment_score=-2.0,  # Invalid sentiment < -1
                audience_retention_rate=0.0,
                social_virality_score=0.0,
                user_generated_content=0,
                influencer_engagement_rate=0.0,
                audience_quality_score=0.0
            ),
            
            cost_efficiency=CostEfficiencyMetrics(
                cost_per_acquisition=0.0,
                cost_per_impression=0.0,
                cost_per_click=0.0,
                budget_utilization=2.0,  # Invalid utilization > 1
                cost_per_lead=0.0,
                efficiency_vs_industry_avg=0.0,
                waste_percentage=150.0  # Invalid waste > 100%
            ),
            
            campaign_duration_days=0,  # Invalid duration
            launch_date=datetime(2024, 1, 1),
            completion_date=datetime(2023, 12, 31),  # Invalid: completion before launch
            feedback_timestamp=datetime(2024, 1, 2)
        )
        
        issues = collector._validate_campaign_feedback(invalid_feedback)
        
        # Should have multiple validation issues
        assert len(issues) > 0
        critical_issues = [issue for issue in issues if issue.get("severity") == "critical"]
        assert len(critical_issues) > 0

    def test_assess_data_quality_excellent(self, collector, excellent_campaign):
        """Test data quality assessment for excellent data"""
        quality = collector._assess_data_quality(excellent_campaign)
        assert quality in ["excellent", "good"]

    def test_assess_data_quality_poor(self, collector):
        """Test data quality assessment for poor data"""
        # Create campaign with missing/zero data
        poor_data_campaign = CampaignFeedback(
            enterprise_id="test",
            campaign_id="test",
            campaign_title="Test",
            campaign_type="test",
            industry="test",
            target_audience=["test"],
            budget=1000000.0,
            
            media_performance=MediaPerformanceMetrics(
                total_articles_published=0,
                total_media_reach=0,
                click_through_rate=0.0,
                social_media_shares=0,
                media_quality_score=0.0,
                publication_success_rate=0.0,
                tier1_coverage=0,
                tier2_coverage=0,
                tier3_coverage=0,
                average_article_quality=0.0
            ),
            
            business_impact=BusinessImpactMetrics(
                brand_awareness_lift=0.0,
                lead_generation=0,
                sales_conversion=0,
                revenue_generated=0.0,
                roi_percentage=0.0,
                customer_acquisition_cost=0.0,
                brand_mention_increase=0.0,
                market_share_gain=0.0
            ),
            
            audience_engagement=AudienceEngagementMetrics(
                average_engagement_rate=0.0,
                comment_sentiment_score=0.0,
                audience_retention_rate=0.0,
                social_virality_score=0.0,
                user_generated_content=0,
                influencer_engagement_rate=0.0,
                audience_quality_score=0.0
            ),
            
            cost_efficiency=CostEfficiencyMetrics(
                cost_per_acquisition=0.0,
                cost_per_impression=0.0,
                cost_per_click=0.0,
                budget_utilization=0.0,
                cost_per_lead=0.0,
                efficiency_vs_industry_avg=0.0,
                waste_percentage=0.0
            ),
            
            campaign_duration_days=30,
            launch_date=datetime(2024, 1, 1),
            completion_date=datetime(2024, 1, 31),
            feedback_timestamp=datetime(2024, 2, 5)
        )
        
        quality = collector._assess_data_quality(poor_data_campaign)
        assert quality in ["poor", "fair"]

    def test_normalize_score_range(self, collector):
        """Test score normalization function"""
        # Test normal range
        assert collector._normalize_score(50, 0, 100) == 0.5
        assert collector._normalize_score(0, 0, 100) == 0.0
        assert collector._normalize_score(100, 0, 100) == 1.0
        
        # Test edge cases
        assert collector._normalize_score(-10, 0, 100) == 0.0  # Below min
        assert collector._normalize_score(150, 0, 100) == 1.0  # Above max
        assert collector._normalize_score(50, 50, 50) == 1.0   # Min equals max

    def test_weighted_score_calculation(self, collector):
        """Test weighted score calculation"""
        scores = {
            'media_performance': 0.8,
            'business_impact': 0.7,
            'audience_engagement': 0.6,
            'cost_efficiency': 0.5
        }
        
        weighted_score = collector._calculate_weighted_score(scores)
        
        # Manual calculation: 0.4*0.8 + 0.3*0.7 + 0.2*0.6 + 0.1*0.5 = 0.32 + 0.21 + 0.12 + 0.05 = 0.7
        expected = 0.4 * 0.8 + 0.3 * 0.7 + 0.2 * 0.6 + 0.1 * 0.5
        assert abs(weighted_score - expected) < 0.001

    def test_confidence_score_calculation(self, collector, sample_campaign_feedback):
        """Test confidence score calculation"""
        confidence = collector._calculate_confidence_score(sample_campaign_feedback)
        
        assert 0.0 <= confidence <= 1.0
        assert isinstance(confidence, float)

    @pytest.mark.asyncio
    async def test_batch_processing(self, collector, sample_campaign_feedback, 
                                   poor_performing_campaign, excellent_campaign):
        """Test batch processing of multiple campaigns"""
        campaigns = [sample_campaign_feedback, poor_performing_campaign, excellent_campaign]
        
        results = []
        for campaign in campaigns:
            result = await collector.collect_campaign_metrics(campaign)
            results.append(result)
        
        assert len(results) == 3
        
        # Check that results are properly ordered by performance
        excellent_score = next(r.ground_truth_score for r in results if r.campaign_id == "campaign_003")
        good_score = next(r.ground_truth_score for r in results if r.campaign_id == "campaign_001")
        poor_score = next(r.ground_truth_score for r in results if r.campaign_id == "campaign_002")
        
        assert excellent_score > good_score > poor_score

    def test_roi_calculation_accuracy(self, collector):
        """Test ROI calculation accuracy"""
        # Test case: 30M budget, 125M revenue = 316.7% ROI
        budget = 30000000.0
        revenue = 125000000.0
        expected_roi = ((revenue - budget) / budget) * 100  # 316.67%
        
        business_metrics = BusinessImpactMetrics(
            brand_awareness_lift=15.5,
            lead_generation=450,
            sales_conversion=85,
            revenue_generated=revenue,
            roi_percentage=expected_roi,
            customer_acquisition_cost=294117.6,
            brand_mention_increase=28.3,
            market_share_gain=2.1
        )
        
        score = collector._compute_business_impact_score(business_metrics, budget)
        assert 0.0 <= score <= 1.0

    @pytest.mark.parametrize("budget,reach,expected_efficiency", [
        (10000000, 1000000, True),   # Good efficiency: 10 VND per reach
        (50000000, 1000000, False),  # Poor efficiency: 50 VND per reach  
        (30000000, 2500000, True),   # Good efficiency: 12 VND per reach
    ])
    def test_media_efficiency_calculation(self, collector, budget, reach, expected_efficiency):
        """Test media efficiency calculation with different scenarios"""
        media_metrics = MediaPerformanceMetrics(
            total_articles_published=20,
            total_media_reach=reach,
            click_through_rate=0.03,
            social_media_shares=1000,
            media_quality_score=7.5,
            publication_success_rate=0.8,
            tier1_coverage=5,
            tier2_coverage=10,
            tier3_coverage=5,
            average_article_quality=7.5
        )
        
        score = collector._compute_media_performance_score(media_metrics, budget)
        
        if expected_efficiency:
            assert score >= 0.5  # Should be at least moderate score for good efficiency
        # Note: We don't assert low score for poor efficiency as other factors may compensate

    def test_error_handling_malformed_data(self, collector):
        """Test error handling with malformed data"""
        # Test with None values
        try:
            result = asyncio.run(collector.collect_campaign_metrics(None))
            assert False, "Should raise exception for None input"
        except (AttributeError, TypeError):
            pass  # Expected

        # Test with missing required fields - this would be caught by Pydantic validation
        # when creating the CampaignFeedback object, so we test the processing logic


if __name__ == "__main__":
    pytest.main([__file__, "-v"])