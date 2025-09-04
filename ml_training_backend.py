"""
Real ML Training Backend for Dashboard Integration
Connects ML model with training data from database
"""

import os
import sys
import json
import sqlite3
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import torch
import torch.nn as nn
from pathlib import Path

# Add ML system to path
sys.path.append(str(Path(__file__).parent / "ml_ranking_system"))

try:
    from ml_ranking_system.ml_ranking_model import MediaRankingLSTM, ModelTrainer, MediaRankingDataset
    from ml_ranking_system.universal_features import UniversalStructureExtractor, UniversalFeatures
    ML_AVAILABLE = True
except ImportError as e:
    print(f"Warning: ML components not available - {e}")
    ML_AVAILABLE = False

class RealMLTrainingBackend:
    """Real ML training backend that connects to database"""
    
    def __init__(self):
        self.model_dir = Path("./models")
        self.model_dir.mkdir(exist_ok=True)
        
        self.config = {
            'model': {
                'content_embedding_dim': 768,
                'universal_features_dim': 64,  # Updated to match actual UniversalStructureExtractor output
                'lstm_hidden_size': 256,
                'lstm_num_layers': 2,
                'attention_heads': 8,
                'lstm_dropout': 0.2,
                'attention_dropout': 0.1,
                'lstm_bidirectional': True
            },
            'training': {
                'batch_size': 16,
                'learning_rate': 0.0005,
                'epochs': 30,
                'validation_split': 0.1,  # Reduced to ensure at least 2 validation samples
                'early_stopping_patience': 8
            }
        }
        
        self.feature_extractor = None
        if ML_AVAILABLE:
            try:
                self.feature_extractor = UniversalStructureExtractor()
            except Exception as e:
                print(f"Warning: Could not initialize feature extractor - {e}")
    
    def load_training_data_from_database(self) -> List[Dict]:
        """Load real training data from ml_feedback_data table"""
        
        conn = sqlite3.connect("media_release.db")
        cursor = conn.cursor()
        
        # Get validated campaign data
        cursor.execute("""
            SELECT campaign_title, campaign_type, industry, budget,
                   total_articles_published, total_media_reach, lead_generation,
                   sales_conversion, roi_percentage, ground_truth_score,
                   target_audience, click_through_rate, social_media_shares,
                   media_quality_score, brand_awareness_lift, average_engagement_rate,
                   comment_sentiment_score, audience_retention_rate, cost_per_acquisition,
                   created_at
            FROM ml_feedback_data 
            WHERE validated = 1 AND ground_truth_score IS NOT NULL
            ORDER BY created_at DESC
        """)
        
        rows = cursor.fetchall()
        
        training_samples = []
        
        for row in rows:
            try:
                # Parse row data
                (title, campaign_type, industry, budget, articles, reach, leads,
                 conversions, roi, ground_truth, target_audience, ctr, shares,
                 quality, awareness, engagement, sentiment, retention, cpa, created_at) = row
                
                # Create content text for text embedding
                content_text = f"{title}. Campaign type: {campaign_type}. Industry: {industry}."
                
                # Extract universal features
                features = self._extract_universal_features({
                    'campaign_title': title,
                    'campaign_type': campaign_type,
                    'industry': industry,
                    'budget': budget,
                    'articles': articles,
                    'reach': reach,
                    'leads': leads,
                    'conversions': conversions,
                    'roi': roi,
                    'ctr': ctr,
                    'shares': shares,
                    'quality': quality,
                    'awareness': awareness,
                    'engagement': engagement,
                    'sentiment': sentiment,
                    'retention': retention
                })
                
                sample = {
                    'features': features,  # Key expected by ModelTrainer
                    'ground_truth_score': ground_truth,
                    'original_content': content_text,  # Key expected by ModelTrainer  
                    'campaign_title': title,  # Also keep for fallback processing
                    'industry': industry,
                    'budget': budget,
                    'roi_percentage': roi,
                    'total_media_reach': reach,
                    'average_engagement_rate': engagement,
                    'metadata': {
                        'campaign_id': title,
                        'industry': industry,
                        'budget': budget,
                        'created_at': created_at
                    }
                }
                
                training_samples.append(sample)
                
            except Exception as e:
                print(f"Warning: Failed to process training sample - {e}")
                continue
        
        # Close connection after processing all data
        conn.close()
        
        print(f"Loaded {len(training_samples)} training samples from database")
        return training_samples
    
    def _extract_universal_features(self, campaign_data: Dict) -> np.ndarray:
        """Extract universal features from campaign data"""
        
        if self.feature_extractor and ML_AVAILABLE:
            try:
                # Use real feature extractor
                content_analysis = {
                    'industry_sector': campaign_data.get('industry', ''),
                    'content': campaign_data.get('campaign_title', ''),
                    'budget_range': self._categorize_budget(campaign_data.get('budget', 0)),
                    'target_audience': campaign_data.get('target_audience', []),
                    'campaign_type': campaign_data.get('campaign_type', ''),
                }
                
                # This would normally be async, but we'll make it sync for simplicity
                import asyncio
                try:
                    # Try to run async extraction
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    features = loop.run_until_complete(
                        self.feature_extractor.extract_universal_features(content_analysis)
                    )
                    return features.to_vector()
                except:
                    # Fallback to manual feature extraction
                    return self._manual_feature_extraction(campaign_data)
            except Exception as e:
                print(f"Feature extraction error: {e}")
                return self._manual_feature_extraction(campaign_data)
        else:
            return self._manual_feature_extraction(campaign_data)
    
    def _manual_feature_extraction(self, campaign_data: Dict) -> np.ndarray:
        """Manual feature extraction as fallback"""
        
        features = []
        
        # Budget features (normalized)
        budget = campaign_data.get('budget', 0)
        features.extend([
            min(budget / 100_000_000, 1.0),  # Budget normalized to 100M max
            1.0 if budget > 50_000_000 else 0.0,  # High budget flag
            1.0 if budget > 20_000_000 else 0.0,  # Medium budget flag
        ])
        
        # Performance features
        articles = campaign_data.get('articles', 0)
        reach = campaign_data.get('reach', 0)
        leads = campaign_data.get('leads', 0)
        
        features.extend([
            min(articles / 20, 1.0),  # Articles normalized
            min(reach / 1_000_000, 1.0),  # Reach normalized to 1M
            min(leads / 5000, 1.0),  # Leads normalized
        ])
        
        # Quality features
        roi = campaign_data.get('roi', 0)
        quality = campaign_data.get('quality', 0)
        engagement = campaign_data.get('engagement', 0)
        
        features.extend([
            min(roi / 1000, 1.0),  # ROI normalized
            quality / 10.0 if quality else 0.5,  # Quality score
            engagement * 100 if engagement else 0.035,  # Engagement rate
        ])
        
        # Industry encoding (one-hot style)
        industry = campaign_data.get('industry', '').lower()
        industry_features = [0.0] * 10  # 10 industry categories
        
        industry_map = {
            'technology': 0, 'artificial_intelligence': 0,
            'financial_technology': 1, 'fintech': 1, 'finance': 1,
            'healthcare': 2, 'health': 2,
            'education': 3, 'education_technology': 3,
            'retail': 4, 'fashion_retail': 4,
            'manufacturing': 5,
            'food_beverage': 6, 'restaurant': 6,
            'logistics_technology': 7, 'logistics': 7,
            'blockchain_technology': 8, 'blockchain': 8,
            'entertainment': 9, 'media': 9
        }
        
        if industry in industry_map:
            industry_features[industry_map[industry]] = 1.0
        
        features.extend(industry_features)
        
        # Campaign type encoding
        campaign_type = campaign_data.get('campaign_type', '').lower()
        type_features = [0.0] * 5
        
        type_map = {
            'product_launch': 0,
            'brand_awareness': 1,
            'lead_generation': 2,
            'event_promotion': 3,
            'crisis_management': 4
        }
        
        if campaign_type in type_map:
            type_features[type_map[campaign_type]] = 1.0
        
        features.extend(type_features)
        
        # Additional derived features
        conversion_rate = 0.0
        if leads > 0:
            conversions = campaign_data.get('conversions', 0)
            conversion_rate = min(conversions / leads, 1.0)
        
        cost_efficiency = 0.0
        if leads > 0 and budget > 0:
            cost_efficiency = min(leads / (budget / 1_000_000), 1.0)
        
        features.extend([
            conversion_rate,
            cost_efficiency,
            campaign_data.get('sentiment', 0.5),  # Sentiment score
            campaign_data.get('retention', 0.8),  # Retention rate
        ])
        
        # Pad to target dimension (50 features)
        while len(features) < 50:
            features.append(0.0)
        
        return np.array(features[:50], dtype=np.float32)
    
    def _categorize_budget(self, budget: float) -> str:
        """Categorize budget into ranges"""
        if budget >= 50_000_000:
            return "high"
        elif budget >= 20_000_000:
            return "medium"
        elif budget >= 5_000_000:
            return "low"
        else:
            return "micro"
    
    def train_model(
        self, 
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """Train the ML model with real data"""
        
        if not ML_AVAILABLE:
            raise RuntimeError("ML components not available")
        
        # Load training data
        if progress_callback:
            progress_callback("Loading training data from database...", 0, 100, 0)
        
        training_samples = self.load_training_data_from_database()
        
        if len(training_samples) < 5:
            raise ValueError(f"Need at least 5 training samples, got {len(training_samples)}")
        
        if progress_callback:
            progress_callback("Initializing ML model...", 1, 100, 10)
        
        # Create model with corrected config
        print(f"[DEBUG] Creating model with config: {self.config['model']}")
        print(f"[DEBUG] Expected input size: {self.config['model']['content_embedding_dim'] + self.config['model']['universal_features_dim']}")
        
        model = MediaRankingLSTM(self.config)
        trainer = ModelTrainer(self.config)
        
        if progress_callback:
            progress_callback("Preparing training data...", 2, 100, 20)
        
        # Prepare data loaders
        train_loader, val_loader = trainer.prepare_data(training_samples)
        
        if progress_callback:
            progress_callback("Starting model training...", 3, 100, 30)
        
        # Train model with progress tracking - use new path to avoid conflicts
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_path = self.model_dir / f"media_ranking_lstm_retrained_{timestamp}.pth"
        
        # Custom training with progress updates
        history = self._train_with_progress(
            model, trainer, train_loader, val_loader, 
            model_path, progress_callback
        )
        
        if progress_callback:
            progress_callback("Training completed successfully!", 100, 100, 100)
        
        # Calculate final metrics
        final_metrics = {
            'final_train_loss': history['train_loss'][-1] if history['train_loss'] else 0,
            'final_val_loss': history['val_loss'][-1] if history['val_loss'] else 0,
            'final_val_r2': history['val_r2'][-1] if history['val_r2'] else 0,
            'epochs_trained': len(history['train_loss']),
            'training_samples': len(training_samples),
            'model_path': str(model_path)
        }
        
        return final_metrics
    
    def _train_with_progress(
        self,
        model: MediaRankingLSTM,
        trainer: ModelTrainer,
        train_loader,
        val_loader,
        save_path: Path,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """Train model with progress updates"""
        
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        model = model.to(device)
        
        # Setup training
        criterion = nn.MSELoss()
        optimizer = torch.optim.Adam(model.parameters(), lr=trainer.learning_rate)
        
        history = {'train_loss': [], 'val_loss': [], 'val_r2': []}
        best_val_loss = float('inf')
        
        epochs = trainer.epochs
        
        for epoch in range(epochs):
            # Training phase
            model.train()
            train_losses = []
            
            for batch in train_loader:
                optimizer.zero_grad()
                
                features = batch['features'].to(device)
                scores = batch['score'].to(device).unsqueeze(1)
                texts = batch['text']
                
                try:
                    predictions = model(texts, features)
                    loss = criterion(predictions, scores)
                    loss.backward()
                    optimizer.step()
                    train_losses.append(loss.item())
                except Exception as e:
                    print(f"Training batch error: {e}")
                    continue
            
            # Validation phase
            model.eval()
            val_losses = []
            val_predictions = []
            val_targets = []
            
            with torch.no_grad():
                for batch in val_loader:
                    features = batch['features'].to(device)
                    scores = batch['score'].to(device).unsqueeze(1)
                    texts = batch['text']
                    
                    try:
                        predictions = model(texts, features)
                        loss = criterion(predictions, scores)
                        val_losses.append(loss.item())
                        val_predictions.extend(predictions.cpu().numpy())
                        val_targets.extend(scores.cpu().numpy())
                    except Exception as e:
                        print(f"Validation batch error: {e}")
                        continue
            
            # Calculate metrics
            avg_train_loss = np.mean(train_losses) if train_losses else float('inf')
            avg_val_loss = np.mean(val_losses) if val_losses else float('inf')
            
            val_r2 = 0.0
            if val_predictions and val_targets:
                try:
                    from sklearn.metrics import r2_score
                    val_r2 = r2_score(val_targets, val_predictions)
                except:
                    val_r2 = 0.0
            
            history['train_loss'].append(avg_train_loss)
            history['val_loss'].append(avg_val_loss)
            history['val_r2'].append(val_r2)
            
            # Save best model
            if avg_val_loss < best_val_loss:
                best_val_loss = avg_val_loss
                try:
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
                    print(f"Failed to save model: {e}")
            
            # Progress update
            progress = 30 + int((epoch / epochs) * 60)  # 30-90% range
            if progress_callback:
                progress_callback(
                    f"Epoch {epoch+1}/{epochs} - Loss: {avg_val_loss:.4f}, R²: {val_r2:.3f}",
                    epoch + 1, epochs, progress
                )
        
        return history


def test_real_training():
    """Test the real training backend"""
    print("Testing Real ML Training Backend")
    print("=" * 40)
    
    backend = RealMLTrainingBackend()
    
    def progress_callback(message, current, total, percentage):
        print(f"[{percentage:3d}%] {message}")
    
    try:
        # Test loading data
        training_samples = backend.load_training_data_from_database()
        print(f"[OK] Loaded {len(training_samples)} training samples")
        
        if len(training_samples) >= 5:
            print("[OK] Sufficient training data available")
            
            if ML_AVAILABLE:
                # Test training
                print("[START] Starting real ML training...")
                metrics = backend.train_model(progress_callback)
                print(f"[OK] Training completed!")
                print(f"   Final validation loss: {metrics['final_val_loss']:.4f}")
                print(f"   Final R² score: {metrics['final_val_r2']:.3f}")
                print(f"   Epochs trained: {metrics['epochs_trained']}")
                print(f"   Model saved to: {metrics['model_path']}")
            else:
                print("[WARN] ML components not available - cannot test training")
        else:
            print("[WARN] Not enough training data for real training")
            
    except Exception as e:
        print(f"❌ Training test failed: {e}")
        return False
    
    return True


if __name__ == "__main__":
    test_real_training()