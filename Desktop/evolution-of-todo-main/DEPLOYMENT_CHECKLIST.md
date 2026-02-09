# 🚀 Todo App Phase 2 - Deployment Checklist

## ✅ Pre-Deployment (COMPLETED)
- [x] Fixed React context errors
- [x] Fixed backend 503 errors
- [x] Fixed bcrypt compatibility
- [x] Created deployment configurations
- [x] Installed Vercel CLI
- [x] Pushed all code to GitHub
- [x] Created deployment guides

---

## 📦 Step 1: Deploy Backend to Railway (15 minutes)

### 1.1 Create Railway Project
- [ ] Go to https://railway.app/
- [ ] Click "Login" → Sign in with GitHub
- [ ] Click "New Project"
- [ ] Select "Deploy from GitHub repo"
- [ ] Choose: `1122anum/todo-app-phase2`
- [ ] Select branch: `001-full-stack-web-app`

### 1.2 Configure Backend Service
- [ ] Click on the deployed service
- [ ] Go to **Settings** tab
- [ ] Set **Root Directory**: `backend`
- [ ] Set **Start Command**: `uvicorn src.main:app --host 0.0.0.0 --port $PORT`

### 1.3 Add Environment Variables
Click **Variables** tab and add these:

```
DATABASE_URL=sqlite:///./todo.db
JWT_SECRET=vjcQjUb5jR6S5o-dHvb6pQHu_J5FSWmjBL_yKogVZLs
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
ENVIRONMENT=production
DEBUG=False
```

### 1.4 Generate Public Domain
- [ ] Go to **Settings** → **Networking**
- [ ] Click **Generate Domain**
- [ ] **COPY YOUR RAILWAY URL** (e.g., `https://todo-backend-production.up.railway.app`)
- [ ] Write it here: _______________________________________________

### 1.5 Verify Backend is Running
- [ ] Visit: `https://your-railway-url.railway.app/`
- [ ] You should see: `{"message":"Todo API - Phase II"}`
- [ ] Visit: `https://your-railway-url.railway.app/docs`
- [ ] You should see the API documentation

---

## 🌐 Step 2: Deploy Frontend to Vercel (10 minutes)

### Option A: Vercel Web Dashboard (Recommended)

#### 2.1 Create Vercel Project
- [ ] Go to https://vercel.com/new
- [ ] Click "Import Git Repository"
- [ ] Select: `1122anum/todo-app-phase2`
- [ ] Click "Import"

#### 2.2 Configure Project Settings
- [ ] **Framework Preset**: Next.js (auto-detected)
- [ ] **Root Directory**: `frontend`
- [ ] **Build Command**: `npm run build` (default)
- [ ] **Output Directory**: `.next` (default)
- [ ] **Install Command**: `npm install` (default)

#### 2.3 Add Environment Variables
Click "Environment Variables" and add:

**Variable 1:**
- Name: `BACKEND_URL`
- Value: [Your Railway URL from Step 1.4]

**Variable 2:**
- Name: `NEXT_PUBLIC_API_URL`
- Value: [Your Railway URL from Step 1.4]

#### 2.4 Deploy
- [ ] Click **"Deploy"**
- [ ] Wait for build to complete (2-3 minutes)
- [ ] **COPY YOUR VERCEL URL** (e.g., `https://todo-app-phase2.vercel.app`)
- [ ] Write it here: _______________________________________________

### Option B: Vercel CLI (Alternative)

```bash
cd frontend
vercel --prod
```

Follow the prompts:
- Set up and deploy? → **Y**
- Which scope? → Select your account
- Link to existing project? → **N**
- Project name? → **todo-app-phase2**
- Directory? → **./frontend**
- Override settings? → **N**

After deployment, add environment variables in Vercel dashboard.

---

## 🧪 Step 3: Test Your Deployment (5 minutes)

### 3.1 Test Backend
- [ ] Visit: `https://your-railway-url.railway.app/docs`
- [ ] Try the `/auth/signup` endpoint with test data
- [ ] Verify you get a success response

### 3.2 Test Frontend
- [ ] Visit: `https://your-vercel-url.vercel.app`
- [ ] Click "Get Started" or "Sign Up"
- [ ] Create a test account
- [ ] Sign in with the account
- [ ] Create a todo item
- [ ] Mark it as complete
- [ ] Delete it

### 3.3 Verify Integration
- [ ] Check browser console for errors (F12)
- [ ] Verify API calls are going to Railway backend
- [ ] Test sign out and sign in again

---

## 🎉 Step 4: Celebrate! Your App is Live!

### Your Live URLs:
- **Frontend**: https://your-vercel-url.vercel.app
- **Backend**: https://your-railway-url.railway.app
- **API Docs**: https://your-railway-url.railway.app/docs

### Share Your App:
- [ ] Update GitHub README with live URLs
- [ ] Share with friends/colleagues
- [ ] Add to your portfolio

---

## 🐛 Troubleshooting

### Backend Issues
**Problem**: Railway deployment fails
- Check logs: Railway Dashboard → Deployments → View Logs
- Verify root directory is set to `backend`
- Ensure all environment variables are set

**Problem**: Database errors
- SQLite is fine for testing
- For production, consider PostgreSQL on Railway

### Frontend Issues
**Problem**: 503 errors when signing up
- Verify BACKEND_URL is set correctly in Vercel
- Check Railway backend is running
- Verify Railway URL is accessible

**Problem**: CORS errors
- Backend already allows all origins
- If issues persist, check Railway logs

### General Issues
**Problem**: Can't access deployed sites
- Wait 2-3 minutes after deployment
- Clear browser cache
- Try incognito/private mode

---

## 📚 Additional Resources

- **Railway Docs**: https://docs.railway.app/
- **Vercel Docs**: https://vercel.com/docs
- **Deployment Guide**: See `DEPLOYMENT_GUIDE.md` in repo

---

## 🔄 Redeployment

### Update Backend:
1. Push changes to GitHub
2. Railway auto-deploys from `001-full-stack-web-app` branch

### Update Frontend:
1. Push changes to GitHub
2. Vercel auto-deploys from `001-full-stack-web-app` branch

---

**Need Help?** Check the logs:
- Railway: Dashboard → Deployments → Logs
- Vercel: Dashboard → Deployments → Function Logs

**Good luck! 🚀**
