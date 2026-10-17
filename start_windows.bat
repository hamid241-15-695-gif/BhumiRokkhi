@echo off
cd /d "%~dp0"
where docker >nul 2>&1
if errorlevel 1 (
 echo Please install and start Docker Desktop first.
 pause
 exit /b 1
)
docker compose up --build -d
if errorlevel 1 (
 echo Check error with: docker compose logs
 pause
 exit /b 1
)
echo Open: http://localhost:3000/register
pause
