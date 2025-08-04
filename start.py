#!/usr/bin/env python3
"""
Start script for trendSaaS application
Runs both the backend (main.py) and frontend (HTTP server) concurrently
"""

import subprocess
import threading
import time
import sys
import os
import signal
from pathlib import Path
import requests
import socket

def is_port_open(host, port, timeout=1):
    """Check if a port is open and accepting connections"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        result = sock.connect_ex((host, port))
        return result == 0
    except socket.error:
        return False
    finally:
        sock.close()

def wait_for_backend(host='localhost', port=8000, max_wait=30):
    """Wait for backend to be fully started and accepting connections"""
    print(f"Waiting for backend to start on {host}:{port}...")
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        if is_port_open(host, port):
            print(f"✓ Backend is ready on {host}:{port}")
            return True
        time.sleep(0.5)
    
    print(f"✗ Backend failed to start within {max_wait} seconds")
    return False

def run_backend():
    """Run the main.py backend server"""
    print("Starting backend server...")
    try:
        # Use Popen instead of run to allow non-blocking execution
        process = subprocess.Popen([sys.executable, "main.py"])
        process.wait()  # Wait for process to complete
    except KeyboardInterrupt:
        print("Backend server stopped")
        if 'process' in locals():
            process.terminate()

def run_frontend():
    """Run the frontend HTTP server"""
    print("Starting frontend server...")
    try:
        # Change to frontend directory and start HTTP server
        frontend_dir = Path("frontend")
        if not frontend_dir.exists():
            print("Error: frontend directory not found")
            return
        
        original_dir = os.getcwd()
        os.chdir(frontend_dir)
        
        # Use Popen for non-blocking execution
        process = subprocess.Popen([sys.executable, "-m", "http.server", "3000"])
        
        # Change back to original directory
        os.chdir(original_dir)
        
        process.wait()  # Wait for process to complete
        
    except KeyboardInterrupt:
        print("Frontend server stopped")
        if 'process' in locals():
            process.terminate()

def main():
    """Main function to start both servers"""
    print("Starting trendSaaS application...")
    print("Backend will run on http://localhost:8000")
    print("Frontend will run on http://localhost:3000")
    print("Press Ctrl+C to stop both servers")
    print("-" * 50)
    
    backend_process = None
    frontend_process = None
    
    try:
        # Start backend in a separate process
        print("🚀 Launching backend...")
        backend_process = subprocess.Popen([sys.executable, "main.py"])
        
        # Wait for backend to be fully ready
        if wait_for_backend():
            # Backend is ready, now start frontend
            print("🚀 Launching frontend...")
            
            frontend_dir = Path("frontend")
            if not frontend_dir.exists():
                print("Error: frontend directory not found")
                return
            
            frontend_process = subprocess.Popen(
                [sys.executable, "-m", "http.server", "3000"],
                cwd=frontend_dir
            )
            
            print("✓ Frontend started on http://localhost:3000")
            print("\n🎉 Both servers are running!")
            print("📱 Open http://localhost:3000 in your browser")
            print("🔧 API available at http://localhost:8000")
            print("\nPress Ctrl+C to stop both servers")
            
            # Keep the main process alive and wait for user interrupt
            while True:
                time.sleep(1)
                
                # Check if processes are still running
                if backend_process.poll() is not None:
                    print("❌ Backend process has stopped")
                    break
                if frontend_process and frontend_process.poll() is not None:
                    print("❌ Frontend process has stopped")
                    break
        else:
            print("❌ Failed to start backend server")
            
    except KeyboardInterrupt:
        print("\n🛑 Shutting down servers...")
        
        # Terminate processes gracefully
        if frontend_process and frontend_process.poll() is None:
            print("Stopping frontend server...")
            frontend_process.terminate()
            try:
                frontend_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                frontend_process.kill()
        
        if backend_process and backend_process.poll() is None:
            print("Stopping backend server...")
            backend_process.terminate()
            try:
                backend_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                backend_process.kill()
        
        print("✓ All servers stopped")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        
    finally:
        # Ensure processes are cleaned up
        for process in [backend_process, frontend_process]:
            if process and process.poll() is None:
                try:
                    process.terminate()
                    process.wait(timeout=3)
                except:
                    try:
                        process.kill()
                    except:
                        pass

if __name__ == "__main__":
    main()