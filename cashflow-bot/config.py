"""
Yapılandırma Dosyası

Telegram Bot Token:
1. https://t.me/BotFather 'a git
2. /newbot komutuyla yeni bot oluştur
3. Aldığın token'ı buraya yapıştır
"""

# Telegram Bot Token (BotFather'dan al)
TELEGRAM_BOT_TOKEN = ""  # Örnek: "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"

# Discord Bot Token (opsiyonel)
DISCORD_BOT_TOKEN = ""

# Analiz ayarları
DEFAULT_TOP_N = 30  # Varsayılan coin sayısı
DEFAULT_TIMEFRAME = "15m"  # Varsayılan zaman dilimi
DEFAULT_LIMIT = 500  # Varsayılan candle sayısı

# API ayarları (opsiyonel)
API_HOST = "0.0.0.0"
API_PORT = 8000
