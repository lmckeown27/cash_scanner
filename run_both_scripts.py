#!/usr/bin/env python3
"""
Helper script to run both CASH scanners with real-time alerts during historical scanning.
"""

import subprocess
import time
import sys
import signal
import os
import threading
import queue
import re

def signal_handler(sig, frame):
    print("\n🛑 Stopping all scripts...")
    sys.exit(0)

def monitor_realtime_output(process, alert_queue):
    """Monitor real-time process output for CASH transaction alerts"""
    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            # Look for CASH transaction alerts
            if "REAL-TIME CASH TRANSACTION DETECTED" in output:
                alert_queue.put(("CASH_ALERT", output.strip()))
            elif "Rate limited" in output or "HTTP 429" in output:
                alert_queue.put(("RATE_LIMIT", output.strip()))
            elif "Error" in output or "Failed" in output:
                alert_queue.put(("ERROR", output.strip()))

def main():
    print("🚀 CASH Token Scanner Launcher")
    print("=" * 60)
    print("This script will run both scanners simultaneously:")
    print("📚 Historical scanner: Analyzes past transactions")
    print("⚡ Real-time monitor: Provides live CASH transaction alerts")
    print("=" * 60)
    
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    # Queue for real-time alerts
    alert_queue = queue.Queue()
    
    print("\n1️⃣  Starting historical scanner...")
    print("📊 Historical scanner will start analyzing immediately.")
    print("📡 Real-time monitor will start in background shortly.")
    print("💡 Press Ctrl+C to stop both scripts.")
    print("=" * 60)
    
    # Start historical scanner first
    historical_process = subprocess.Popen([
        sys.executable, "historical_cash_scanner.py"
    ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, universal_newlines=True)
    
    print("✅ Historical scanner started (PID: {})".format(historical_process.pid))
    
    # Start real-time monitor in background after a short delay
    print("\n2️⃣  Starting real-time monitor in background...")
    time.sleep(2)  # Brief delay to let historical scanner start
    
    realtime_process = subprocess.Popen([
        sys.executable, "realtime_cash_monitor.py"
    ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, universal_newlines=True)
    
    print("✅ Real-time monitor started in background (PID: {})".format(realtime_process.pid))
    
    # Start monitoring thread for real-time alerts
    monitor_thread = threading.Thread(
        target=monitor_realtime_output, 
        args=(realtime_process, alert_queue),
        daemon=True
    )
    monitor_thread.start()
    
    # Monitor both processes
    historical_output = ""
    last_alert_check = time.time()
    
    try:
        while True:
            # Check for real-time alerts
            try:
                while not alert_queue.empty():
                    alert_type, alert_message = alert_queue.get_nowait()
                    
                    if alert_type == "CASH_ALERT":
                        print("\n" + "=" * 60)
                        print("🔥 REAL-TIME CASH TRANSACTION ALERT!")
                        print("=" * 60)
                        print(alert_message)
                        print("=" * 60 + "\n")
                    elif alert_type == "RATE_LIMIT":
                        print(f"\n⚠️  RATE LIMIT WARNING: {alert_message}")
                    elif alert_type == "ERROR":
                        print(f"\n❌ REAL-TIME ERROR: {alert_message}")
                        
            except queue.Empty:
                pass
            
            # Check historical scanner output
            if historical_process.stdout:
                historical_line = historical_process.stdout.readline()
                if historical_line:
                    print(historical_line.rstrip())
                    historical_output += historical_line
            
            # Check if historical scanner is done
            if historical_process.poll() is not None:
                # Read any remaining output
                if historical_process.stdout:
                    remaining_output = historical_process.stdout.read()
                    if remaining_output:
                        print(remaining_output)
                break
            
            # Check if real-time monitor is still running
            if realtime_process.poll() is not None:
                print("\n⚠️  Real-time monitor has stopped unexpectedly!")
                break
            
            # Small delay to prevent busy waiting
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping both scripts...")
    
    finally:
        print("\n🛑 Cleaning up processes...")
        
        # Stop historical scanner
        if historical_process.poll() is None:
            historical_process.terminate()
            try:
                historical_process.wait(timeout=5)
                print("✅ Historical scanner stopped gracefully.")
            except subprocess.TimeoutExpired:
                historical_process.kill()
                historical_process.wait()
                print("✅ Historical scanner stopped.")
        
        # Stop real-time monitor
        if realtime_process.poll() is None:
            realtime_process.terminate()
            try:
                realtime_process.wait(timeout=5)
                print("✅ Real-time monitor stopped gracefully.")
            except subprocess.TimeoutExpired:
                realtime_process.kill()
                realtime_process.wait()
                print("✅ Real-time monitor stopped.")
    
    print("\n🎯 Both scripts have been stopped.")

if __name__ == "__main__":
    main() 