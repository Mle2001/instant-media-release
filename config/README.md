# ML-Enhanced Ranking System Configuration

This directory contains configuration files for the Machine Learning enhanced ranking system.

## Configuration Files

### `ml_config.yaml`
Main configuration file containing:
- Model architecture parameters (LSTM, attention, features)
- Training configuration (batch size, learning rate, epochs)
- Continuous learning settings (retraining frequency, A/B testing)
- Data processing parameters (feature extraction, ground truth computation)
- Safety and validation thresholds
- Monitoring and alerting settings
- Storage paths

### `ml_requirements.txt`
Additional Python dependencies specifically for the ML system, beyond the main project requirements.

## Key Configuration Sections

### Model Configuration
- **Base Model**: PhoBERT (Vietnamese BERT) for text encoding
- **Architecture**: Bidirectional LSTM with multi-head attention
- **Features**: 1,670-dimensional feature vectors combining content, audience, business, timing, and competitive signals

### Continuous Learning
- **Retraining Frequency**: Every 30 days with minimum 100 new samples
- **Performance Threshold**: 2% improvement required for model update
- **A/B Testing**: 5% traffic split for 7 days during validation
- **Deployment Stages**: Gradual rollout from 10% to 100% traffic

### Safety Measures
- **Accuracy Threshold**: Minimum 85% accuracy required
- **Bias Detection**: Maximum 10% bias score allowed
- **Latency Limits**: 500ms response time maximum
- **Fallback System**: Automatic revert to traditional ranking if ML fails

### Data Processing
- **Ground Truth Weighting**:
  - Media Performance: 40%
  - Business Impact: 30%
  - Audience Engagement: 20%
  - Cost Efficiency: 10%

### Enterprise Integration
The ML system provides enterprise APIs for:
- Campaign feedback submission
- Performance metrics tracking
- Learning statistics monitoring
- Model version management

## Usage

The configuration is automatically loaded by the ML system during startup. Key settings can be overridden via environment variables using the pattern `ML_<SECTION>_<KEY>`.

For example:
```bash
export ML_TRAINING_BATCH_SIZE=64
export ML_CONTINUOUS_LEARNING_RETRAIN_FREQUENCY_DAYS=14
```

## Monitoring

The system includes comprehensive monitoring:
- Real-time performance metrics
- Model drift detection
- Error rate tracking
- Latency monitoring
- Business impact measurement

Alerts are triggered when thresholds are exceeded, ensuring system reliability and performance.