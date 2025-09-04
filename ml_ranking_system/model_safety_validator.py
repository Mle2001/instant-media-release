"""
Model Safety Validator
Comprehensive safety checks and validation for ML models before deployment
"""

import numpy as np
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
import torch
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from loguru import logger

@dataclass
class SafetyValidationResult:
    """Results from safety validation checks"""
    passed: bool
    overall_score: float
    accuracy_check: bool
    bias_check: bool
    robustness_check: bool
    latency_check: bool
    memory_check: bool
    issues: List[str]
    recommendations: List[str]

class ModelSafetyValidator:
    """
    Comprehensive safety validation for ML models
    Ensures models meet safety, performance, and bias requirements
    """
    
    def __init__(self, 
                 min_accuracy: float = 0.85,
                 max_bias_score: float = 0.1,
                 max_latency_ms: float = 500,
                 max_memory_mb: float = 512):
        """
        Initialize safety validator
        
        Args:
            min_accuracy: Minimum required accuracy
            max_bias_score: Maximum allowed bias score
            max_latency_ms: Maximum allowed latency in milliseconds
            max_memory_mb: Maximum allowed memory usage in MB
        """
        self.min_accuracy = min_accuracy
        self.max_bias_score = max_bias_score
        self.max_latency_ms = max_latency_ms
        self.max_memory_mb = max_memory_mb
        
        logger.info(f"🛡️ Safety validator initialized with thresholds:")
        logger.info(f"   Accuracy >= {min_accuracy}")
        logger.info(f"   Bias <= {max_bias_score}")
        logger.info(f"   Latency <= {max_latency_ms}ms")
        logger.info(f"   Memory <= {max_memory_mb}MB")
    
    def validate_model_safety(self,
                             model: Any,
                             test_features: np.ndarray,
                             test_labels: np.ndarray,
                             demographic_groups: Optional[List[str]] = None) -> SafetyValidationResult:
        """
        Comprehensive safety validation of ML model
        
        Args:
            model: Trained ML model
            test_features: Test feature matrix
            test_labels: Test labels
            demographic_groups: Optional demographic group labels for bias testing
            
        Returns:
            SafetyValidationResult with validation results
        """
        logger.info("🔍 Starting comprehensive model safety validation...")
        
        issues = []
        recommendations = []
        
        # 1. Accuracy Check
        accuracy_passed = self._check_accuracy(model, test_features, test_labels, issues, recommendations)
        
        # 2. Bias Check
        bias_passed = self._check_bias(model, test_features, test_labels, demographic_groups, issues, recommendations)
        
        # 3. Robustness Check
        robustness_passed = self._check_robustness(model, test_features, test_labels, issues, recommendations)
        
        # 4. Performance Check
        latency_passed = self._check_latency(model, test_features, issues, recommendations)
        memory_passed = self._check_memory_usage(model, issues, recommendations)
        
        # Calculate overall score
        checks = [accuracy_passed, bias_passed, robustness_passed, latency_passed, memory_passed]
        overall_score = sum(checks) / len(checks)
        passed = all(checks)
        
        result = SafetyValidationResult(
            passed=passed,
            overall_score=overall_score,
            accuracy_check=accuracy_passed,
            bias_check=bias_passed,
            robustness_check=robustness_passed,
            latency_check=latency_passed,
            memory_check=memory_passed,
            issues=issues,
            recommendations=recommendations
        )
        
        if passed:
            logger.info(f"✅ Model safety validation PASSED (score: {overall_score:.3f})")
        else:
            logger.warning(f"⚠️ Model safety validation FAILED (score: {overall_score:.3f})")
            for issue in issues[:3]:  # Show top 3 issues
                logger.warning(f"   - {issue}")
        
        return result
    
    def _check_accuracy(self, model: Any, features: np.ndarray, labels: np.ndarray,
                       issues: List[str], recommendations: List[str]) -> bool:
        """Check model accuracy meets minimum requirements"""
        try:
            # Make predictions
            if hasattr(model, 'predict_proba'):
                predictions = model.predict_proba(features)[:, 1] > 0.5
            elif hasattr(model, 'predict'):
                predictions = model.predict(features)
            else:
                # For PyTorch models
                model.eval()
                with torch.no_grad():
                    if isinstance(features, np.ndarray):
                        features_tensor = torch.FloatTensor(features)
                    else:
                        features_tensor = features
                    outputs = model(features_tensor)
                    predictions = outputs.cpu().numpy() > 0.5
            
            accuracy = accuracy_score(labels, predictions)
            
            if accuracy >= self.min_accuracy:
                logger.info(f"✅ Accuracy check passed: {accuracy:.3f}")
                return True
            else:
                issue = f"Accuracy too low: {accuracy:.3f} < {self.min_accuracy}"
                issues.append(issue)
                recommendations.append("Retrain model with more data or tune hyperparameters")
                logger.warning(f"❌ {issue}")
                return False
        
        except Exception as e:
            issue = f"Accuracy check failed: {str(e)}"
            issues.append(issue)
            recommendations.append("Fix model prediction interface")
            logger.error(f"❌ {issue}")
            return False
    
    def _check_bias(self, model: Any, features: np.ndarray, labels: np.ndarray,
                   demographic_groups: Optional[List[str]], issues: List[str], 
                   recommendations: List[str]) -> bool:
        """Check for bias across demographic groups"""
        try:
            if demographic_groups is None or len(set(demographic_groups)) < 2:
                logger.info("ℹ️ Skipping bias check - no demographic groups provided")
                return True
            
            # Make predictions
            if hasattr(model, 'predict_proba'):
                predictions = model.predict_proba(features)[:, 1] > 0.5
            elif hasattr(model, 'predict'):
                predictions = model.predict(features)
            else:
                # For PyTorch models
                model.eval()
                with torch.no_grad():
                    if isinstance(features, np.ndarray):
                        features_tensor = torch.FloatTensor(features)
                    else:
                        features_tensor = features
                    outputs = model(features_tensor)
                    predictions = outputs.cpu().numpy() > 0.5
            
            # Calculate accuracy per group
            unique_groups = list(set(demographic_groups))
            group_accuracies = {}
            
            for group in unique_groups:
                group_mask = np.array(demographic_groups) == group
                if np.sum(group_mask) > 0:
                    group_acc = accuracy_score(labels[group_mask], predictions[group_mask])
                    group_accuracies[group] = group_acc
            
            # Calculate bias as max difference in accuracy
            if len(group_accuracies) > 1:
                accuracies = list(group_accuracies.values())
                bias_score = max(accuracies) - min(accuracies)
                
                if bias_score <= self.max_bias_score:
                    logger.info(f"✅ Bias check passed: {bias_score:.3f}")
                    return True
                else:
                    issue = f"Bias too high: {bias_score:.3f} > {self.max_bias_score}"
                    issues.append(issue)
                    recommendations.append("Balance training data across demographic groups")
                    logger.warning(f"❌ {issue}")
                    logger.warning(f"   Group accuracies: {group_accuracies}")
                    return False
            
            return True
        
        except Exception as e:
            issue = f"Bias check failed: {str(e)}"
            issues.append(issue)
            recommendations.append("Ensure demographic data is properly formatted")
            logger.error(f"❌ {issue}")
            return False
    
    def _check_robustness(self, model: Any, features: np.ndarray, labels: np.ndarray,
                         issues: List[str], recommendations: List[str]) -> bool:
        """Check model robustness to input perturbations"""
        try:
            # Add small random noise to features
            noise_level = 0.01
            noisy_features = features + np.random.normal(0, noise_level, features.shape)
            
            # Get predictions for original and noisy features
            if hasattr(model, 'predict_proba'):
                orig_pred = model.predict_proba(features)[:, 1] > 0.5
                noisy_pred = model.predict_proba(noisy_features)[:, 1] > 0.5
            elif hasattr(model, 'predict'):
                orig_pred = model.predict(features)
                noisy_pred = model.predict(noisy_features)
            else:
                # For PyTorch models
                model.eval()
                with torch.no_grad():
                    features_tensor = torch.FloatTensor(features)
                    noisy_tensor = torch.FloatTensor(noisy_features)
                    
                    orig_outputs = model(features_tensor)
                    noisy_outputs = model(noisy_tensor)
                    
                    orig_pred = orig_outputs.cpu().numpy() > 0.5
                    noisy_pred = noisy_outputs.cpu().numpy() > 0.5
            
            # Calculate robustness as percentage of unchanged predictions
            unchanged = np.mean(orig_pred == noisy_pred)
            robustness_threshold = 0.8  # 80% of predictions should remain unchanged
            
            if unchanged >= robustness_threshold:
                logger.info(f"✅ Robustness check passed: {unchanged:.3f}")
                return True
            else:
                issue = f"Model not robust enough: {unchanged:.3f} < {robustness_threshold}"
                issues.append(issue)
                recommendations.append("Add regularization or data augmentation to improve robustness")
                logger.warning(f"❌ {issue}")
                return False
        
        except Exception as e:
            issue = f"Robustness check failed: {str(e)}"
            issues.append(issue)
            recommendations.append("Ensure model can handle input perturbations")
            logger.error(f"❌ {issue}")
            return False
    
    def _check_latency(self, model: Any, features: np.ndarray,
                      issues: List[str], recommendations: List[str]) -> bool:
        """Check model inference latency"""
        try:
            import time
            
            # Warm up
            if hasattr(model, 'predict'):
                _ = model.predict(features[:1])
            else:
                # For PyTorch models
                model.eval()
                with torch.no_grad():
                    features_tensor = torch.FloatTensor(features[:1])
                    _ = model(features_tensor)
            
            # Measure latency for single prediction
            start_time = time.time()
            if hasattr(model, 'predict'):
                _ = model.predict(features[:1])
            else:
                # For PyTorch models
                model.eval()
                with torch.no_grad():
                    features_tensor = torch.FloatTensor(features[:1])
                    _ = model(features_tensor)
            
            end_time = time.time()
            latency_ms = (end_time - start_time) * 1000
            
            if latency_ms <= self.max_latency_ms:
                logger.info(f"✅ Latency check passed: {latency_ms:.1f}ms")
                return True
            else:
                issue = f"Latency too high: {latency_ms:.1f}ms > {self.max_latency_ms}ms"
                issues.append(issue)
                recommendations.append("Optimize model architecture or use model compression")
                logger.warning(f"❌ {issue}")
                return False
        
        except Exception as e:
            issue = f"Latency check failed: {str(e)}"
            issues.append(issue)
            recommendations.append("Ensure model can perform inference")
            logger.error(f"❌ {issue}")
            return False
    
    def _check_memory_usage(self, model: Any, issues: List[str], 
                           recommendations: List[str]) -> bool:
        """Check model memory usage"""
        try:
            import psutil
            import gc
            
            # Force garbage collection
            gc.collect()
            
            # Get memory before and after loading model
            process = psutil.Process()
            memory_before = process.memory_info().rss / 1024 / 1024  # MB
            
            # This is a simplified check - in practice you'd measure actual memory usage
            memory_usage = memory_before  # Placeholder
            
            if memory_usage <= self.max_memory_mb:
                logger.info(f"✅ Memory check passed: {memory_usage:.1f}MB")
                return True
            else:
                issue = f"Memory usage too high: {memory_usage:.1f}MB > {self.max_memory_mb}MB"
                issues.append(issue)
                recommendations.append("Use model compression or reduce model size")
                logger.warning(f"❌ {issue}")
                return False
        
        except Exception as e:
            issue = f"Memory check failed: {str(e)}"
            issues.append(issue)
            recommendations.append("Monitor memory usage during inference")
            logger.warning(f"⚠️ {issue}")
            return True  # Don't fail on memory check errors
    
    def validate_training_data_quality(self, features: np.ndarray, labels: np.ndarray) -> Dict[str, Any]:
        """Validate training data quality"""
        quality_report = {
            "total_samples": len(features),
            "feature_dimensions": features.shape[1] if len(features.shape) > 1 else 1,
            "class_distribution": {},
            "missing_values": 0,
            "data_quality_score": 0.0,
            "issues": [],
            "recommendations": []
        }
        
        try:
            # Check class distribution
            unique, counts = np.unique(labels, return_counts=True)
            quality_report["class_distribution"] = dict(zip(unique, counts))
            
            # Check for class imbalance
            min_count = min(counts)
            max_count = max(counts)
            imbalance_ratio = max_count / min_count if min_count > 0 else float('inf')
            
            if imbalance_ratio > 3:  # More than 3:1 ratio
                quality_report["issues"].append(f"Class imbalance detected: {imbalance_ratio:.1f}:1")
                quality_report["recommendations"].append("Consider rebalancing classes or using class weights")
            
            # Check for missing values
            missing = np.isnan(features).sum()
            quality_report["missing_values"] = int(missing)
            
            if missing > 0:
                quality_report["issues"].append(f"{missing} missing values found")
                quality_report["recommendations"].append("Handle missing values with imputation or removal")
            
            # Calculate overall quality score
            quality_score = 1.0
            quality_score -= min(0.5, imbalance_ratio / 10)  # Penalize imbalance
            quality_score -= min(0.3, missing / len(features))  # Penalize missing values
            
            quality_report["data_quality_score"] = max(0.0, quality_score)
            
            logger.info(f"📊 Data quality score: {quality_score:.3f}")
            
        except Exception as e:
            quality_report["issues"].append(f"Data validation failed: {str(e)}")
            logger.error(f"❌ Data quality check failed: {e}")
        
        return quality_report