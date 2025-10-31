# WhatsApp Detection & Entity Extraction Fixes

## 🐛 Issues Fixed

Based on your VPS logs showing `whatsapp_chat_1.txt` failing to process correctly.

### Issue 1: WhatsApp Export Not Detected

**Problem:**
- File named `whatsapp_chat_1.txt` (clearly a WhatsApp export)
- But was processed as a regular document
- Detection only checked first 1000 characters
- Your file may have had a header or intro text before chat messages started

**Error Result:**
```
[STEP 1/5] Parsing document...     ← Should be WhatsApp-specific processing!
[STEP 3/5] Running RAG extraction...
[ERROR] Failed RAG extraction: 'name'
```

**Fix Applied:**
- ✅ Check first **5000 characters** instead of 1000
- ✅ Support **3 WhatsApp timestamp formats**:
  - `MM/DD/YYYY, HH:MM - ` (standard)
  - `[MM/DD/YYYY, HH:MM:SS]` (alternative)
  - `YYYY-MM-DD, HH:MM - ` (ISO format)
- ✅ Fallback detection: If filename has "whatsapp" and content has message structure (`-` or `:`), treat as WhatsApp

### Issue 2: Entity Extraction Crash

**Problem:**
- Mistral API sometimes returns entities without `name` field
- Code assumed `org['name']` always exists
- Caused `KeyError: 'name'` crash

**Error:**
```python
KeyError: 'name'
  File "parse_for_rag.py", line 196, in _process_entities
    entity_id = self._generate_id(org['name'])
                                  ~~~^^^^^^^^
```

**Fix Applied:**
- ✅ Check if `name` exists before accessing it
- ✅ Skip entities without names (they're invalid anyway)
- ✅ Applied to: Organizations, Countries, Topics
- ✅ No more crashes on malformed entity data

---

## 🔍 What Changed

### File 1: `src/gdrive/gdrive_rag_pipeline.py`

**Lines 198-234:** Better WhatsApp detection

```python
# OLD (Lines 198-212)
def _is_whatsapp_export(self, file_name: str, file_content: bytes) -> bool:
    file_name_lower = file_name.lower()
    if 'whatsapp' in file_name_lower or 'chat' in file_name_lower:
        try:
            text = file_content.decode('utf-8', errors='ignore')
            pattern = r'\d{1,2}/\d{1,2}/\d{4},\s\d{1,2}:\d{2}\s-\s'
            return bool(re.search(pattern, text[:1000]))  # ⚠️ Only 1000 chars
        except:
            return False
    return False

# NEW (Lines 198-234)
def _is_whatsapp_export(self, file_name: str, file_content: bytes) -> bool:
    file_name_lower = file_name.lower()
    if 'whatsapp' in file_name_lower or 'chat' in file_name_lower:
        try:
            text = file_content.decode('utf-8', errors='ignore')
            
            # Multiple WhatsApp timestamp patterns
            pattern = r'\d{1,2}/\d{1,2}/\d{4},\s\d{1,2}:\d{2}\s-\s'
            alt_pattern1 = r'\[\d{1,2}/\d{1,2}/\d{4},\s\d{1,2}:\d{2}:\d{2}\]'
            alt_pattern2 = r'\d{4}-\d{2}-\d{2},\s\d{1,2}:\d{2}\s-\s'
            
            search_text = text[:5000]  # ✅ Check 5000 chars
            
            if re.search(pattern, search_text):
                return True
            if re.search(alt_pattern1, search_text):
                return True
            if re.search(alt_pattern2, search_text):
                return True
            
            # ✅ Fallback: filename + message structure
            if 'whatsapp' in file_name_lower and (' - ' in text or ': ' in text):
                print(f"  [LOG] Filename suggests WhatsApp, treating as chat export")
                return True
                
            return False
        except Exception as e:
            print(f"  [WARN] Error detecting WhatsApp format: {e}")
            return False
    return False
```

### File 2: `src/core/parse_for_rag.py`

**Lines 194-209:** Safe organization processing

```python
# OLD
for org in entities_data.get('organizations', []):
    entity_id = self._generate_id(org['name'])  # ⚠️ Crash if no 'name'
    entities.append({...})

# NEW
for org in entities_data.get('organizations', []):
    # ✅ Skip if no name provided
    if not org.get('name'):
        continue
    
    entity_id = self._generate_id(org['name'])
    entities.append({...})
```

**Lines 211-226:** Safe country processing

```python
# OLD
for country in entities_data.get('countries', []):
    entity_id = self._generate_id(country['name'])  # ⚠️ Crash if no 'name'

# NEW
for country in entities_data.get('countries', []):
    # ✅ Skip if no name provided
    if not country.get('name'):
        continue
    
    entity_id = self._generate_id(country['name'])
```

**Lines 228-233:** Safe topic processing

```python
# OLD
for topic in entities_data.get('topics', []):
    entity_id = self._generate_id(topic['name'])  # ⚠️ Crash if no 'name'

# NEW
for topic in entities_data.get('topics', []):
    # ✅ Skip if no name provided
    if not topic.get('name'):
        continue
    
    entity_id = self._generate_id(topic['name'])
```

---

## 🧪 Testing on VPS

### Step 1: Pull Latest Code

```bash
ssh your-vps
cd /path/to/Otter\ Transcripts
git pull origin master
```

### Step 2: Reset State for Failed File

```bash
# Check which file failed
cat config/gdrive_state.json

# If whatsapp_chat_1.txt is in processed list, remove it
python3 -c "
import json
state = json.load(open('config/gdrive_state.json'))
# Find and remove the file ID (you'll need the actual ID)
# Or just reset everything:
state['processed_files'] = []
json.dump(state, open('config/gdrive_state.json', 'w'), indent=2)
print('State reset')
"
```

### Step 3: Reprocess

```bash
# Batch reprocess all files
python3 run_gdrive.py batch

# Or restart monitor
python3 run_gdrive.py monitor
```

### Step 4: Watch for Success

You should now see:

**Before:**
```
[STEP 1/5] Parsing document...          ← Wrong path!
[ERROR] Failed RAG extraction: 'name'   ← Crash!
```

**After:**
```
[INFO] Detected WhatsApp chat export    ← Correct detection!
[STEP 1/3] Parsing WhatsApp chat...     ← Correct path!
  [OK] Parsed WhatsApp chat:
    - Messages: 262
    - Chunks: 25
    - Participants: X
    - Entities: Y
[STEP 2/3] Loading to databases...
  [OK] Loaded to Neo4j
[SUCCESS] WHATSAPP CHAT PROCESSING COMPLETE
```

---

## 📊 Impact Assessment

### Files That May Have Failed

Look for these patterns in your logs:

```bash
# On VPS, check for previous failures
grep -B 5 "KeyError: 'name'" unified_agent.log

# Or check for WhatsApp files processed as documents
grep -B 10 "whatsapp.*[STEP 1/5]" unified_agent.log
```

Any files matching these patterns:
- Were processed as regular documents (wrong!)
- Crashed during entity extraction
- NOT properly loaded to Neo4j
- Need to be reprocessed with the fix

### Quick Count

```bash
# How many times did this error occur?
grep -c "KeyError: 'name'" unified_agent.log

# How many WhatsApp files were mis-processed?
grep -c "whatsapp.*STEP 1/5" unified_agent.log
```

---

## 🎯 What to Do Now

### Immediate Actions

1. **Pull the fixes:**
   ```bash
   git pull origin master
   ```

2. **Check state file:**
   ```bash
   python3 scripts/check_gdrive_state.py
   ```

3. **Reprocess failed files:**
   ```bash
   # If only a few failed, manually remove from state
   # Or reset everything:
   python3 scripts/reset_gdrive_state.py
   python3 run_gdrive.py batch
   ```

### Verification

After reprocessing, check Neo4j:

```cypher
// Count WhatsApp chats
MATCH (w:WhatsAppGroup)
RETURN count(w) as whatsapp_chats, 
       collect(w.group_name) as chat_names

// Check if whatsapp_chat_1 is there
MATCH (w:WhatsAppGroup)
WHERE w.group_name CONTAINS 'chat_1' OR w.id CONTAINS 'chat_1'
RETURN w.group_name, w.message_count, w.participant_count
```

---

## 🔍 Why This Happened

### Detection Issue

Your WhatsApp export likely had:
- A header or intro text
- Metadata at the top
- Chat messages started after line 20-30
- Pattern was outside the first 1000 characters

**Example structure that would fail:**
```
WhatsApp Chat Export
Generated: Oct 31, 2025
Group: Climate Team
Participants: 15

[... more metadata ...]

[After 1000+ characters]
10/15/2024, 14:30 - John: Hey everyone!
```

### Entity Extraction Issue

Mistral API occasionally returns malformed entities:
```json
{
  "organizations": [
    {"name": "Climate Hub", "type": "NGO"},     // ✅ Good
    {"type": "NGO"},                            // ❌ No name!
    {"name": "UNEP"}                            // ✅ Good
  ]
}
```

The code crashed on the second one. Now it skips invalid entries.

---

## ✅ Summary

**Fixed Issues:**
1. ✅ WhatsApp detection now checks 5000 chars (not 1000)
2. ✅ Supports 3 WhatsApp timestamp formats
3. ✅ Fallback detection for files with "whatsapp" in name
4. ✅ Entity extraction no longer crashes on missing names
5. ✅ Skips invalid entities instead of crashing

**What You Need to Do:**
1. Pull latest code (`git pull`)
2. Reprocess failed WhatsApp files
3. Verify in Neo4j

**Files Changed:**
- `src/gdrive/gdrive_rag_pipeline.py` (detection)
- `src/core/parse_for_rag.py` (entity safety)

---

**Your `whatsapp_chat_1.txt` should now process correctly!** 🎉

