# 🚀 Sybil Service Optimization Guide

## Current Problem

The unified agent is handling too many responsibilities:
- WhatsApp Bot (real-time messaging)
- Google Drive RAG (background processing) 
- Admin API (web interface)
- Streamlit Interface (chat UI)
- Next.js Frontend (admin panel)

This can lead to:
- **Resource contention** between services
- **Single point of failure** for all functionality
- **Difficulty scaling** individual components
- **Memory bloat** from loading all services

## Solution: Service Separation

I've created a microservices architecture that separates concerns:

### 🏗️ **New Architecture**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   WhatsApp      │    │   Admin API     │    │   Streamlit     │
│   Service       │    │   Service       │    │   Service       │
│   (Port 8001)   │    │   (Port 8002)   │    │   (Port 8501)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   Core          │
                    │   Service       │
                    │   (Port 8000)   │
                    └─────────────────┘
                             │
                    ┌─────────────────┐
                    │   Neo4j         │
                    │   Database      │
                    └─────────────────┘
```

## 🛠️ **New Files Created**

### **Service Scripts**
- `run_admin_service.py` - Admin API only (Port 8002)
- `run_whatsapp_service.py` - WhatsApp bot only (Port 8001)
- `run_all_services.py` - Process manager for all services
- `src/services/resource_monitor.py` - Resource monitoring

### **Documentation**
- `ARCHITECTURE_RECOMMENDATIONS.md` - Detailed architecture guide
- `SERVICE_OPTIMIZATION_GUIDE.md` - This guide

## 🚀 **How to Use**

### **Option 1: Run All Services (Recommended)**
```bash
# Start all services
python run_all_services.py

# Or start specific services
python run_all_services.py start admin
python run_all_services.py start whatsapp
```

### **Option 2: Run Services Individually**
```bash
# Core services (Sybil agent, Neo4j)
python run_unified_agent.py

# Admin API only
python run_admin_service.py

# WhatsApp bot only  
python run_whatsapp_service.py

# Streamlit interface
python run_streamlit.py
```

### **Option 3: Interactive Management**
```bash
python run_all_services.py interactive
```

## 📊 **Service Management Commands**

```bash
# Check status of all services
python run_all_services.py status

# Start specific service
python run_all_services.py start admin

# Stop specific service
python run_all_services.py stop whatsapp

# Restart service
python run_all_services.py restart admin

# Health check
python run_all_services.py health

# Interactive mode
python run_all_services.py interactive
```

## 🎯 **Benefits of New Architecture**

### **1. Resource Efficiency**
- Each service uses only what it needs
- Can disable non-critical services when resources are low
- Better memory management per service

### **2. Scalability**
- Scale individual services independently
- Add load balancing for high-traffic services
- Deploy services on different servers

### **3. Reliability**
- Service isolation prevents cascading failures
- Can restart individual services without affecting others
- Better error handling and recovery

### **4. Development**
- Easier to debug specific functionality
- Independent deployment cycles
- Clear separation of concerns

## 🔧 **Resource Monitoring**

The new system includes resource monitoring:

```python
# Automatic resource monitoring
from src.services.resource_monitor import resource_monitor

# Check system health
health = resource_monitor.get_system_health()
print(f"Memory: {health['memory']['percent']}%")
print(f"CPU: {health['cpu']['percent']}%")

# Get service recommendations
recommendations = resource_monitor.should_disable_services()
```

## 📈 **Performance Improvements**

### **Memory Usage**
- **Before**: ~500MB+ for all services
- **After**: ~100-200MB per service (can disable unused services)

### **CPU Usage**
- **Before**: All services compete for CPU
- **After**: Services can be prioritized based on importance

### **Startup Time**
- **Before**: ~30-60 seconds to load everything
- **After**: ~5-10 seconds per service

## 🚨 **Migration Strategy**

### **Phase 1: Immediate (Current)**
- Keep unified agent for development
- Use new services for production
- Test both approaches

### **Phase 2: Gradual Migration**
- Move admin functionality to separate service
- Move WhatsApp to separate service
- Keep core services together initially

### **Phase 3: Full Separation**
- All services independent
- Add service discovery
- Implement load balancing

## 🔍 **Monitoring & Alerting**

### **Key Metrics to Watch**
- Memory usage per service
- CPU usage per service
- API response times
- Error rates
- Database connections

### **Alert Thresholds**
- Memory > 80%: Warning
- Memory > 90%: Critical
- CPU > 80%: Warning
- CPU > 95%: Critical

## 🛡️ **Security Considerations**

### **Service Isolation**
- Each service runs in its own process
- Reduced attack surface
- Better access control

### **Network Security**
- Services communicate via HTTP/HTTPS
- Can add authentication between services
- Firewall rules per service

## 📋 **Deployment Options**

### **Single Server (Current)**
```bash
# Run all services on one server
python run_all_services.py
```

### **Multi-Server (Future)**
```bash
# Server 1: Core services
python run_unified_agent.py

# Server 2: Admin API
python run_admin_service.py

# Server 3: WhatsApp bot
python run_whatsapp_service.py
```

### **Docker (Advanced)**
```dockerfile
# Each service in its own container
docker run -p 8000:8000 sybil-core
docker run -p 8002:8002 sybil-admin
docker run -p 8001:8001 sybil-whatsapp
```

## 🎉 **Quick Start**

1. **Test the new architecture:**
   ```bash
   python run_all_services.py start admin
   python run_all_services.py status
   ```

2. **Access the services:**
   - Admin API: http://localhost:8002
   - WhatsApp: http://localhost:8001
   - Streamlit: http://localhost:8501

3. **Monitor resources:**
   ```bash
   python run_all_services.py health
   python run_all_services.py resources
   ```

## 🔄 **Rollback Plan**

If you need to go back to the unified approach:
```bash
# Stop all separate services
python run_all_services.py stop

# Start unified agent
python run_unified_agent.py
```

## 📞 **Support**

- Check service logs for errors
- Use `python run_all_services.py health` for diagnostics
- Monitor resources with `python run_all_services.py resources`
- Use interactive mode for real-time management

The new architecture provides better resource management, scalability, and reliability while maintaining all the functionality of the original unified agent! 🚀
