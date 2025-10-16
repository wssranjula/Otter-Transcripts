# Google Service Account Setup (Production Alternative)

## Service Account vs OAuth - Which Should You Use?

### OAuth "Desktop Application" (Current Setup) ✅ Recommended for Now
**Best for:** Personal use, development, small teams

**Pros:**
- ✅ Easy to set up
- ✅ Works with personal Google accounts
- ✅ Access to all folders in your Drive
- ✅ Already configured and working

**Cons:**
- ❌ Requires manual browser authentication (once)
- ❌ Tied to a specific Google user

---

### Service Account (Production Alternative)
**Best for:** Production deployments, automation, enterprise

**Pros:**
- ✅ No manual authentication needed
- ✅ Fully automated setup (no browser)
- ✅ Not tied to a personal account
- ✅ More secure (no user credentials)
- ✅ Better for CI/CD and automation

**Cons:**
- ❌ Requires sharing Drive folder with service account email
- ❌ Slightly more complex initial setup
- ❌ Requires modifying code

---

## Recommendation

**For your Infomaniak deployment:**

**Stick with OAuth "Desktop Application"** because:
1. ✅ It's already set up and working
2. ✅ One-time browser auth is acceptable
3. ✅ Simpler for initial deployment
4. ✅ No code changes needed

**Consider Service Account later if:**
- You need fully automated deployments (CI/CD)
- Multiple developers manage the system
- You want to decouple from personal Google account
- Company security policies require it

---

## How Service Accounts Work

### Traditional OAuth Flow:
```
Server → Browser → User Login → Google → Token → Server
        (manual)
```

### Service Account Flow:
```
Server → JSON Key File → Google → Token → Server
        (automatic)
```

**Key difference:** No browser or user interaction needed!

---

## Setup Steps (If You Want Service Account)

### Step 1: Create Service Account (5 minutes)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to **IAM & Admin** > **Service Accounts**
3. Click **Create Service Account**

**Configuration:**
- **Name:** `gdrive-rag-pipeline`
- **Description:** `Service account for RAG pipeline Google Drive access`

4. Click **Create and Continue**
5. Skip role assignment
6. Click **Done**

### Step 2: Create JSON Key

1. Click on your new service account
2. Go to **Keys** tab
3. Click **Add Key** > **Create new key**
4. Select **JSON** format
5. Click **Create**

**Downloaded file example:**
```json
{
  "type": "service_account",
  "project_id": "your-project-123",
  "private_key_id": "abc123...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...",
  "client_email": "gdrive-rag-pipeline@your-project.iam.gserviceaccount.com",
  "client_id": "123456789",
  ...
}
```

**Save as:** `config/service_account.json`

**Update .gitignore** (add if not present):
```
config/service_account.json
```

### Step 3: Enable Google Drive API

1. In Google Cloud Console: **APIs & Services** > **Library**
2. Search **Google Drive API**
3. Click **Enable**

### Step 4: Share Drive Folder

**Critical Step:** Service accounts can't see your files unless you share!

1. Open **Google Drive**
2. Find **"RAG Documents"** folder
3. Right-click > **Share**
4. Add service account email:
   ```
   gdrive-rag-pipeline@your-project.iam.gserviceaccount.com
   ```
   (Get email from JSON file: `client_email` field)
5. Set permission: **Viewer** (read-only)
6. **Uncheck** "Notify people"
7. Click **Share**

---

## Code Changes Needed

### Option 1: Create New Launcher (Easiest)

Create `run_gdrive_service_account.py`:

```python
#!/usr/bin/env python3
"""
Google Drive RAG Pipeline Launcher (Service Account Mode)
"""
import sys
from src.gdrive.google_drive_monitor import GoogleDriveMonitor

def main():
    # Use service account instead of OAuth
    monitor = GoogleDriveMonitor(
        service_account_file='config/service_account.json',
        state_file='config/gdrive_state.json'
    )

    if not monitor.authenticate():
        print("[ERROR] Authentication failed!")
        sys.exit(1)

    # Rest same as run_gdrive.py
    ...
```

### Option 2: Modify Existing Code

**Update `src/gdrive/google_drive_monitor.py`:**

Add service account support to `authenticate()` method:

```python
from google.oauth2 import service_account

def authenticate(self) -> bool:
    """Authenticate with Google Drive (OAuth or Service Account)."""
    try:
        # Check for service account file first
        if hasattr(self, 'service_account_file') and self.service_account_file:
            if os.path.exists(self.service_account_file):
                print(f"[INFO] Using service account authentication...")
                self.creds = service_account.Credentials.from_service_account_file(
                    self.service_account_file,
                    scopes=['https://www.googleapis.com/auth/drive.readonly']
                )
                self.service = build('drive', 'v3', credentials=self.creds)
                print("[INFO] Service account authentication successful!")
                return True

        # Fall back to OAuth flow (existing code)
        print(f"[INFO] Using OAuth authentication...")
        # ... existing OAuth code unchanged ...
```

---

## Deployment with Service Account

### On Infomaniak VPS:

**1. Upload service account key:**
```bash
# From local machine
scp config/service_account.json gdrive@YOUR_VPS_IP:~/Otter-Transcripts/config/
```

**2. Update config (if using Option 2):**
```json
{
  "google_drive": {
    "service_account_file": "config/service_account.json",
    "state_file": "config/gdrive_state.json",
    "folder_name": "RAG Documents",
    ...
  }
}
```

**3. Test:**
```bash
cd ~/Otter-Transcripts
source venv/bin/activate
python run_gdrive.py batch
```

**Expected output:**
```
[INFO] Using service account authentication...
[INFO] Service account authentication successful!
[INFO] Looking for folder: RAG Documents
[INFO] Found folder ID: 17ks1yga...
```

**No browser authentication needed!** ✅

---

## Security Comparison

### OAuth Token (`token.pickle`):
- Contains user's access/refresh tokens
- Tied to specific user account
- Revocable from Google Account settings
- **Security:** Medium (user credentials)

### Service Account Key (`service_account.json`):
- Contains private key for service account
- Not tied to any user
- Revocable from Google Cloud Console
- **Security:** High (machine credentials, no user access)

**Both must be kept secret!** Already in `.gitignore`.

---

## Troubleshooting Service Account

### Issue 1: "Insufficient Permission"
**Cause:** Folder not shared with service account

**Solution:** Share Drive folder with service account email

### Issue 2: "Service account does not exist"
**Cause:** Wrong project or service account deleted

**Solution:** Verify service account exists in Google Cloud Console

### Issue 3: "Invalid grant"
**Cause:** Service account key expired or revoked

**Solution:** Create new key from Google Cloud Console

### Issue 4: "File not found" errors
**Cause:** Service account can only see shared folders

**Solution:** Explicitly share folders with service account email

---

## When to Migrate to Service Account

**Migrate when:**
- ✅ You're comfortable with current setup and want to optimize
- ✅ OAuth token refresh becomes problematic
- ✅ You want fully automated deployments
- ✅ Multiple environments (dev/staging/prod)

**Don't migrate if:**
- ❌ Current OAuth setup works fine
- ❌ Not confident with the changes yet
- ❌ Don't want to modify working code

---

## Summary

### Current Setup (OAuth):
```
✅ Working perfectly
✅ Simple to deploy
⚠️ Requires one-time browser auth
```

### Service Account Alternative:
```
✅ Fully automated
✅ No browser needed
⚠️ Requires code changes
⚠️ Need to share folders explicitly
```

**My Recommendation:** **Stick with OAuth for now!** It's working, it's simple, and one-time browser authentication is acceptable. Consider service accounts later if you need more automation.

---

**Questions about service accounts?** Ask me when you're ready to make the switch!
