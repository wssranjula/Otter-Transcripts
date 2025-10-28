"""
Resource monitoring for unified agent
"""

import psutil
import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class ResourceMonitor:
    """Monitor system resources and service health"""
    
    def __init__(self):
        self.memory_threshold_warning = 70
        self.memory_threshold_critical = 85
        self.cpu_threshold_warning = 80
        self.cpu_threshold_critical = 90
        
    def get_system_health(self) -> Dict[str, Any]:
        """Get current system health status"""
        try:
            memory = psutil.virtual_memory()
            cpu = psutil.cpu_percent(interval=1)
            disk = psutil.disk_usage('/')
            
            # Determine overall status
            if memory.percent >= self.memory_threshold_critical or cpu >= self.cpu_threshold_critical:
                status = "critical"
            elif memory.percent >= self.memory_threshold_warning or cpu >= self.cpu_threshold_warning:
                status = "warning"
            else:
                status = "healthy"
            
            return {
                "status": status,
                "timestamp": datetime.now().isoformat(),
                "memory": {
                    "percent": memory.percent,
                    "available_gb": round(memory.available / (1024**3), 2),
                    "total_gb": round(memory.total / (1024**3), 2)
                },
                "cpu": {
                    "percent": cpu,
                    "count": psutil.cpu_count()
                },
                "disk": {
                    "percent": disk.percent,
                    "free_gb": round(disk.free / (1024**3), 2),
                    "total_gb": round(disk.total / (1024**3), 2)
                }
            }
        except Exception as e:
            logger.error(f"Error getting system health: {e}")
            return {
                "status": "error",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
    
    def should_disable_services(self) -> Dict[str, bool]:
        """Determine which services should be disabled based on resource usage"""
        health = self.get_system_health()
        
        if health["status"] == "critical":
            return {
                "gdrive_monitoring": True,  # Disable background processing
                "whatsapp_webhook": False,  # Keep critical services
                "admin_api": False,
                "streamlit": True  # Disable non-critical UI
            }
        elif health["status"] == "warning":
            return {
                "gdrive_monitoring": True,  # Disable background processing
                "whatsapp_webhook": False,
                "admin_api": False,
                "streamlit": False
            }
        else:
            return {
                "gdrive_monitoring": False,
                "whatsapp_webhook": False,
                "admin_api": False,
                "streamlit": False
            }
    
    def log_resource_usage(self):
        """Log current resource usage"""
        health = self.get_system_health()
        logger.info(f"Resource usage - Memory: {health['memory']['percent']:.1f}%, CPU: {health['cpu']['percent']:.1f}%")
        
        if health["status"] == "warning":
            logger.warning(f"High resource usage detected: {health['status']}")
        elif health["status"] == "critical":
            logger.error(f"Critical resource usage detected: {health['status']}")

# Global instance
resource_monitor = ResourceMonitor()
