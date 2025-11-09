@echo off
echo ========================================
echo   Accumulation Detector
echo   Gizli Toplanan Coinleri Bul
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

echo [BASLATILIYOR] Akumulasyon taramasi...
echo.
echo Tum Binance USDT ciftleri taranacak (200+ coin)
echo Bu islem 2-5 dakika surebilir...
echo.
python accumulation_detector.py

echo.
pause
