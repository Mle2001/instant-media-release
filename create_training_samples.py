"""
Create training samples for continuous learning testing
"""

import json
import os
from datetime import datetime, timedelta

def create_training_samples():
    """Create multiple training samples"""
    
    samples_dir = "data/training_samples"
    os.makedirs(samples_dir, exist_ok=True)
    
    industries = ["technology", "healthcare", "finance", "education", "food_beverage"]
    
    for i in range(3, 16):  # Create samples 003-015 to have total 15
        sample = {
            "enterprise_id": f"SAMPLE{i:03d}",
            "campaign_id": f"CAMP{i:03d}",
            "content_text": f"Sample campaign {i} for {industries[i % len(industries)]} industry targeting specific audience segments",
            "industry": industries[i % len(industries)],
            "budget": 10000000 + (i * 2000000),
            "target_audience": ["professionals", "consumers", "businesses"][i % 3:],
            "campaign_metrics": {
                "reach": 5000000 + (i * 1000000),
                "engagement_rate": 0.03 + (i * 0.003),
                "click_through_rate": 0.015 + (i * 0.002),
                "conversion_rate": 0.008 + (i * 0.001),
                "roi": 120.0 + (i * 8.0)
            },
            "media_outlets_used": [
                {"name": "VnExpress", "effectiveness": 7.0 + (i * 0.2)},
                {"name": "24H", "effectiveness": 6.5 + (i * 0.25)},
                {"name": "Dantri", "effectiveness": 7.2 + (i * 0.18)}
            ],
            "timestamp": (datetime.now() - timedelta(days=i)).isoformat() + "Z"
        }
        
        with open(f"{samples_dir}/sample_{i:03d}.json", "w", encoding="utf-8") as f:
            json.dump(sample, f, indent=2, ensure_ascii=False)
            
    print(f"Created training samples 003-015 in {samples_dir}")

if __name__ == "__main__":
    create_training_samples()