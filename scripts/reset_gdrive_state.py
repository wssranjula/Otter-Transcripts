#!/usr/bin/env python3
"""
Reset Google Drive Pipeline State
Clears the processed files list so everything will be reprocessed
"""

import json
import os
import sys
from datetime import datetime


def reset_state(state_file='config/gdrive_state.json', backup=True):
    """Reset the state file"""
    
    print("="*70)
    print("RESET GOOGLE DRIVE PIPELINE STATE")
    print("="*70)
    print()
    
    # Check if state file exists
    if not os.path.exists(state_file):
        print(f"ℹ️  State file doesn't exist: {state_file}")
        print("   Creating new empty state file...")
        state = {'processed_files': [], 'last_updated': ''}
    else:
        # Load current state
        with open(state_file, 'r') as f:
            state = json.load(f)
        
        processed_count = len(state.get('processed_files', []))
        last_updated = state.get('last_updated', 'Unknown')
        
        print(f"📊 Current state:")
        print(f"   Processed files: {processed_count}")
        print(f"   Last updated: {last_updated}")
        print()
        
        # Backup if requested
        if backup and processed_count > 0:
            backup_file = f"{state_file}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            with open(backup_file, 'w') as f:
                json.dump(state, f, indent=2)
            print(f"💾 Backup saved to: {backup_file}")
            print()
    
    # Confirm
    if len(state.get('processed_files', [])) > 0:
        print("⚠️  WARNING: This will mark all files as unprocessed!")
        print("   They will be reprocessed on the next batch or monitor run.")
        print()
        
        response = input("Continue? (yes/no): ").strip().lower()
        if response not in ['yes', 'y']:
            print("❌ Cancelled")
            return False
        print()
    
    # Reset state
    state['processed_files'] = []
    state['last_updated'] = datetime.now().isoformat()
    
    with open(state_file, 'w') as f:
        json.dump(state, f, indent=2)
    
    print("✅ State reset successfully!")
    print()
    print("Next steps:")
    print("  1. Run: python run_gdrive.py batch")
    print("     (Reprocess all existing files)")
    print()
    print("  OR")
    print()
    print("  2. Run: python run_gdrive.py monitor")
    print("     (Monitor will reprocess files as they're detected)")
    print()
    
    return True


def main():
    """Main execution"""
    
    # Check for --no-backup flag
    backup = '--no-backup' not in sys.argv
    
    reset_state(backup=backup)


if __name__ == "__main__":
    main()

