@echo off
REM Course Availability Notifier - Windows Run Script

echo 🎓 Course Availability Notifier Startup
echo ========================================

REM Check if virtual environment exists
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/upgrade requirements
echo 📋 Installing dependencies...
python -m pip install -U pip
python -m pip install -r requirements.txt

REM Check if .env exists
if not exist ".env" (
    echo ⚠️  No .env file found!
    echo 📝 Please copy env.example to .env and configure your settings:
    echo    copy env.example .env
    echo    notepad .env
    pause
    exit /b 1
)

REM Create chrome profile directory
if not exist "chrome_profile" (
    echo 🌐 Creating Chrome profile directory...
    mkdir chrome_profile
)

REM Run the application
echo 🚀 Starting Course Availability Notifier...
echo 📱 Monitor will send SMS alerts to the configured number
echo ⏹️  Press Ctrl+C to stop
echo.

python main.py 