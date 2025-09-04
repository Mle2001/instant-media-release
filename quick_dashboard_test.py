"""
Quick Dashboard Test - Manual verification
Test dashboard khởi động và accessible
"""

import requests
import time
import subprocess
import sys
from pathlib import Path

def test_dashboard_accessibility():
    """Test if dashboards are accessible"""
    print("Testing Dashboard Accessibility...")
    print("=" * 50)
    
    # Test upload dashboard
    try:
        response = requests.get("http://localhost:8501", timeout=5)
        if response.status_code == 200:
            print("[OK] Enterprise Data Upload Dashboard: ACCESSIBLE")
            upload_working = True
        else:
            print(f"[FAIL] Upload Dashboard HTTP {response.status_code}")
            upload_working = False
    except Exception as e:
        print(f"[FAIL] Upload Dashboard: {e}")
        upload_working = False
    
    # Test monitoring dashboard  
    try:
        response = requests.get("http://localhost:8502", timeout=5)
        if response.status_code == 200:
            print("[OK] ML Monitoring Dashboard: ACCESSIBLE")
            monitor_working = True
        else:
            print(f"[FAIL] Monitor Dashboard HTTP {response.status_code}")
            monitor_working = False
    except Exception as e:
        print(f"[FAIL] Monitor Dashboard: {e}")
        monitor_working = False
    
    return upload_working, monitor_working

def test_enterprise_api():
    """Test enterprise API endpoints"""
    print("\nTesting Enterprise API...")
    print("=" * 50)
    
    # First check if main API is running
    try:
        response = requests.get("http://localhost:8000/health", timeout=3)
        if response.status_code != 200:
            print("[INFO] Main API not running. This is OK for dashboard testing.")
            return False
    except:
        print("[INFO] Main API not running. This is OK for dashboard testing.")
        return False
    
    # Test enterprise endpoints
    endpoints = [
        "/enterprise/learning_stats",
        "/enterprise/model_performance",
        "/enterprise/health"
    ]
    
    working = 0
    for endpoint in endpoints:
        try:
            response = requests.get(f"http://localhost:8000{endpoint}", timeout=5)
            if response.status_code == 200:
                print(f"[OK] {endpoint}: Working")
                working += 1
            else:
                print(f"[FAIL] {endpoint}: HTTP {response.status_code}")
        except Exception as e:
            print(f"[FAIL] {endpoint}: {e}")
    
    return working == len(endpoints)

def manual_csv_test():
    """Test CSV sample data"""
    print("\nTesting Sample Data...")
    print("=" * 50)
    
    csv_file = Path("sample_data/sample_campaigns.csv")
    if csv_file.exists():
        try:
            import pandas as pd
            df = pd.read_csv(csv_file)
            print(f"[OK] Sample CSV: {len(df)} records loaded")
            print(f"     Campaigns: {df['campaign_name'].nunique()}")
            print(f"     Media outlets: {df['media_name'].nunique()}")
            return True
        except Exception as e:
            print(f"[FAIL] CSV processing: {e}")
            return False
    else:
        print("[FAIL] Sample CSV not found")
        return False

def test_database_data():
    """Test if sample data is in database"""
    print("\nTesting Database Data...")
    print("=" * 50)
    
    try:
        import sqlite3
        conn = sqlite3.connect("media_release.db")
        cursor = conn.cursor()
        
        # Check feedback data
        cursor.execute("SELECT COUNT(*) FROM ml_feedback_data")
        feedback_count = cursor.fetchone()[0]
        print(f"[OK] ML Feedback records: {feedback_count}")
        
        # Check model versions
        cursor.execute("SELECT COUNT(*) FROM ml_model_versions") 
        model_count = cursor.fetchone()[0]
        print(f"[OK] ML Model versions: {model_count}")
        
        # Check training jobs
        cursor.execute("SELECT COUNT(*) FROM ml_training_jobs")
        job_count = cursor.fetchone()[0]
        print(f"[OK] Training jobs: {job_count}")
        
        conn.close()
        return feedback_count > 0 and model_count > 0
        
    except Exception as e:
        print(f"[FAIL] Database access: {e}")
        return False

def main():
    """Run all tests"""
    print("Quick Dashboard Testing Suite")
    print("=" * 60)
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {}
    
    # Test 1: Dashboard accessibility
    upload_ok, monitor_ok = test_dashboard_accessibility()
    results['dashboards'] = upload_ok or monitor_ok
    
    # Test 2: Enterprise API
    results['api'] = test_enterprise_api()
    
    # Test 3: Sample data
    results['csv'] = manual_csv_test()
    
    # Test 4: Database
    results['database'] = test_database_data()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    for test_name, result in results.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {test_name.upper()}: {'Working' if result else 'Issues found'}")
    
    success_rate = (passed_tests / total_tests) * 100
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed ({success_rate:.1f}%)")
    
    if success_rate >= 75:
        print("[OK] Dashboard system is working well!")
        if not upload_ok:
            print("NOTE: Upload dashboard may need manual restart")
        if not monitor_ok:
            print("NOTE: Monitor dashboard may need manual restart")
    elif success_rate >= 50:
        print("[WARNING] Dashboard system has some issues")
    else:
        print("[ERROR] Dashboard system needs fixes")
    
    # Specific recommendations
    print("\nRECOMMENDATIONS:")
    if results['dashboards']:
        print("- Dashboards are accessible via browser")
        print("- You can manually test upload/monitoring features")
    else:
        print("- Try running: python run_dashboards.py")
        print("- Check if ports 8501/8502 are available")
    
    if results['csv'] and results['database']:
        print("- Sample data is ready for testing")
    else:
        print("- Run: python create_sample_data.py")
    
    print("\nManual test URLs:")
    if upload_ok:
        print("- Upload Dashboard: http://localhost:8501")
    if monitor_ok:
        print("- Monitor Dashboard: http://localhost:8502")

if __name__ == "__main__":
    main()