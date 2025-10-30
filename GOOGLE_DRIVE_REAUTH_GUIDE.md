# Quick Guide: Re-authenticate Google Drive on VPS

## Problem
Your Google Drive token has expired on the VPS. Error: `Token has been expired or revoked`

## Solution (5 minutes)

### Option 1: Authenticate on VPS (Copy URL Method) ⭐ RECOMMENDED

**On the VPS, run:**

```bash
cd ~/Otter-Transcripts
source venv/bin/activate

# Delete expired token
rm config/token.pickle

# Start authentication
python run_gdrive.py setup
```

**You'll see output like:**

```
[INFO] Starting Google Drive authentication...
Please visit this URL to authorize this application:
https://accounts.google.com/o/oauth2/auth?client_id=YOUR_CLIENT_ID&...

[INFO] Waiting for authorization...
```

**Steps:**

1. **Copy the entire URL** from the terminal (select and copy the long https:// link)
2. **Paste it in your browser** (on your Windows machine)
3. **Login to Google** (use the account that has access to the Drive folder)
4. **Click "Allow"** when Google asks for permissions
5. **Wait for success message** in browser: "The authentication flow has completed"
6. **Check VPS terminal** - should show: `[INFO] Authentication successful!`

**Verify it worked:**

```bash
# Check token was created
ls -la config/token.pickle

# Test Drive access
python run_gdrive.py batch
```

✅ **Done!** Token is now refreshed and will auto-renew.

---

### Option 2: Authenticate Locally Then Upload (Easier but requires SCP)

**On your LOCAL Windows machine:**

```bash
cd "C:\Users\Admin\Desktop\Suresh\Otter Transcripts"

# Delete old token
del config\token.pickle

# Activate venv
venv\Scripts\activate

# Authenticate (browser will open automatically)
python run_gdrive.py setup
```

Browser opens → Login → Grant permissions → Token created locally

**Upload token to VPS:**

```bash
scp config/token.pickle ubuntu@83.228.211.124:~/Otter-Transcripts/config/
```

**On VPS, verify:**

```bash
ls -la config/token.pickle
python run_gdrive.py batch
```

✅ **Done!**

---

## Common Issues

### "Folder not found"
Check folder name in `config/config.json`:
```json
"google_drive": {
  "folder_name": "RAG Documents"  // Must match your Drive folder exactly
}
```

### "Credentials file not found"
Make sure `config/credentials.json` exists on VPS:
```bash
ls -la config/credentials.json
```

If missing, upload from local:
```bash
scp config/credentials.json ubuntu@83.228.211.124:~/Otter-Transcripts/config/
```

### "redirect_uri_mismatch"
Your OAuth credentials might be set as "Web application" instead of "Desktop application".

**Fix:** Create new OAuth credentials in Google Cloud Console as "Desktop application"

---

## What Files You Need

### On VPS:

1. ✅ `config/credentials.json` - OAuth client (download from Google Cloud Console)
2. ✅ `config/token.pickle` - Access token (created during auth)
3. ✅ `config/config.json` - Must have `google_drive` section

### Check all files exist:

```bash
ls -la config/credentials.json config/token.pickle config/config.json
```

---

## Enable Google Drive After Authentication

**On VPS, edit config:**

```bash
nano config/config.json
```

Find `"gdrive_monitor"` section and set:

```json
"gdrive_monitor": {
  "enabled": true,
  "auto_start": true,
  ...
}
```

Save and restart the agent:

```bash
python run_unified_agent.py
```

---

## Testing

**Test Drive connection:**

```bash
cd ~/Otter-Transcripts
source venv/bin/activate
python run_gdrive.py batch
```

**Expected output:**

```
[INFO] Authentication successful!
[INFO] Looking for folder: RAG Documents
[INFO] Found folder ID: 17ks1yga...
[INFO] Found 5 files in folder
[INFO] Processing 3 new files...
```

✅ **All good!**

---

## Token Lifecycle

- **Access Token**: Valid for 1 hour, auto-refreshes
- **Refresh Token**: Valid indefinitely (until revoked)
- **token.pickle**: Stores both tokens

**You only need to authenticate once.** After that, tokens auto-refresh forever!

---

## Next Steps

1. Re-authenticate using Option 1 or 2 above
2. Verify token works: `python run_gdrive.py batch`
3. Re-enable Google Drive in config (if disabled)
4. Restart unified agent: `python run_unified_agent.py`

**Need help?** Check the full guide: `docs/GOOGLE_OAUTH_SETUP.md`

