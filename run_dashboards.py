"""
Dashboard Runner for ML System
Launch both Enterprise Data Upload and ML Monitoring dashboards
"""

import subprocess
import sys
import os
import time
from multiprocessing import Process
import webbrowser
from loguru import logger

def run_data_upload_dashboard():
    """Run the Enterprise Data Upload Dashboard"""
    try:
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "dashboards/enterprise_data_upload.py",
            "--server.port", "8501",
            "--server.address", "localhost",
            "--server.headless", "true",
            "--browser.gatherUsageStats", "false",
            "--logger.level", "error"
        ])
    except Exception as e:
        print(f"Error running data upload dashboard: {e}")

def run_ml_monitoring_dashboard():
    """Run the ML Monitoring Dashboard"""
    try:
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        subprocess.run([
            sys.executable, "-m", "streamlit", "run",
            "dashboards/ml_monitoring.py", 
            "--server.port", "8502",
            "--server.address", "localhost",
            "--server.headless", "true",
            "--browser.gatherUsageStats", "false",
            "--logger.level", "error"
        ])
    except Exception as e:
        print(f"Error running ML monitoring dashboard: {e}")

def kill_existing_streamlit_processes():
    """Kill any existing Streamlit processes on ports 8501 and 8502"""
    try:
        import psutil
        killed_processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info['cmdline']
                if cmdline and 'streamlit' in ' '.join(cmdline):
                    if any(port in ' '.join(cmdline) for port in ['8501', '8502']):
                        proc.terminate()
                        killed_processes.append(proc.info['pid'])
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        if killed_processes:
            print(f"[CLEANUP] Killed existing Streamlit processes: {killed_processes}")
            time.sleep(2)  # Wait for cleanup
        
    except ImportError:
        # psutil not available, try alternative method
        try:
            if os.name == 'nt':  # Windows
                subprocess.run(['taskkill', '/F', '/IM', 'python.exe'], 
                             capture_output=True, text=True)
            else:  # Unix-like
                subprocess.run(['pkill', '-f', 'streamlit'], 
                             capture_output=True, text=True)
            print("[CLEANUP] Attempted to kill existing processes")
        except:
            pass

def main():
    """Main function to launch both dashboards"""
    print("Starting ML System Dashboards...")
    print("="*60)
    
    # Kill existing processes first
    print("[CLEANUP] Checking for existing Streamlit processes...")
    kill_existing_streamlit_processes()
    
    # Check if streamlit is installed
    try:
        import streamlit
    except ImportError:
        print("[INSTALL] Streamlit not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "streamlit", "plotly"])
        print("[OK] Streamlit installed successfully!")
    
    # Start both dashboards in parallel
    print("[START] Starting Enterprise Data Upload Dashboard on http://localhost:8501")
    upload_process = Process(target=run_data_upload_dashboard)
    upload_process.start()
    
    print("[START] Starting ML Monitoring Dashboard on http://localhost:8502")
    monitoring_process = Process(target=run_ml_monitoring_dashboard)
    monitoring_process.start()
    
    # Wait a moment for servers to start
    time.sleep(3)
    
    # Open browsers
    print("[BROWSER] Opening dashboards in browser...")
    try:
        webbrowser.open("http://localhost:8501")
        time.sleep(1)
        webbrowser.open("http://localhost:8502")
    except:
        pass
    
    print("="*60)
    print("[OK] Dashboards launched successfully!")
    print("[URL] Enterprise Data Upload: http://localhost:8501")
    print("[URL] ML Monitoring: http://localhost:8502")
    print("[INFO] Press Ctrl+C to stop both dashboards")
    print("="*60)
    
    try:
        # Wait for both processes
        upload_process.join()
        monitoring_process.join()
    except KeyboardInterrupt:
        print("\n[STOP] Shutting down dashboards...")
        upload_process.terminate()
        monitoring_process.terminate()
        upload_process.join()
        monitoring_process.join()
        print("[OK] Dashboards stopped successfully!")

if __name__ == "__main__":
    main()