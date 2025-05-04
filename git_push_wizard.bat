@echo off
echo 🧠 AutoCrate Git Push Script
git add .
set /p msg="Enter commit message: "
if "%msg%"=="" set msg=Update on %DATE% %TIME%
git commit -m "%msg%"
git push origin main
echo ✅ All changes pushed.
pause
