#!/bin/bash
# Clean/Rotate Log Files
# Backs up old logs and creates fresh files

echo "=========================================================================="
echo "CLEAN LOG FILES"
echo "=========================================================================="
echo

# Get timestamp for backup
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="logs_backup"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

echo "Backing up old logs to $BACKUP_DIR/"
echo

# Function to backup and clean a log file
backup_and_clean() {
    local LOG_FILE=$1
    
    if [ -f "$LOG_FILE" ]; then
        local SIZE=$(du -h "$LOG_FILE" | cut -f1)
        echo "  $LOG_FILE ($SIZE)"
        
        # Create backup
        cp "$LOG_FILE" "$BACKUP_DIR/$(basename $LOG_FILE).$TIMESTAMP"
        
        # Clear the file (keep it existing for file handles)
        > "$LOG_FILE"
        
        echo "    ✓ Backed up and cleared"
    else
        echo "  $LOG_FILE - not found (will be created on next run)"
    fi
    echo
}

# Clean all log files
echo "Processing log files:"
echo

backup_and_clean "unified_agent.log"
backup_and_clean "whatsapp_agent.log"
backup_and_clean "agent_monitoring.log"
backup_and_clean "gdrive_transcripts/processing.log"

echo "=========================================================================="
echo "✓ Log files cleaned"
echo "=========================================================================="
echo
echo "Backups saved in: $BACKUP_DIR/"
echo "Next run will start with fresh logs"
echo
echo "To view old logs:"
echo "  ls -lh $BACKUP_DIR/"
echo "  cat $BACKUP_DIR/unified_agent.log.$TIMESTAMP"
echo

