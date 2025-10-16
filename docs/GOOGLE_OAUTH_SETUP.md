# Google OAuth Setup for Server Deployment

## Understanding OAuth for "Desktop Application"

### Why "Desktop Application" is Correct ✅

When you created your Google OAuth credentials, you selected **"Desktop application"**. This is the **correct choice** for:
- Python scripts
- Command-line tools
- Background services
- VPS/server deployments
- Any application without a public web server URL

**Don't worry!** Even though it says "Desktop," it works perfectly on remote servers.

---

## How OAuth Works in Your Setup

### First Time (One-Time Manual Setup)

```
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│   Server     │──1──▶ │ Your Browser │──2──▶ │   Google     │
│ (generates   │       │  (you login  │       │   (grants    │
│  auth URL)   │       │   & approve) │       │   access)    │
└──────────────┘       └──────────────┘       └──────────────┘
       ▲                                              │
       │                                              │
       └──────────────3─ token.pickle saved ─────────┘
```

### After First Time (Automatic Forever)

```
┌──────────────┐                    ┌──────────────┐
│   Server     │───────────────────▶│   Google     │
│ (uses stored │   Auto-refresh     │   (grants    │
│ token.pickle)│   access tokens    │   access)    │
└──────────────┘                    └──────────────┘
```

---

## Step-by-Step: First-Time Authentication on Server

### Method 1: Auth on Server (Copy URL to Browser)

**On the VPS:**
```bash
cd ~/Otter-Transcripts
source venv/bin/activate
python run_gdrive.py setup
```

**You'll see:**
```
[INFO] Starting Google Drive authentication...
[INFO] No existing token found. Starting OAuth flow...

Please visit this URL to authorize this application:
https://accounts.google.com/o/oauth2/auth?client_id=YOUR_CLIENT_ID&redirect_uri=...

[INFO] Waiting for authorization...
```

**Steps:**
1. **Copy the entire URL** (select text in terminal, right-click copy)
2. **Paste in your local browser** (on your Windows machine)
3. **Login to Google** (the account that has access to the Drive folder)
4. **Click "Allow"** when prompted
5. **See success message** in the browser
6. **Check terminal** - should show: `[INFO] Authentication successful!`
7. **Verify token created**: `ls -la config/token.pickle`

**Done!** ✅ The server now has permanent access (until you revoke it).

---

### Method 2: Auth Locally Then Upload (Easier)

**On your LOCAL machine (Windows):**
```bash
cd "C:\Users\Admin\Desktop\Suresh\Otter Transcripts"
python run_gdrive.py setup
# Browser opens automatically
# Login and grant permissions
# token.pickle is created locally
```

**Upload to server:**
```bash
scp config/token.pickle gdrive@YOUR_VPS_IP:~/Otter-Transcripts/config/
```

**On the VPS:**
```bash
cd ~/Otter-Transcripts
ls -la config/token.pickle  # Verify it's there
python run_gdrive.py batch   # Test it works
```

**Done!** ✅ Server can now access Google Drive.

---

## What Gets Created

### credentials.json (You create this manually)
- Downloaded from Google Cloud Console
- Contains your OAuth client ID and secret
- **Never changes**
- Safe to upload to server (it's not a secret by itself)

**Location:** `config/credentials.json`

### token.pickle (Created during OAuth flow)
- Contains your access token and refresh token
- **This is the actual secret** that grants access
- Gets auto-refreshed when expired
- **Never commit to git!** (already in .gitignore)

**Location:** `config/token.pickle`

### gdrive_state.json (Created automatically)
- Tracks which files have been processed
- Prevents reprocessing same files
- Safe to delete (will reprocess everything)

**Location:** `config/gdrive_state.json`

---

## Security Notes

### ✅ Safe to Commit to Git:
- `config/credentials.json` (your project's OAuth client ID)
- `config/gdrive_config.json.template` (template with examples)

### ❌ NEVER Commit to Git:
- `config/token.pickle` (actual access token) ← **Already in .gitignore**
- `config/gdrive_config.json` (contains API keys) ← **Already in .gitignore**
- `config/gdrive_state.json` (tracks processed files) ← **Already in .gitignore**

---

## Token Lifecycle

### Access Token (Short-lived)
- Valid for **1 hour**
- Used for API requests
- Auto-refreshed by the library

### Refresh Token (Long-lived)
- Stored in `token.pickle`
- Used to get new access tokens
- Valid until you revoke access

### When Token Refresh Fails:
```bash
# Delete token and re-authenticate
rm config/token.pickle
python run_gdrive.py setup
```

---

## Common Issues & Solutions

### Issue 1: "The browser opened but nothing happened"
**Solution:** Copy the URL manually and paste in browser
```bash
python run_gdrive.py setup
# Copy the URL shown
# Paste in browser manually
```

### Issue 2: "redirect_uri_mismatch"
**Cause:** OAuth credentials configured as "Web application" instead of "Desktop application"

**Solution:** Create new OAuth credentials as "Desktop application" in Google Cloud Console

### Issue 3: "Token has been expired or revoked"
**Solution:** Re-authenticate
```bash
rm config/token.pickle
python run_gdrive.py setup
```

### Issue 4: "Permission denied" when accessing Drive
**Cause:** Authenticated with wrong Google account

**Solution:** Re-authenticate with correct account
```bash
rm config/token.pickle
python run_gdrive.py setup
# Make sure to login with the account that owns the folder
```

---

## Testing Authentication

### Test 1: Check if token exists
```bash
ls -la config/token.pickle
# Should show file with size > 0
```

### Test 2: Test Google Drive connection
```bash
cd ~/Otter-Transcripts
source venv/bin/activate
python run_gdrive.py batch
```

**Expected output:**
```
[INFO] Loaded configuration from config/gdrive_config.json
[INFO] Authenticating with Google Drive...
[INFO] Authentication successful!
[INFO] Looking for folder: RAG Documents
[INFO] Found folder ID: 17ks1yga...
[INFO] Found 5 files in folder
[INFO] Processing 3 new files...
```

### Test 3: Manual authentication test
```python
# Test script
from src.gdrive.google_drive_monitor import GoogleDriveMonitor

monitor = GoogleDriveMonitor()
if monitor.authenticate():
    print("✅ Authentication successful!")
    folder_id = monitor.get_folder_id("RAG Documents")
    if folder_id:
        print(f"✅ Found folder: {folder_id}")
    else:
        print("❌ Folder not found")
else:
    print("❌ Authentication failed")
```

---

## FAQ

### Q: Do I need to re-authenticate every time the server restarts?
**A:** No! The `token.pickle` file stores the refresh token, which is used automatically.

### Q: How long does the token last?
**A:** The refresh token lasts indefinitely (until you revoke it). Access tokens are auto-refreshed every hour.

### Q: What if I change my Google password?
**A:** Your token remains valid. You only need to re-authenticate if you explicitly revoke access.

### Q: Can multiple servers use the same token?
**A:** Yes, but it's better to authenticate each server separately for security.

### Q: What permissions does the app request?
**A:** Read-only access to Google Drive files and metadata (defined in `google_drive_monitor.py`)

### Q: Can I use a service account instead?
**A:** Yes! Service accounts are better for production. Let me know if you want to set that up.

---

## Summary

✅ **"Desktop application" OAuth is perfect for your use case**

✅ **You only authenticate once manually**

✅ **After that, everything is automatic**

✅ **Token auto-refreshes forever**

✅ **No browser needed after initial setup**

---

**Ready to deploy?** Follow the steps in `INFOMANIAK_CHECKLIST.md` Phase 5!
