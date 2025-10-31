#!/bin/bash
# Safe Start Unified Agent
# Stops any existing instances, cleans logs, and starts fresh

echo "=========================================================================="
echo "SAFE START UNIFIED AGENT"
echo "=========================================================================="
echo

# Step 1: Stop any existing instances
echo "[1/4] Checking for existing instances..."
EXISTING=$(ps aux | grep "run_unified_agent.py" | grep -v grep)
if [ ! -z "$EXISTING" ]; then
    echo "Found existing instances - stopping them..."
    ./scripts/stop_all_agents.sh
    sleep 2
else
    echo "✓ No existing instances found"
fi
echo

# Step 2: Clean logs (optional - comment out if you want to keep them)
echo "[2/4] Cleaning old logs..."
./scripts/clean_logs.sh
echo

# Step 3: Verify prerequisites
echo "[3/4] Verifying prerequisites..."

# Check config file
if [ ! -f "config/config.json" ]; then
    echo "❌ ERROR: config/config.json not found"
    echo "Please create it from config.template.json"
    exit 1
fi
echo "✓ Config file exists"

# Check if Neo4j is accessible
echo "Checking Neo4j connection..."
python3 -c "
import json, ssl, certifi
from neo4j import GraphDatabase

try:
    cfg = json.load(open('config/config.json'))
    ctx = ssl.create_default_context(cafile=certifi.where())
    drv = GraphDatabase.driver(cfg['neo4j']['uri'], auth=(cfg['neo4j']['user'], cfg['neo4j']['password']), ssl_context=ctx)
    with drv.session() as s:
        s.run('RETURN 1')
    drv.close()
    print('✓ Neo4j accessible')
except Exception as e:
    print(f'⚠️  Neo4j connection failed: {e}')
    print('Agent will start but may not work properly')
"
echo

# Step 4: Start the agent
echo "[4/4] Starting unified agent..."
echo
echo "=========================================================================="
echo "UNIFIED AGENT STARTING"
echo "=========================================================================="
echo

# Start in foreground (use nohup for background)
python3 run_unified_agent.py

# If you want to run in background, use this instead:
# nohup python3 run_unified_agent.py > unified_agent.out 2>&1 &
# echo "Agent started in background (PID: $!)"
# echo "View logs: tail -f unified_agent.log"
# echo "Stop with: ./scripts/stop_all_agents.sh"

