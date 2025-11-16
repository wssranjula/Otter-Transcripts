# Cloudflare Tunnel Setup - Complete Guide

## Overview

Set up HTTPS access to your Infomaniak VPS backend **without buying a domain**.

**Your VPS**: `83.228.211.124:8000`  
**Result**: `https://random-name.trycloudflare.com` with automatic HTTPS

---
 
## Step-by-Step Setup

### Step 1: SSH to Your VPS

```bash
ssh your-user@83.228.211.124
```

### Step 2: Install cloudflared

```bash
# Download cloudflared
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb

# Install it
sudo dpkg -i cloudflared-linux-amd64.deb

# Verify installation
cloudflared --version
```

**Expected output**: `cloudflared version 20XX.X.X`

### Step 3: Login to Cloudflare

```bash
cloudflared tunnel login
```

**What happens**:
1. A URL will appear in terminal
2. Copy and paste it into your browser
3. Login with your Cloudflare account (or create free account)
4. Select a domain (or choose "I don't have a domain")
5. Click "Authorize"

**After authorization**:
- Browser shows: "You may now close this window"
- Terminal shows: "You have successfully logged in"
- A cert file is saved at: `~/.cloudflared/cert.pem`

### Step 4: Create a Tunnel

```bash
# Create tunnel with a name
cloudflared tunnel create sybil-backend
```

**Expected output**:
```
Tunnel credentials written to /home/your-user/.cloudflared/UUID.json
Created tunnel sybil-backend with id UUID
```

**Important**: Note the UUID (long string like `abc123-def456-...`)

### Step 5: Create Configuration File

```bash
# Create config directory (if not exists)
mkdir -p ~/.cloudflared

# Create config file
nano ~/.cloudflared/config.yml
```

**Paste this configuration** (replace `YOUR-TUNNEL-UUID` with the UUID from Step 4):

```yaml
url: http://localhost:8000
tunnel: YOUR-TUNNEL-UUID
credentials-file: /home/YOUR-USERNAME/.cloudflared/YOUR-TUNNEL-UUID.json
```

**Example**:
```yaml
url: http://localhost:8000
tunnel: abc123-def456-ghi789
credentials-file: /home/ubuntu/.cloudflared/abc123-def456-ghi789.json
```

**Save and exit**: `Ctrl+X`, then `Y`, then `Enter`

### Step 6: Route DNS (Quick Route)

```bash
# Get your tunnel UUID (if you forgot it)
cloudflared tunnel list

# Create a quick route (generates random URL)
cloudflared tunnel route dns sybil-backend sybil-backend
```

**Or for a custom subdomain** (if you have a domain in Cloudflare):
```bash
cloudflared tunnel route dns sybil-backend api.yourdomain.com
```

### Step 7: Run the Tunnel (Test)

```bash
cloudflared tunnel run sybil-backend
```

**Expected output**:
```
2024-11-03 10:30:00 INF Starting tunnel tunnelID=abc123...
2024-11-03 10:30:01 INF Connection established connIndex=0
2024-11-03 10:30:02 INF Connection established connIndex=1
2024-11-03 10:30:03 INF Connection established connIndex=2
2024-11-03 10:30:04 INF Connection established connIndex=3
```

**Your tunnel URL will be shown**. Look for something like:
```
https://sybil-backend.trycloudflare.com
```

**Keep this terminal open and test in a new terminal/browser!**

### Step 8: Test the Tunnel

Open a **new terminal** on your local machine:

```bash
# Test the tunnel URL (replace with your actual URL)
curl https://sybil-backend.trycloudflare.com/health
```

**Expected**: JSON response from your backend!

**Or open in browser**: `https://sybil-backend.trycloudflare.com/health`

---

## Make It Permanent (Run as Service)

Once testing works, make it run automatically:

### Step 9: Install as System Service

```bash
# Stop the test tunnel first (Ctrl+C in the terminal running it)

# Install as a service
sudo cloudflared service install

# Copy your config to system location
sudo cp ~/.cloudflared/config.yml /etc/cloudflared/config.yml
sudo cp ~/.cloudflared/*.json /etc/cloudflared/

# Start the service
sudo systemctl start cloudflared
sudo systemctl enable cloudflared

# Check status
sudo systemctl status cloudflared
```

**Expected output**: `active (running)`

### Step 10: Find Your Public URL

```bash
# List your tunnels
cloudflared tunnel list

# Or check the service logs
sudo journalctl -u cloudflared -f
```

Look for your tunnel URL in the logs.

---

## Alternative: Quick Tunnel (No Account Needed!)

If you just want to test quickly without creating an account:

```bash
# This creates a temporary tunnel (changes every time)
cloudflared tunnel --url http://localhost:8000
```

**You'll get a URL like**: `https://random-words-abc.trycloudflare.com`

**Note**: This URL changes every time you restart. Good for testing, not for production.

---

## Update Your Admin Panel

### Step 11: Update Vercel Environment Variable

Go to Vercel Dashboard:

1. **Settings** → **Environment Variables**
2. Update `NEXT_PUBLIC_API_URL`
3. **Value**: `https://your-tunnel-url.trycloudflare.com`
4. Save

### Step 12: Update Backend CORS

SSH to your VPS:

```bash
cd ~/path/to/Otter\ Transcripts
nano config/config.json
```

Update the `admin` section:

```json
{
  "admin": {
    "allowed_origins": [
      "http://localhost:3000",
      "https://*.vercel.app",
      "https://sybil-admin-panel-h3evefkag-wssranjulas-projects.vercel.app",
      "https://*.trycloudflare.com"
    ]
  }
}
```

Restart backend:

```bash
sudo systemctl restart unified-agent
```

### Step 13: Redeploy Vercel

In Vercel dashboard:
- **Deployments** → **Redeploy**

### Step 14: Test Everything

1. Open your Vercel admin panel
2. Go to Whitelist page
3. **Expected**: ✅ Data loads, no errors!

---

## Troubleshooting

### Issue 1: "tunnel login" - Nothing happens after browser authorization

**This is normal!** After you click "Authorize" in browser:
1. Browser shows "You may now close this window"
2. Go back to your terminal
3. Terminal should show "Successfully logged in"
4. Certificate saved at `~/.cloudflared/cert.pem`

**Verify**:
```bash
ls -la ~/.cloudflared/
# Should show: cert.pem
```

### Issue 2: Can't find tunnel UUID

```bash
# List all your tunnels
cloudflared tunnel list

# Output shows:
# ID                                   NAME            CREATED
# abc123-def456-ghi789                 sybil-backend   2024-11-03...
```

Use the ID (first column) in your config.yml

### Issue 3: Tunnel won't start

**Check config file**:
```bash
cat ~/.cloudflared/config.yml
```

**Common mistakes**:
- Wrong indentation (YAML is space-sensitive!)
- Wrong tunnel UUID
- Wrong path to credentials file
- Username doesn't match in path

**Fix example**:
```bash
# Check your username
whoami

# Update config with correct username
nano ~/.cloudflared/config.yml
```

### Issue 4: Connection refused

**Check backend is running**:
```bash
curl http://localhost:8000/health
```

**If not running**:
```bash
sudo systemctl start unified-agent
sudo systemctl status unified-agent
```

### Issue 5: Can't access tunnel URL

**Check tunnel is running**:
```bash
sudo systemctl status cloudflared
# Should show: active (running)

# Check logs
sudo journalctl -u cloudflared -n 50
```

**Look for**:
- "Connection established" messages
- Your public URL

### Issue 6: 502 Bad Gateway

**Cause**: Tunnel is running but can't reach backend

**Fix**:
```bash
# Verify backend is on port 8000
sudo netstat -tlnp | grep 8000

# Check cloudflared config points to correct port
cat /etc/cloudflared/config.yml
# Should have: url: http://localhost:8000
```

---

## Check Tunnel Status

```bash
# Check service status
sudo systemctl status cloudflared

# View live logs
sudo journalctl -u cloudflared -f

# List all tunnels
cloudflared tunnel list

# Get tunnel info
cloudflared tunnel info sybil-backend

# Restart tunnel
sudo systemctl restart cloudflared
```

---

## Comparison: Cloudflare vs. Nginx

| Feature | Cloudflare Tunnel | Nginx + Let's Encrypt |
|---------|------------------|----------------------|
| **Domain needed** | ❌ No | ✅ Yes |
| **Cost** | Free | Free (domain: $0-15/year) |
| **Setup time** | 10 minutes | 30-60 minutes |
| **URL** | `*.trycloudflare.com` | Your domain |
| **SSL** | Automatic | Auto-renew (Let's Encrypt) |
| **DNS config** | None | A record needed |
| **Professional** | Good | Better |
| **Customizable** | Limited | Full control |

---

## When to Use Cloudflare Tunnel

✅ **Use Cloudflare Tunnel if**:
- Don't have a domain
- Want quick setup
- Testing/development
- Don't care about custom URL

✅ **Use Nginx + Domain if**:
- Want professional custom URL
- Have or can buy domain
- Production system
- Want full control

---

## Security Notes

### Cloudflare Tunnel Security

✅ **Secure**: Traffic encrypted end-to-end  
✅ **No open ports**: Tunnel creates outbound connection  
✅ **DDoS protection**: Cloudflare's network protects you  
✅ **No exposed IP**: Your VPS IP stays hidden  

### Best Practices

1. **Use named tunnel** (not quick tunnel) for production
2. **Keep cloudflared updated**:
   ```bash
   sudo apt update
   sudo apt upgrade cloudflared
   ```
3. **Monitor logs**:
   ```bash
   sudo journalctl -u cloudflared -f
   ```

---

## Get Custom URL (If You Have Domain)

If you have a domain in Cloudflare, you can use a custom subdomain:

### Step 1: Add Domain to Cloudflare

1. Go to Cloudflare dashboard
2. Add your domain
3. Update nameservers at your registrar

### Step 2: Create DNS Route

```bash
cloudflared tunnel route dns sybil-backend api.yourdomain.com
```

Now your tunnel will be accessible at: `https://api.yourdomain.com`

---

## Uninstall (If Needed)

```bash
# Stop and disable service
sudo systemctl stop cloudflared
sudo systemctl disable cloudflared

# Remove service
sudo cloudflared service uninstall

# Remove cloudflared
sudo apt remove cloudflared

# Remove config and credentials
rm -rf ~/.cloudflared
sudo rm -rf /etc/cloudflared
```

---

## Summary

### What You Did:

1. ✅ Installed cloudflared
2. ✅ Logged in to Cloudflare
3. ✅ Created named tunnel
4. ✅ Configured tunnel to point to localhost:8000
5. ✅ Started tunnel as service
6. ✅ Got HTTPS URL: `https://something.trycloudflare.com`

### What You Get:

✅ **Free HTTPS** without buying domain  
✅ **Automatic SSL** (no certificate management)  
✅ **Hidden VPS IP** (extra security)  
✅ **DDoS protection** (Cloudflare's network)  
✅ **No DNS configuration** needed  

---

## Quick Commands Reference

```bash
# Check if tunnel is running
sudo systemctl status cloudflared

# View tunnel logs
sudo journalctl -u cloudflared -f

# List tunnels
cloudflared tunnel list

# Restart tunnel
sudo systemctl restart cloudflared

# Test backend
curl http://localhost:8000/health

# Test tunnel
curl https://your-tunnel-url.trycloudflare.com/health
```

---

## Next Steps

1. ✅ Update Vercel env var with tunnel URL
2. ✅ Update backend CORS config
3. ✅ Redeploy Vercel app
4. ✅ Test admin panel
5. ✅ Monitor tunnel logs

---

**Total Setup Time**: 10-15 minutes  
**Cost**: $0  
**Result**: Production-ready HTTPS backend! 🚀

---

**Questions?** Check the logs:
```bash
sudo journalctl -u cloudflared -f
```



