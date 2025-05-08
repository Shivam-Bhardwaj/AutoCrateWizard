@echo off
rem Script to stage, commit, and push recent AutoCrate Wizard changes

rem Define commit message
rem Summarizes the UI improvements from Task 1
set COMMIT_MSG=feat: Implement Regenerate button, optimize sidebar, fix plot zoom (v0.6.3)

echo Staging changes...
git add .

echo Committing changes...
git commit -m "%COMMIT_MSG%"

echo Pushing changes...
git push

echo Script finished.
pause
rem The 'pause' command will keep the window open after execution so you can see the output. Remove if not needed.