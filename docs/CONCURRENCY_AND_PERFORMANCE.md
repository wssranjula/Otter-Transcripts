# Concurrency and Performance Guide

## Current Architecture

### ✅ What Works Well

1. **FastAPI Async Framework**
   - Uses async/await for I/O operations
   - Handles multiple concurrent requests efficiently
   - Each request runs in async event loop

2. **Thread Pool for CPU-bound Operations**
   - LLM calls use `asyncio.to_thread()` to avoid blocking
   - Neo4j queries run in thread pool
   - Prevents blocking the async event loop

3. **Connection Management**
   - Postgres: Connection pool (1-10 connections)
   - Neo4j: Driver manages connection pool automatically (default: ~50 connections)

### ⚠️ Current Limitations

1. **Single Process**
   - FastAPI runs as single process (systemd service)
   - No worker pool configuration
   - Limited by single CPU core for CPU-bound tasks

2. **LLM API Rate Limits**
   - Mistral free tier: ~3 requests/minute
   - Mistral paid tier: Varies by plan
   - **Bottleneck**: Multiple concurrent requests will hit rate limits

3. **Memory Constraints**
   - VPS Lite 2: 4GB RAM
   - Each LLM call loads model context (memory)
   - Multiple concurrent requests = memory pressure

4. **No Request Queue**
   - All requests processed immediately
   - No prioritization or throttling

---

## Performance Under Load

### Scenario 1: 5 Concurrent Requests

**What happens:**
- ✅ FastAPI accepts all 5 requests
- ✅ Each request starts processing
- ⚠️ All 5 hit Mistral API simultaneously
- ⚠️ Mistral rate limit: 3 requests/minute → **2 requests fail/wait**
- ✅ Neo4j handles 5 queries (connection pool: ~50)
- ⚠️ Memory usage: ~2-3GB (moderate)

**Result:** 3 succeed immediately, 2 wait or timeout

### Scenario 2: 10 Concurrent Requests

**What happens:**
- ✅ FastAPI accepts all 10 requests
- ⚠️ **Critical bottleneck**: Mistral rate limit exceeded
- ⚠️ Requests queue up waiting for API availability
- ⚠️ Memory usage: ~3-4GB (high)
- ⚠️ Some requests may timeout (60s timeout)

**Result:** Requests processed sequentially due to rate limits, some timeouts

### Scenario 3: 50 Concurrent Requests

**What happens:**
- ✅ FastAPI accepts all 50 requests
- ❌ **Mistral API overwhelmed** (rate limit)
- ❌ Memory pressure (4GB limit)
- ❌ Many requests timeout
- ✅ Neo4j handles fine (connection pool)

**Result:** System struggles, many failures

---

## Recommendations for Production

### 1. Add Request Rate Limiting ⭐ **HIGH PRIORITY**

**Problem:** No protection against API rate limits

**Solution:** Add rate limiting middleware

```python
# Install: pip install slowapi
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/admin/chat")
@limiter.limit("5/minute")  # 5 requests per minute per IP
async def admin_chat(...):
    ...
```

**Benefits:**
- Prevents API rate limit exhaustion
- Protects against abuse
- Better user experience (clear error messages)

### 2. Add Request Queue for LLM Calls ⭐ **HIGH PRIORITY**

**Problem:** Multiple concurrent LLM calls hit rate limits

**Solution:** Queue LLM requests with priority

```python
import asyncio
from collections import deque

class LLMRequestQueue:
    def __init__(self, max_concurrent=3):
        self.queue = asyncio.Queue()
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.workers = []
    
    async def process_request(self, request_id, prompt):
        async with self.semaphore:  # Limit concurrent API calls
            # Process LLM request
            result = await call_llm(prompt)
            return result
```

**Benefits:**
- Respects API rate limits
- Prevents overwhelming Mistral API
- Better reliability

### 3. Add FastAPI Workers (Gunicorn/Uvicorn) ⭐ **MEDIUM PRIORITY**

**Problem:** Single process limits CPU utilization

**Solution:** Use Gunicorn with Uvicorn workers

```bash
# Install: pip install gunicorn uvicorn

# Update systemd service
[Service]
ExecStart=/home/user/Otter-Transcripts/venv/bin/gunicorn \
    run_unified_agent:app \
    --workers 2 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --timeout 120
```

**Benefits:**
- Better CPU utilization (2 workers = 2 CPU cores)
- Handles more concurrent requests
- Better fault tolerance (one worker crashes, others continue)

**Trade-off:** More memory usage (2x workers = 2x memory)

### 4. Optimize Neo4j Connection Pool ⭐ **LOW PRIORITY**

**Current:** Default pool (~50 connections)

**Recommendation:** Explicitly configure based on load

```python
from neo4j import GraphDatabase

driver = GraphDatabase.driver(
    uri,
    auth=(user, password),
    max_connection_lifetime=3600,  # 1 hour
    max_connection_pool_size=20,   # Limit to 20 connections
    connection_acquisition_timeout=30  # Wait max 30s for connection
)
```

**Benefits:**
- Better connection management
- Prevents connection exhaustion
- More predictable performance

### 5. Add Caching for Frequent Queries ⭐ **MEDIUM PRIORITY**

**Problem:** Same queries hit LLM repeatedly

**Solution:** Redis or in-memory cache

```python
from functools import lru_cache
import redis

redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

@lru_cache(maxsize=100)
def cached_llm_call(query_hash, query):
    # Check Redis first
    cached = redis_client.get(f"query:{query_hash}")
    if cached:
        return cached
    
    # Call LLM
    result = call_llm(query)
    
    # Cache for 1 hour
    redis_client.setex(f"query:{query_hash}", 3600, result)
    return result
```

**Benefits:**
- Faster responses for repeated queries
- Reduces LLM API calls
- Lower costs

---

## Production Configuration

### Recommended Setup for Infomaniak VPS Lite 2 (2 vCPU, 4GB RAM)

```python
# config/config.json additions
{
  "performance": {
    "max_concurrent_llm_requests": 3,
    "request_queue_size": 50,
    "rate_limit_per_minute": 5,
    "cache_enabled": true,
    "cache_ttl_seconds": 3600
  },
  "mistral": {
    "api_key": "...",
    "model": "mistral-small-latest",  // Use smaller model for better rate limits
    "max_retries": 3,
    "retry_delay": 2.0
  }
}
```

### Systemd Service with Gunicorn

```ini
[Service]
ExecStart=/home/user/Otter-Transcripts/venv/bin/gunicorn \
    "run_unified_agent:app" \
    --workers 2 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --timeout 120 \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    --preload

# Resource limits
MemoryMax=3G
CPUQuota=200%
```

---

## Monitoring and Alerts

### Key Metrics to Monitor

1. **Request Rate**
   ```bash
   # Count requests per minute
   tail -f unified-agent.log | grep "POST /admin/chat" | \
   awk '{print $1}' | uniq -c
   ```

2. **Response Times**
   ```bash
   # Average response time
   grep "Response time" unified-agent.log | \
   awk '{sum+=$NF; count++} END {print sum/count "ms"}'
   ```

3. **Error Rate**
   ```bash
   # Count errors
   grep -c "ERROR" unified-agent.log
   ```

4. **Memory Usage**
   ```bash
   # Check memory
   ps aux | grep python | awk '{sum+=$6} END {print sum/1024 "MB"}'
   ```

### Alert Thresholds

- **Response time > 30s**: Alert
- **Error rate > 10%**: Alert
- **Memory usage > 80%**: Alert
- **API rate limit errors**: Alert

---

## Expected Performance

### With Current Setup (No Optimizations)

| Concurrent Requests | Success Rate | Avg Response Time | Notes |
|-------------------|--------------|------------------|-------|
| 1-3 | 100% | 5-15s | ✅ Good |
| 4-5 | 60-80% | 15-30s | ⚠️ Some timeouts |
| 6-10 | 30-50% | 30-60s | ⚠️ Many timeouts |
| 10+ | <20% | 60s+ | ❌ Poor |

### With Recommended Optimizations

| Concurrent Requests | Success Rate | Avg Response Time | Notes |
|-------------------|--------------|------------------|-------|
| 1-5 | 100% | 5-15s | ✅ Excellent |
| 6-10 | 90-95% | 15-25s | ✅ Good |
| 11-20 | 70-85% | 25-40s | ⚠️ Some queuing |
| 20+ | 50-70% | 40-60s | ⚠️ Queue delays |

---

## Quick Wins (Easy to Implement)

1. **Switch to Smaller Mistral Model**
   - `mistral-small-latest` has better rate limits
   - Lower latency
   - Still good quality

2. **Add Request Timeout**
   - Already implemented (60s)
   - Prevents hanging requests

3. **Add Health Check Endpoint**
   - Already implemented (`/health`)
   - Monitor system status

4. **Enable Request Logging**
   - Track request patterns
   - Identify bottlenecks

---

## Scaling Beyond VPS Lite 2

If you need to handle >20 concurrent requests:

1. **Upgrade VPS**
   - VPS Lite 4: 4 vCPU, 8GB RAM (~€12/month)
   - Allows 4 workers instead of 2

2. **Add Redis Cache**
   - Reduces LLM calls
   - Faster responses

3. **Upgrade Mistral Plan**
   - Higher rate limits
   - Better performance

4. **Load Balancing** (Advanced)
   - Multiple VPS instances
   - Nginx load balancer
   - Only if handling 100+ concurrent requests

---

## Summary

**Current State:**
- ✅ Handles 1-3 concurrent requests well
- ⚠️ Struggles with 5+ concurrent requests
- ⚠️ Limited by Mistral API rate limits

**Recommended Actions:**
1. Add rate limiting (prevents abuse)
2. Add request queue for LLM calls (respects API limits)
3. Use Gunicorn with 2 workers (better CPU utilization)
4. Switch to smaller Mistral model (better rate limits)

**Expected Improvement:**
- Handle 5-10 concurrent requests reliably
- Better response times
- Fewer timeouts
- More stable system




