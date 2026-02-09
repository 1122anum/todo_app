@echo off
echo ========================================
echo   Todo App Phase 2 - Vercel Deployment
echo ========================================
echo.
echo IMPORTANT: Before running this script:
echo 1. Deploy your backend to Railway first
echo 2. Get your Railway backend URL
echo 3. Update BACKEND_URL below with your Railway URL
echo.
echo ========================================
echo.

cd frontend

echo Setting up environment variables...
echo.

REM Replace YOUR_RAILWAY_URL with your actual Railway backend URL
set BACKEND_URL=https://your-backend.up.railway.app
set NEXT_PUBLIC_API_URL=https://your-backend.up.railway.app

echo BACKEND_URL=%BACKEND_URL%
echo NEXT_PUBLIC_API_URL=%NEXT_PUBLIC_API_URL%
echo.

echo Starting Vercel deployment...
echo.
echo Follow the prompts:
echo - Set up and deploy? Y
echo - Which scope? (select your account)
echo - Link to existing project? N
echo - Project name? todo-app-phase2
echo - Directory? ./
echo - Override settings? N
echo.

vercel --prod

echo.
echo ========================================
echo   Deployment Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Visit your Vercel URL
echo 2. Test signup/signin functionality
echo 3. Create some todos!
echo.
pause
