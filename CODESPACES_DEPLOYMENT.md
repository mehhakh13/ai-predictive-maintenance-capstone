# GitHub Codespaces Deployment Guide

This guide explains how to deploy and demo the AI Predictive Maintenance application using GitHub Codespaces for **free** (perfect for 1-2 day demos).

## 🚀 Quick Start (5 minutes)

### Step 1: Create a Codespace

1. Go to your GitHub repository: https://github.com/mehhakh13/ai-predictive-maintenance-capstone
2. Click the **"Code"** button (green button)
3. Click the **"Codespaces"** tab
4. Click **"Create codespace on main"** (or your branch name)

GitHub will create a cloud development environment and automatically:
- Install Python 3.10 and Node.js 20
- Install all Python dependencies from `requirements.txt`
- Install all frontend dependencies with `npm install`
- Forward ports 5173 (frontend) and 8000 (backend)

**Wait time:** ~2-3 minutes for initial setup

### Step 2: Start the Application

Once the Codespace is ready, open a terminal and run:

```bash
cd frontend
npm run dev
```

This will start both:
- **Frontend** (React + Vite) on port 5173
- **Backend** (FastAPI) on port 8000

### Step 3: Make Ports Public

**IMPORTANT:** By default, forwarded ports are private. To share your demo:

1. Click the **"Ports"** tab at the bottom of VS Code
2. Find port **5173** (Frontend)
   - Right-click → **"Port Visibility"** → **"Public"**
3. Find port **8000** (Backend)
   - Right-click → **"Port Visibility"** → **"Public"**

### Step 4: Access Your App

In the **Ports** tab, you'll see URLs like:

```
https://your-codespace-name-5173.app.github.dev  ← Frontend (share this!)
https://your-codespace-name-8000.app.github.dev  ← Backend API
```

**Share the frontend URL** with your demo audience!

## 📋 What URLs Look Like

Your Codespace will have auto-generated URLs:

```
Frontend: https://friendly-space-giggle-5173.app.github.dev
Backend:  https://friendly-space-giggle-8000.app.github.dev
```

- **Codespace name** is auto-generated (e.g., "friendly-space-giggle")
- **Port number** is appended to the URL
- **HTTPS** is automatic (free SSL certificate)
- **URLs stay the same** for the life of that Codespace

## 🔧 How It Works

### Automatic Environment Detection

The app automatically detects when it's running in Codespaces:

**Frontend** (`frontend/src/config.js`):
- Detects `*.app.github.dev` hostname
- Automatically uses Codespaces backend URL
- No manual configuration needed!

**Backend** (`backend/main.py`):
- Detects `CODESPACE_NAME` environment variable
- Auto-configures CORS to accept Codespaces frontend
- Supports regex pattern matching for any Codespaces URL

### Port Forwarding

Defined in `.devcontainer/devcontainer.json`:
```json
{
  "forwardPorts": [5173, 8000],
  "portsAttributes": {
    "5173": { "label": "Frontend (React)" },
    "8000": { "label": "Backend (FastAPI)" }
  }
}
```

## 💰 Free Tier Limits

GitHub Codespaces free tier includes:
- **60 hours/month** of usage (2-core machine)
- **15 GB/month** of storage
- Perfect for 1-2 day demos!

**For a 2-day demo:**
- Continuous runtime: ~48 hours
- Well within the 60-hour free limit ✅

## 🛠️ Troubleshooting

### Issue: "CORS error" in browser console

**Solution:** Make sure both ports are set to **Public** visibility.

```bash
# Check CORS origins in backend logs
# You should see: "🚀 Codespaces detected: your-codespace-name"
```

### Issue: Frontend can't connect to backend

**Solution:**
1. Check that port 8000 is running (Ports tab)
2. Verify port 8000 is **Public**
3. Check browser console for the API URL being used
4. Should be: `https://your-codespace-name-8000.app.github.dev`

### Issue: App starts slowly

**Solution:** Large dataset (~2.5GB) loads on backend startup.
- First startup: ~30-60 seconds
- Subsequent requests: Fast (data is cached in memory)

### Issue: Codespace times out

**Solution:** Codespaces auto-sleep after 30 minutes of inactivity.
- Just refresh the page to wake it up
- All your data persists

## 🎯 Best Practices for Demos

### 1. Pre-warm the Codespace
Start it 5 minutes before your demo to ensure everything loads.

### 2. Keep it Running
Keep a browser tab open to prevent auto-sleep during demos.

### 3. Test the URLs
Share the frontend URL with yourself first to verify it works.

### 4. Have a Backup
Keep localhost working too in case of network issues.

### 5. Monitor Usage
Check your GitHub Codespaces usage:
- Go to GitHub Settings → Billing → Codespaces
- Monitor hours used

## 🔐 Environment Variables

The app uses Supabase and Anthropic API keys stored in `.env` files.

**For Codespaces:**
1. Go to your repository Settings → Secrets → Codespaces
2. Add secrets:
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY`
   - `ANTHROPIC_API_KEY`

**Or:** Just use the existing `.env` files (already in the repo).

## 📊 What Gets Deployed

When you create a Codespace, it includes:
- ✅ All source code
- ✅ All data files (~2.5GB in `/data`)
- ✅ All ML models (XGBoost, SHAP)
- ✅ All dependencies (Python + Node.js)
- ✅ HTTPS endpoints with free SSL

## 🚫 What's NOT Included

- ❌ No database hosting (uses local CSV/Parquet files)
- ❌ No CDN or caching
- ❌ No load balancing (single instance)
- ❌ No persistent storage (Codespace is ephemeral)

Perfect for demos, NOT for production! 😊

## 🔄 Alternative: Local Development

If Codespaces doesn't work, run locally:

```bash
# Start everything
./start-dev.sh

# Or manually:
cd frontend
npm run dev
```

Then use ngrok or Cloudflare Tunnel to expose it:

```bash
# Install ngrok
npm install -g ngrok

# Tunnel frontend
ngrok http 5173
```

## 📞 Support

If you have issues:
1. Check the Codespaces logs in the terminal
2. Verify ports are Public in the Ports tab
3. Check browser console for errors
4. Restart the Codespace if needed

## 🎉 Success Checklist

Before your demo:
- [ ] Codespace created and running
- [ ] Port 5173 is **Public**
- [ ] Port 8000 is **Public**
- [ ] Frontend URL works in browser
- [ ] Backend API responds (visit `/api/summary`)
- [ ] No CORS errors in console
- [ ] Dashboard loads data successfully

**You're ready to demo!** 🚀
