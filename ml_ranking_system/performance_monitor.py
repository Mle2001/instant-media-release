"""
Performance Monitor for ML System
Real-time monitoring and metrics collection for the ML-enhanced ranking system
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
import numpy as np
from collections import deque, defaultdict
import threading
from loguru import logger
import psutil
import json

@dataclass
class PerformanceMetrics:
    """Container for performance metrics"""
    timestamp: datetime
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    latency_ms: float
    throughput_rps: float
    memory_usage_mb: float
    cpu_usage_percent: float
    error_rate: float
    prediction_confidence: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'accuracy': self.accuracy,
            'precision': self.precision,
            'recall': self.recall,
            'f1_score': self.f1_score,
            'latency_ms': self.latency_ms,
            'throughput_rps': self.throughput_rps,
            'memory_usage_mb': self.memory_usage_mb,
            'cpu_usage_percent': self.cpu_usage_percent,
            'error_rate': self.error_rate,
            'prediction_confidence': self.prediction_confidence
        }

@dataclass
class ModelDriftMetrics:
    """Model drift detection metrics"""
    feature_drift_score: float
    prediction_drift_score: float
    data_quality_drift: float
    performance_degradation: float
    drift_detected: bool
    drift_severity: str  # 'low', 'medium', 'high'

@dataclass
class Alert:
    """Performance alert"""
    alert_id: str
    severity: str  # 'info', 'warning', 'error', 'critical'
    category: str  # 'performance', 'drift', 'system', 'data'
    message: str
    timestamp: datetime
    resolved: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

class PerformanceMonitor:
    """
    Real-time performance monitoring for the ML system
    Tracks model performance, system resources, and data drift
    """
    
    def __init__(self, 
                 metrics_window_size: int = 1000,
                 alert_thresholds: Optional[Dict[str, float]] = None):
        """
        Initialize performance monitor
        
        Args:
            metrics_window_size: Size of sliding window for metrics
            alert_thresholds: Threshold values for triggering alerts
        """
        self.metrics_window_size = metrics_window_size
        self.alert_thresholds = alert_thresholds or self._default_thresholds()
        
        # Metrics storage
        self.metrics_history = deque(maxlen=metrics_window_size)
        self.latency_buffer = deque(maxlen=100)  # For real-time latency tracking
        self.error_buffer = deque(maxlen=100)
        self.prediction_buffer = deque(maxlen=1000)
        
        # Alert system
        self.active_alerts: List[Alert] = []
        self.alert_history: List[Alert] = []
        
        # Monitoring state
        self.monitoring_active = False
        self.last_health_check = datetime.now()
        self.system_start_time = datetime.now()
        
        # Threading
        self._monitor_thread = None
        self._stop_event = threading.Event()
        
        # Performance counters
        self.request_count = 0
        self.error_count = 0
        self.total_predictions = 0
        
        logger.info("🔍 Performance Monitor initialized")
    
    def _default_thresholds(self) -> Dict[str, float]:
        """Default alert thresholds"""
        return {
            'accuracy_min': 0.80,
            'latency_max_ms': 500.0,
            'error_rate_max': 0.02,
            'memory_max_mb': 2048.0,
            'cpu_max_percent': 80.0,
            'drift_score_max': 0.15,
            'throughput_min_rps': 5.0
        }
    
    def start_monitoring(self):
        """Start continuous monitoring in background thread"""
        if self.monitoring_active:
            logger.warning("Monitoring already active")
            return
        
        self.monitoring_active = True
        self._stop_event.clear()
        self._monitor_thread = threading.Thread(target=self._monitor_loop)
        self._monitor_thread.daemon = True
        self._monitor_thread.start()
        
        logger.info("✅ Performance monitoring started")
    
    def stop_monitoring(self):
        """Stop continuous monitoring"""
        if not self.monitoring_active:
            return
        
        self.monitoring_active = False
        self._stop_event.set()
        
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        
        logger.info("🛑 Performance monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while not self._stop_event.is_set():
            try:
                self._collect_system_metrics()
                self._check_alerts()
                self._update_health_status()
                
                # Wait for next collection cycle
                self._stop_event.wait(10)  # 10 second intervals
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(1)
    
    def record_prediction(self, 
                         prediction_time_ms: float,
                         confidence_score: float,
                         success: bool = True,
                         error_type: Optional[str] = None):
        """
        Record a model prediction for performance tracking
        
        Args:
            prediction_time_ms: Time taken for prediction in milliseconds
            confidence_score: Model confidence score (0-1)
            success: Whether prediction was successful
            error_type: Type of error if prediction failed
        """
        self.request_count += 1
        self.total_predictions += 1
        
        # Record latency
        self.latency_buffer.append(prediction_time_ms)
        
        # Record prediction confidence
        self.prediction_buffer.append(confidence_score)
        
        # Record errors
        if not success:
            self.error_count += 1
            self.error_buffer.append({
                'timestamp': datetime.now(),
                'error_type': error_type,
                'latency_ms': prediction_time_ms
            })
        
        # Check for immediate alerts
        self._check_prediction_alerts(prediction_time_ms, success)
    
    def record_model_performance(self,
                                accuracy: float,
                                precision: float, 
                                recall: float,
                                f1_score: float):
        """
        Record model performance metrics from validation/testing
        
        Args:
            accuracy: Model accuracy score
            precision: Model precision score
            recall: Model recall score
            f1_score: Model F1 score
        """
        # Create performance metrics record
        metrics = PerformanceMetrics(
            timestamp=datetime.now(),
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            f1_score=f1_score,
            latency_ms=self._get_average_latency(),
            throughput_rps=self._calculate_throughput(),
            memory_usage_mb=self._get_memory_usage(),
            cpu_usage_percent=self._get_cpu_usage(),
            error_rate=self._calculate_error_rate(),
            prediction_confidence=self._get_average_confidence()
        )
        
        # Store in history
        self.metrics_history.append(metrics)
        
        # Check performance-based alerts
        self._check_performance_alerts(metrics)
        
        logger.info(f"📊 Performance recorded: Acc={accuracy:.3f}, Latency={metrics.latency_ms:.1f}ms")
    
    def detect_model_drift(self, 
                          reference_predictions: List[float],
                          current_predictions: List[float]) -> ModelDriftMetrics:
        """
        Detect model drift by comparing prediction distributions
        
        Args:
            reference_predictions: Historical predictions for comparison
            current_predictions: Recent predictions
            
        Returns:
            ModelDriftMetrics object with drift analysis
        """
        if len(reference_predictions) < 10 or len(current_predictions) < 10:
            return ModelDriftMetrics(
                feature_drift_score=0.0,
                prediction_drift_score=0.0,
                data_quality_drift=0.0,
                performance_degradation=0.0,
                drift_detected=False,
                drift_severity='low'
            )
        
        # Calculate prediction drift using KL divergence approximation
        ref_mean, ref_std = np.mean(reference_predictions), np.std(reference_predictions)
        curr_mean, curr_std = np.mean(current_predictions), np.std(current_predictions)
        
        # Simple drift score based on distribution shift
        prediction_drift = abs(ref_mean - curr_mean) / (ref_std + 1e-6)
        prediction_drift += abs(ref_std - curr_std) / (ref_std + 1e-6)
        
        # Confidence drift
        ref_confidence = np.mean([abs(p - 0.5) for p in reference_predictions])
        curr_confidence = np.mean([abs(p - 0.5) for p in current_predictions])
        confidence_drift = abs(ref_confidence - curr_confidence)
        
        # Overall drift score
        drift_score = (prediction_drift + confidence_drift) / 2
        
        # Determine drift severity
        drift_detected = drift_score > self.alert_thresholds.get('drift_score_max', 0.15)
        
        if drift_score > 0.3:
            severity = 'high'
        elif drift_score > 0.15:
            severity = 'medium'
        else:
            severity = 'low'
        
        drift_metrics = ModelDriftMetrics(
            feature_drift_score=prediction_drift,
            prediction_drift_score=drift_score,
            data_quality_drift=confidence_drift,
            performance_degradation=self._calculate_performance_degradation(),
            drift_detected=drift_detected,
            drift_severity=severity
        )
        
        # Generate drift alert if detected
        if drift_detected:
            self._create_alert(
                severity='warning' if severity == 'medium' else 'error',
                category='drift',
                message=f"Model drift detected (severity: {severity}, score: {drift_score:.3f})"
            )
        
        return drift_metrics
    
    def get_current_metrics(self) -> Optional[PerformanceMetrics]:
        """Get the most recent performance metrics"""
        if not self.metrics_history:
            return None
        return self.metrics_history[-1]
    
    def get_metrics_summary(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get summary of metrics for the specified time period
        
        Args:
            hours: Number of hours to include in summary
            
        Returns:
            Dictionary containing metrics summary
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_metrics = [m for m in self.metrics_history if m.timestamp >= cutoff_time]
        
        if not recent_metrics:
            return {}
        
        # Calculate aggregated metrics
        accuracies = [m.accuracy for m in recent_metrics]
        latencies = [m.latency_ms for m in recent_metrics]
        throughputs = [m.throughput_rps for m in recent_metrics]
        
        return {
            'time_period_hours': hours,
            'sample_count': len(recent_metrics),
            'accuracy': {
                'mean': np.mean(accuracies),
                'min': np.min(accuracies),
                'max': np.max(accuracies),
                'std': np.std(accuracies)
            },
            'latency_ms': {
                'mean': np.mean(latencies),
                'p50': np.percentile(latencies, 50),
                'p95': np.percentile(latencies, 95),
                'p99': np.percentile(latencies, 99),
                'max': np.max(latencies)
            },
            'throughput_rps': {
                'mean': np.mean(throughputs),
                'min': np.min(throughputs),
                'max': np.max(throughputs)
            },
            'error_rate': self._calculate_error_rate(),
            'uptime_hours': (datetime.now() - self.system_start_time).total_seconds() / 3600,
            'total_predictions': self.total_predictions
        }
    
    def get_active_alerts(self) -> List[Alert]:
        """Get list of active (unresolved) alerts"""
        return [alert for alert in self.active_alerts if not alert.resolved]
    
    def resolve_alert(self, alert_id: str):
        """Mark an alert as resolved"""
        for alert in self.active_alerts:
            if alert.alert_id == alert_id:
                alert.resolved = True
                alert.metadata['resolved_at'] = datetime.now().isoformat()
                logger.info(f"✅ Alert resolved: {alert_id}")
                break
    
    def export_metrics(self, format: str = 'json') -> str:
        """
        Export metrics in specified format
        
        Args:
            format: Export format ('json', 'csv')
            
        Returns:
            Formatted metrics string
        """
        if format == 'json':
            metrics_data = [m.to_dict() for m in self.metrics_history]
            return json.dumps(metrics_data, indent=2)
        
        elif format == 'csv':
            if not self.metrics_history:
                return "No metrics data available"
            
            # Convert to CSV format
            headers = self.metrics_history[0].to_dict().keys()
            csv_lines = [','.join(headers)]
            
            for metrics in self.metrics_history:
                values = [str(v) for v in metrics.to_dict().values()]
                csv_lines.append(','.join(values))
            
            return '\n'.join(csv_lines)
        
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    # Private helper methods
    
    def _collect_system_metrics(self):
        """Collect system resource metrics"""
        try:
            # Get system metrics
            memory_mb = self._get_memory_usage()
            cpu_percent = self._get_cpu_usage()
            
            # Check resource alerts
            if memory_mb > self.alert_thresholds['memory_max_mb']:
                self._create_alert('warning', 'system', 
                                 f"High memory usage: {memory_mb:.0f}MB")
            
            if cpu_percent > self.alert_thresholds['cpu_max_percent']:
                self._create_alert('warning', 'system',
                                 f"High CPU usage: {cpu_percent:.1f}%")
        
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
    
    def _check_alerts(self):
        """Check for alert conditions"""
        # Clean up old resolved alerts
        self._cleanup_old_alerts()
        
        # Check throughput
        throughput = self._calculate_throughput()
        if throughput < self.alert_thresholds['throughput_min_rps']:
            self._create_alert('warning', 'performance',
                             f"Low throughput: {throughput:.1f} req/s")
    
    def _check_prediction_alerts(self, latency_ms: float, success: bool):
        """Check for prediction-specific alerts"""
        if latency_ms > self.alert_thresholds['latency_max_ms']:
            self._create_alert('warning', 'performance',
                             f"High prediction latency: {latency_ms:.1f}ms")
        
        if not success:
            error_rate = self._calculate_error_rate()
            if error_rate > self.alert_thresholds['error_rate_max']:
                self._create_alert('error', 'performance',
                                 f"High error rate: {error_rate:.3f}")
    
    def _check_performance_alerts(self, metrics: PerformanceMetrics):
        """Check performance-based alert conditions"""
        if metrics.accuracy < self.alert_thresholds['accuracy_min']:
            self._create_alert('error', 'performance',
                             f"Low model accuracy: {metrics.accuracy:.3f}")
    
    def _create_alert(self, severity: str, category: str, message: str):
        """Create a new alert"""
        alert_id = f"{category}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Check if similar alert already exists
        existing_alert = any(
            alert.category == category and 
            alert.message.split(':')[0] == message.split(':')[0] and 
            not alert.resolved
            for alert in self.active_alerts
        )
        
        if existing_alert:
            return  # Don't duplicate alerts
        
        alert = Alert(
            alert_id=alert_id,
            severity=severity,
            category=category,
            message=message,
            timestamp=datetime.now(),
            metadata={'source': 'performance_monitor'}
        )
        
        self.active_alerts.append(alert)
        self.alert_history.append(alert)
        
        logger.warning(f"🚨 Alert created: [{severity.upper()}] {message}")
    
    def _cleanup_old_alerts(self):
        """Remove old resolved alerts"""
        cutoff_time = datetime.now() - timedelta(hours=24)
        self.active_alerts = [
            alert for alert in self.active_alerts 
            if not alert.resolved or alert.timestamp >= cutoff_time
        ]
    
    def _update_health_status(self):
        """Update overall system health status"""
        self.last_health_check = datetime.now()
    
    def _get_average_latency(self) -> float:
        """Calculate average latency from recent predictions"""
        if not self.latency_buffer:
            return 0.0
        return float(np.mean(list(self.latency_buffer)))
    
    def _get_average_confidence(self) -> float:
        """Calculate average prediction confidence"""
        if not self.prediction_buffer:
            return 0.0
        return float(np.mean(list(self.prediction_buffer)))
    
    def _calculate_throughput(self) -> float:
        """Calculate requests per second throughput"""
        if not self.metrics_history:
            return 0.0
        
        # Calculate based on recent activity
        recent_time_window = 60  # seconds
        cutoff_time = datetime.now() - timedelta(seconds=recent_time_window)
        
        recent_count = sum(1 for _ in self.latency_buffer)  # Use latency buffer as proxy
        return recent_count / recent_time_window
    
    def _calculate_error_rate(self) -> float:
        """Calculate current error rate"""
        if self.request_count == 0:
            return 0.0
        return self.error_count / self.request_count
    
    def _calculate_performance_degradation(self) -> float:
        """Calculate performance degradation compared to baseline"""
        if len(self.metrics_history) < 10:
            return 0.0
        
        # Compare recent performance to historical baseline
        recent_metrics = list(self.metrics_history)[-5:]
        baseline_metrics = list(self.metrics_history)[:10]
        
        if not recent_metrics or not baseline_metrics:
            return 0.0
        
        recent_accuracy = np.mean([m.accuracy for m in recent_metrics])
        baseline_accuracy = np.mean([m.accuracy for m in baseline_metrics])
        
        degradation = max(0, baseline_accuracy - recent_accuracy)
        return float(degradation)
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            return memory_info.rss / 1024 / 1024  # Convert to MB
        except:
            return 0.0
    
    def _get_cpu_usage(self) -> float:
        """Get current CPU usage percentage"""
        try:
            return psutil.cpu_percent(interval=1)
        except:
            return 0.0
    
    def get_current_performance(self) -> float:
        """Get current model performance score"""
        if not self.metrics_history:
            return 0.75  # Default score if no metrics available
        
        # Calculate average accuracy from recent metrics
        recent_metrics = list(self.metrics_history)[-10:]  # Last 10 metrics
        if recent_metrics:
            accuracy_scores = [m.accuracy for m in recent_metrics if hasattr(m, 'accuracy')]
            if accuracy_scores:
                return sum(accuracy_scores) / len(accuracy_scores)
        
        return 0.75  # Default performance score
    
    def get_baseline_performance(self) -> float:
        """Get baseline model performance score"""
        if len(self.metrics_history) < 50:
            return 0.85  # Default baseline if insufficient history
        
        # Calculate baseline from historical metrics
        historical_metrics = list(self.metrics_history)[:50]  # First 50 metrics as baseline
        accuracy_scores = [m.accuracy for m in historical_metrics if hasattr(m, 'accuracy')]
        if accuracy_scores:
            return sum(accuracy_scores) / len(accuracy_scores)
        
        return 0.85  # Default baseline score

# Global performance monitor instance
performance_monitor = PerformanceMonitor()

def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance"""
    return performance_monitor