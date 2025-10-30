# Emoji Encoding Fix for Windows

## Issue
Windows console uses `cp1252` encoding by default, which doesn't support emoji characters. This caused `UnicodeEncodeError` when logging with emojis like 🔵, ✅, ❌.

## Solution

### 1. Fixed Logging Emojis (`src/agents/sybil_subagents.py`)
Added automatic emoji detection:

```python
# Check if console supports UTF-8 (for emoji display)
USE_EMOJI = sys.stdout.encoding and 'utf' in sys.stdout.encoding.lower()
```

Now the code uses:
- **Emojis** (🔵, ✅, ❌) on systems that support UTF-8
- **Text alternatives** ([START], [OK], [FAIL]) on systems that don't

### 2. Fixed Response Logging (`src/unified_agent.py`)
Added safe logging function to handle emojis in Sybil's responses:

```python
def safe_log_text(text: str, max_length: int = 100) -> str:
    """Safely truncate and encode text for logging, handling emojis on Windows"""
    truncated = text[:max_length] + "..." if len(text) > max_length else text
    # On Windows (cp1252), remove emojis for console display
    if sys.stdout.encoding and 'utf' not in sys.stdout.encoding.lower():
        safe_text = truncated.encode('ascii', errors='ignore').decode('ascii')
        return safe_text if safe_text.strip() else "[response contains emoji]"
    return truncated
```

This handles cases where Sybil's response includes emojis (like "Hello! 😊")

## Console Output

### Before (error on Windows):
```
UnicodeEncodeError: 'charmap' codec can't encode character '\U0001f535'
```

### After (works on all platforms):

**Windows (cp1252):**
```
[START] Starting query session 1730270400.123
[OK] Query succeeded: 5 results in 0.45s
[FAIL] Query failed in 0.12s: Cypher syntax error...
[OK] Query completed in 8.45s - 523 chars
```

**Linux/Mac (UTF-8):**
```
🔵 Starting query session 1730270400.123
✅ Query succeeded: 5 results in 0.45s
❌ Query failed in 0.12s: Cypher syntax error...
✅ Query completed in 8.45s - 523 chars
```

## Testing

Restart your agent:
```bash
python run_unified_agent.py
```

You should now see clean logs without any Unicode errors! 🎉

## Important Notes

1. **Emojis in API responses are preserved** - Users still receive emojis in the actual responses (like "Hello! 😊")
2. **Only logging is affected** - The fix only applies to console log output
3. **JSON logs are unaffected** - All monitoring logs in `agent_monitoring.log` work perfectly
4. **Cross-platform compatible** - Works on Windows, Linux, and Mac

## Technical Details

The fix detects console encoding using `sys.stdout.encoding`:
- **UTF-8 consoles** (Linux/Mac): Display emojis normally
- **cp1252 consoles** (Windows): Strip emojis from log messages only
- **ASCII mode**: Replace with text alternatives

