# -*- coding: utf-8 -*-
"""
Continuous Learning Test Script
Test continuous learning system and debug any issues
"""

import requests
import time
import json
import os
from datetime import datetime

class ContinuousLearningTest:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        
    def test_continuous_learning_trigger(self):
        """Test trigger continuous learning vi forced mode"""
        print("Testing continuous learning trigger...")
        
        # First check current status
        try:
            status_response = requests.get(f"{self.base_url}/api/enterprise/learning-status", timeout=10)
            if status_response.status_code == 200:
                status = status_response.json()
                print(f"Current learning status: {status}")
            else:
                print("Learning status endpoint not available")
        except Exception as e:
            print(f"Status check error: {e}")
            
        # Trigger with force flag  b qua sample requirements
        try:
            trigger_data = {
                "force": True,
                "reason": "Manual test trigger",
                "samples_required": False
            }
            
            print("Triggering forced retraining...")
            response = requests.post(
                f"{self.base_url}/api/enterprise/trigger-retrain", 
                json=trigger_data,
                timeout=120  # Longer timeout for training
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"Trigger successful: {result}")
                
                # Monitor training progress
                self.monitor_training_progress()
                return True
            else:
                print(f"Trigger failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"Trigger error: {e}")
            return False
            
    def monitor_training_progress(self):
        """Monitor training progress"""
        print("Monitoring training progress...")
        
        max_wait = 300  # 5 minutes max
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            try:
                response = requests.get(f"{self.base_url}/api/enterprise/training-status", timeout=10)
                if response.status_code == 200:
                    status = response.json()
                    print(f"Training status: {status}")
                    
                    if status.get("status") == "completed":
                        print("Training completed!")
                        return True
                    elif status.get("status") == "failed":
                        print("Training failed!")
                        return False
                        
                time.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                print(f"Status check error: {e}")
                time.sleep(5)
                
        print("Training monitoring timeout")
        return False
        
    def check_model_files(self):
        """Check if new model files are created"""
        print("Checking model files...")
        
        models_dir = "models"
        if not os.path.exists(models_dir):
            print("Models directory not found")
            return False
            
        model_files = [f for f in os.listdir(models_dir) if f.endswith('.pth')]
        print(f"Found model files: {model_files}")
        
        # Check timestamps
        for model_file in model_files:
            filepath = os.path.join(models_dir, model_file)
            mod_time = os.path.getmtime(filepath)
            mod_datetime = datetime.fromtimestamp(mod_time)
            print(f"  {model_file}: {mod_datetime}")
            
        return len(model_files) > 0
        
    def test_model_loading(self):
        """Test if system loads newest model"""
        print("Testing model loading...")
        
        try:
            response = requests.get(f"{self.base_url}/api/enterprise/model-info", timeout=10)
            if response.status_code == 200:
                model_info = response.json()
                print(f"Current loaded model: {model_info}")
                return True
            else:
                print("Model info endpoint not available")
                return False
                
        except Exception as e:
            print(f"Model info error: {e}")
            return False
            
    def create_sample_feedback_data(self):
        """Create sample feedback data  trigger learning"""
        print("Creating sample feedback data...")
        
        sample_data = []
        for i in range(15):  # Create 15 samples to exceed threshold
            feedback = {
                "enterprise_id": f"TEST{i:03d}",
                "campaign_id": f"CAMP{i:03d}",
                "feedback_data": {
                    "campaign_title": f"Test Campaign {i}",
                    "industry": ["technology", "healthcare", "finance"][i % 3],
                    "budget": 10000000 + (i * 1000000),
                    "actual_performance": {
                        "reach": 1000000 + (i * 100000),
                        "engagement": 0.03 + (i * 0.001),
                        "roi": 120.0 + (i * 5.0)
                    },
                    "media_outlets": ["VnExpress", "CafeF", "24H"][i % 3],
                    "effectiveness_rating": 7.0 + (i * 0.2)
                }
            }
            sample_data.append(feedback)
            
        # Submit feedback data
        success_count = 0
        for feedback in sample_data:
            try:
                response = requests.post(
                    f"{self.base_url}/api/enterprise/submit-feedback",
                    json=feedback,
                    timeout=30
                )
                
                if response.status_code == 200:
                    success_count += 1
                    print(f"Feedback {feedback['enterprise_id']} submitted")
                else:
                    print(f"Feedback {feedback['enterprise_id']} failed: {response.status_code}")
                    
            except Exception as e:
                print(f"Feedback submission error: {e}")
                
        print(f"Successfully submitted {success_count}/{len(sample_data)} feedback samples")
        return success_count >= 10
        
    def run_comprehensive_cl_test(self):
        """Run comprehensive continuous learning test"""
        print("STARTING CONTINUOUS LEARNING TEST")
        print("="*60)
        
        success_count = 0
        total_tests = 6
        
        # Test 1: Check initial state
        print("\n1. Checking initial model state...")
        if self.check_model_files():
            success_count += 1
            print("Initial model files found")
        else:
            print("No initial model files")
            
        # Test 2: Check model loading
        print("\n2. Testing model info...")
        if self.test_model_loading():
            success_count += 1
            print("Model info accessible")
        else:
            print("Model info not accessible")
            
        # Test 3: Create sample data
        print("\n3. Creating sample feedback data...")
        if self.create_sample_feedback_data():
            success_count += 1
            print("Sample data created")
        else:
            print("Sample data creation failed")
            
        # Test 4: Force trigger continuous learning
        print("\n4. Triggering continuous learning...")
        if self.test_continuous_learning_trigger():
            success_count += 1
            print("Continuous learning triggered")
        else:
            print("Continuous learning trigger failed")
            
        # Test 5: Check for new model files
        print("\n5. Checking for new model files...")
        time.sleep(5)  # Wait a bit
        if self.check_model_files():
            success_count += 1
            print("Model files present (may be updated)")
        else:
            print("No model files found")
            
        # Test 6: Verify model reloading
        print("\n6. Verifying model reloading...")
        if self.test_model_loading():
            success_count += 1
            print("Model info still accessible")
        else:
            print("Model loading issues")
            
        # Report results
        print("\n" + "="*60)
        print("CONTINUOUS LEARNING TEST RESULTS")
        print("="*60)
        print(f"Passed: {success_count}/{total_tests}")
        print(f"Success Rate: {(success_count/total_tests)*100:.1f}%")
        
        if success_count >= total_tests * 0.8:
            print("CONTINUOUS LEARNING TEST PASSED!")
            return True
        else:
            print("CONTINUOUS LEARNING TEST FAILED!")
            return False

if __name__ == "__main__":
    cl_test = ContinuousLearningTest()
    cl_test.run_comprehensive_cl_test()