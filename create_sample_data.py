"""
Script để tạo sample data cho enterprise ML system
Tạo dữ liệu mẫu realistic cho testing dashboard
"""

import sqlite3
import json
from datetime import datetime, timedelta
import random
import pandas as pd
from pathlib import Path

def create_sample_ml_data():
    """Tạo sample data trong ML database tables"""
    
    # Connect to database
    db_path = "media_release.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Sample enterprise feedback data
    enterprises = [
        {"id": "ENTERPRISE_001", "name": "EduTech Startup"},
        {"id": "ENTERPRISE_002", "name": "Fashion ABC"},
        {"id": "ENTERPRISE_003", "name": "Fintech XYZ"},
        {"id": "ENTERPRISE_004", "name": "Food Festival Organizer"},
        {"id": "ENTERPRISE_005", "name": "Drone Delivery Service"}
    ]
    
    campaigns_data = [
        {
            "enterprise_id": "ENTERPRISE_001",
            "campaign_name": "Ra mắt ứng dụng EduTech cho học sinh THPT - Q1/2025",
            "campaign_data": {
                "start_date": "2025-01-01",
                "end_date": "2025-01-31", 
                "description": "Giới thiệu ứng dụng học tập EduTech mới tích hợp AI cá nhân hóa",
                "target_audience": ["students", "parents", "educators"],
                "industry": "education",
                "budget": 25000000
            },
            "feedback_data": {
                "media_results": {
                    "VnExpress": {"published": True, "views": 45000, "interactions": 280, "type": "News Article"},
                    "Tuoi Tre": {"published": True, "views": 32000, "interactions": 195, "type": "Interview"},
                    "Dantri": {"published": True, "views": 28000, "interactions": 150, "type": "Feature Story"},
                    "Thanh Nien": {"published": False, "reason": "not_relevant"},
                    "VietnamNet": {"published": True, "views": 18000, "interactions": 85, "type": "Press Release"}
                },
                "business_metrics": {
                    "revenue": 150000000,
                    "cost": 25000000,
                    "new_customers": 1200,
                    "conversion_rate": 2.8,
                    "customer_acquisition_cost": 20833
                }
            },
            "training_labels": {
                "VnExpress": 0.92,
                "Tuoi Tre": 0.85,
                "Dantri": 0.78,
                "Thanh Nien": 0.15,
                "VietnamNet": 0.65
            }
        },
        {
            "enterprise_id": "ENTERPRISE_002", 
            "campaign_name": "Khuyến mãi Black Friday 2024 - Shop thời trang ABC",
            "campaign_data": {
                "start_date": "2024-11-20",
                "end_date": "2024-11-30",
                "description": "Chiến dịch khuyến mãi Black Friday với giảm giá lên đến 70%",
                "target_audience": ["young_adults", "fashion_lovers", "bargain_hunters"],
                "industry": "fashion_retail",
                "budget": 40000000
            },
            "feedback_data": {
                "media_results": {
                    "VnExpress": {"published": True, "views": 55000, "interactions": 420, "type": "News Article"},
                    "Zing.vn": {"published": True, "views": 38000, "interactions": 295, "type": "Feature Story"},
                    "Eva.vn": {"published": True, "views": 25000, "interactions": 180, "type": "Product Review"},
                    "Kenh14": {"published": False, "reason": "timing_conflict"}
                },
                "business_metrics": {
                    "revenue": 300000000,
                    "cost": 40000000,
                    "new_customers": 2500,
                    "conversion_rate": 4.2,
                    "customer_acquisition_cost": 16000
                }
            },
            "training_labels": {
                "VnExpress": 0.88,
                "Zing.vn": 0.82,
                "Eva.vn": 0.75,
                "Kenh14": 0.25
            }
        },
        {
            "enterprise_id": "ENTERPRISE_003",
            "campaign_name": "IPO công ty Fintech XYZ tại HOSE", 
            "campaign_data": {
                "start_date": "2024-12-01",
                "end_date": "2024-12-31",
                "description": "Công ty fintech XYZ chính thức niêm yết cổ phiếu tại sàn HOSE",
                "target_audience": ["investors", "business_community", "fintech_enthusiasts"],
                "industry": "financial_technology",
                "budget": 60000000
            },
            "feedback_data": {
                "media_results": {
                    "CafeF": {"published": True, "views": 75000, "interactions": 580, "type": "News Article"},
                    "VnEconomy": {"published": True, "views": 42000, "interactions": 320, "type": "Interview"},
                    "Dau Tu": {"published": True, "views": 38000, "interactions": 250, "type": "Feature Story"},
                    "Tien Phong": {"published": True, "views": 28000, "interactions": 185, "type": "Opinion Piece"}
                },
                "business_metrics": {
                    "revenue": 500000000,
                    "cost": 60000000,
                    "new_customers": 800,
                    "conversion_rate": 1.6,
                    "customer_acquisition_cost": 75000
                }
            },
            "training_labels": {
                "CafeF": 0.95,
                "VnEconomy": 0.89,
                "Dau Tu": 0.84,
                "Tien Phong": 0.76
            }
        }
    ]
    
    # Insert enterprise feedback data
    for i, campaign in enumerate(campaigns_data):
        # Calculate ground truth score
        revenue = campaign["feedback_data"]["business_metrics"]["revenue"]
        cost = campaign["feedback_data"]["business_metrics"]["cost"]
        roi = (revenue - cost) / cost
        articles_published = len([m for m in campaign["feedback_data"]["media_results"].values() if m.get("published", False)])
        total_reach = sum(m.get("views", 0) for m in campaign["feedback_data"]["media_results"].values())
        
        # Simple ground truth calculation (0-1 scale)
        ground_truth = min(1.0, max(0.0, (roi * 0.5 + (articles_published / 5) * 0.3 + (total_reach / 100000) * 0.2)))
        
        cursor.execute("""
            INSERT OR REPLACE INTO ml_feedback_data 
            (id, enterprise_id, campaign_id, campaign_title, campaign_type, industry, 
             target_audience, budget, total_articles_published, total_media_reach, 
             click_through_rate, social_media_shares, media_quality_score, 
             brand_awareness_lift, lead_generation, sales_conversion, roi_percentage,
             average_engagement_rate, comment_sentiment_score, audience_retention_rate,
             cost_per_acquisition, cost_per_impression, budget_utilization,
             ground_truth_score, confidence_score, feedback_source, data_quality, validated, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            i + 1,
            campaign["enterprise_id"],
            f"CAMP_{i+1:03d}",  # campaign_id
            campaign["campaign_name"],  # campaign_title
            "product_launch",  # campaign_type
            campaign["campaign_data"]["industry"],
            json.dumps(campaign["campaign_data"].get("target_audience", [])),
            campaign["campaign_data"].get("budget", 0),
            articles_published,  # total_articles_published
            total_reach,  # total_media_reach
            2.5,  # click_through_rate
            sum(m.get("interactions", 0) for m in campaign["feedback_data"]["media_results"].values()),  # social_media_shares
            7.5,  # media_quality_score
            15.0,  # brand_awareness_lift
            campaign["feedback_data"]["business_metrics"]["new_customers"],  # lead_generation
            int(campaign["feedback_data"]["business_metrics"]["new_customers"] * campaign["feedback_data"]["business_metrics"]["conversion_rate"] / 100),  # sales_conversion
            roi * 100,  # roi_percentage
            3.2,  # average_engagement_rate
            0.7,  # comment_sentiment_score
            85.5,  # audience_retention_rate
            cost / campaign["feedback_data"]["business_metrics"]["new_customers"] if campaign["feedback_data"]["business_metrics"]["new_customers"] > 0 else 0,  # cost_per_acquisition
            0.05,  # cost_per_impression
            95.0,  # budget_utilization
            ground_truth,  # ground_truth_score
            0.85,  # confidence_score
            "enterprise_api",  # feedback_source
            "good",  # data_quality
            True,  # validated
            datetime.now().isoformat()
        ))
    
    # Sample model versions
    model_versions = [
        {
            "version_name": "v1.0_baseline",
            "model_path": "/models/baseline_v1.0.pkl",
            "performance_metrics": {
                "accuracy": 0.72,
                "precision": 0.68,
                "recall": 0.75,
                "f1_score": 0.71,
                "training_samples": 50,
                "validation_samples": 15
            },
            "is_active": False
        },
        {
            "version_name": "v2.1_enhanced",
            "model_path": "/models/enhanced_v2.1.pkl", 
            "performance_metrics": {
                "accuracy": 0.84,
                "precision": 0.82,
                "recall": 0.86,
                "f1_score": 0.84,
                "training_samples": 120,
                "validation_samples": 30
            },
            "is_active": False
        },
        {
            "version_name": "v2.3_current",
            "model_path": "/models/current_v2.3.pkl",
            "performance_metrics": {
                "accuracy": 0.873,
                "precision": 0.869,
                "recall": 0.881,
                "f1_score": 0.875,
                "training_samples": 180,
                "validation_samples": 45,
                "feature_importance": {
                    "content_relevance": 0.28,
                    "audience_match": 0.22,
                    "media_category": 0.18,
                    "timing_factors": 0.15,
                    "industry_match": 0.12,
                    "geographic_focus": 0.05
                }
            },
            "is_active": True
        }
    ]
    
    for i, model in enumerate(model_versions):
        perf = model["performance_metrics"]
        cursor.execute("""
            INSERT OR REPLACE INTO ml_model_versions
            (id, version, model_type, accuracy, precision, recall, f1_score, auc_score,
             training_samples, validation_samples, training_time_hours, hyperparameters, 
             is_active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            i + 1,
            model["version_name"],
            "MediaRankingLSTM",
            perf["accuracy"],
            perf["precision"],
            perf["recall"],
            perf["f1_score"],
            perf.get("auc_score", 0.82),
            perf["training_samples"],
            perf["validation_samples"],
            0.75,  # training_time_hours
            json.dumps({"learning_rate": 0.001, "batch_size": 32, "epochs": 50}),
            model["is_active"],
            (datetime.now() - timedelta(days=30-i*10)).isoformat()
        ))
    
    # Sample training jobs
    training_jobs = [
        {
            "job_id": "train_job_001",
            "status": "completed",
            "config": {
                "model_type": "lstm_attention",
                "learning_rate": 0.001,
                "batch_size": 32,
                "epochs": 50,
                "features": ["content", "audience", "business", "timing", "competitive"]
            },
            "metrics": {
                "final_loss": 0.23,
                "best_accuracy": 0.873,
                "training_time_minutes": 45,
                "convergence_epoch": 38
            },
            "error_log": None,
            "started_at": (datetime.now() - timedelta(hours=2)).isoformat(),
            "completed_at": (datetime.now() - timedelta(hours=1, minutes=15)).isoformat()
        },
        {
            "job_id": "train_job_002",
            "status": "failed",
            "config": {
                "model_type": "lstm_attention",
                "learning_rate": 0.01,
                "batch_size": 64,
                "epochs": 30
            },
            "metrics": None,
            "error_log": "Insufficient training data: only 15 samples available, minimum 50 required",
            "started_at": (datetime.now() - timedelta(days=3)).isoformat(),
            "completed_at": None
        },
        {
            "job_id": "train_job_003",
            "status": "running",
            "config": {
                "model_type": "lstm_attention_v2",
                "learning_rate": 0.0005,
                "batch_size": 16,
                "epochs": 100
            },
            "metrics": {
                "current_epoch": 45,
                "current_loss": 0.31,
                "current_accuracy": 0.81,
                "estimated_time_remaining_minutes": 25
            },
            "error_log": None,
            "started_at": datetime.now().isoformat(),
            "completed_at": None
        }
    ]
    
    for i, job in enumerate(training_jobs):
        config = job["config"]
        metrics = job.get("metrics", {})
        cursor.execute("""
            INSERT OR REPLACE INTO ml_training_jobs
            (id, job_id, job_type, status, progress, model_version, 
             training_data_size, validation_data_size, batch_size, learning_rate, epochs,
             final_accuracy, final_loss, best_epoch, error_message, started_at, completed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            i + 1,
            job["job_id"],
            "retraining",
            job["status"],
            100.0 if job["status"] == "completed" else (75.0 if job["status"] == "running" else 0.0),
            f"v{2+i}.{i}",
            config.get("training_samples", 150),
            config.get("validation_samples", 30),
            config.get("batch_size", 32),
            config.get("learning_rate", 0.001),
            config.get("epochs", 50),
            metrics.get("best_accuracy", 0.87) if job["status"] == "completed" else 0.0,
            metrics.get("final_loss", 0.23) if job["status"] == "completed" else 0.0,
            metrics.get("convergence_epoch", 38) if job["status"] == "completed" else 0,
            job.get("error_log"),
            job["started_at"],
            job["completed_at"]
        ))
    
    conn.commit()
    conn.close()
    
    print("[OK] Sample ML data created successfully!")
    print(f"   - {len(campaigns_data)} campaign feedback records")
    print(f"   - {len(model_versions)} model versions")
    print(f"   - {len(training_jobs)} training jobs")

def create_sample_files():
    """Tạo sample files và directories"""
    
    # Tạo sample_data directory
    sample_dir = Path("sample_data")
    sample_dir.mkdir(exist_ok=True)
    
    print("[OK] Sample files and directories created!")

def validate_sample_data():
    """Validate sample data đã được tạo thành công"""
    
    # Check CSV file
    csv_file = Path("sample_data/sample_campaigns.csv")
    if csv_file.exists():
        df = pd.read_csv(csv_file)
        print(f"[OK] CSV file created with {len(df)} records")
        print(f"   - {df['campaign_name'].nunique()} unique campaigns")
        print(f"   - {df['media_name'].nunique()} unique media outlets")
    else:
        print("[ERROR] CSV file not found")
    
    # Check database
    try:
        conn = sqlite3.connect("media_release.db")
        cursor = conn.cursor()
        
        # Check ml_feedback_data
        cursor.execute("SELECT COUNT(*) FROM ml_feedback_data")
        feedback_count = cursor.fetchone()[0]
        print(f"[OK] Database has {feedback_count} feedback records")
        
        # Check ml_model_versions 
        cursor.execute("SELECT COUNT(*) FROM ml_model_versions")
        model_count = cursor.fetchone()[0]
        print(f"[OK] Database has {model_count} model versions")
        
        # Check active model
        cursor.execute("SELECT version FROM ml_model_versions WHERE is_active = 1")
        active_model = cursor.fetchone()
        if active_model:
            print(f"[OK] Active model: {active_model[0]}")
        
        conn.close()
        
    except Exception as e:
        print(f"[ERROR] Database error: {e}")

if __name__ == "__main__":
    print("Creating sample data for Enterprise ML Dashboard...")
    print("=" * 60)
    
    # Create sample files
    create_sample_files()
    
    # Create sample database data
    create_sample_ml_data()
    
    # Validate
    print("\nValidating sample data...")
    print("=" * 60)
    validate_sample_data()
    
    print("\nSample data creation completed!")
    print("\nNext steps:")
    print("1. Run 'python run_dashboards.py' to start dashboards")
    print("2. Visit http://localhost:8501 for data upload dashboard") 
    print("3. Visit http://localhost:8502 for ML monitoring dashboard")
    print("4. Run 'python test_dashboard.py' to test functionality")