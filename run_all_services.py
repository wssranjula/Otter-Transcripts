#!/usr/bin/env python3
"""
Process Manager for Sybil Services
Runs all services as separate processes for better resource management
"""

import subprocess
import sys
import os
import time
import signal
import psutil
from pathlib import Path

class ServiceManager:
    """Manage multiple Sybil services"""
    
    def __init__(self):
        self.processes = {}
        self.services = {
            "core": {
                "script": "run_unified_agent.py",
                "port": 8000,
                "description": "Core services (Sybil agent, Neo4j tools)"
            },
            "whatsapp": {
                "script": "run_whatsapp_service.py", 
                "port": 8001,
                "description": "WhatsApp bot service"
            },
            "admin": {
                "script": "run_admin_service.py",
                "port": 8002,
                "description": "Admin API service"
            },
            "streamlit": {
                "script": "run_streamlit.py",
                "port": 8501,
                "description": "Streamlit chat interface"
            }
        }
    
    def start_service(self, service_name: str):
        """Start a specific service"""
        if service_name not in self.services:
            print(f"❌ Unknown service: {service_name}")
            return False
        
        service = self.services[service_name]
        
        if service_name in self.processes:
            print(f"⚠️  Service {service_name} is already running")
            return True
        
        try:
            print(f"🚀 Starting {service_name} service...")
            process = subprocess.Popen(
                [sys.executable, service["script"]],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.processes[service_name] = process
            print(f"✅ {service_name} service started (PID: {process.pid})")
            return True
            
        except Exception as e:
            print(f"❌ Failed to start {service_name} service: {e}")
            return False
    
    def stop_service(self, service_name: str):
        """Stop a specific service"""
        if service_name not in self.processes:
            print(f"⚠️  Service {service_name} is not running")
            return True
        
        try:
            process = self.processes[service_name]
            process.terminate()
            process.wait(timeout=10)
            del self.processes[service_name]
            print(f"✅ {service_name} service stopped")
            return True
            
        except subprocess.TimeoutExpired:
            process.kill()
            del self.processes[service_name]
            print(f"⚠️  {service_name} service force killed")
            return True
        except Exception as e:
            print(f"❌ Failed to stop {service_name} service: {e}")
            return False
    
    def start_all(self):
        """Start all services"""
        print("🚀 Starting all Sybil services...")
        print("=" * 60)
        
        for service_name in self.services:
            self.start_service(service_name)
            time.sleep(2)  # Give each service time to start
        
        print("=" * 60)
        print("✅ All services started!")
        self.print_status()
    
    def stop_all(self):
        """Stop all services"""
        print("🛑 Stopping all Sybil services...")
        print("=" * 60)
        
        for service_name in list(self.processes.keys()):
            self.stop_service(service_name)
        
        print("=" * 60)
        print("✅ All services stopped!")
    
    def restart_service(self, service_name: str):
        """Restart a specific service"""
        print(f"🔄 Restarting {service_name} service...")
        self.stop_service(service_name)
        time.sleep(1)
        self.start_service(service_name)
    
    def print_status(self):
        """Print status of all services"""
        print("\n📊 Service Status:")
        print("-" * 60)
        
        for service_name, service in self.services.items():
            if service_name in self.processes:
                process = self.processes[service_name]
                if process.poll() is None:
                    status = "🟢 Running"
                    pid = process.pid
                else:
                    status = "🔴 Stopped"
                    pid = "N/A"
            else:
                status = "⚪ Not started"
                pid = "N/A"
            
            print(f"{service_name:12} | {status:12} | PID: {pid:>6} | Port: {service['port']}")
        
        print("-" * 60)
    
    def check_health(self):
        """Check health of all services"""
        print("\n🏥 Health Check:")
        print("-" * 60)
        
        for service_name, service in self.services.items():
            if service_name in self.processes:
                try:
                    import requests
                    response = requests.get(f"http://localhost:{service['port']}/health", timeout=5)
                    if response.status_code == 200:
                        print(f"✅ {service_name}: Healthy")
                    else:
                        print(f"⚠️  {service_name}: Unhealthy (HTTP {response.status_code})")
                except Exception as e:
                    print(f"❌ {service_name}: Error - {e}")
            else:
                print(f"⚪ {service_name}: Not running")
    
    def monitor_resources(self):
        """Monitor system resources"""
        try:
            memory = psutil.virtual_memory()
            cpu = psutil.cpu_percent(interval=1)
            
            print(f"\n💻 System Resources:")
            print(f"Memory: {memory.percent:.1f}% used ({memory.available / (1024**3):.1f} GB available)")
            print(f"CPU: {cpu:.1f}% used")
            
            if memory.percent > 85:
                print("⚠️  High memory usage detected!")
            if cpu > 90:
                print("⚠️  High CPU usage detected!")
                
        except Exception as e:
            print(f"❌ Error monitoring resources: {e}")
    
    def interactive_mode(self):
        """Interactive management mode"""
        print("\n🎛️  Interactive Service Manager")
        print("Commands: start <service>, stop <service>, restart <service>, status, health, resources, quit")
        
        while True:
            try:
                command = input("\n> ").strip().lower().split()
                
                if not command:
                    continue
                
                if command[0] == "quit" or command[0] == "exit":
                    break
                elif command[0] == "start":
                    if len(command) > 1:
                        self.start_service(command[1])
                    else:
                        self.start_all()
                elif command[0] == "stop":
                    if len(command) > 1:
                        self.stop_service(command[1])
                    else:
                        self.stop_all()
                elif command[0] == "restart":
                    if len(command) > 1:
                        self.restart_service(command[1])
                    else:
                        print("Please specify a service to restart")
                elif command[0] == "status":
                    self.print_status()
                elif command[0] == "health":
                    self.check_health()
                elif command[0] == "resources":
                    self.monitor_resources()
                else:
                    print("Unknown command. Available: start, stop, restart, status, health, resources, quit")
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")
        
        print("\n👋 Goodbye!")

def main():
    """Main execution"""
    manager = ServiceManager()
    
    print("🤖 Sybil Service Manager")
    print("=" * 60)
    print("Available services:")
    for name, service in manager.services.items():
        print(f"  {name:12} - {service['description']} (Port {service['port']})")
    print("=" * 60)
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "start":
            if len(sys.argv) > 2:
                manager.start_service(sys.argv[2])
            else:
                manager.start_all()
        elif command == "stop":
            if len(sys.argv) > 2:
                manager.stop_service(sys.argv[2])
            else:
                manager.stop_all()
        elif command == "restart":
            if len(sys.argv) > 2:
                manager.restart_service(sys.argv[2])
            else:
                print("Please specify a service to restart")
        elif command == "status":
            manager.print_status()
        elif command == "health":
            manager.check_health()
        elif command == "interactive":
            manager.interactive_mode()
        else:
            print("Unknown command. Available: start, stop, restart, status, health, interactive")
    else:
        # Default: start all services
        manager.start_all()
        
        try:
            print("\nPress CTRL+C to stop all services")
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\nShutting down all services...")
            manager.stop_all()

if __name__ == "__main__":
    main()
