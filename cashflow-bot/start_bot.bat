@echo off
echo ========================================
echo   Market Cash Flow Bot - Baslatiliyor
echo ========================================
echo.

REM Python kontrolu
python --version >nul 2>&1
if errorlevel 1 (
    echo [HATA] Python bulunamadi!
    echo Python yuklenmis mi kontrol edin.
    pause
    exit /b 1
)

echo [1/3] Config kontrol ediliyor...
python -c "import config; assert config.TELEGRAM_BOT_TOKEN, 'Token yok'" 2>nul
if errorlevel 1 (
    echo [HATA] config.py'de TELEGRAM_BOT_TOKEN ayarlanmamis!
    echo.
    echo BotFather'dan token alin ve config.py'ye ekleyin:
    echo   TELEGRAM_BOT_TOKEN = "123456789:ABCdefGHI..."
    echo.
    pause
    exit /b 1
)

echo [2/3] Bagimliliklari kontrol ediliyor...
pip show python-telegram-bot >nul 2>&1
if errorlevel 1 (
    echo [UYARI] Bazi paketler eksik, yukleniyor...
    pip install -q -r requirements.txt
)

echo [3/3] Telegram bot baslatiliyor...
echo.
echo ========================================
echo   BOT HAZIR!
echo ========================================
echo.
echo   Telegram'da botunuza gidin ve su komutlari deneyin:
echo   /start       - Hosgeldin mesaji
echo   /cashflow    - Tam analiz (text)
echo   /table       - Tablo formati
echo   /html        - HTML raporu indir
echo   /quick       - Hizli ozet
echo.
echo   Bot durdurmak icin: CTRL+C
echo.
echo ========================================
echo.

python telegram_bot.py

pause
