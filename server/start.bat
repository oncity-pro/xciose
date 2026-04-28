@echo off
setlocal EnableDelayedExpansion
REM ONCITY-Django Backend One-Click Startup Script for Windows

set "SKIP_MIGRATIONS=0"
set "PORT=8000"

REM Parse arguments
:parse_args
if "%~1"=="" goto :done_parse
if /I "%~1"=="-SkipMigrations" set "SKIP_MIGRATIONS=1"
if /I "%~1"=="--skip-migrations" set "SKIP_MIGRATIONS=1"
if /I "%~1"=="-Port" (
    shift
    set "PORT=%~1"
)
if /I "%~1"=="--port" (
    shift
    set "PORT=%~1"
)
shift
goto :parse_args
:done_parse

echo ========================================
echo   ONCITY-Django Backend Startup
echo ========================================
echo.

REM 1. Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.10+
    exit /b 1
)
for /f "tokens=*" %%a in ('python --version') do set "PYTHON_VERSION=%%a"
echo Python: %PYTHON_VERSION%
echo.

REM 2. Check MySQL
powershell -Command "try { $tcp = New-Object System.Net.Sockets.TcpClient; $tcp.Connect('localhost', 3306); $tcp.Close(); exit 0 } catch { exit 1 }" >nul 2>&1
if errorlevel 1 (
    echo WARNING: MySQL is not running on localhost:3306!
    echo Please make sure MySQL service is started.
    set /p "CONTINUE=Continue anyway? (y/N): "
    if /I not "!CONTINUE!"=="y" exit /b 1
) else (
    echo MySQL is running
)
echo.

REM 3. Virtual environment
set "VENV_PYTHON=%~dp0venv\Scripts\python.exe"

if not exist "%VENV_PYTHON%" (
    echo Creating virtual environment...
    python -m venv "%~dp0venv"
    echo Virtual environment created
    echo.
)

REM 4. Install dependencies
echo Installing dependencies...
"%VENV_PYTHON%" -m pip install --upgrade pip >nul 2>&1
"%VENV_PYTHON%" -m pip install -r "%~dp0requirements.txt" >nul 2>&1
echo Dependencies installed
echo.

REM 5. Check .env
if not exist "%~dp0.env" (
    echo WARNING: .env file not found
    echo Creating .env from .env.example...
    copy "%~dp0.env.example" "%~dp0.env" >nul
    echo Created .env, please check the configuration!
    pause
)

REM 6. Run migrations
if "%SKIP_MIGRATIONS%"=="0" (
    echo Running database migrations...
    "%VENV_PYTHON%" "%~dp0manage.py" migrate
    echo Migrations complete
    echo.
) else (
    echo Skipping migrations (--skip-migrations)
    echo.
)

REM 7. Start server
echo ========================================
echo   Starting Django Development Server
echo   URL: http://127.0.0.1:%PORT%
echo   Admin: http://127.0.0.1:%PORT%/admin/
echo   API Health: http://127.0.0.1:%PORT%/api/health/
echo ========================================
echo.
echo Press Ctrl+C to stop the server
echo.

"%VENV_PYTHON%" "%~dp0manage.py" runserver 127.0.0.1:%PORT%
