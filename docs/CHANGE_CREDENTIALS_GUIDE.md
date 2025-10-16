# How to Change Google Drive Credentials

## Overview

This guide covers how to switch to a different Google account or update your credentials.

---

## Use Cases

1. **Different Google Account**: Switch from one Google account to another
2. **New Credentials**: Update expired or revoked OAuth credentials
3. **Different Folder**: Access a folder owned by a different account
4. **Team Handover**: Transfer to a team member's account

---

## Quick Steps (Summary)

1. Stop the monitoring service
2. Delete old token file
3. Upload new credentials.json (if different account)
4. Re-authenticate
5. Update folder configuration
6. Restart service

---

## Detailed Instructions

### Step 1: Stop the Monitoring Service

**On your Infomaniak server (SSH):**

```bash
# Stop the service
sudo systemctl stop gdrive-monitor

# Verify it stopped
sudo systemctl status gdrive-monitor
```

**Expected output:** `Active: inactive (dead)`

---

### Step 2: Delete the Old Token

```bash
cd ~/Otter-Transcripts

# Delete the authentication token
rm config/token.pickle

# Verify it's deleted
ls -la config/token.pickle
```

**Expected output:** `No such file or directory`

---

### Step 3: Upload New Credentials (If Changing Account)

#### Option A: Same Google Account, Just Re-authenticate

**Skip this step!** Your existing `credentials.json` works fine. Jump to Step 4.

---

#### Option B: Different Google Account

You need new OAuth credentials from the new account's Google Cloud Console.

**3.1: Create New OAuth Credentials**

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. **Login with the NEW Google account**
3. Create a new project or select existing
4. Enable Google Drive API:
   - APIs & Services → Library
   - Search "Google Drive API"
   - Click Enable

5. Create OAuth credentials:
   - APIs & Services → Credentials
   - Click "Create Credentials" → "OAuth client ID"
   - Application type: **Desktop app**
   - Name: `Otter Transcripts`
   - Click Create

6. Download the JSON file
   - Click the download button (⬇)
   - Save as `credentials.json`

**3.2: Upload New Credentials to Server**

**On your Windows machine (PowerShell):**

```powershell
cd "C:\Users\Admin\Desktop\Suresh\Otter Transcripts"

# Backup old credentials (optional)
scp -i .\gdrive.txt ubuntu@83.228.211.124:~/Otter-Transcripts/config/credentials.json .\config\credentials_old.json

# Upload new credentials
scp -i .\gdrive.txt config\credentials.json ubuntu@83.228.211.124:~/Otter-Transcripts/config/
```

---

### Step 4: Re-authenticate with Google Drive

**On your Infomaniak server (SSH):**

```bash
cd ~/Otter-Transcripts
source venv/bin/activate

# Run authentication
python run_gdrive.py setup
```

**Follow the prompts:**
1. Copy the URL shown
2. Open in your browser
3. **Login with the NEW Google account** (important!)
4. Grant permissions
5. Copy the authorization code
6. Paste it back into the terminal

**Expected output:**
```
[OK] Successfully authenticated with Google Drive
[OK] Found folder 'RAG Documents': abc123xyz
[OK] Folder ID saved to config
```

---

### Step 5: Update Folder Configuration (If Different Folder)

If the new account has a different folder name:

```bash
nano ~/Otter-Transcripts/config/gdrive_config.json
```

**Update the folder name:**
```json
{
  "google_drive": {
    "folder_name": "New Folder Name",
    "folder_id": null
  }
}
```

**Save:** `Ctrl+X`, `Y`, `Enter`

**Re-run setup to find new folder:**
```bash
python run_gdrive.py setup
```

---

### Step 6: Test the New Configuration

```bash
# Test batch processing
python run_gdrive.py batch
```

**Expected output:**
```
[INFO] Found X files in folder
[INFO] Processing Y new files...
```

If successful, you're connected to the new account! ✅

---

### Step 7: Restart the Service

```bash
sudo systemctl start gdrive-monitor
sudo systemctl status gdrive-monitor
```

**Expected output:** `Active: active (running)`

**View logs:**
```bash
tail -f ~/gdrive-monitor.log
```

---

## Common Scenarios

### Scenario 1: Same Account, Just Refresh Token

**Reason:** Token expired or revoked

**Steps:**
```bash
sudo systemctl stop gdrive-monitor
cd ~/Otter-Transcripts
rm config/token.pickle
source venv/bin/activate
python run_gdrive.py setup
# Follow authentication prompts
sudo systemctl start gdrive-monitor
```

**Time:** ~2 minutes

---

### Scenario 2: Different Personal Account

**Reason:** Switching from your account to another team member's account

**Steps:**
1. Stop service
2. Delete token
3. Create new OAuth credentials in new account's Google Cloud Console
4. Upload new credentials.json
5. Re-authenticate (login with new account)
6. Update folder name if different
7. Restart service

**Time:** ~10 minutes

---

### Scenario 3: Team/Shared Account Setup

**Reason:** Multiple people need to access the same Google Drive

**Best Approach:** Use a shared Google account (e.g., `team@company.com`)

**Steps:**
1. Create Google Workspace or shared Gmail account
2. Create Google Drive folder in this account
3. Share folder with team members (for manual access)
4. Create OAuth credentials in this shared account
5. Use these credentials on the server
6. Everyone can add files to the shared folder

**Benefit:** No need to change credentials when team members change

---

### Scenario 4: Moving to Service Account (Advanced)

**Reason:** Want fully automated auth without browser interaction

**See:** `docs/SERVICE_ACCOUNT_GUIDE.md`

**Note:** Requires code changes but more suitable for production

---

## Troubleshooting

### Issue 1: "Folder not found" after changing accounts

**Cause:** New account doesn't have access to the folder

**Solution:**
- Create the folder in the new account, OR
- Share the existing folder with the new account, OR
- Update `folder_name` in config to a folder the new account owns

```bash
nano ~/Otter-Transcripts/config/gdrive_config.json
# Change folder_name
python run_gdrive.py setup
```

---

### Issue 2: "Invalid grant" error

**Cause:** Old credentials are still cached

**Solution:**
```bash
# Delete everything and start fresh
rm config/token.pickle
rm -rf ~/.config/gcloud  # If exists
python run_gdrive.py setup
```

---

### Issue 3: Service won't start after credential change

**Cause:** Permission or configuration error

**Solution:**
```bash
# Check logs
sudo journalctl -u gdrive-monitor -n 50

# Test manually
cd ~/Otter-Transcripts
source venv/bin/activate
python run_gdrive.py batch

# If manual works, restart service
sudo systemctl restart gdrive-monitor
```

---

### Issue 4: Authentication works but no files found

**Cause:** Wrong folder or folder ID

**Solution:**
```bash
# Reset folder ID
nano ~/Otter-Transcripts/config/gdrive_config.json
# Set folder_id to null

# Re-run setup to find folder
python run_gdrive.py setup
```

---

## Security Best Practices

### 1. Keep Credentials Secure

**Do:**
- ✅ Store `credentials.json` securely
- ✅ Never commit to git (already in .gitignore)
- ✅ Use separate credentials for different environments (dev/prod)

**Don't:**
- ❌ Share credentials publicly
- ❌ Use personal credentials for production
- ❌ Commit `token.pickle` or `credentials.json` to git

---

### 2. Use Principle of Least Privilege

**Read-only scope** (current setup):
```python
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
```

Only requests read access to Google Drive. ✅ Recommended

---

### 3. Revoke Access When Needed

**To revoke access:**
1. Go to [Google Account Permissions](https://myaccount.google.com/permissions)
2. Find "Otter Transcripts" (or your app name)
3. Click "Remove Access"

**On server:**
```bash
rm config/token.pickle
```

Re-authenticate when ready to restore access.

---

## Quick Reference Commands

```bash
# Stop service
sudo systemctl stop gdrive-monitor

# Delete token
rm ~/Otter-Transcripts/config/token.pickle

# Upload new credentials (from Windows PowerShell)
scp -i .\gdrive.txt config\credentials.json ubuntu@83.228.211.124:~/Otter-Transcripts/config/

# Re-authenticate (on server)
cd ~/Otter-Transcripts
source venv/bin/activate
python run_gdrive.py setup

# Test
python run_gdrive.py batch

# Restart service
sudo systemctl start gdrive-monitor

# Check status
sudo systemctl status gdrive-monitor
tail -f ~/gdrive-monitor.log
```

---

## Example: Full Credential Change Process

**Scenario:** Switching from `john@company.com` to `team@company.com`

**Windows PowerShell:**
```powershell
cd "C:\Users\Admin\Desktop\Suresh\Otter Transcripts"

# 1. Download new credentials from Google Cloud Console (team account)
# 2. Save as config\credentials.json

# 3. Upload to server
scp -i .\gdrive.txt config\credentials.json ubuntu@83.228.211.124:~/Otter-Transcripts/config/
```

**Server (SSH):**
```bash
# 1. Stop service
sudo systemctl stop gdrive-monitor

# 2. Delete old token
rm ~/Otter-Transcripts/config/token.pickle

# 3. Re-authenticate
cd ~/Otter-Transcripts
source venv/bin/activate
python run_gdrive.py setup
# Copy URL, login with team@company.com, paste code

# 4. Test
python run_gdrive.py batch

# 5. Restart service
sudo systemctl start gdrive-monitor

# 6. Verify
sudo systemctl status gdrive-monitor
tail -f ~/gdrive-monitor.log
```

**Time:** 5-10 minutes

**Done!** ✅

---

## FAQ

### Q: Can I use the same credentials on multiple servers?

**A:** Yes! The same `credentials.json` can be used on multiple servers. Each server will have its own `token.pickle`.

---

### Q: Do I need to re-process all files after changing accounts?

**A:** No. The processed files state (`gdrive_state.json`) is separate. However, if you switch to a completely different folder, you may want to reset the state:

```bash
rm config/gdrive_state.json
python run_gdrive.py batch
```

---

### Q: What if I want to access folders from multiple Google accounts?

**A:** You have two options:

**Option 1:** Share folders
- Have all folders shared with one Google account
- Use that account's credentials

**Option 2:** Multiple instances
- Run separate instances with different credentials
- Use different config files and services

---

### Q: How do I know which account is currently authenticated?

**A:** Check the logs or test manually:

```bash
cd ~/Otter-Transcripts
source venv/bin/activate
python run_gdrive.py batch
```

The logs will show which folder it's accessing.

---

## Summary Checklist

**To change Google Drive credentials:**

- [ ] Stop the monitoring service
- [ ] Delete `config/token.pickle`
- [ ] Upload new `credentials.json` (if different account)
- [ ] Run `python run_gdrive.py setup`
- [ ] Authenticate in browser (use new account)
- [ ] Update `folder_name` in config (if needed)
- [ ] Test with `python run_gdrive.py batch`
- [ ] Restart service
- [ ] Verify logs

**Estimated time:** 5-10 minutes

---

**Need help?** Check the troubleshooting section or review the main documentation:
- `INFOMANIAK_CHECKLIST.md` - Full deployment guide
- `docs/GOOGLE_OAUTH_SETUP.md` - OAuth authentication details
- `docs/SERVICE_ACCOUNT_GUIDE.md` - Alternative authentication method

---

**Last updated:** October 2025
