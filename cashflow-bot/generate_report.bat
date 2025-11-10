@echo off
echo ========================================
echo   Market Cash Flow - HTML Rapor
echo ========================================
echo.

REM Python kontrolu
python --version >nul 2>&1
if errorlevel 1 (
    echo [HATA] Python bulunamadi!
    pause
    exit /b 1
)

REM Bagimliliklari kontrol et
pip show pandas >nul 2>&1
if errorlevel 1 (
    echo [1/2] Bagimliliklari yukleniyor...
    pip install -q -r requirements.txt
    echo.
)

REM Rapor olustur
echo [2/2] HTML raporu olusturuluyor...
echo.
python generate_report.py

REM Hata durumunda pause
if errorlevel 1 pause
