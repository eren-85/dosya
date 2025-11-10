@echo off
echo ========================================
echo   Market Cash Flow - Web UI
echo ========================================
echo.

REM Python kontrolu
python --version >nul 2>&1
if errorlevel 1 (
    echo [HATA] Python bulunamadi!
    echo Python 3.7+ yukleyin: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Flask kontrolu
pip show flask >nul 2>&1
if errorlevel 1 (
    echo [1/2] Flask yukleniyor...
    pip install -q flask
    echo.
)

REM Pandas kontrolu
pip show pandas >nul 2>&1
if errorlevel 1 (
    echo [2/2] Bagimliliklari yukleniyor...
    pip install -q -r requirements.txt
    echo.
)

REM Web UI baslat
echo [Baslatiliyor] Web UI aciliyor...
echo.
echo Browser'da otomatik acilacak: http://localhost:5000
echo.
echo Durdurmak icin: Ctrl+C
echo.
python web_ui.py

pause
