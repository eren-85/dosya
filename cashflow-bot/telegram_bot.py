"""
Telegram Bot - Market Cash Flow

Komutlar:
/cashflow - Tam market analizi
/risk - Sadece risk değerlendirmesi
/top10 - Top 10 coin
/help - Yardım

Kullanım:
1. Bot token'ınızı config.py'ye ekleyin
2. python telegram_bot.py
"""

import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from cashflow_analyzer import CashFlowAnalyzer
import config

analyzer = CashFlowAnalyzer()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Hoş geldin mesajı"""
    await update.message.reply_text(
        "📊 Market Cash Flow Bot'a Hoş Geldiniz!\n\n"
        "Komutlar:\n"
        "/cashflow - Tam market analizi (30 coin)\n"
        "/risk - Risk değerlendirmesi\n"
        "/top10 - Top 10 coin analizi\n"
        "/quick - Hızlı özet (10 coin)\n"
        "/help - Yardım\n\n"
        "🔴 Canlı Binance verisi kullanılır!"
    )


async def cashflow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tam market cash flow analizi"""
    await update.message.reply_text("📊 Analiz yapılıyor (30-45 saniye)...")

    try:
        report = analyzer.analyze(top_n=30, timeframe='15m')

        if report['status'] == 'success':
            text = report['text_report']

            # Telegram 4096 karakter limiti
            if len(text) > 4000:
                chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
                for chunk in chunks:
                    await update.message.reply_text(f"<pre>{chunk}</pre>", parse_mode='HTML')
            else:
                await update.message.reply_text(f"<pre>{text}</pre>", parse_mode='HTML')
        else:
            await update.message.reply_text(f"❌ Hata: {report.get('message')}")

    except Exception as e:
        await update.message.reply_text(f"❌ Beklenmeyen hata: {str(e)}")


async def risk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sadece risk değerlendirmesi"""
    await update.message.reply_text("⏳ Risk analizi yapılıyor...")

    try:
        report = analyzer.analyze(top_n=10, timeframe='15m')

        if report['status'] == 'success':
            risk = report['risk_assessment']
            metrics = report['market_metrics']

            risk_emoji = {
                'low': '🟢',
                'medium': '🟡',
                'high': '🔴'
            }.get(risk['level'], '⚪')

            text = (
                f"{risk_emoji} **RISK SEVİYESİ: {risk['level'].upper()}**\n\n"
                f"{risk['message']}\n\n"
                f"📊 **Market Metrikleri:**\n"
                f"• 1d Alım Oranı: %{risk['buyer_1d']:.1f}\n"
                f"• Alım Gücü: {metrics['short_term_power']:.1f}X\n\n"
            )

            # Timeframes
            text += "⏰ **Zaman Dilimleri:**\n"
            for tf, data in metrics['timeframes'].items():
                pct = data['buyer_percentage']
                ind = '🔼' if pct >= 50 else '🔻'
                text += f"• {tf}: %{pct:.1f} {ind}\n"

            await update.message.reply_text(text, parse_mode='Markdown')
        else:
            await update.message.reply_text(f"❌ Hata: {report.get('message')}")

    except Exception as e:
        await update.message.reply_text(f"❌ Hata: {str(e)}")


async def top10(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Top 10 coin analizi"""
    await update.message.reply_text("🔝 Top 10 analiz ediliyor...")

    try:
        report = analyzer.analyze(top_n=10, timeframe='15m')

        if report['status'] == 'success':
            flows = report['top_flows'][:10]

            text = "🔝 **Top 10 Nakit Akışı**\n\n"
            for i, coin in enumerate(flows, 1):
                sym = coin['symbol'].replace('USDT', '')
                text += (
                    f"{i}. **{sym}**\n"
                    f"   Nakit: %{coin['cash_share']:.1f} | "
                    f"15m: %{coin['buyer_15m']:.0f} | "
                    f"Mts: {coin['momentum']:.1f}\n"
                    f"   {coin['indicators']}\n\n"
                )

            await update.message.reply_text(text, parse_mode='Markdown')
        else:
            await update.message.reply_text(f"❌ Hata: {report.get('message')}")

    except Exception as e:
        await update.message.reply_text(f"❌ Hata: {str(e)}")


async def quick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Hızlı özet (10 coin)"""
    await update.message.reply_text("⚡ Hızlı analiz (10 coin)...")

    try:
        report = analyzer.analyze(top_n=10, timeframe='15m', limit=300)

        if report['status'] == 'success':
            risk = report['risk_assessment']
            flows = report['top_flows'][:5]

            risk_emoji = {'low': '🟢', 'medium': '🟡', 'high': '🔴'}.get(risk['level'], '⚪')

            text = (
                f"{risk_emoji} **{risk['level'].upper()} RISK**\n\n"
                f"**Top 5 Nakit Akışı:**\n"
            )

            for coin in flows:
                sym = coin['symbol'].replace('USDT', '')
                text += f"• {sym}: %{coin['cash_share']:.1f} {coin['indicators'][:2]}\n"

            await update.message.reply_text(text, parse_mode='Markdown')
        else:
            await update.message.reply_text(f"❌ Hata: {report.get('message')}")

    except Exception as e:
        await update.message.reply_text(f"❌ Hata: {str(e)}")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Yardım"""
    help_text = """
📊 **Market Cash Flow Bot**

**Komutlar:**
/cashflow - Tam analiz (30 coin, 30-45 sn)
/risk - Risk değerlendirmesi (hızlı)
/top10 - Top 10 coin analizi
/quick - Hızlı özet (5 coin, 10 sn)

**Göstergeler:**
🔼 - Alım baskınlığı (%50+)
🔻 - Satış baskınlığı (%50-)

**Risk Seviyeleri:**
🟢 LOW - Alım yapılabilir
🟡 MEDIUM - Dikkatli olun
🔴 HIGH - Piyasaya bulaşmayın

**Veri:** Binance Spot (Canlı)
**Güncelleme:** Her komutta yeni veri
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')


def main():
    """Bot başlat"""
    if not config.TELEGRAM_BOT_TOKEN:
        print("❌ HATA: config.py'de TELEGRAM_BOT_TOKEN ayarlanmamış!")
        print("BotFather'dan token alıp config.py'ye ekleyin.")
        return

    print("🤖 Telegram bot başlatılıyor...")
    print(f"📊 Cash Flow Analyzer hazır")

    app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()

    # Komutlar
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("cashflow", cashflow))
    app.add_handler(CommandHandler("risk", risk))
    app.add_handler(CommandHandler("top10", top10))
    app.add_handler(CommandHandler("quick", quick))
    app.add_handler(CommandHandler("help", help_command))

    print("✅ Bot hazır! Komutlar:")
    print("  /cashflow - Tam analiz")
    print("  /risk - Risk değerlendirmesi")
    print("  /top10 - Top 10 coin")
    print("  /quick - Hızlı özet")
    print("\n🚀 Başlatılıyor...\n")

    app.run_polling()


if __name__ == '__main__':
    main()
