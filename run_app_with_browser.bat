@echo off
chcp 65001 >nul
echo ==========================================
echo   UAE Annual Leave Management System
echo ==========================================
echo.

:: Find Python Scripts path
set "PYTHON_SCRIPTS=C:\Users\Lenovo\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\LocalCache\local-packages\Python313\Scripts"
set "STREAMLIT=%PYTHON_SCRIPTS%\streamlit.exe"

:: Check if streamlit exists
if not exist "%STREAMLIT%" (
    echo [ERROR] Streamlit not found at: %STREAMLIT%
    echo.
    echo Trying to install streamlit...
    pip install streamlit pandas
    if errorlevel 1 (
        echo [ERROR] Failed to install streamlit.
        pause
        exit /b 1
    )
)

:: Disable usage stats
set STREAMLIT_BROWSER_GATHERUSAGESTATS=false

echo Starting Streamlit app...
echo This will open your browser automatically...
echo.

:: Run the app (browser will open automatically)
"%STREAMLIT%" run annual_leave_system.py

if errorlevel 1 (
    echo.
    echo [ERROR] Failed to start the application.
    pause
    exit /b 1
)

pause
