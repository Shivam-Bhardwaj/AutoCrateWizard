@echo off
echo ============================================
echo AutoCrate Web - Installation Script
echo ============================================
echo.
echo [INFO] Installing Node.js dependencies...
echo [INFO] This may take 2-3 minutes...
echo.

npm install

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Installation failed!
    echo [ERROR] Please ensure Node.js is installed and try again.
    echo.
    pause
    exit /b 1
)

echo.
echo ============================================
echo [SUCCESS] Installation complete!
echo ============================================
echo.
echo To start development server:
echo   npm run dev
echo.
echo To build for production:
echo   npm run build
echo.
echo To deploy to Vercel:
echo   npx vercel
echo.
pause