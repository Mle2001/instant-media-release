"""
ML-Enhanced Media Ranking Model
LSTM + Transfer Learning model for Vietnamese media recommendation ranking
"""

import os
import json
import math
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass
import asyncio
import pickle

import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from transformers import AutoModel, AutoTokenizer
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score, accuracy_score
import yaml

from loguru import logger
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.storage.agent.sqlite import SqliteAgentStorage

# Optional imports for enhanced functionality
try:
    from agno.tools.googlesearch import GoogleSearchTools
    GOOGLE_SEARCH_AVAILABLE = True
except ImportError:
    logger.warning("GoogleSearchTools not available - enhanced search features disabled")
    GoogleSearchTools = None
    GOOGLE_SEARCH_AVAILABLE = False

# Import our modules - delay imports to avoid circular dependencies
def _import_dependencies():
    """Lazy import dependencies to avoid circular imports"""
    try:
        from .universal_features import UniversalStructureExtractor, UniversalFeatures
        from .ground_truth_collector import GroundTruthKPICollector
        return UniversalStructureExtractor, UniversalFeatures, GroundTruthKPICollector
    except ImportError as e:
        logger.warning(f"ML components import error (will retry later): {e}")
        return None, None, None

def _import_external_dependencies():
    """Lazy import external dependencies"""
    try:
        from database import media_db
        # Define local models to avoid circular imports
        from pydantic import BaseModel
        from typing import Dict, List, Any, Optional
        
        class ContentAnalysis(BaseModel):
            topic: Optional[str] = None
            industry: Optional[str] = None
            content_type: Optional[str] = None
            urgency: Optional[str] = None
            target_audience: Optional[List[str]] = None
        
        class MediaRecommendation(BaseModel):
            outlet_id: str
            outlet_name: str
            relevance_score: float
            reasoning: str
            
        return media_db, ContentAnalysis, MediaRecommendation
    except ImportError as e:
        logger.warning(f"External dependencies import error: {e}")
        return None, None, None


@dataclass
class ModelPrediction:
    """Model prediction result"""
    ranking_score: float
    confidence: float
    attention_weights: Optional[torch.Tensor] = None
    feature_importance: Optional[Dict[str, float]] = None
    reasoning: Optional[str] = None


class MediaRankingDataset(Dataset):
    """
    Dataset for training media ranking model
    """
    
    def __init__(self, features: List[np.ndarray], scores: List[float], texts: List[str] = None, device=None):
        """
        Args:
            features: List of feature vectors
            scores: List of ground truth scores
            texts: Optional list of content texts for text encoding
            device: Device to put tensors on (CPU or CUDA)
        """
        self.device = device or torch.device('cpu')
        self.features = [torch.FloatTensor(f).to(self.device) for f in features]
        self.scores = torch.FloatTensor(scores).to(self.device)
        self.texts = texts or [''] * len(features)
        
        if len(self.features) != len(self.scores):
            raise ValueError("Features and scores must have same length")
    
    def __len__(self):
        return len(self.features)
    
    def __getitem__(self, idx):
        return {
            'features': self.features[idx],
            'score': self.scores[idx],
            'text': self.texts[idx]
        }


class MediaRankingLSTM(nn.Module):
    """
    LSTM + Transfer Learning model for media ranking
    
    Architecture:
    1. PhoBERT encoder for Vietnamese content
    2. Universal features integration
    3. Bidirectional LSTM for temporal patterns
    4. Multi-head attention for media-specific focus
    5. Final ranking prediction layers
    """
    
    def __init__(self, config: Dict[str, Any]):
        super(MediaRankingLSTM, self).__init__()
        
        self.config = config
        model_config = config.get('model', {})
        
        # Model dimensions
        self.content_embedding_dim = model_config.get('content_embedding_dim', 768)
        self.universal_features_dim = model_config.get('universal_features_dim', 50)
        self.lstm_hidden_size = model_config.get('lstm_hidden_size', 256)
        self.lstm_num_layers = model_config.get('lstm_num_layers', 2)
        self.attention_heads = model_config.get('attention_heads', 8)
        
        # Vietnamese language model (PhoBERT)
        base_model_name = model_config.get('base_model', 'vinai/phobert-base')
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(base_model_name)
            self.language_encoder = AutoModel.from_pretrained(base_model_name)
            logger.info(f"✅ Loaded language model: {base_model_name}")
        except Exception as e:
            logger.error(f"❌ Failed to load language model: {e}")
            # Fallback to dummy embeddings for testing
            self.tokenizer = None
            self.language_encoder = nn.Embedding(10000, self.content_embedding_dim)
        
        # Freeze some layers of pre-trained model for transfer learning
        if hasattr(self.language_encoder, 'embeddings'):
            for param in self.language_encoder.embeddings.parameters():
                param.requires_grad = False
        
        # Feature projection layer
        total_input_dim = self.content_embedding_dim + self.universal_features_dim
        
        # LSTM for temporal pattern recognition
        self.lstm = nn.LSTM(
            input_size=total_input_dim,
            hidden_size=self.lstm_hidden_size,
            num_layers=self.lstm_num_layers,
            batch_first=True,
            dropout=model_config.get('lstm_dropout', 0.2),
            bidirectional=model_config.get('lstm_bidirectional', True)
        )
        
        # Bidirectional LSTM output size
        lstm_output_size = self.lstm_hidden_size * (2 if model_config.get('lstm_bidirectional', True) else 1)
        
        # Multi-head attention for media-specific features
        self.attention = nn.MultiheadAttention(
            embed_dim=lstm_output_size,
            num_heads=self.attention_heads,
            dropout=model_config.get('attention_dropout', 0.1),
            batch_first=True
        )
        
        # Final ranking prediction layers
        self.ranking_layers = nn.Sequential(
            nn.Linear(lstm_output_size, 256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 1),  # Single ranking score output
            nn.Sigmoid()  # Ensure output is between 0-1
        )
        
        # Confidence estimation layer
        self.confidence_layer = nn.Sequential(
            nn.Linear(lstm_output_size, 64),
            nn.ReLU(),
            nn.Linear(64, 1),
            nn.Sigmoid()
        )
        
        logger.info(f"✅ MediaRankingLSTM initialized with {self._count_parameters()} parameters")
    
    def _count_parameters(self) -> int:
        """Count total trainable parameters"""
        return sum(p.numel() for p in self.parameters() if p.requires_grad)
    
    def encode_text(self, texts: List[str], max_length: int = 512) -> torch.Tensor:
        """
        Encode Vietnamese text using PhoBERT
        
        Args:
            texts: List of Vietnamese text strings
            max_length: Maximum sequence length
            
        Returns:
            Text embeddings tensor [batch_size, embedding_dim]
        """
        
        if not self.tokenizer:
            # Fallback: use dummy embeddings on correct device
            batch_size = len(texts)
            device = next(self.parameters()).device
            return torch.randn(batch_size, self.content_embedding_dim, device=device)
        
        # Tokenize texts
        encodings = self.tokenizer(
            texts,
            truncation=True,
            padding=True,
            max_length=max_length,
            return_tensors='pt'
        )
        
        # Move encodings to the same device as the model
        device = next(self.parameters()).device
        encodings = {k: v.to(device) for k, v in encodings.items()}
        
        # Get embeddings from PhoBERT
        with torch.no_grad():
            outputs = self.language_encoder(**encodings)
            # Use [CLS] token embedding for sentence representation
            text_embeddings = outputs.last_hidden_state[:, 0, :]  # [batch_size, hidden_size]
        
        return text_embeddings
    
    def forward(
        self, 
        content_texts: List[str],
        universal_features: torch.Tensor,
        return_attention: bool = False
    ) -> Union[torch.Tensor, Tuple[torch.Tensor, torch.Tensor, torch.Tensor]]:
        """
        Forward pass of the model
        
        Args:
            content_texts: List of content text strings
            universal_features: Universal features tensor [batch_size, features_dim]
            return_attention: Whether to return attention weights
            
        Returns:
            ranking_scores: Predicted ranking scores [batch_size, 1]
            confidence_scores: Confidence estimates [batch_size, 1] (if return_attention=True)
            attention_weights: Attention weights (if return_attention=True)
        """
        
        batch_size = len(content_texts)
        device = next(self.parameters()).device
        
        # 1. Encode content text
        content_embeddings = self.encode_text(content_texts)
        content_embeddings = content_embeddings.to(device)
        
        # 2. Ensure universal features are on correct device
        universal_features = universal_features.to(device)
        
        # 3. Combine content embeddings with universal features
        if universal_features.dim() == 2:
            # [batch_size, features_dim] -> [batch_size, 1, features_dim] for sequence
            universal_features = universal_features.unsqueeze(1)
        
        if content_embeddings.dim() == 2:
            # [batch_size, embedding_dim] -> [batch_size, 1, embedding_dim] for sequence
            content_embeddings = content_embeddings.unsqueeze(1)
        
        # Combine features
        combined_features = torch.cat([content_embeddings, universal_features], dim=-1)
        # [batch_size, 1, content_embedding_dim + universal_features_dim]
        
        # 4. LSTM processing for temporal patterns
        lstm_output, (hidden, cell) = self.lstm(combined_features)
        # lstm_output: [batch_size, seq_len=1, lstm_hidden_size * 2]
        
        # 5. Multi-head attention for media-specific focus
        attended_output, attention_weights = self.attention(
            lstm_output, lstm_output, lstm_output
        )
        # attended_output: [batch_size, seq_len=1, lstm_hidden_size * 2]
        
        # 6. Global pooling (since seq_len=1, just squeeze)
        pooled_features = attended_output.squeeze(1)  # [batch_size, lstm_hidden_size * 2]
        
        # 7. Final ranking prediction
        ranking_scores = self.ranking_layers(pooled_features)  # [batch_size, 1]
        
        if return_attention:
            # Also compute confidence scores
            confidence_scores = self.confidence_layer(pooled_features)  # [batch_size, 1]
            return ranking_scores, confidence_scores, attention_weights
        else:
            return ranking_scores
    
    def predict_single(
        self, 
        content_text: str, 
        universal_features: np.ndarray
    ) -> ModelPrediction:
        """
        Predict ranking score for a single content-media pair
        
        Args:
            content_text: Content text string
            universal_features: Universal features array
            
        Returns:
            ModelPrediction: Prediction result with score and confidence
        """
        
        self.eval()
        with torch.no_grad():
            # Prepare inputs
            universal_tensor = torch.FloatTensor(universal_features).unsqueeze(0)  # Add batch dim
            
            # Forward pass
            ranking_score, confidence, attention_weights = self.forward(
                [content_text], 
                universal_tensor,
                return_attention=True
            )
            
            prediction = ModelPrediction(
                ranking_score=ranking_score.item(),
                confidence=confidence.item(),
                attention_weights=attention_weights,
                reasoning=self._generate_prediction_reasoning(
                    ranking_score.item(), 
                    confidence.item(),
                    attention_weights
                )
            )
            
        return prediction
    
    def _generate_prediction_reasoning(
        self,
        score: float, 
        confidence: float,
        attention_weights: torch.Tensor
    ) -> str:
        """Generate human-readable reasoning for prediction"""
        
        if score >= 0.8:
            score_desc = "Very High Match"
        elif score >= 0.6:
            score_desc = "Good Match" 
        elif score >= 0.4:
            score_desc = "Moderate Match"
        else:
            score_desc = "Low Match"
        
        if confidence >= 0.8:
            conf_desc = "High Confidence"
        elif confidence >= 0.6:
            conf_desc = "Medium Confidence"
        else:
            conf_desc = "Low Confidence"
        
        reasoning = f"{score_desc} ({score:.3f}) with {conf_desc} ({confidence:.3f})"
        
        return reasoning


class EnhancedMediaRankingAgent(Agent):
    """
    Enhanced Media Specialist Agent với ML-powered ranking
    Integrates seamlessly with existing Agno agent system
    """
    
    def __init__(self, model_path: str = None):
        """Initialize enhanced media agent with ML model"""
        
        # Lazy import to avoid circular dependencies
        _, _, MediaRecommendation = _import_external_dependencies()
        
        # Initialize base Agent
        super().__init__(
            name="Enhanced Media Specialist",
            role="AI-powered media outlet recommendation with learning capabilities",
            model=OpenAIChat(id="gpt-4o"),
            tools=[GoogleSearchTools()] if GOOGLE_SEARCH_AVAILABLE and GoogleSearchTools else [],
            structured_outputs=True,
            response_model=MediaRecommendation if MediaRecommendation else dict,
            storage=SqliteAgentStorage(table_name="enhanced_media_sessions"),
            instructions="""
            You are an advanced media specialist with ML-enhanced ranking capabilities.
            Your role is to recommend the best Vietnamese media outlets for press releases
            using both traditional analysis and machine learning predictions.
            
            Always provide:
            1. ML-powered ranking scores with confidence levels
            2. Clear reasoning for each recommendation
            3. Budget-optimized media selections
            4. Tier-balanced coverage recommendations
            
            Focus on Vietnamese market expertise and data-driven insights.
            """
        )
        
        # Load configuration
        self.config = self._load_config()
        
        # Initialize ML components
        self.ml_model = None
        from .universal_features import UniversalStructureExtractor
        from .ground_truth_collector import GroundTruthKPICollector
        self.feature_extractor = UniversalStructureExtractor()
        self.ground_truth_collector = GroundTruthKPICollector()
        
        # Load trained ML model - auto-detect latest if not specified
        self.model_path = self._get_latest_model_path() if model_path is None else model_path
        self._load_ml_model()
        
        # Feature scaling
        self.feature_scaler = StandardScaler()
        self._load_feature_scaler()
        
        logger.info("✅ EnhancedMediaRankingAgent initialized with ML capabilities")
    
    def _load_config(self) -> Dict:
        """Load ML configuration"""
        try:
            with open('./config/ml_config.yaml', 'r') as f:
                config = yaml.safe_load(f)
            return config
        except Exception as e:
            logger.warning(f"Could not load ML config: {e}")
            return {
                'model': {
                    'content_embedding_dim': 768,
                    'universal_features_dim': 50,
                    'lstm_hidden_size': 256
                }
            }
    
    def _get_latest_model_path(self) -> str:
        """Get the latest trained model path"""
        import glob
        from pathlib import Path
        
        models_dir = Path("./models")
        
        # First check for production model
        production_model = models_dir / "production_model.pth"
        if production_model.exists():
            logger.info(f"🎯 Using production model: {production_model}")
            return str(production_model)
        
        # Look for latest versioned model
        pattern = str(models_dir / "media_ranking_lstm_v*.pth")
        model_files = glob.glob(pattern)
        
        if model_files:
            # Sort by modification time to get latest
            latest_model = max(model_files, key=os.path.getmtime)
            logger.info(f"📈 Using latest model: {latest_model}")
            return latest_model
        
        # Fallback to default path
        fallback = "./models/media_ranking_lstm_v1.pth"
        logger.warning(f"⚠️ No models found, using fallback: {fallback}")
        return fallback
    
    def _load_ml_model(self):
        """Load trained ML model"""
        try:
            if os.path.exists(self.model_path):
                try:
                    checkpoint = torch.load(self.model_path, map_location='cpu', weights_only=False)
                    # Update config with checkpoint config if available
                    if 'config' in checkpoint:
                        self.config.update(checkpoint['config'])
                    
                    self.ml_model = MediaRankingLSTM(self.config)
                    self.ml_model.load_state_dict(checkpoint['model_state_dict'])
                    self.ml_model.eval()
                    logger.info(f"Loaded ML model from {self.model_path}")
                except Exception as load_error:
                    logger.error(f"Failed to load ML model: {load_error}")
                    logger.info("Initializing new model without pretrained weights")
                    self.ml_model = MediaRankingLSTM(self.config)
            else:
                logger.warning(f"ML model not found at {self.model_path}, using traditional ranking")
                self.ml_model = None
        except Exception as e:
            logger.error(f"❌ Failed to load ML model: {e}")
            self.ml_model = None
    
    def _load_feature_scaler(self):
        """Load feature scaler"""
        scaler_path = "./models/feature_scaler.pkl"
        try:
            if os.path.exists(scaler_path):
                with open(scaler_path, 'rb') as f:
                    self.feature_scaler = pickle.load(f)
                logger.info("✅ Loaded feature scaler")
            else:
                # Initialize and fit feature scaler with dummy data if not found
                from sklearn.preprocessing import StandardScaler
                import numpy as np
                self.feature_scaler = StandardScaler()
                # Fit with dummy data - check actual feature count first
                from .universal_features import UniversalStructureExtractor
                temp_extractor = UniversalStructureExtractor()
                # Get actual feature count by running a test extraction
                # Use dummy analysis for testing feature count
                import asyncio
                dummy_analysis = {
                    'industry_sector': 'technology',
                    'content': 'test content',
                    'budget_range': 'medium',
                    'target_audience': ['businesses'],
                    'campaign_type': 'product_launch'
                }
                try:
                    test_features = asyncio.run(temp_extractor.extract_universal_features(dummy_analysis))
                    test_vector = test_features.to_vector() if hasattr(test_features, 'to_vector') else None
                except:
                    test_vector = None
                feature_count = len(test_vector) if test_vector is not None else 64  # Updated default to 64
                dummy_data = np.random.randn(10, feature_count)  # Use actual feature count
                self.feature_scaler.fit(dummy_data)
                logger.warning("Feature scaler not found, initialized with default fitting")
        except Exception as e:
            logger.warning(f"Could not load feature scaler: {e}")
    
    async def enhanced_media_recommendation(
        self,
        content_analysis: Dict[str, Any],
        budget_constraints: Dict[str, Any],
        progress_callback: Optional[callable] = None
    ) -> List[Dict[str, Any]]:
        """
        Enhanced media recommendation using ML ranking
        
        Args:
            content_analysis: Analyzed content data
            budget_constraints: Budget and package info  
            progress_callback: Optional progress callback
            
        Returns:
            List of enhanced media recommendations
        """
        
        logger.info("🧠 Starting ML-enhanced media recommendation...")
        
        if progress_callback:
            await progress_callback({
                "step": "enhanced_media_matching",
                "message": "🧠 Applying ML-enhanced ranking...",
                "completed": 0,
                "total": 4,
                "percentage": 0
            })
        
        # 1. Extract universal features
        try:
            universal_features = await self.feature_extractor.extract_universal_features(
                content_analysis
            )
            feature_vector = universal_features.to_vector()
            
            # Scale features
            if hasattr(self.feature_scaler, 'transform'):
                feature_vector = self.feature_scaler.transform(feature_vector.reshape(1, -1))[0]
            
            logger.info(f"📊 Extracted {len(feature_vector)} universal features")
            
        except Exception as e:
            logger.error(f"❌ Feature extraction failed: {e}")
            # Fallback to traditional recommendation
            return await self._traditional_recommendation(content_analysis, budget_constraints)
        
        if progress_callback:
            await progress_callback({
                "step": "feature_engineering",
                "message": "⚙️ Engineering features for ML model...",
                "completed": 1,
                "total": 4,
                "percentage": 25
            })
        
        # 2. Get candidate media outlets
        try:
            candidate_outlets = await self._get_candidate_outlets(content_analysis)
            logger.info(f"📰 Found {len(candidate_outlets)} candidate outlets")
        except Exception as e:
            logger.error(f"❌ Failed to get candidates: {e}")
            return []
        
        if progress_callback:
            await progress_callback({
                "step": "ml_ranking",
                "message": "🤖 Applying ML ranking predictions...",
                "completed": 2, 
                "total": 4,
                "percentage": 50
            })
        
        # 3. Apply ML ranking if model is available
        enhanced_recommendations = []
        content_text = content_analysis.get('content', '') or content_analysis.get('user_input', '')
        
        for outlet in candidate_outlets:
            try:
                # Get ML prediction if model available
                if self.ml_model:
                    ml_prediction = self.ml_model.predict_single(content_text, feature_vector)
                    ml_score = ml_prediction.ranking_score
                    ml_confidence = ml_prediction.confidence
                    ml_reasoning = ml_prediction.reasoning
                else:
                    # Fallback to traditional scoring
                    ml_score = self._compute_traditional_score(content_analysis, outlet)
                    ml_confidence = 0.5
                    ml_reasoning = "Traditional rule-based scoring"
                
                # Combine with traditional signals for hybrid approach
                traditional_score = self._compute_traditional_score(content_analysis, outlet)
                
                # Weighted combination (70% ML, 30% traditional)
                if self.ml_model:
                    final_score = 0.7 * ml_score + 0.3 * traditional_score
                else:
                    final_score = traditional_score
                
                # Create enhanced recommendation
                recommendation = {
                    'media_outlet_id': outlet.get('id', 0),
                    'media_name': outlet.get('name', ''),
                    'matching_score': min(max(final_score, 0.0), 1.0),
                    'ml_score': ml_score,
                    'traditional_score': traditional_score,
                    'confidence': ml_confidence,
                    'reasoning': ml_reasoning,
                    'estimated_reach': outlet.get('monthly_visits', 0),
                    'cost_vnd': outlet.get('cost_per_article', 0),
                    'tier': outlet.get('tier', 3),
                    'language_match': True,  # Assuming all outlets support Vietnamese
                    'topic_overlap': self._compute_topic_overlap(content_analysis, outlet),
                    'audience_fit': self._compute_audience_fit(content_analysis, outlet),
                    'category': outlet.get('category', 'UNKNOWN')
                }
                
                enhanced_recommendations.append(recommendation)
                
            except Exception as e:
                logger.error(f"❌ Failed to process outlet {outlet.get('name', 'Unknown')}: {e}")
                continue
        
        if progress_callback:
            await progress_callback({
                "step": "ranking_finalization", 
                "message": "🎯 Finalizing ML-enhanced recommendations...",
                "completed": 3,
                "total": 4,
                "percentage": 75
            })
        
        # 4. Sort by enhanced scores and apply budget filtering
        enhanced_recommendations.sort(key=lambda x: x['matching_score'], reverse=True)
        
        # Apply budget constraints
        final_recommendations = self._apply_budget_filtering(
            enhanced_recommendations, 
            budget_constraints
        )
        
        if progress_callback:
            await progress_callback({
                "step": "enhanced_recommendations_complete",
                "message": f"✅ Generated {len(final_recommendations)} ML-enhanced recommendations",
                "completed": 4,
                "total": 4,
                "percentage": 100
            })
        
        logger.info(f"🎯 Enhanced recommendation complete: {len(final_recommendations)} outlets")
        
        return final_recommendations[:15]  # Return top 15
    
    async def _get_candidate_outlets(self, content_analysis: Dict) -> List[Dict]:
        """Get candidate media outlets from database"""
        try:
            # This would integrate with existing database
            # For now, return mock data structure
            mock_outlets = [
                {
                    'id': 1, 'name': 'VnExpress', 'tier': 1, 'category': 'MAINSTREAM',
                    'monthly_visits': 25000000, 'cost_per_article': 8000000
                },
                {
                    'id': 2, 'name': 'CafeF', 'tier': 1, 'category': 'BUSINESS', 
                    'monthly_visits': 3000000, 'cost_per_article': 3000000
                },
                {
                    'id': 3, 'name': 'GenK', 'tier': 2, 'category': 'TECHNOLOGY',
                    'monthly_visits': 2000000, 'cost_per_article': 2000000
                }
            ]
            return mock_outlets
            
        except Exception as e:
            logger.error(f"Failed to get candidates: {e}")
            return []
    
    def _compute_traditional_score(self, content_analysis: Dict, outlet: Dict) -> float:
        """Compute traditional rule-based matching score"""
        
        score = 0.5  # Base score
        
        # Industry/category matching
        industry = content_analysis.get('industry_sector', '').lower()
        outlet_category = outlet.get('category', '').lower()
        
        category_matches = {
            'tech': 'technology',
            'technology': 'technology', 
            'finance': 'business',
            'business': 'business',
            'startup': 'business'
        }
        
        if industry in category_matches and category_matches[industry] in outlet_category:
            score += 0.3
        
        # Tier preference (higher tier = higher score)
        tier = outlet.get('tier', 3)
        tier_bonus = (4 - tier) * 0.1  # Tier 1 = +0.3, Tier 2 = +0.2, etc.
        score += tier_bonus
        
        # Reach consideration 
        reach = outlet.get('monthly_visits', 0)
        if reach > 10000000:  # 10M+ = premium
            score += 0.1
        elif reach > 1000000:  # 1M+ = good
            score += 0.05
        
        return min(max(score, 0.0), 1.0)
    
    def _compute_topic_overlap(self, content_analysis: Dict, outlet: Dict) -> float:
        """Compute topic overlap score"""
        # Simplified implementation
        return 0.7  # Mock score
    
    def _compute_audience_fit(self, content_analysis: Dict, outlet: Dict) -> float:
        """Compute audience fit score"""
        # Simplified implementation  
        return 0.8  # Mock score
    
    def _apply_budget_filtering(
        self, 
        recommendations: List[Dict], 
        budget_constraints: Dict
    ) -> List[Dict]:
        """Apply budget constraints to filter recommendations"""
        
        budget = budget_constraints.get('budget', float('inf'))
        
        filtered = []
        cumulative_cost = 0
        
        for rec in recommendations:
            cost = rec.get('cost_vnd', 0)
            if cumulative_cost + cost <= budget:
                filtered.append(rec)
                cumulative_cost += cost
            else:
                break
        
        return filtered
    
    async def _traditional_recommendation(
        self, 
        content_analysis: Dict,
        budget_constraints: Dict
    ) -> List[Dict]:
        """Fallback traditional recommendation"""
        logger.info("📰 Using traditional recommendation (ML unavailable)")
        
        candidates = await self._get_candidate_outlets(content_analysis)
        
        recommendations = []
        for outlet in candidates:
            score = self._compute_traditional_score(content_analysis, outlet)
            
            rec = {
                'media_outlet_id': outlet.get('id', 0),
                'media_name': outlet.get('name', ''),
                'matching_score': score,
                'reasoning': 'Traditional rule-based matching',
                'estimated_reach': outlet.get('monthly_visits', 0),
                'cost_vnd': outlet.get('cost_per_article', 0),
                'tier': outlet.get('tier', 3),
                'language_match': True,
                'topic_overlap': 0.7,
                'audience_fit': 0.8
            }
            recommendations.append(rec)
        
        recommendations.sort(key=lambda x: x['matching_score'], reverse=True)
        return self._apply_budget_filtering(recommendations, budget_constraints)


# Training and utility functions
class ModelTrainer:
    """
    Trainer for MediaRankingLSTM model
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.training_config = config.get('training', {})
        
        # Training parameters
        self.batch_size = self.training_config.get('batch_size', 32)
        self.learning_rate = self.training_config.get('learning_rate', 0.001)
        self.epochs = self.training_config.get('epochs', 50)
        self.validation_split = self.training_config.get('validation_split', 0.2)
        
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Initialize feature extractor for handling raw data
        self.feature_extractor = None
        logger.info(f"🎯 Training device: {self.device}")
    
    def prepare_data(
        self, 
        training_samples: List[Dict]
    ) -> Tuple[DataLoader, DataLoader]:
        """
        Prepare training and validation data loaders
        
        Args:
            training_samples: List of training samples from GroundTruthKPICollector
            
        Returns:
            train_loader, val_loader
        """
        
        # Extract features, scores, and texts
        features = []
        scores = []
        texts = []
        
        for sample in training_samples:
            try:
                # Handle both formats: pre-extracted features or raw data
                if 'features' in sample:
                    # Pre-extracted features format
                    feature_vector = np.array(sample['features'])
                    ground_truth = sample['ground_truth_score']
                    content_text = sample.get('original_content', '') or ''
                else:
                    # Raw database format - extract features on the fly
                    if not hasattr(self, 'feature_extractor') or self.feature_extractor is None:
                        # Initialize feature extractor if needed
                        from .universal_features import UniversalStructureExtractor
                        self.feature_extractor = UniversalStructureExtractor()
                    
                    # Extract features from campaign data
                    campaign_data = {
                        'campaign_title': sample.get('campaign_title', ''),
                        'industry': sample.get('industry', ''),
                        'budget': sample.get('budget', 0),
                        'roi_percentage': sample.get('roi_percentage', 0),
                        'total_media_reach': sample.get('total_media_reach', 0),
                        'average_engagement_rate': sample.get('average_engagement_rate', 0),
                    }
                    
                    # Create content analysis dict for feature extraction
                    content_analysis = {
                        'industry_sector': campaign_data.get('industry', ''),
                        'content': campaign_data.get('campaign_title', ''),
                        'budget': campaign_data.get('budget', 0),
                        'roi_target': campaign_data.get('roi_percentage', 0),
                    }
                    
                    # Extract features using async method
                    import asyncio
                    if asyncio.iscoroutinefunction(self.feature_extractor.extract_universal_features):
                        # If we're in async context
                        try:
                            loop = asyncio.get_event_loop()
                            universal_features = loop.run_until_complete(
                                self.feature_extractor.extract_universal_features(content_analysis)
                            )
                        except RuntimeError:
                            # Create new event loop if needed
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            universal_features = loop.run_until_complete(
                                self.feature_extractor.extract_universal_features(content_analysis)
                            )
                        
                        feature_vector = universal_features.to_vector()
                    else:
                        # Fallback to sync method if available
                        universal_features = self.feature_extractor.extract_universal_features(content_analysis)
                        feature_vector = universal_features.to_vector()
                    
                    if feature_vector is None:
                        logger.warning("Failed to extract features from sample")
                        continue
                        
                    ground_truth = sample.get('ground_truth_score', 0)
                    content_text = campaign_data.get('campaign_title', '')
                
                # Validate sample
                if len(feature_vector) > 0 and 0 <= ground_truth <= 1:
                    features.append(feature_vector)
                    scores.append(ground_truth)
                    texts.append(content_text)
                    
            except Exception as e:
                logger.warning(f"Skipping invalid training sample: {e}")
                continue
        
        if len(features) == 0:
            raise ValueError("No valid training samples found")
        
        # Split train/validation
        split_idx = int(len(features) * (1 - self.validation_split))
        
        train_features = features[:split_idx]
        train_scores = scores[:split_idx]
        train_texts = texts[:split_idx]
        
        val_features = features[split_idx:]
        val_scores = scores[split_idx:]
        val_texts = texts[split_idx:]
        
        # Create datasets with correct device
        train_dataset = MediaRankingDataset(train_features, train_scores, train_texts, device=self.device)
        val_dataset = MediaRankingDataset(val_features, val_scores, val_texts, device=self.device)
        
        # Create data loaders with proper CUDA settings
        train_loader = DataLoader(
            train_dataset, 
            batch_size=self.batch_size,
            shuffle=True,
            num_workers=0,  # Set to 0 for Windows compatibility
            pin_memory=False  # Disable pin_memory to avoid CUDA issues
        )
        
        val_loader = DataLoader(
            val_dataset,
            batch_size=self.batch_size,
            shuffle=False,
            num_workers=0,
            pin_memory=False
        )
        
        logger.info(f"📊 Training samples: {len(train_dataset)}")
        logger.info(f"📊 Validation samples: {len(val_dataset)}")
        
        return train_loader, val_loader
    
    def train_model(
        self, 
        model: MediaRankingLSTM,
        train_loader: DataLoader,
        val_loader: DataLoader,
        save_path: str = "./models/media_ranking_lstm.pth"
    ) -> Dict[str, Any]:
        """
        Train the MediaRankingLSTM model
        
        Returns:
            Training history and metrics
        """
        
        model = model.to(self.device)
        
        # Loss function and optimizer
        criterion = nn.MSELoss()
        optimizer = optim.Adam(model.parameters(), lr=self.learning_rate)
        scheduler = optim.lr_scheduler.ReduceLROnPlateau(
            optimizer, mode='min', factor=0.5, patience=5
        )
        
        # Training history
        history = {
            'train_loss': [],
            'val_loss': [],
            'val_r2': []
        }
        
        best_val_loss = float('inf')
        patience_counter = 0
        patience_limit = self.training_config.get('early_stopping_patience', 10)
        
        logger.info(f"🚀 Starting training for {self.epochs} epochs...")
        
        for epoch in range(self.epochs):
            # Training phase
            model.train()
            train_losses = []
            
            for batch in train_loader:
                optimizer.zero_grad()
                
                # Get batch data - they should already be on correct device from dataset
                features = batch['features']
                scores = batch['score'].unsqueeze(1)
                texts = batch['text']
                
                # Forward pass
                try:
                    predictions = model(texts, features)
                    loss = criterion(predictions, scores)
                    
                    # Backward pass
                    loss.backward()
                    optimizer.step()
                    
                    train_losses.append(loss.item())
                    
                except Exception as e:
                    logger.error(f"Training batch error: {e}")
                    continue
            
            # Validation phase
            model.eval()
            val_losses = []
            val_predictions = []
            val_targets = []
            
            with torch.no_grad():
                for batch in val_loader:
                    # Data should already be on correct device from dataset
                    features = batch['features'] 
                    scores = batch['score'].unsqueeze(1)
                    texts = batch['text']
                    
                    try:
                        predictions = model(texts, features)
                        loss = criterion(predictions, scores)
                        
                        val_losses.append(loss.item())
                        val_predictions.extend(predictions.cpu().numpy())
                        val_targets.extend(scores.cpu().numpy())
                        
                    except Exception as e:
                        logger.error(f"Validation batch error: {e}")
                        continue
            
            # Calculate metrics
            avg_train_loss = np.mean(train_losses) if train_losses else float('inf')
            avg_val_loss = np.mean(val_losses) if val_losses else float('inf')
            
            val_r2 = 0.0
            if val_predictions and val_targets:
                try:
                    val_r2 = r2_score(val_targets, val_predictions)
                except:
                    val_r2 = 0.0
            
            # Update history
            history['train_loss'].append(avg_train_loss)
            history['val_loss'].append(avg_val_loss)
            history['val_r2'].append(val_r2)
            
            # Learning rate scheduling
            scheduler.step(avg_val_loss)
            
            # Early stopping check
            if avg_val_loss < best_val_loss:
                best_val_loss = avg_val_loss
                patience_counter = 0
                
                # Save best model
                try:
                    os.makedirs(os.path.dirname(save_path), exist_ok=True)
                    torch.save({
                        'epoch': epoch,
                        'model_state_dict': model.state_dict(),
                        'optimizer_state_dict': optimizer.state_dict(),
                        'train_loss': avg_train_loss,
                        'val_loss': avg_val_loss,
                        'val_r2': val_r2,
                        'config': self.config
                    }, save_path)
                    
                except Exception as e:
                    logger.error(f"Failed to save model: {e}")
            else:
                patience_counter += 1
            
            # Log progress
            if epoch % 5 == 0:
                logger.info(
                    f"Epoch {epoch:3d}/{self.epochs} | "
                    f"Train Loss: {avg_train_loss:.4f} | "
                    f"Val Loss: {avg_val_loss:.4f} | "
                    f"Val R²: {val_r2:.4f}"
                )
            
            # Early stopping
            if patience_counter >= patience_limit:
                logger.info(f"Early stopping at epoch {epoch}")
                break
        
        logger.info(f"✅ Training completed. Best validation loss: {best_val_loss:.4f}")
        
        return history


def create_default_model(config_path: str = "./config/ml_config.yaml") -> MediaRankingLSTM:
    """
    Create a default MediaRankingLSTM model with configuration
    
    This can be used for initial model creation before training
    """
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        logger.warning(f"Could not load config: {e}")
        config = {
            'model': {
                'content_embedding_dim': 768,
                'universal_features_dim': 50,
                'lstm_hidden_size': 256,
                'lstm_num_layers': 2,
                'attention_heads': 8
            }
        }
    
    model = MediaRankingLSTM(config)
    logger.info("✅ Created default MediaRankingLSTM model")
    
    return model