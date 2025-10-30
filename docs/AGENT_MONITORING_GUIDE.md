# Agent Monitoring System Guide

Comprehensive monitoring and logging system for tracking Sybil agent behavior, performance, and errors.

---

## Overview

The agent monitoring system tracks:
- **Query sessions** - Each user query from start to finish
- **Performance metrics** - Duration, retries, tool usage
- **Errors** - Failed queries, syntax errors, retry attempts
- **Tool execution** - Database queries, schema checks, search operations
- **Sub-agent usage** - Which sub-agents were called and when

All data is logged in structured JSON format for easy analysis.

---

## Log Files

### Main Log Files

1. **`agent_monitoring.log`** - Structured JSON logs for analysis
   - Session tracking
   - Performance metrics
   - Error details
   - Tool execution data

2. **`unified_agent.log`** - Human-readable application logs
   - Info and error messages
   - Standard logging output
   - Debug information

---

## Log Structure

Each log entry is a JSON object with this structure:

```json
{
  "event": "session_start",
  "session_id": "1730270400.123",
  "timestamp": "2024-10-30T08:00:00.123Z",
  "data": {
    // Event-specific data
  }
}
```

### Event Types

#### 1. **session_start**
Marks the beginning of a query session.

```json
{
  "event": "session_start",
  "session_id": "1730270400.123",
  "data": {
    "source": "admin_panel",
    "user_question": "What UNEA meetings happened?",
    "timestamp": "2024-10-30T08:00:00Z"
  }
}
```

#### 2. **tool_call**
Logs each tool execution.

```json
{
  "event": "tool_call",
  "data": {
    "tool": "execute_cypher_query",
    "success": false,
    "duration_ms": 45.23,
    "error": "Cypher syntax error...",
    "timestamp": "2024-10-30T08:00:01Z"
  }
}
```

#### 3. **query_attempt**
Logs each Cypher query attempt.

```json
{
  "event": "query_attempt",
  "data": {
    "cypher": "MATCH (m:Meeting) WHERE...",
    "success": true,
    "result_count": 5,
    "retry_number": 2
  }
}
```

#### 4. **session_end**
Marks completion with summary statistics.

```json
{
  "event": "session_end",
  "data": {
    "session_id": "1730270400.123",
    "source": "admin_panel",
    "duration_seconds": 8.45,
    "status": "completed",
    "subagent_calls": 1,
    "tool_calls": 3,
    "retries": 2,
    "errors": 1,
    "answer_length": 523
  }
}
```

---

## Using the Monitoring System

### Automatic Monitoring

Monitoring is **automatic** - no setup required!

1. Start your unified agent:
   ```bash
   python run_unified_agent.py
   ```

2. Use the admin panel or WhatsApp bot

3. Logs are written to `agent_monitoring.log` automatically

### Console Logging

You'll also see enhanced console logs:

```
🔵 Starting query session 1730270400.123
✅ Query succeeded: 5 results in 0.45s
❌ Query failed in 0.12s: Cypher syntax error...
✅ Query completed in 8.45s - 523 chars
```

---

## Analyzing Logs

### Using the Analysis Script

Run the built-in analysis tool:

```bash
python scripts/analyze_agent_logs.py
```

This generates a comprehensive report with:

#### 1. **Performance Analysis**
```
📊 PERFORMANCE ANALYSIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 Query Duration:
  Average: 8.34s
  Min: 2.15s
  Max: 25.67s

✅ Success Rate: 95.2% (40/42)

🔄 Retry Statistics:
  Total retries: 15
  Average per query: 0.36
  Queries with retries: 8/42
```

#### 2. **Error Analysis**
```
🐛 ERROR ANALYSIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❌ Total failed queries: 15

📊 Error Types:
  contains_syntax: 8
  datetime_functions: 4
  cypher_syntax: 2
  missing_properties: 1

🔍 Sample Failed Queries:
  Query: MATCH (m:Meeting {title: CONTAINS 'UNEA'})...
  Error: Invalid input 'CONTAINS': expected...
```

#### 3. **Source Analysis**
```
📍 SOURCE ANALYSIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Queries by Source:
  admin_panel: 35
  whatsapp: 7
```

#### 4. **Tool Performance**
```
🔧 TOOL PERFORMANCE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Tool Statistics:

  execute_cypher_query:
    Calls: 58
    Success rate: 74.1%
    Avg duration: 245ms

  get_database_schema:
    Calls: 12
    Success rate: 100.0%
    Avg duration: 123ms
```

#### 5. **Recent Sessions**
```
📜 RECENT SESSIONS (Last 5)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. ✅ Session 17302704...
   Source: admin_panel
   Duration: 8.45s
   Retries: 2
   Sub-agents: 1
   Tool calls: 3
   Answer length: 523 chars
```

---

## Manual Log Analysis

### Using jq (JSON query tool)

```bash
# Get all successful sessions
cat agent_monitoring.log | jq 'select(.event == "session_end" and .data.status == "completed")'

# Find sessions with retries
cat agent_monitoring.log | jq 'select(.event == "session_end" and .data.retries > 0)'

# Get average query duration
cat agent_monitoring.log | jq -s 'map(select(.event == "session_end")) | map(.data.duration_seconds) | add / length'

# Find all errors
cat agent_monitoring.log | jq 'select(.event == "error")'
```

### Using Python

```python
import json

# Load and analyze logs
sessions = []
with open('agent_monitoring.log', 'r') as f:
    for line in f:
        event = json.loads(line)
        if event['event'] == 'session_end':
            sessions.append(event['data'])

# Calculate metrics
avg_duration = sum(s['duration_seconds'] for s in sessions) / len(sessions)
success_rate = sum(1 for s in sessions if s['status'] == 'completed') / len(sessions)
avg_retries = sum(s['retries'] for s in sessions) / len(sessions)

print(f"Average duration: {avg_duration:.2f}s")
print(f"Success rate: {success_rate*100:.1f}%")
print(f"Average retries: {avg_retries:.2f}")
```

---

## Key Metrics to Monitor

### 1. **Success Rate**
Target: > 95%

If lower:
- Check error types
- Review failing queries
- Improve prompt examples

### 2. **Average Retries**
Target: < 0.5 per query

If higher:
- Common errors indicate prompt issues
- Add more examples for common mistakes
- Improve error hints

### 3. **Query Duration**
Target: < 10s for simple queries

If higher:
- Check database performance
- Review complex queries
- Consider caching frequently accessed data

### 4. **Tool Success Rate**
Target: > 85% for execute_cypher_query

If lower:
- Schema mismatches
- Prompt needs improvement
- Database issues

---

## Improving Agent Based on Logs

### 1. **Identify Common Errors**

Run analysis:
```bash
python scripts/analyze_agent_logs.py
```

Look at "Error Types" section.

### 2. **Add Examples for Common Mistakes**

If you see many `contains_syntax` errors:

```python
# In sybil_subagents.py QUERY_SUBAGENT_PROMPT
**Common Mistakes:**
- ❌ {property: CONTAINS 'value'}
- ✅ WHERE property CONTAINS 'value'
```

### 3. **Improve Error Hints**

In `execute_cypher_query` tool, add specific hints:

```python
if "your_error_pattern" in error_msg:
    retry_hint = "Specific guidance for this error"
```

### 4. **Monitor Performance Trends**

Run analysis weekly:
```bash
python scripts/analyze_agent_logs.py > reports/week_$(date +%Y%m%d).txt
```

Compare metrics over time:
- Success rate trending up? ✅ Improvements working
- Retries going down? ✅ Better prompts
- Duration increasing? ⚠️ Investigate

---

## Log Rotation

To prevent logs from growing too large:

### Manual Rotation

```bash
# Archive old logs
mv agent_monitoring.log agent_monitoring_$(date +%Y%m%d).log

# Start fresh
touch agent_monitoring.log
```

### Automatic Rotation (Linux/Mac)

Add to crontab:
```bash
# Rotate logs weekly (Sunday midnight)
0 0 * * 0 mv /path/to/agent_monitoring.log /path/to/archive/agent_monitoring_$(date +\%Y\%m\%d).log && touch /path/to/agent_monitoring.log
```

### Automatic Rotation (Windows)

Use Windows Task Scheduler to run:
```powershell
$date = Get-Date -Format "yyyyMMdd"
Move-Item "agent_monitoring.log" "archive\agent_monitoring_$date.log"
New-Item "agent_monitoring.log" -ItemType File
```

---

## Monitoring Best Practices

### 1. **Regular Reviews**

- **Daily**: Check for new error patterns
- **Weekly**: Run full analysis report
- **Monthly**: Review trends and improvements

### 2. **Alert on Issues**

Create alerts for:
- Success rate < 90%
- Average retries > 1.0
- Any session taking > 30s

### 3. **Track Improvements**

After making changes:
1. Note baseline metrics
2. Make improvements
3. Run queries
4. Compare new metrics
5. Iterate

### 4. **Share Insights**

Use reports to:
- Identify training needs
- Guide prompt engineering
- Prioritize improvements
- Track progress over time

---

## Troubleshooting

### Logs Not Being Created

**Issue**: No `agent_monitoring.log` file

**Solution**:
1. Check file permissions
2. Verify monitoring is initialized:
   ```python
   from src.core.agent_logger import get_monitor
   monitor = get_monitor()
   ```
3. Run a test query

### Analysis Script Errors

**Issue**: `python scripts/analyze_agent_logs.py` fails

**Solutions**:
- Check Python path: `cd` to project root first
- Verify log file exists
- Check JSON formatting in logs

### Missing Events

**Issue**: Some events not appearing in logs

**Solution**:
- Check if monitoring session was started
- Verify tool calls have monitoring code
- Check for exceptions in code

---

## Advanced Usage

### Custom Analysis

Create custom analysis scripts:

```python
from src.core.agent_logger import get_monitor
import json

# During runtime
monitor = get_monitor()
metrics = monitor.get_session_metrics()
print(f"Current session: {metrics}")

# Post-processing
with open('agent_monitoring.log') as f:
    for line in f:
        event = json.loads(line)
        # Your custom analysis
```

### Real-time Monitoring

Watch logs in real-time:

```bash
# Linux/Mac
tail -f agent_monitoring.log | jq .

# Windows PowerShell
Get-Content agent_monitoring.log -Wait -Tail 10
```

### Integration with Monitoring Tools

Export to monitoring platforms:

```python
# Send to Prometheus, Datadog, etc.
import requests

def send_metrics(session_data):
    requests.post('http://monitoring-service/metrics', json=session_data)
```

---

## Summary

The agent monitoring system provides:

✅ **Automatic tracking** of all queries  
✅ **Structured JSON logs** for easy analysis  
✅ **Built-in analysis tool** for insights  
✅ **Performance metrics** to track improvements  
✅ **Error tracking** to identify issues  
✅ **Retry monitoring** to measure resilience  

Use it to continuously improve your Sybil agent! 🚀

---

**Next Steps:**
1. Run some queries to generate logs
2. Use `python scripts/analyze_agent_logs.py` to see insights
3. Identify patterns and make improvements
4. Track progress over time

---

**Version**: 1.0.0  
**Last Updated**: October 30, 2024

