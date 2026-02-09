# 🚀 Deployment Guide - Todo App Phase 2

## Overview
This guide will help you deploy your full-stack todo application:
- **Frontend (Next.js)** → Vercel
- **Backend (FastAPI)** → Railway

---

## Part 1: Deploy Backend to Railway

### Step 1: Create Railway Account
1. Go to https://railway.app/
2. Sign up with your GitHub account
3. Authorize Railway to access your repositories

### Step 2: Deploy Backend
1. Click **"New Project"**
2. Select **"Deploy from GitHub repo"**
3. Choose: `1122anum/todo-app-phase2`
4. Railway will detect the Python project automatically

### Step 3: Configure Backend Environment Variables
In Railway project settings, add these environment variables:

```env
DATABASE_URL=sqlite:///./todo.db
JWT_SECRET=vjcQjUb5jR6S5o-dHvb6pQHu_J5FSWmjBL_yKogVZLs
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
ENVIRONMENT=production
DEBUG=False
```

### Step 4: Configure Root Directory
1. In Railway Settings → **Root Directory**: `backend`
2. In Railway Settings → **Start Command**: `uvicorn src.main:app --host 0.0.0.0 --port $PORT`

### Step 5: Get Backend URL
1. Railway will generate a public URL like: `https://your-app.railway.app`
2. **Copy this URL** - you'll need it for the frontend

---

## Part 2: Deploy Frontend to Vercel

### Step 1: Install Vercel CLI (Optional)
```bash
npm install -g vercel
```

### Step 2: Deploy via Vercel Dashboard
1. Go to https://vercel.com/
2. Sign up/Login with GitHub
3. Click **"Add New Project"**
4. Import: `1122anum/todo-app-phase2`
5. Configure project:
   - **Framework Preset**: Next.js
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `.next`

### Step 3: Configure Frontend Environment Variables
In Vercel project settings → Environment Variables, add:

```env
BACKEND_URL=https://your-backend.railway.app
NEXT_PUBLIC_API_URL=https://your-backend.railway.app
```

**Important:** Replace `https://your-backend.railway.app` with your actual Railway backend URL!

### Step 4: Deploy
1. Click **"Deploy"**
2. Vercel will build and deploy your frontend
3. You'll get a URL like: `https://your-app.vercel.app`

---

## Part 3: Update Backend CORS Settings

After deployment, update your backend to allow requests from your Vercel domain.

In `backend/src/main.py`, update CORS origins:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://your-app.vercel.app",  # Add your Vercel URL
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Commit and push this change - Railway will auto-redeploy.

---

## Part 4: Test Your Deployment

1. Visit your Vercel URL: `https://your-app.vercel.app`
2. Try signing up with a new account
3. Create some todos
4. Test signin/signout functionality

---

## Troubleshooting

### Backend Issues
- Check Railway logs: Railway Dashboard → Deployments → View Logs
- Verify environment variables are set correctly
- Ensure root directory is set to `backend`

### Frontend Issues
- Check Vercel logs: Vercel Dashboard → Deployments → View Function Logs
- Verify BACKEND_URL points to your Railway URL
- Check browser console for errors

### CORS Errors
- Make sure your Vercel URL is added to CORS origins in backend
- Redeploy backend after updating CORS settings

---

## Database Upgrade (Optional)

For production, consider upgrading from SQLite to PostgreSQL:

1. Create a free PostgreSQL database on Railway
2. Update `DATABASE_URL` in Railway environment variables
3. Backend will automatically create tables on startup

---

## 🎉 Your App is Live!

**Frontend:** https://your-app.vercel.app
**Backend:** https://your-backend.railway.app
**API Docs:** https://your-backend.railway.app/docs

Congratulations! Your full-stack todo app is now deployed and accessible worldwide! 🚀
