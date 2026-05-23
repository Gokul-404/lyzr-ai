REM GitAgent Interviewer Setup Script for Windows

echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║         GitAgent Interviewer Setup ^& Installation             ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.

REM Check Python version
echo Checking Python version...
python --version
echo ✓ Python OK
echo.

REM Create virtual environment
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    echo ✓ Virtual environment created
)

echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo ✓ Virtual environment activated
echo.

REM Install dependencies
echo Installing dependencies...
pip install -q -r requirements.txt
echo ✓ Dependencies installed
echo.

REM Setup .env
if not exist ".env" (
    echo Creating .env file...
    copy .env.example .env
    echo ✓ .env file created
    echo.
    echo ⚠ IMPORTANT: Edit .env and add your credentials:
    echo   - GITHUB_TOKEN from https://github.com/settings/tokens
    echo   - ANTHROPIC_API_KEY ^(optional^)
) else (
    echo ✓ .env already exists
)

echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║                   Setup Complete!                             ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.
echo Next steps:
echo.
echo 1. Edit .env and add your GITHUB_TOKEN:
echo    notepad .env
echo.
echo 2. Run the quick start check:
echo    python quickstart.py
echo.
echo 3. Try the demo:
echo    python demo.py
echo.
echo 4. Run an interview:
echo    python main.py ^<github_username^>
echo.

pause
