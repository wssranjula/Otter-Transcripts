# Agent Monitoring System - Setup Complete! 📊

Comprehensive monitoring and logging system has been added to track agent behavior and performance.

---

## ✅ What Was Added

### 1. **Monitoring System** (`src/core/agent_logger.py`)
- `AgentMonitor` class for structured logging
- Tracks sessions, tool calls, queries, errors, and performance
- JSON format for easy analysis
- Automatic log rotation support

### 2. **Integration with Sybil Agent**
- Modified `src/agents/sybil_subagents.py` to log all activities:
  - Query sessions (start/end)
  - Tool executions (success/failure/duration)
  - Cypher query attempts (with retry tracking)
  - Error tracking with context
  - Performance metrics

### 3. **Source Tracking**
- Modified `src/unified_agent.py` - Admin panel queries tagged as `"admin_panel"`
- Modified `src/whatsapp/whatsapp_agent.py` - WhatsApp queries tagged as `"whatsapp"`

### 4. **Log Analysis Tool** (`scripts/analyze_agent_logs.py`)
Comprehensive analysis script that generates:
- Performance metrics (duration, success rate)
- Error analysis (types, patterns, examples)
- Source breakdown (admin vs WhatsApp)
- Tool performance stats
- Recent session summaries

### 5. **Documentation** (`docs/AGENT_MONITORING_GUIDE.md`)
Complete guide covering:
- Log structure and event types
- How to use the monitoring system
- Analysis techniques
- Best practices
- Troubleshooting

---

## 🚀 Quick Start

### Run Queries

Just use your system normally:

```bash
# Start unified agent
python run_unified_agent.py

# Use admin panel at http://localhost:3000
# Or send WhatsApp messages
```

Logs are automatically written to `agent_monitoring.log`

### Analyze Logs

Generate a comprehensive report:

```bash
python scripts/analyze_agent_logs.py
```

You'll see:

```
✅ Loaded 156 events from 42 sessions

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

🐛 ERROR ANALYSIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❌ Total failed queries: 15

📊 Error Types:
  contains_syntax: 8
  datetime_functions: 4
  cypher_syntax: 2
```

---

## 📋 What Gets Logged

### Session Events
- **session_start** - When query begins
- **session_end** - When query completes (with summary)

### Tool Events
- **tool_call** - Each tool execution (success/failure/duration)
- **query_attempt** - Each Cypher query (with retry tracking)

### Error Events
- **error** - Any error with context

### Console Logs
You'll also see enhanced console output:
```
🔵 Starting query session 1730270400.123
✅ Query succeeded: 5 results in 0.45s
❌ Query failed in 0.12s: Cypher syntax error...
✅ Query completed in 8.45s - 523 chars
```

---

## 📊 Key Metrics Tracked

### Performance
- Query duration (average, min, max)
- Success rate
- Tool execution time
- Response length

### Reliability
- Retry attempts per query
- Error frequency and types
- Tool success rates

### Usage
- Queries by source (admin vs WhatsApp)
- Sub-agent usage patterns
- Tool call frequency

---

## 🔍 Example Analysis Output

### Performance Section
```
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

### Error Analysis
```
🐛 ERROR ANALYSIS

❌ Total failed queries: 15

📊 Error Types:
  contains_syntax: 8
  datetime_functions: 4
  cypher_syntax: 2
  missing_properties: 1

🔍 Sample Failed Queries:
  Query: MATCH (m:Meeting {title: CONTAINS 'UNEA'})...
  Error: Invalid input 'CONTAINS': expected an expression...
```

### Tool Performance
```
🔧 TOOL PERFORMANCE

  execute_cypher_query:
    Calls: 58
    Success rate: 74.1%
    Avg duration: 245ms

  get_database_schema:
    Calls: 12
    Success rate: 100.0%
    Avg duration: 123ms
```

---

## 💡 How to Use This for Improvements

### 1. Identify Patterns

Run analysis after using the system:
```bash
python scripts/analyze_agent_logs.py
```

Look for:
- Common error types
- Low success rates
- High retry counts
- Slow queries

### 2. Make Targeted Improvements

**If you see many "contains_syntax" errors:**
- Add more examples to query sub-agent prompt
- Improve error hints

**If average retries > 1.0:**
- Review failing queries
- Update prompt with common patterns
- Add more specific error hints

**If query duration > 15s:**
- Check database performance
- Look for inefficient queries
- Consider caching

### 3. Track Progress

After improvements:
1. Clear or archive old logs
2. Run new queries
3. Compare new analysis results
4. Iterate

---

## 📁 Log Files

### `agent_monitoring.log`
Structured JSON logs:
```json
{"event": "session_start", "session_id": "...", "data": {...}}
{"event": "tool_call", "session_id": "...", "data": {...}}
{"event": "query_attempt", "session_id": "...", "data": {...}}
{"event": "session_end", "session_id": "...", "data": {...}}
```

### `unified_agent.log`
Human-readable application logs:
```
2024-10-30 08:00:00,123 - INFO - 🔵 Starting query session 1730270400.123
2024-10-30 08:00:01,234 - INFO - ✅ Query succeeded: 5 results in 0.45s
```

---

## 🛠️ Advanced Usage

### Watch Logs in Real-Time

**Linux/Mac:**
```bash
tail -f agent_monitoring.log | jq .
```

**Windows PowerShell:**
```powershell
Get-Content agent_monitoring.log -Wait -Tail 10
```

### Custom Analysis

```python
import json

with open('agent_monitoring.log') as f:
    sessions = []
    for line in f:
        event = json.loads(line)
        if event['event'] == 'session_end':
            sessions.append(event['data'])

# Your custom analysis
avg_duration = sum(s['duration_seconds'] for s in sessions) / len(sessions)
print(f"Average: {avg_duration:.2f}s")
```

### Archive Old Logs

```bash
# Archive and start fresh
mv agent_monitoring.log archive/agent_monitoring_$(date +%Y%m%d).log
touch agent_monitoring.log
```

---

## 🎯 Best Practices

### Daily
- ✅ Monitor console logs for errors
- ✅ Check for new error patterns

### Weekly
- ✅ Run full analysis report
- ✅ Review metrics trends
- ✅ Archive old logs

### Monthly
- ✅ Compare month-over-month metrics
- ✅ Identify improvement opportunities
- ✅ Update prompts based on patterns

---

## 📚 Documentation

Full documentation available at:
- **Complete Guide**: `docs/AGENT_MONITORING_GUIDE.md`
- **Log Structure**: See guide for JSON schemas
- **Analysis Examples**: See guide for use cases

---

## ✅ Benefits

### For Debugging
- See exactly what happened in failed queries
- Track retry attempts and what changed
- Identify root causes quickly

### For Optimization
- Find slow queries
- Identify inefficient patterns
- Track improvement over time

### For Reliability
- Monitor success rates
- Track error patterns
- Measure retry effectiveness

### For Understanding
- See how users interact
- Understand common questions
- Identify usage patterns

---

## 🚀 Next Steps

1. **Run some queries** to generate logs
2. **Analyze the logs**: `python scripts/analyze_agent_logs.py`
3. **Review the report** and identify patterns
4. **Make improvements** based on findings
5. **Track progress** over time

---

**Status**: ✅ Fully integrated and ready to use!  
**Version**: 1.0.0  
**Created**: October 30, 2024

---

Happy monitoring! 📊✨

