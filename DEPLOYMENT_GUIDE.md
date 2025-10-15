# Streamlit Chatbot - Deployment Guide

## 🚀 Deploying to Streamlit Community Cloud

### Prerequisites
- GitHub account
- Streamlit Community Cloud account (free at https://streamlit.io/cloud)

---

## Step 1: Prepare Your Repository

### 1.1 Create a GitHub Repository
```bash
# Initialize git if not already done
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit - Meeting Knowledge Chatbot"

# Create a new repository on GitHub and push
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git branch -M main
git push -u origin main
```

### 1.2 Verify .gitignore
Make sure `.streamlit/secrets.toml` is in your `.gitignore` file to prevent committing credentials!

✅ Already done - check `.gitignore`

---

## Step 2: Deploy on Streamlit Cloud

### 2.1 Go to Streamlit Cloud
1. Visit https://share.streamlit.io/
2. Sign in with GitHub
3. Click "New app"

### 2.2 Configure the App
- **Repository:** Select your GitHub repository
- **Branch:** main
- **Main file path:** `streamlit_chatbot.py`
- Click "Advanced settings" (optional):
  - Python version: 3.9+
  - Secrets: See Step 3 below

### 2.3 Add Secrets
In the "Secrets" section of Advanced settings, paste:

```toml
[neo4j]
uri = "bolt://220210fe.databases.neo4j.io:7687"
user = "neo4j"
password = "uefo7_cCO4KdvrpS3knrhJ39Pwn2KDrFD0NCH4SKHv8"

[mistral]
api_key = "xELPoQf6Msav4CZ7fPEAfcKnJTa4UOxn"
model = "mistral-small-latest"
```

**Important:** These secrets are stored securely by Streamlit and NOT visible in your repository!

### 2.4 Deploy
Click "Deploy" and wait 2-3 minutes for the app to build and start.

---

## Step 3: Test Your Deployed App

1. Once deployed, you'll get a URL like: `https://YOUR_USERNAME-YOUR_REPO.streamlit.app`
2. Visit the URL
3. Test with a sample question like "What were the key decisions?"
4. Verify chunks are displayed correctly

---

## Step 4: Update Secrets (If Needed)

### On Streamlit Cloud:
1. Go to your app dashboard
2. Click the "⚙️" (settings) icon
3. Go to "Secrets"
4. Edit and save

### Locally:
Edit `.streamlit/secrets.toml` (never commit this file!)

---

## 🔒 Security Best Practices

### ✅ DO:
- Use `.streamlit/secrets.toml` for local development
- Use Streamlit Cloud secrets for deployment
- Keep `.streamlit/secrets.toml` in `.gitignore`
- Rotate API keys periodically
- Use environment-specific credentials

### ❌ DON'T:
- Commit secrets to git
- Hardcode credentials in code
- Share secrets in public channels
- Use production credentials in development

---

## 📦 Dependencies

Make sure `requirements_streamlit.txt` includes all dependencies:

```
streamlit>=1.28.0
neo4j>=5.0.0
certifi
langchain-mistralai
langchain-core
```

---

## 🐛 Troubleshooting

### "Connection error"
- Check Neo4j credentials in secrets
- Verify Neo4j Aura instance is running
- Check firewall/network settings

### "Module not found"
- Add missing package to `requirements_streamlit.txt`
- Redeploy the app

### "Secrets not loading"
- Verify secrets format (TOML syntax)
- Check for typos in secret keys
- Restart the app after updating secrets

### App is slow
- Neo4j Aura free tier has limits
- Consider upgrading to paid tier
- Reduce chunk retrieval count (slider)

---

## 🎯 App URL Structure

After deployment, your app will be at:
```
https://[your-username]-[repo-name]-[random-id].streamlit.app
```

You can customize this in Streamlit Cloud settings.

---

## 🔄 Updating Your Deployed App

1. Make changes locally
2. Commit and push to GitHub:
   ```bash
   git add .
   git commit -m "Update chatbot features"
   git push
   ```
3. Streamlit Cloud auto-deploys on push!

---

## 💡 Tips

- **Share your app:** Send the URL to anyone (no login required for viewers)
- **Monitor usage:** Check Streamlit Cloud dashboard for analytics
- **Custom domain:** Available on paid plans
- **Password protection:** Add auth with `streamlit-authenticator` package

---

## 📚 Additional Resources

- Streamlit Docs: https://docs.streamlit.io/
- Streamlit Cloud: https://docs.streamlit.io/streamlit-community-cloud
- Neo4j Aura: https://neo4j.com/cloud/aura/
- Mistral AI: https://docs.mistral.ai/

---

## ✅ Deployment Checklist

- [ ] Repository pushed to GitHub
- [ ] `.streamlit/secrets.toml` in `.gitignore`
- [ ] `requirements_streamlit.txt` includes all dependencies
- [ ] Streamlit Cloud account created
- [ ] App deployed on Streamlit Cloud
- [ ] Secrets configured in Streamlit Cloud settings
- [ ] App tested with sample questions
- [ ] Chunks displaying correctly
- [ ] Share URL with team

---

**Your app is now live! 🎉**
