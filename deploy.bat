@echo off
echo ============================================
echo AutoCrate Web - Vercel Deployment Script
echo ============================================
echo.
echo [INFO] Preparing for Vercel deployment...
echo.

REM Check if dependencies are installed
if not exist "node_modules\" (
    echo [INFO] Installing dependencies first...
    call npm install
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Dependency installation failed!
        pause
        exit /b 1
    )
)

echo [INFO] Running type check...
call npm run type-check
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Type check found issues, but continuing...
)

echo [INFO] Running build test...
call npm run build
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Build failed! Please fix errors before deploying.
    pause
    exit /b 1
)

echo.
echo [INFO] Build successful! Ready for deployment.
echo.
echo Choose deployment option:
echo [1] Development deployment (preview)
echo [2] Production deployment
echo [3] Cancel
echo.
set /p choice="Enter choice (1-3): "

if "%choice%"=="1" (
    echo [INFO] Deploying to Vercel development...
    npx vercel
) else if "%choice%"=="2" (
    echo [INFO] Deploying to Vercel production...
    npx vercel --prod
) else (
    echo [INFO] Deployment cancelled.
    pause
    exit /b 0
)

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Deployment failed!
    echo [ERROR] Check your Vercel configuration and try again.
    pause
    exit /b 1
)

echo.
echo ============================================
echo [SUCCESS] Deployment complete!
echo ============================================
echo.
echo Your AutoCrate Web application is now live!
echo Check the Vercel dashboard for the URL.
echo.
pause