@echo off
echo ========================================
echo   Market Cash Flow Bot - Kurulum
echo ========================================
echo.

echo [1/3] Python kontrol ediliyor...
python --version
if errorlevel 1 (
    echo HATA: Python bulunamadi!
    pause
    exit /b 1
)

echo.
echo [2/3] Bagimliliklari yukluyor...
pip install -r requirements.txt

echo.
echo [3/3] Kurulum tamamlandi!
echo.
echo ========================================
echo   SONRAKI ADIMLAR:
echo ========================================
echo 1. config.py dosyasini duzenle
echo 2. TELEGRAM_BOT_TOKEN ekle
echo 3. python telegram_bot.py ile baslat
echo.
pause
