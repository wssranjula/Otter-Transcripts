#!/bin/bash
# Stop All Running Agent Processes
# Use this to kill any stuck or duplicate processes

echo "=========================================================================="
echo "STOP ALL AGENT PROCESSES"
echo "=========================================================================="
echo

# Find all Python processes running agent scripts
echo "Looking for running agent processes..."
echo

# Check for unified_agent
UNIFIED=$(ps aux | grep "run_unified_agent.py" | grep -v grep)
if [ ! -z "$UNIFIED" ]; then
    echo "Found unified_agent processes:"
    echo "$UNIFIED"
    echo
    PIDS=$(ps aux | grep "run_unified_agent.py" | grep -v grep | awk '{print $2}')
    echo "Killing PIDs: $PIDS"
    kill $PIDS 2>/dev/null
    sleep 2
    # Force kill if still running
    kill -9 $PIDS 2>/dev/null
    echo "✓ Stopped unified_agent"
else
    echo "No unified_agent processes found"
fi
echo

# Check for gdrive monitor
GDRIVE=$(ps aux | grep "run_gdrive.py" | grep -v grep)
if [ ! -z "$GDRIVE" ]; then
    echo "Found gdrive_monitor processes:"
    echo "$GDRIVE"
    echo
    PIDS=$(ps aux | grep "run_gdrive.py" | grep -v grep | awk '{print $2}')
    echo "Killing PIDs: $PIDS"
    kill $PIDS 2>/dev/null
    sleep 2
    kill -9 $PIDS 2>/dev/null
    echo "✓ Stopped gdrive_monitor"
else
    echo "No gdrive_monitor processes found"
fi
echo

# Check for whatsapp agent
WHATSAPP=$(ps aux | grep "run_whatsapp_agent.py" | grep -v grep)
if [ ! -z "$WHATSAPP" ]; then
    echo "Found whatsapp_agent processes:"
    echo "$WHATSAPP"
    echo
    PIDS=$(ps aux | grep "run_whatsapp_agent.py" | grep -v grep | awk '{print $2}')
    echo "Killing PIDs: $PIDS"
    kill $PIDS 2>/dev/null
    sleep 2
    kill -9 $PIDS 2>/dev/null
    echo "✓ Stopped whatsapp_agent"
else
    echo "No whatsapp_agent processes found"
fi
echo

# Check for uvicorn
UVICORN=$(ps aux | grep "uvicorn" | grep -v grep)
if [ ! -z "$UVICORN" ]; then
    echo "Found uvicorn processes:"
    echo "$UVICORN"
    echo
    PIDS=$(ps aux | grep "uvicorn" | grep -v grep | awk '{print $2}')
    echo "Killing PIDs: $PIDS"
    kill $PIDS 2>/dev/null
    sleep 2
    kill -9 $PIDS 2>/dev/null
    echo "✓ Stopped uvicorn"
else
    echo "No uvicorn processes found"
fi
echo

echo "=========================================================================="
echo "✓ All agent processes stopped"
echo "=========================================================================="
echo
echo "Verify with: ps aux | grep -E 'run_unified|run_gdrive|run_whatsapp|uvicorn'"
echo

