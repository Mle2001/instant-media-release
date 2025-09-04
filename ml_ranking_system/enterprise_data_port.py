"""
Enterprise Data Port
API endpoints for enterprises to submit campaign feedback data
This is the bridge between business results and ML learning
"""

import os
import json
import hashlib
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, validator
from loguru import logger
import yaml

# Import our ML components
try:
    from .ground_truth_collector import GroundTruthKPICollector, CampaignFeedbackData
    from .universal_features import UniversalStructureExtractor
    from .continuous_learning import ContinuousLearningManager
except ImportError:
    logger.warning("ML components not available in development mode")


class DataIngestionResponse(BaseModel):
    """Response model for data submission"""
    success: bool
    message: str
    feedback_id: str
    processing_status: str = "queued"
    estimated_impact_on_model: str
    receipt_timestamp: str


class FeedbackProcessingStatus(BaseModel):
    """Feedback processing status model"""
    feedback_id: str
    session_id: str
    status: str  # queued, processing, processed, failed
    processed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    ground_truth_score: Optional[float] = None
    confidence_level: Optional[float] = None
    contribution_to_learning: Optional[str] = None


class BatchFeedbackResponse(BaseModel):
    """Response for batch feedback submission"""
    batch_id: str
    items_count: int
    status: str = "processing"
    message: str
    estimated_processing_time_minutes: int


class LearningStatistics(BaseModel):
    """Learning progress statistics for enterprises"""
    total_feedback_submissions: int
    processed_submissions: int
    average_ground_truth_score: float
    model_improvement_percentage: float
    last_model_update: Optional[datetime] = None
    next_retraining_estimate: Optional[datetime] = None
    your_contribution_rank: str  # "Top 10%", "Above Average", etc.


class EnterpriseDataValidator:
    """Validate enterprise feedback data quality"""
    
    def __init__(self):
        self.min_campaign_duration_days = 3
        self.min_revenue_threshold = 1_000_000  # VND
        self.required_media_metrics = ['actual_reach', 'article_published']
        self.required_business_metrics = ['revenue_generated', 'leads_generated', 'customers_acquired']
    
    async def validate_feedback(self, feedback_data: CampaignFeedbackData) -> Dict[str, Any]:
        """
        Comprehensive validation of feedback data
        
        Returns:
            {
                'is_valid': bool,
                'errors': List[str],
                'warnings': List[str],
                'quality_score': float (0-1)
            }
        """
        
        errors = []
        warnings = []
        quality_factors = []
        
        # 1. Basic data validation (already handled by Pydantic)
        try:
            # Campaign duration check
            duration = (feedback_data.end_date - feedback_data.start_date).days
            if duration < self.min_campaign_duration_days:
                errors.append(f"Campaign duration too short: {duration} days (minimum: {self.min_campaign_duration_days})")
            else:
                quality_factors.append(min(duration / 30, 1.0))  # 30 days = max quality
            
            # Revenue threshold check
            revenue = feedback_data.business_metrics.get('revenue_generated', 0)
            if revenue < self.min_revenue_threshold:
                warnings.append(f"Low revenue campaign: {revenue:,} VND")
            quality_factors.append(min(revenue / 100_000_000, 1.0))  # 100M VND = max quality
            
            # Media results completeness
            media_completeness = 0
            for outlet_name, result in feedback_data.media_results.items():
                outlet_completeness = 0
                for metric in self.required_media_metrics:
                    if metric in result:
                        outlet_completeness += 1
                media_completeness += outlet_completeness / len(self.required_media_metrics)
            
            if len(feedback_data.media_results) > 0:
                media_completeness /= len(feedback_data.media_results)
                quality_factors.append(media_completeness)
            else:
                errors.append("No media results provided")
            
            # Business metrics completeness  
            business_completeness = sum(
                1 for metric in self.required_business_metrics 
                if metric in feedback_data.business_metrics
            ) / len(self.required_business_metrics)
            quality_factors.append(business_completeness)
            
            # Data richness bonus
            optional_data_bonus = 0
            if feedback_data.cost_metrics:
                optional_data_bonus += 0.1
            if feedback_data.audience_metrics:
                optional_data_bonus += 0.1
            if feedback_data.qualitative_feedback:
                optional_data_bonus += 0.05
            
            quality_factors.append(min(optional_data_bonus + 0.75, 1.0))  # Base 0.75 + bonuses
            
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
        
        # Calculate overall quality score
        quality_score = sum(quality_factors) / max(len(quality_factors), 1) if quality_factors else 0.0
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'quality_score': quality_score
        }


class EnterpriseDataPort:
    """
    Enterprise data ingestion port for campaign feedback
    Handles authentication, validation, and processing of enterprise feedback
    """
    
    def __init__(self):
        # Load configuration
        self.config = self._load_config()
        
        # Initialize components
        self.ground_truth_collector = None
        self.feature_extractor = None  
        self.learning_manager = None
        self.data_validator = EnterpriseDataValidator()
        
        try:
            self.ground_truth_collector = GroundTruthKPICollector()
            self.feature_extractor = UniversalStructureExtractor()
            logger.info("✅ ML components loaded")
        except Exception as e:
            logger.warning(f"ML components not available: {e}")
        
        # Authentication
        self.security = HTTPBearer()
        self.valid_tokens = self._load_enterprise_tokens()
        
        # Processing status tracking
        self.processing_status: Dict[str, Dict] = {}
        
        # Rate limiting
        self.rate_limits: Dict[str, Dict] = {}
        
        logger.info("✅ EnterpriseDataPort initialized")
    
    def _load_config(self) -> Dict:
        """Load configuration"""
        try:
            with open('./config/ml_config.yaml', 'r') as f:
                config = yaml.safe_load(f)
            return config.get('enterprise_data_port', {})
        except Exception as e:
            logger.warning(f"Could not load config: {e}")
            return {}
    
    def _load_enterprise_tokens(self) -> Dict[str, Dict]:
        """Load enterprise authentication tokens"""
        try:
            with open('./config/enterprise_tokens.json', 'r') as f:
                token_data = json.load(f)
            return token_data.get('enterprise_tokens', {})
        except Exception as e:
            logger.warning(f"Could not load enterprise tokens: {e}")
            return {}
    
    async def _authenticate_enterprise(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate enterprise token
        
        Returns:
            Enterprise info dict if valid, None if invalid
        """
        
        for enterprise_id, token_info in self.valid_tokens.items():
            if token_info.get('token') == token and token_info.get('active', False):
                # Check expiration
                expires_at = token_info.get('expires_at')
                if expires_at:
                    expire_date = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                    if datetime.now() > expire_date.replace(tzinfo=None):
                        logger.warning(f"Expired token for enterprise: {enterprise_id}")
                        continue
                
                return {
                    'enterprise_id': enterprise_id,
                    'company_name': token_info.get('company_name', ''),
                    'access_level': token_info.get('access_level', 'limited'),
                    'rate_limit': token_info.get('rate_limit_per_hour', 100)
                }
        
        return None
    
    async def _check_rate_limit(self, enterprise_id: str, rate_limit: int) -> bool:
        """
        Check if enterprise has exceeded rate limit
        
        Returns:
            True if within limit, False if exceeded
        """
        
        now = datetime.now()
        hour_key = now.strftime('%Y-%m-%d-%H')
        
        if enterprise_id not in self.rate_limits:
            self.rate_limits[enterprise_id] = {}
        
        enterprise_limits = self.rate_limits[enterprise_id]
        
        # Clean old entries
        for key in list(enterprise_limits.keys()):
            if key != hour_key:
                del enterprise_limits[key]
        
        # Check current hour limit
        current_count = enterprise_limits.get(hour_key, 0)
        
        if current_count >= rate_limit:
            return False
        
        # Increment counter
        enterprise_limits[hour_key] = current_count + 1
        return True
    
    def create_data_ingestion_endpoints(self, app: FastAPI):
        """
        Create all data ingestion endpoints for FastAPI app
        """
        
        @app.post("/feedback", response_model=DataIngestionResponse)
        async def submit_campaign_feedback(
            feedback_data: CampaignFeedbackData,
            background_tasks: BackgroundTasks,
            credentials: HTTPAuthorizationCredentials = Depends(self.security),
            request: Request = None
        ):
            """
            MAIN ENDPOINT: Submit campaign feedback for ML learning
            
            This is the primary way enterprises feed real campaign results
            back into the system for continuous model improvement.
            """
            
            # 1. Authenticate enterprise
            enterprise_info = await self._authenticate_enterprise(credentials.credentials)
            if not enterprise_info:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired enterprise token"
                )
            
            # 2. Check rate limiting
            rate_limit_ok = await self._check_rate_limit(
                enterprise_info['enterprise_id'],
                enterprise_info['rate_limit']
            )
            if not rate_limit_ok:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded. Maximum {enterprise_info['rate_limit']} requests per hour."
                )
            
            # 3. Validate data quality
            validation_result = await self.data_validator.validate_feedback(feedback_data)
            if not validation_result['is_valid']:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail={
                        "message": "Data validation failed",
                        "errors": validation_result['errors'],
                        "warnings": validation_result.get('warnings', [])
                    }
                )
            
            # 4. Generate feedback ID
            timestamp = int(datetime.now().timestamp())
            feedback_id = f"fb_{enterprise_info['enterprise_id']}_{timestamp}_{feedback_data.session_id[:8]}"
            
            # 5. Log and track submission
            logger.info(f"📊 Enterprise feedback received:")
            logger.info(f"   Enterprise: {enterprise_info['company_name']}")
            logger.info(f"   Campaign: {feedback_data.campaign_name}")
            logger.info(f"   Feedback ID: {feedback_id}")
            logger.info(f"   Quality Score: {validation_result['quality_score']:.3f}")
            
            # 6. Initialize processing status
            self.processing_status[feedback_id] = {
                'feedback_id': feedback_id,
                'session_id': feedback_data.session_id,
                'enterprise_id': enterprise_info['enterprise_id'],
                'status': 'queued',
                'submitted_at': datetime.now(),
                'quality_score': validation_result['quality_score']
            }
            
            # 7. Queue for background processing
            background_tasks.add_task(
                self._process_feedback_background,
                feedback_data,
                feedback_id,
                enterprise_info
            )
            
            # 8. Estimate impact on model learning
            estimated_impact = await self._estimate_learning_impact(
                feedback_data, 
                validation_result['quality_score']
            )
            
            return DataIngestionResponse(
                success=True,
                message="Campaign feedback received and queued for processing",
                feedback_id=feedback_id,
                processing_status="queued",
                estimated_impact_on_model=estimated_impact,
                receipt_timestamp=datetime.now().isoformat()
            )
        
        @app.get("/feedback/{feedback_id}/status", response_model=FeedbackProcessingStatus)
        async def get_feedback_processing_status(
            feedback_id: str,
            credentials: HTTPAuthorizationCredentials = Depends(self.security)
        ):
            """
            Get processing status of submitted feedback
            """
            
            # Authenticate
            enterprise_info = await self._authenticate_enterprise(credentials.credentials)
            if not enterprise_info:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid enterprise token"
                )
            
            # Check if feedback exists and belongs to this enterprise
            if feedback_id not in self.processing_status:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Feedback ID not found"
                )
            
            status_info = self.processing_status[feedback_id]
            
            # Verify ownership
            if status_info.get('enterprise_id') != enterprise_info['enterprise_id']:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this feedback"
                )
            
            return FeedbackProcessingStatus(
                feedback_id=feedback_id,
                session_id=status_info['session_id'],
                status=status_info['status'],
                processed_at=status_info.get('processed_at'),
                error_message=status_info.get('error_message'),
                ground_truth_score=status_info.get('ground_truth_score'),
                confidence_level=status_info.get('confidence_level'),
                contribution_to_learning=status_info.get('contribution_to_learning')
            )
        
        @app.post("/batch-feedback", response_model=BatchFeedbackResponse)
        async def submit_batch_feedback(
            feedback_batch: List[CampaignFeedbackData],
            background_tasks: BackgroundTasks,
            credentials: HTTPAuthorizationCredentials = Depends(self.security)
        ):
            """
            Submit multiple campaign feedback items in batch
            More efficient for enterprises with many campaigns
            """
            
            # Authenticate
            enterprise_info = await self._authenticate_enterprise(credentials.credentials)
            if not enterprise_info:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid enterprise token"
                )
            
            # Check batch size limits
            max_batch_size = 50  # Configurable
            if len(feedback_batch) > max_batch_size:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"Batch size too large. Maximum {max_batch_size} items per batch."
                )
            
            # Check rate limiting for batch
            batch_rate_cost = len(feedback_batch)
            rate_limit_ok = await self._check_rate_limit(
                enterprise_info['enterprise_id'],
                enterprise_info['rate_limit'] - batch_rate_cost + 1  # Allow if sufficient remaining
            )
            if not rate_limit_ok:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Insufficient rate limit remaining for batch submission"
                )
            
            # Generate batch ID
            batch_id = f"batch_{enterprise_info['enterprise_id']}_{int(datetime.now().timestamp())}"
            
            # Queue batch processing
            background_tasks.add_task(
                self._process_feedback_batch,
                feedback_batch,
                batch_id,
                enterprise_info
            )
            
            # Estimate processing time (2 minutes per item average)
            estimated_time = max(len(feedback_batch) * 2, 5)
            
            logger.info(f"📦 Batch feedback submitted:")
            logger.info(f"   Enterprise: {enterprise_info['company_name']}")  
            logger.info(f"   Batch ID: {batch_id}")
            logger.info(f"   Items: {len(feedback_batch)}")
            
            return BatchFeedbackResponse(
                batch_id=batch_id,
                items_count=len(feedback_batch),
                status="processing",
                message=f"Batch of {len(feedback_batch)} feedback items queued for processing",
                estimated_processing_time_minutes=estimated_time
            )
        
        @app.get("/learning-stats", response_model=LearningStatistics) 
        async def get_learning_statistics(
            credentials: HTTPAuthorizationCredentials = Depends(self.security)
        ):
            """
            Get learning progress statistics
            Shows how enterprise contributions are improving the model
            """
            
            # Authenticate
            enterprise_info = await self._authenticate_enterprise(credentials.credentials)
            if not enterprise_info:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid enterprise token"
                )
            
            try:
                stats = await self._compute_learning_statistics(enterprise_info['enterprise_id'])
                return stats
                
            except Exception as e:
                logger.error(f"Failed to compute learning stats: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to retrieve learning statistics"
                )
        
        @app.get("/model-info")
        async def get_model_information(
            credentials: HTTPAuthorizationCredentials = Depends(self.security)
        ):
            """
            Get information about the current ML model
            """
            
            # Authenticate
            enterprise_info = await self._authenticate_enterprise(credentials.credentials)
            if not enterprise_info:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid enterprise token"
                )
            
            try:
                model_info = await self._get_model_information()
                return model_info
                
            except Exception as e:
                logger.error(f"Failed to get model info: {e}")
                return {
                    "error": "Model information not available",
                    "status": "ML system initializing"
                }
    
    async def _process_feedback_background(
        self,
        feedback_data: CampaignFeedbackData,
        feedback_id: str,
        enterprise_info: Dict[str, Any]
    ):
        """
        Background processing of individual feedback
        """
        
        try:
            logger.info(f"🔄 Processing feedback: {feedback_id}")
            
            # Update status
            self.processing_status[feedback_id]['status'] = 'processing'
            
            if not self.ground_truth_collector or not self.feature_extractor:
                raise Exception("ML components not available")
            
            # 1. Convert to campaign metrics and compute ground truth
            campaign_metrics = await self.ground_truth_collector.collect_campaign_metrics(feedback_data)
            
            # 2. Extract universal features (this would come from original session data)
            # For now, we'll extract what we can from the feedback
            mock_content_analysis = {
                'content': feedback_data.qualitative_feedback.get('campaign_manager_notes', '') if feedback_data.qualitative_feedback else '',
                'industry_sector': 'business',  # Could infer from feedback
                'target_audiences': ['SME', 'Businesses']  # Could infer from feedback
            }
            
            universal_features = await self.feature_extractor.extract_universal_features(mock_content_analysis)
            feature_vector = universal_features.to_vector()
            
            # 3. Create complete training sample
            training_sample = self.ground_truth_collector.create_training_sample(
                campaign_metrics, 
                feature_vector
            )
            
            # 4. Validate training sample
            is_valid, validation_errors = self.ground_truth_collector.validate_training_sample(training_sample)
            
            if not is_valid:
                raise Exception(f"Training sample validation failed: {validation_errors}")
            
            # 5. Store training sample for future model training
            await self._store_training_sample(training_sample, enterprise_info)
            
            # 6. Update processing status
            self.processing_status[feedback_id].update({
                'status': 'processed',
                'processed_at': datetime.now(),
                'ground_truth_score': campaign_metrics.composite_ground_truth_score,
                'confidence_level': campaign_metrics.confidence_level,
                'contribution_to_learning': self._assess_contribution_value(
                    campaign_metrics.composite_ground_truth_score,
                    campaign_metrics.confidence_level
                )
            })
            
            # 7. Check if we should trigger model retraining
            if self.learning_manager:
                await self.learning_manager.check_retrain_trigger()
            
            logger.info(f"✅ Feedback processed successfully: {feedback_id}")
            logger.info(f"   Ground Truth Score: {campaign_metrics.composite_ground_truth_score:.3f}")
            logger.info(f"   Confidence Level: {campaign_metrics.confidence_level:.3f}")
            
        except Exception as e:
            logger.error(f"❌ Feedback processing failed: {feedback_id} - {e}")
            
            # Update status with error
            self.processing_status[feedback_id].update({
                'status': 'failed',
                'processed_at': datetime.now(),
                'error_message': str(e)
            })
    
    async def _process_feedback_batch(
        self,
        feedback_batch: List[CampaignFeedbackData],
        batch_id: str,
        enterprise_info: Dict[str, Any]
    ):
        """
        Background processing of feedback batch
        """
        
        logger.info(f"🔄 Processing feedback batch: {batch_id}")
        
        processed_count = 0
        failed_count = 0
        
        for i, feedback_data in enumerate(feedback_batch):
            try:
                # Generate individual feedback ID for this batch item
                feedback_id = f"{batch_id}_item_{i+1:03d}"
                
                # Process individual item
                await self._process_feedback_background(feedback_data, feedback_id, enterprise_info)
                processed_count += 1
                
            except Exception as e:
                logger.error(f"❌ Batch item {i+1} failed: {e}")
                failed_count += 1
                continue
        
        logger.info(f"✅ Batch processing completed: {batch_id}")
        logger.info(f"   Processed: {processed_count}/{len(feedback_batch)}")
        logger.info(f"   Failed: {failed_count}/{len(feedback_batch)}")
    
    async def _store_training_sample(
        self, 
        training_sample: Dict[str, Any],
        enterprise_info: Dict[str, Any]
    ):
        """
        Store training sample for future model training
        """
        
        try:
            # Create storage directory if it doesn't exist
            storage_dir = Path("./data/training_samples")
            storage_dir.mkdir(parents=True, exist_ok=True)
            
            # Add enterprise metadata
            training_sample['enterprise_metadata'] = {
                'enterprise_id': enterprise_info['enterprise_id'],
                'company_name': enterprise_info['company_name'],
                'submission_timestamp': datetime.now().isoformat()
            }
            
            # Save to JSON file
            filename = f"training_sample_{training_sample['session_id']}_{int(datetime.now().timestamp())}.json"
            file_path = storage_dir / filename
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(training_sample, f, indent=2, ensure_ascii=False)
            
            logger.info(f"💾 Training sample stored: {filename}")
            
        except Exception as e:
            logger.error(f"❌ Failed to store training sample: {e}")
            raise
    
    async def _estimate_learning_impact(
        self,
        feedback_data: CampaignFeedbackData,
        quality_score: float
    ) -> str:
        """
        Estimate the impact this feedback will have on model learning
        """
        
        try:
            # Factors affecting learning impact
            impact_factors = []
            
            # 1. Data quality
            if quality_score >= 0.9:
                impact_factors.append("Excellent data quality")
            elif quality_score >= 0.7:
                impact_factors.append("Good data quality")
            else:
                impact_factors.append("Moderate data quality")
            
            # 2. Campaign scale  
            total_reach = sum(
                result.get('actual_reach', 0) 
                for result in feedback_data.media_results.values()
            )
            if total_reach > 10_000_000:
                impact_factors.append("Large scale campaign")
            elif total_reach > 1_000_000:
                impact_factors.append("Medium scale campaign")
            
            # 3. Data uniqueness (simplified check)
            campaign_duration = (feedback_data.end_date - feedback_data.start_date).days
            if campaign_duration >= 14:
                impact_factors.append("Extended campaign period")
            
            # 4. Business impact significance
            revenue = feedback_data.business_metrics.get('revenue_generated', 0)
            if revenue > 100_000_000:  # 100M VND
                impact_factors.append("High business impact")
            
            # Determine overall impact
            if len(impact_factors) >= 3 and quality_score >= 0.8:
                return f"High Impact - {', '.join(impact_factors[:2])} + {len(impact_factors)-2} more factors"
            elif len(impact_factors) >= 2 and quality_score >= 0.6:
                return f"Medium Impact - {', '.join(impact_factors[:2])}"
            else:
                return f"Low Impact - {impact_factors[0] if impact_factors else 'Basic data contribution'}"
                
        except Exception as e:
            logger.error(f"Failed to estimate impact: {e}")
            return "Impact estimation unavailable"
    
    def _assess_contribution_value(self, ground_truth_score: float, confidence_level: float) -> str:
        """Assess the value of this contribution to learning"""
        
        if ground_truth_score >= 0.8 and confidence_level >= 0.8:
            return "High Value - Excellent campaign data for model learning"
        elif ground_truth_score >= 0.6 and confidence_level >= 0.6:
            return "Medium Value - Good campaign data with solid metrics"
        elif confidence_level >= 0.7:
            return "Medium Value - High confidence data despite lower performance"
        else:
            return "Standard Value - Contributes to model learning diversity"
    
    async def _compute_learning_statistics(self, enterprise_id: str) -> LearningStatistics:
        """
        Compute learning progress statistics for an enterprise
        """
        
        # Count enterprise submissions
        enterprise_submissions = [
            status for status in self.processing_status.values()
            if status.get('enterprise_id') == enterprise_id
        ]
        
        total_submissions = len(enterprise_submissions)
        processed_submissions = sum(
            1 for status in enterprise_submissions 
            if status.get('status') == 'processed'
        )
        
        # Calculate average ground truth score
        ground_truth_scores = [
            status.get('ground_truth_score', 0)
            for status in enterprise_submissions
            if status.get('ground_truth_score') is not None
        ]
        
        avg_ground_truth = sum(ground_truth_scores) / max(len(ground_truth_scores), 1)
        
        # Mock model improvement (in real system, this would come from model metrics)
        model_improvement = min(processed_submissions * 0.5, 15.0)  # Max 15% improvement
        
        # Mock contribution ranking
        if avg_ground_truth >= 0.8:
            contribution_rank = "Top 10% Contributors"
        elif avg_ground_truth >= 0.6:
            contribution_rank = "Above Average Contributors" 
        else:
            contribution_rank = "Standard Contributors"
        
        return LearningStatistics(
            total_feedback_submissions=total_submissions,
            processed_submissions=processed_submissions,
            average_ground_truth_score=avg_ground_truth,
            model_improvement_percentage=model_improvement,
            last_model_update=datetime.now() - timedelta(days=7),  # Mock
            next_retraining_estimate=datetime.now() + timedelta(days=14),  # Mock
            your_contribution_rank=contribution_rank
        )
    
    async def _get_model_information(self) -> Dict[str, Any]:
        """Get current ML model information"""
        
        return {
            "model_version": "1.0.0",
            "model_type": "LSTM + Transfer Learning",
            "language_model": "PhoBERT (Vietnamese)",
            "total_training_samples": len(self.processing_status),
            "last_training_date": datetime.now() - timedelta(days=7),
            "model_accuracy": 0.87,  # Mock
            "confidence_threshold": 0.75,
            "supported_features": [
                "Universal structure analysis",
                "Vietnamese content processing", 
                "Multi-factor ranking",
                "Confidence estimation"
            ]
        }

# Create FastAPI app instance for mounting
app = FastAPI(
    title="Enterprise ML Data Port",
    description="API for enterprise feedback submission and ML learning statistics",
    version="1.0.0"
)

# Initialize enterprise data port
enterprise_port = EnterpriseDataPort()
enterprise_port.create_data_ingestion_endpoints(app)