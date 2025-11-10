@echo off
echo ========================================
echo   Market Cash Flow - HIZLI RAPOR
echo   (10 coin, tablo formati)
echo ========================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [HATA] Python bulunamadi!
    pause
    exit /b 1
)

echo Hizli analiz yapiliyor (10-15 saniye)...
echo.

python generate_report.py --coins 10 --format table

if errorlevel 1 pause
