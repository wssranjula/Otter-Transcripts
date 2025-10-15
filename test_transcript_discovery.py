"""Test script to verify transcript discovery"""
from pathlib import Path

TRANSCRIPT_DIR = Path(r"C:\Users\Admin\Desktop\Suresh\Otter Transcripts\transcripts")

print("Testing transcript file discovery...")
print(f"Looking in: {TRANSCRIPT_DIR}")
print()

transcript_files = list(TRANSCRIPT_DIR.rglob('*.txt'))
print(f"All .txt files found: {len(transcript_files)}")
for f in transcript_files:
    print(f"  - {f.relative_to(TRANSCRIPT_DIR)}")

print()

# Apply filters
transcript_files = [f for f in transcript_files
                   if not f.name.upper().startswith(('PARSED_', 'README', 'SETUP', 'NEO4J', 'QUICK'))
                   and f.name.lower() not in ('requirements.txt', 'license.txt', 'readme.txt')]

print(f"After filtering: {len(transcript_files)}")
for f in transcript_files:
    print(f"  - {f.relative_to(TRANSCRIPT_DIR)}")
