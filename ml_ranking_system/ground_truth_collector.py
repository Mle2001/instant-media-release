"""
Ground Truth KPI Collector
Thu thập và tính toán Ground Truth scores từ campaign results
Đây là TRÁI TIM của continuous learning system
"""

import os
import json
import math
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, field
import asyncio

from pydantic import BaseModel, Field, field_validator, model_validator
from loguru import logger
import yaml

@dataclass
class CampaignMetrics:
    """Container cho all campaign metrics"""
    
    # Identifiers
    session_id: str
    campaign_id: str
    campaign_name: str
    start_date: datetime
    end_date: datetime
    
    # Media Performance Metrics (40% weight)
    media_performance: Dict[str, float] = field(default_factory=dict)
    
    # Business Impact Metrics (30% weight) 
    business_impact: Dict[str, float] = field(default_factory=dict)
    
    # Audience Engagement Metrics (20% weight)
    audience_engagement: Dict[str, float] = field(default_factory=dict)
    
    # Cost Efficiency Metrics (10% weight)
    cost_efficiency: Dict[str, float] = field(default_factory=dict)
    
    # Raw data for reference
    raw_media_results: Dict = field(default_factory=dict)
    raw_business_metrics: Dict = field(default_factory=dict)
    raw_cost_metrics: Dict = field(default_factory=dict)
    raw_audience_metrics: Dict = field(default_factory=dict)
    
    # Computed scores
    composite_ground_truth_score: Optional[float] = None
    performance_tier: Optional[str] = None
    confidence_level: Optional[float] = None
    
    def __post_init__(self):
        """Validate data after initialization"""
        if self.end_date <= self.start_date:
            raise ValueError("End date must be after start date")
        
        if not self.session_id or not self.campaign_id:
            raise ValueError("Session ID and Campaign ID are required")


class CampaignFeedbackData(BaseModel):
    """
    Pydantic model for enterprise feedback data submission
    Matches the JSON schema defined earlier
    """
    
    # Campaign Identification
    session_id: str = Field(..., min_length=8, max_length=64)
    campaign_id: str = Field(..., min_length=8, max_length=128)
    campaign_name: str = Field(..., min_length=3, max_length=200)
    start_date: datetime
    end_date: datetime
    
    # Media Results
    media_results: Dict[str, Dict[str, Any]] = Field(..., min_length=1)
    
    # Business Metrics
    business_metrics: Dict[str, float] = Field(...)
    
    # Optional metrics
    cost_metrics: Optional[Dict[str, float]] = None
    audience_metrics: Optional[Dict[str, Any]] = None
    qualitative_feedback: Optional[Dict[str, str]] = None
    
    @field_validator('end_date')
    @classmethod
    def end_date_after_start(cls, v, info):
        if info.data and 'start_date' in info.data and v <= info.data['start_date']:
            raise ValueError('End date must be after start date')
        return v
    
    @field_validator('business_metrics')
    @classmethod
    def validate_required_business_metrics(cls, v):
        if v is None:
            return v
        required = ['revenue_generated', 'leads_generated', 'customers_acquired']
        missing = [key for key in required if key not in v]
        if missing:
            raise ValueError(f'Missing required business metrics: {missing}')
        return v
    
    @field_validator('media_results')
    @classmethod
    def validate_media_results(cls, v):
        if v is None:
            return v
        for outlet_name, result in v.items():
            if 'article_published' not in result:
                raise ValueError(f'Missing article_published for {outlet_name}')
            if 'actual_reach' not in result:
                raise ValueError(f'Missing actual_reach for {outlet_name}')
        return v


class GroundTruthKPICollector:
    """
    Thu thập và tính toán Ground Truth KPIs từ campaign results
    
    This is the HEART of the continuous learning system.
    Converts real campaign results into training labels for ML model.
    """
    
    def __init__(self, config_path: str = "./config/ml_config.yaml"):
        """Initialize with configuration"""
        
        # Load configuration
        self.config = self._load_config(config_path)
        
        # KPI computation weights from config
        self.kpi_weights = self.config.get('ground_truth_weights', {
            'media_performance': 0.4,
            'business_impact': 0.3, 
            'audience_engagement': 0.2,
            'cost_efficiency': 0.1
        })
        
        # Normalization parameters for different metrics
        self.normalization_params = {
            'max_revenue_vnd': 1_000_000_000,  # 1B VND
            'max_leads': 1000,
            'max_reach': 50_000_000,  # 50M people
            'max_roi_percent': 500,   # 500% ROI
            'max_engagement_rate': 0.1,  # 10% engagement rate
            'max_cost_per_lead': 1_000_000,  # 1M VND per lead
        }
        
        # Performance tier thresholds
        self.performance_tiers = {
            'excellent': (0.8, 1.0),
            'good': (0.6, 0.8),
            'average': (0.4, 0.6),
            'poor': (0.0, 0.4)
        }
        
        logger.info("✅ GroundTruthKPICollector initialized")
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            return config.get('data', {})
        except Exception as e:
            logger.warning(f"Could not load config: {e}")
            return {}
    
    async def collect_campaign_metrics(self, feedback_data: CampaignFeedbackData) -> CampaignMetrics:
        """
        Main method: Convert feedback data to structured campaign metrics
        
        Args:
            feedback_data: Enterprise feedback submission
            
        Returns:
            CampaignMetrics: Structured metrics for ML training
        """
        
        logger.info(f"🔍 Collecting metrics for campaign: {feedback_data.campaign_id}")
        
        # Create campaign metrics container
        metrics = CampaignMetrics(
            session_id=feedback_data.session_id,
            campaign_id=feedback_data.campaign_id,
            campaign_name=feedback_data.campaign_name,
            start_date=feedback_data.start_date,
            end_date=feedback_data.end_date,
            raw_media_results=feedback_data.media_results,
            raw_business_metrics=feedback_data.business_metrics,
            raw_cost_metrics=feedback_data.cost_metrics or {},
            raw_audience_metrics=feedback_data.audience_metrics or {}
        )
        
        # Collect metrics in parallel for efficiency
        collection_tasks = [
            self._collect_media_performance_metrics(feedback_data, metrics),
            self._collect_business_impact_metrics(feedback_data, metrics),
            self._collect_audience_engagement_metrics(feedback_data, metrics),
            self._collect_cost_efficiency_metrics(feedback_data, metrics)
        ]
        
        results = await asyncio.gather(*collection_tasks, return_exceptions=True)
        
        # Handle any collection errors
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Metrics collection error in task {i}: {result}")
        
        # Compute composite ground truth score
        metrics.composite_ground_truth_score = self._compute_composite_score(metrics)
        metrics.performance_tier = self._classify_performance_tier(metrics.composite_ground_truth_score)
        metrics.confidence_level = self._compute_confidence_level(metrics)
        
        logger.info(f"✅ Campaign metrics collected - Ground Truth Score: {metrics.composite_ground_truth_score:.3f}")
        
        return metrics
    
    async def _collect_media_performance_metrics(
        self, 
        feedback_data: CampaignFeedbackData,
        metrics: CampaignMetrics
    ) -> None:
        """
        Collect media performance metrics (40% weight)
        
        These are the most important metrics as they directly measure
        how well our media recommendations performed.
        """
        
        media_results = feedback_data.media_results
        media_metrics = {}
        
        # 1. Media Outlet Success Rate
        total_outlets = len(media_results)
        published_outlets = sum(1 for result in media_results.values() if result.get('article_published', False))
        media_metrics['outlet_success_rate'] = published_outlets / max(total_outlets, 1)
        
        # 2. Total Actual Reach
        total_reach = sum(result.get('actual_reach', 0) for result in media_results.values())
        media_metrics['total_reach_normalized'] = min(total_reach / self.normalization_params['max_reach'], 1.0)
        
        # 3. Average Engagement Rate
        engagement_rates = []
        for outlet_result in media_results.values():
            engagement_data = outlet_result.get('engagement_metrics', {})
            if engagement_data and outlet_result.get('actual_reach', 0) > 0:
                total_engagement = (
                    engagement_data.get('shares', 0) + 
                    engagement_data.get('comments', 0)
                )
                engagement_rate = total_engagement / outlet_result['actual_reach']
                engagement_rates.append(engagement_rate)
        
        if engagement_rates:
            avg_engagement_rate = np.mean(engagement_rates)
            media_metrics['avg_engagement_rate'] = min(avg_engagement_rate / self.normalization_params['max_engagement_rate'], 1.0)
        else:
            media_metrics['avg_engagement_rate'] = 0.0
        
        # 4. Media Quality Score (based on tier and editor satisfaction)
        quality_scores = []
        for outlet_name, result in media_results.items():
            # Infer tier from outlet name (this could be improved with actual tier data)
            tier_score = self._infer_media_tier_score(outlet_name)
            
            # Editor satisfaction if available
            editor_satisfaction = result.get('editor_satisfaction', 5) / 10  # Normalize to 0-1
            
            outlet_quality = 0.7 * tier_score + 0.3 * editor_satisfaction
            quality_scores.append(outlet_quality)
        
        if quality_scores:
            media_metrics['avg_media_quality'] = np.mean(quality_scores)
        else:
            media_metrics['avg_media_quality'] = 0.5
        
        # 5. Publication Speed (faster = better)
        publication_speeds = []
        for result in media_results.values():
            if result.get('article_published') and result.get('publication_date'):
                try:
                    pub_date = datetime.fromisoformat(result['publication_date'].replace('Z', '+00:00'))
                    days_to_publish = (pub_date.date() - feedback_data.start_date.date()).days
                    if days_to_publish >= 0:  # Only valid positive durations
                        publication_speeds.append(days_to_publish)
                except:
                    continue
        
        if publication_speeds:
            avg_days = np.mean(publication_speeds)
            # Convert to 0-1 score (faster = higher score)
            media_metrics['publication_speed_score'] = max(0, 1 - avg_days / 30)  # 30 days = 0 score
        else:
            media_metrics['publication_speed_score'] = 0.5
        
        metrics.media_performance = media_metrics
        
        logger.debug(f"Media performance metrics: {media_metrics}")
    
    async def _collect_business_impact_metrics(
        self,
        feedback_data: CampaignFeedbackData,
        metrics: CampaignMetrics
    ) -> None:
        """
        Collect business impact metrics (30% weight)
        
        These measure the actual business value generated by the campaign.
        """
        
        business_data = feedback_data.business_metrics
        business_metrics = {}
        
        # 1. Revenue Impact (normalized)
        revenue = business_data.get('revenue_generated', 0)
        business_metrics['revenue_normalized'] = min(revenue / self.normalization_params['max_revenue_vnd'], 1.0)
        
        # 2. Lead Generation Performance
        leads = business_data.get('leads_generated', 0)
        business_metrics['leads_normalized'] = min(leads / self.normalization_params['max_leads'], 1.0)
        
        # 3. Customer Acquisition
        customers = business_data.get('customers_acquired', 0)
        business_metrics['customers_normalized'] = min(customers / 100, 1.0)  # Max 100 customers
        
        # 4. Brand Metrics Growth
        brand_mentions_increase = business_data.get('brand_mentions_increase', 0)
        business_metrics['brand_growth'] = min(max(brand_mentions_increase, 0), 1.0)
        
        # 5. Search Volume Lift
        search_lift = business_data.get('search_volume_lift', 0)
        business_metrics['search_lift'] = min(max(search_lift, 0), 1.0)
        
        # 6. Website Traffic Impact
        traffic_increase = business_data.get('website_traffic_increase', 0)
        business_metrics['traffic_growth'] = min(max(traffic_increase, 0), 1.0)
        
        # 7. Social Media Growth
        social_growth = business_data.get('social_media_followers_gained', 0)
        business_metrics['social_growth_normalized'] = min(social_growth / 10000, 1.0)  # Max 10k followers
        
        metrics.business_impact = business_metrics
        
        logger.debug(f"Business impact metrics: {business_metrics}")
    
    async def _collect_audience_engagement_metrics(
        self,
        feedback_data: CampaignFeedbackData,
        metrics: CampaignMetrics
    ) -> None:
        """
        Collect audience engagement metrics (20% weight)
        
        These measure how well the content resonated with the target audience.
        """
        
        audience_data = feedback_data.audience_metrics or {}
        engagement_metrics = {}
        
        # 1. Target Audience Accuracy
        accuracy = audience_data.get('target_audience_accuracy', 0.5)  # Default to 50% if unknown
        engagement_metrics['audience_accuracy'] = min(max(accuracy, 0), 1.0)
        
        # 2. Sentiment Improvement
        sentiment_data = audience_data.get('sentiment_scores', {})
        if sentiment_data and 'pre_campaign' in sentiment_data and 'post_campaign' in sentiment_data:
            sentiment_improvement = (
                sentiment_data['post_campaign'] - sentiment_data['pre_campaign']
            ) / 10  # Normalize to 0-1 (assuming 0-10 scale)
            engagement_metrics['sentiment_improvement'] = min(max(sentiment_improvement + 0.5, 0), 1.0)
        else:
            engagement_metrics['sentiment_improvement'] = 0.5
        
        # 3. Demographic Alignment Score
        demo_data = audience_data.get('demographic_breakdown', {})
        if demo_data:
            # Check if demographic data is complete and balanced
            total_demo = sum(demo_data.values())
            if total_demo > 0:
                # Higher score for more complete demographic data
                completeness = min(len(demo_data) / 7, 1.0)  # Max 7 demo categories
                balance = 1 - np.std(list(demo_data.values())) if len(demo_data) > 1 else 0.5
                engagement_metrics['demographic_alignment'] = (completeness + balance) / 2
            else:
                engagement_metrics['demographic_alignment'] = 0.0
        else:
            engagement_metrics['demographic_alignment'] = 0.5
        
        # 4. Content Consumption Quality (from media engagement metrics)
        total_engagement_quality = []
        for outlet_result in feedback_data.media_results.values():
            engagement_data = outlet_result.get('engagement_metrics', {})
            if engagement_data:
                # Time on page indicates content quality
                time_on_page = engagement_data.get('time_on_page', 0)
                if time_on_page > 0:
                    # Normalize time on page (60 seconds = good engagement)
                    time_score = min(time_on_page / 60, 1.0)
                    total_engagement_quality.append(time_score)
        
        if total_engagement_quality:
            engagement_metrics['content_quality_score'] = np.mean(total_engagement_quality)
        else:
            engagement_metrics['content_quality_score'] = 0.5
        
        metrics.audience_engagement = engagement_metrics
        
        logger.debug(f"Audience engagement metrics: {engagement_metrics}")
    
    async def _collect_cost_efficiency_metrics(
        self,
        feedback_data: CampaignFeedbackData,
        metrics: CampaignMetrics
    ) -> None:
        """
        Collect cost efficiency metrics (10% weight)
        
        These measure the ROI and cost-effectiveness of the campaign.
        """
        
        cost_data = feedback_data.cost_metrics or {}
        business_data = feedback_data.business_metrics
        efficiency_metrics = {}
        
        # 1. ROI Calculation
        total_cost = cost_data.get('total_campaign_cost', 0)
        revenue = business_data.get('revenue_generated', 0)
        
        if total_cost > 0:
            roi_percent = ((revenue - total_cost) / total_cost) * 100
            # Normalize ROI (500% = max score)
            efficiency_metrics['roi_normalized'] = min(max(roi_percent / self.normalization_params['max_roi_percent'], 0), 1.0)
        else:
            efficiency_metrics['roi_normalized'] = 0.0
        
        # 2. Cost per Lead
        leads = business_data.get('leads_generated', 0)
        if leads > 0 and total_cost > 0:
            cost_per_lead = total_cost / leads
            # Lower cost per lead = higher score
            efficiency_metrics['cost_per_lead_score'] = max(0, 1 - cost_per_lead / self.normalization_params['max_cost_per_lead'])
        else:
            efficiency_metrics['cost_per_lead_score'] = 0.0
        
        # 3. Cost per Customer Acquisition
        customers = business_data.get('customers_acquired', 0)
        if customers > 0 and total_cost > 0:
            cost_per_customer = total_cost / customers
            # Normalize (10M VND per customer = 0 score)
            efficiency_metrics['cost_per_customer_score'] = max(0, 1 - cost_per_customer / 10_000_000)
        else:
            efficiency_metrics['cost_per_customer_score'] = 0.0
        
        # 4. Time Efficiency
        time_to_market = cost_data.get('time_to_market_days', 7)  # Default 7 days
        if time_to_market > 0:
            # Faster time to market = higher score (30 days = 0 score)
            efficiency_metrics['time_efficiency'] = max(0, 1 - time_to_market / 30)
        else:
            efficiency_metrics['time_efficiency'] = 0.5
        
        # 5. Resource Efficiency
        resource_hours = cost_data.get('resource_hours', 0)
        if resource_hours > 0 and leads > 0:
            hours_per_lead = resource_hours / leads
            # Lower hours per lead = higher efficiency (20 hours per lead = 0 score)
            efficiency_metrics['resource_efficiency'] = max(0, 1 - hours_per_lead / 20)
        else:
            efficiency_metrics['resource_efficiency'] = 0.5
        
        # 6. Budget Variance (staying on budget = higher score)
        planned_cost = cost_data.get('planned_cost', total_cost)  # Use actual as planned if not provided
        if planned_cost > 0:
            variance = abs(total_cost - planned_cost) / planned_cost
            # Lower variance = higher score
            efficiency_metrics['budget_accuracy'] = max(0, 1 - variance)
        else:
            efficiency_metrics['budget_accuracy'] = 0.5
        
        metrics.cost_efficiency = efficiency_metrics
        
        logger.debug(f"Cost efficiency metrics: {efficiency_metrics}")
    
    def _compute_composite_score(self, metrics: CampaignMetrics) -> float:
        """
        Compute composite Ground Truth score (0-1)
        
        This is the final training label for our ML model.
        Higher score = better campaign performance.
        """
        
        # Compute weighted score for each category
        category_scores = {}
        
        # 1. Media Performance Score (40% weight)
        if metrics.media_performance:
            media_score = np.mean([
                metrics.media_performance.get('outlet_success_rate', 0) * 0.3,
                metrics.media_performance.get('total_reach_normalized', 0) * 0.25,
                metrics.media_performance.get('avg_engagement_rate', 0) * 0.2,
                metrics.media_performance.get('avg_media_quality', 0) * 0.15,
                metrics.media_performance.get('publication_speed_score', 0) * 0.1
            ])
            category_scores['media'] = media_score
        else:
            category_scores['media'] = 0.0
        
        # 2. Business Impact Score (30% weight)
        if metrics.business_impact:
            business_score = np.mean([
                metrics.business_impact.get('revenue_normalized', 0) * 0.25,
                metrics.business_impact.get('leads_normalized', 0) * 0.2,
                metrics.business_impact.get('customers_normalized', 0) * 0.2,
                metrics.business_impact.get('brand_growth', 0) * 0.15,
                metrics.business_impact.get('search_lift', 0) * 0.1,
                metrics.business_impact.get('traffic_growth', 0) * 0.1
            ])
            category_scores['business'] = business_score
        else:
            category_scores['business'] = 0.0
        
        # 3. Audience Engagement Score (20% weight)
        if metrics.audience_engagement:
            engagement_score = np.mean([
                metrics.audience_engagement.get('audience_accuracy', 0) * 0.4,
                metrics.audience_engagement.get('sentiment_improvement', 0) * 0.3,
                metrics.audience_engagement.get('demographic_alignment', 0) * 0.2,
                metrics.audience_engagement.get('content_quality_score', 0) * 0.1
            ])
            category_scores['audience'] = engagement_score
        else:
            category_scores['audience'] = 0.0
        
        # 4. Cost Efficiency Score (10% weight)
        if metrics.cost_efficiency:
            efficiency_score = np.mean([
                metrics.cost_efficiency.get('roi_normalized', 0) * 0.3,
                metrics.cost_efficiency.get('cost_per_lead_score', 0) * 0.25,
                metrics.cost_efficiency.get('cost_per_customer_score', 0) * 0.2,
                metrics.cost_efficiency.get('time_efficiency', 0) * 0.15,
                metrics.cost_efficiency.get('resource_efficiency', 0) * 0.1
            ])
            category_scores['efficiency'] = efficiency_score
        else:
            category_scores['efficiency'] = 0.0
        
        # Compute weighted composite score
        composite_score = (
            category_scores['media'] * self.kpi_weights['media_performance'] +
            category_scores['business'] * self.kpi_weights['business_impact'] +
            category_scores['audience'] * self.kpi_weights['audience_engagement'] +
            category_scores['efficiency'] * self.kpi_weights['cost_efficiency']
        )
        
        # Clamp to [0, 1] range
        composite_score = min(max(composite_score, 0.0), 1.0)
        
        logger.info(f"📊 Composite score calculation:")
        logger.info(f"   Media: {category_scores['media']:.3f} (weight: {self.kpi_weights['media_performance']})")
        logger.info(f"   Business: {category_scores['business']:.3f} (weight: {self.kpi_weights['business_impact']})")
        logger.info(f"   Audience: {category_scores['audience']:.3f} (weight: {self.kpi_weights['audience_engagement']})")
        logger.info(f"   Efficiency: {category_scores['efficiency']:.3f} (weight: {self.kpi_weights['cost_efficiency']})")
        logger.info(f"   🎯 Final Score: {composite_score:.3f}")
        
        return composite_score
    
    def _classify_performance_tier(self, score: float) -> str:
        """Classify performance into tiers"""
        for tier, (min_score, max_score) in self.performance_tiers.items():
            if min_score <= score <= max_score:
                return tier
        return 'poor'  # Default fallback
    
    def _compute_confidence_level(self, metrics: CampaignMetrics) -> float:
        """
        Compute confidence level in the ground truth score
        
        Higher confidence when:
        - More complete data
        - Longer campaign duration
        - More media outlets involved
        """
        
        confidence_factors = []
        
        # 1. Data completeness
        required_categories = ['media_performance', 'business_impact']
        available_categories = sum(1 for cat in required_categories if getattr(metrics, cat))
        data_completeness = available_categories / len(required_categories)
        confidence_factors.append(data_completeness)
        
        # 2. Campaign duration (longer campaigns = higher confidence)
        campaign_duration = (metrics.end_date - metrics.start_date).days
        duration_confidence = min(campaign_duration / 30, 1.0)  # 30 days = max confidence
        confidence_factors.append(duration_confidence)
        
        # 3. Number of media outlets (more outlets = higher confidence)
        outlet_count = len(metrics.raw_media_results)
        outlet_confidence = min(outlet_count / 10, 1.0)  # 10 outlets = max confidence
        confidence_factors.append(outlet_confidence)
        
        # 4. Business metrics completeness
        business_completeness = len(metrics.raw_business_metrics) / 6  # Assuming 6 key metrics
        confidence_factors.append(min(business_completeness, 1.0))
        
        # Overall confidence is the average of all factors
        overall_confidence = np.mean(confidence_factors)
        
        return overall_confidence
    
    def _infer_media_tier_score(self, outlet_name: str) -> float:
        """
        Infer media tier score from outlet name
        This is a simplified approach - in production, this should come from the database
        """
        
        tier_1_indicators = ['vnexpress', 'vietnamnet', '24h', 'dantri', 'tuoitre', 'thanhnien']
        tier_2_indicators = ['cafef', 'cafebiz', 'genk', 'tinhte', 'kenh14']
        
        outlet_lower = outlet_name.lower()
        
        for indicator in tier_1_indicators:
            if indicator in outlet_lower:
                return 1.0  # Tier 1 = highest score
        
        for indicator in tier_2_indicators:
            if indicator in outlet_lower:
                return 0.7  # Tier 2 = good score
        
        return 0.5  # Unknown = medium score
    
    def create_training_sample(self, metrics: CampaignMetrics, features: np.ndarray) -> Dict[str, Any]:
        """
        Create a complete training sample for ML model
        
        Args:
            metrics: Computed campaign metrics
            features: Universal features extracted from initial content
            
        Returns:
            Dict containing all data needed for model training
        """
        
        training_sample = {
            # Identifiers
            'session_id': metrics.session_id,
            'campaign_id': metrics.campaign_id,
            'campaign_name': metrics.campaign_name,
            
            # Features (input to model)
            'features': features.tolist() if isinstance(features, np.ndarray) else features,
            'feature_version': '1.0.0',
            
            # Labels (output from model)
            'ground_truth_score': metrics.composite_ground_truth_score,
            'performance_tier': metrics.performance_tier,
            'confidence_level': metrics.confidence_level,
            
            # Detailed scores for analysis
            'category_scores': {
                'media_performance': metrics.media_performance,
                'business_impact': metrics.business_impact,
                'audience_engagement': metrics.audience_engagement,
                'cost_efficiency': metrics.cost_efficiency
            },
            
            # Metadata
            'campaign_duration_days': (metrics.end_date - metrics.start_date).days,
            'media_outlets_count': len(metrics.raw_media_results),
            'data_completeness': metrics.confidence_level,
            
            # Timestamps
            'campaign_start': metrics.start_date.isoformat(),
            'campaign_end': metrics.end_date.isoformat(), 
            'processed_at': datetime.now().isoformat(),
            
            # Raw data for reference (optional, for debugging)
            'raw_metrics': {
                'media_results': metrics.raw_media_results,
                'business_metrics': metrics.raw_business_metrics,
                'cost_metrics': metrics.raw_cost_metrics,
                'audience_metrics': metrics.raw_audience_metrics
            } if logger.level <= 10 else None  # Only include in debug mode
        }
        
        return training_sample
    
    def sigmoid(self, x: float) -> float:
        """Sigmoid function for normalization"""
        return 1 / (1 + math.exp(-max(min(x, 500), -500)))  # Clamp to prevent overflow
    
    def validate_training_sample(self, sample: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate training sample for quality and completeness
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        
        errors = []
        
        # Check required fields
        required_fields = ['session_id', 'features', 'ground_truth_score']
        for field in required_fields:
            if field not in sample:
                errors.append(f"Missing required field: {field}")
        
        # Validate score range
        if 'ground_truth_score' in sample:
            score = sample['ground_truth_score']
            if not (0 <= score <= 1):
                errors.append(f"Ground truth score out of range [0,1]: {score}")
        
        # Validate features
        if 'features' in sample:
            features = sample['features']
            if not isinstance(features, (list, np.ndarray)):
                errors.append("Features must be list or array")
            elif len(features) == 0:
                errors.append("Features array is empty")
        
        # Check confidence level
        if 'confidence_level' in sample:
            confidence = sample['confidence_level']
            if confidence < 0.3:  # Minimum confidence threshold
                errors.append(f"Confidence level too low: {confidence}")
        
        is_valid = len(errors) == 0
        
        return is_valid, errors