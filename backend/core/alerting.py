"""
Alerting system for email and Telegram notifications
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional
import asyncio
import aiohttp
from datetime import datetime
from .config import settings


class AlertManager:
    """
    Multi-channel alerting system
    - Email
    - Telegram
    - WebSocket (real-time dashboard)
    """

    def __init__(self):
        # Email config (from env)
        self.email_enabled = bool(settings.smtp_host if hasattr(settings, 'smtp_host') else False)
        self.smtp_host = getattr(settings, 'smtp_host', 'smtp.gmail.com')
        self.smtp_port = getattr(settings, 'smtp_port', 587)
        self.smtp_user = getattr(settings, 'smtp_user', None)
        self.smtp_password = getattr(settings, 'smtp_password', None)
        self.from_email = getattr(settings, 'from_email', 'noreply@sigma-analyst.com')

        # Telegram config
        self.telegram_enabled = bool(getattr(settings, 'telegram_bot_token', None))
        self.telegram_bot_token = getattr(settings, 'telegram_bot_token', None)
        self.telegram_chat_id = getattr(settings, 'telegram_chat_id', None)

        # Alert history (in-memory for session)
        self.alert_history: List[Dict] = []

    async def send_alert(
        self,
        alert_type: str,
        title: str,
        message: str,
        priority: str = 'medium',
        channels: List[str] = None
    ):
        """
        Send alert through specified channels

        Args:
            alert_type: 'liquidation', 'price_alert', 'signal', etc.
            title: Alert title
            message: Alert message
            priority: 'low', 'medium', 'high', 'critical'
            channels: ['email', 'telegram', 'websocket'] (None = all enabled)
        """

        alert = {
            'type': alert_type,
            'title': title,
            'message': message,
            'priority': priority,
            'timestamp': datetime.now().isoformat()
        }

        # Store in history
        self.alert_history.append(alert)

        # Determine channels
        if channels is None:
            channels = []
            if self.email_enabled:
                channels.append('email')
            if self.telegram_enabled:
                channels.append('telegram')
            channels.append('websocket')  # Always send to websocket

        # Send to each channel
        tasks = []
        if 'email' in channels and self.email_enabled:
            tasks.append(self._send_email(title, message, priority))

        if 'telegram' in channels and self.telegram_enabled:
            tasks.append(self._send_telegram(title, message, priority))

        if 'websocket' in channels:
            # WebSocket broadcasting handled separately in API
            pass

        # Execute in parallel
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        print(f"📢 Alert sent: [{alert_type}] {title}")

    async def _send_email(self, title: str, message: str, priority: str):
        """Send email alert"""
        if not self.smtp_user or not self.smtp_password:
            return

        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"[{priority.upper()}] {title} - Sigma Analyst"
            msg['From'] = self.from_email
            msg['To'] = self.smtp_user  # Send to self (can be configured for multiple recipients)

            # HTML body
            html = f"""
            <html>
              <head></head>
              <body>
                <h2 style="color: {'#FF6B6B' if priority == 'critical' else '#00BFA6'};">
                  {title}
                </h2>
                <p>{message}</p>
                <hr>
                <p style="color: #888; font-size: 12px;">
                  Sigma Analyst - {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
                </p>
              </body>
            </html>
            """

            msg.attach(MIMEText(html, 'html'))

            # Send via SMTP
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            print(f"✅ Email sent: {title}")

        except Exception as e:
            print(f"❌ Email send error: {e}")

    async def _send_telegram(self, title: str, message: str, priority: str):
        """Send Telegram alert"""
        if not self.telegram_bot_token or not self.telegram_chat_id:
            return

        try:
            # Priority emoji
            emoji = {
                'low': '🟢',
                'medium': '🟡',
                'high': '🟠',
                'critical': '🔴'
            }.get(priority, '⚪')

            # Format message
            telegram_message = f"{emoji} **{title}**\n\n{message}\n\n_Sigma Analyst - {datetime.now().strftime('%H:%M:%S UTC')}_"

            # Send via Telegram API
            url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
            params = {
                'chat_id': self.telegram_chat_id,
                'text': telegram_message,
                'parse_mode': 'Markdown'
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=params) as resp:
                    if resp.status == 200:
                        print(f"✅ Telegram sent: {title}")
                    else:
                        print(f"❌ Telegram error: {resp.status}")

        except Exception as e:
            print(f"❌ Telegram send error: {e}")

    def get_recent_alerts(self, limit: int = 50) -> List[Dict]:
        """Get recent alerts"""
        return self.alert_history[-limit:]

    def clear_history(self):
        """Clear alert history"""
        self.alert_history = []


# Pre-configured alert templates
class AlertTemplates:
    """Pre-defined alert message templates"""

    @staticmethod
    def price_alert(symbol: str, price: float, trigger_level: float, direction: str) -> Dict:
        """Price level alert"""
        return {
            'type': 'price_alert',
            'title': f'{symbol} Price Alert',
            'message': f'{symbol} has {direction} {trigger_level:.2f}. Current price: ${price:.2f}',
            'priority': 'medium'
        }

    @staticmethod
    def liquidation_alert(symbol: str, side: str, size: float, value_usd: float) -> Dict:
        """Large liquidation alert"""
        return {
            'type': 'liquidation',
            'title': f'Large {side.upper()} Liquidation',
            'message': f'{size:.4f} {symbol} liquidated (${value_usd:,.0f})',
            'priority': 'high' if value_usd > 1_000_000 else 'medium'
        }

    @staticmethod
    def signal_alert(symbol: str, signal_type: str, confidence: float, action: str) -> Dict:
        """Trading signal alert"""
        return {
            'type': 'signal',
            'title': f'{symbol} {signal_type} Signal',
            'message': f'Action: {action}\nConfidence: {confidence*100:.1f}%',
            'priority': 'high' if confidence > 0.8 else 'medium'
        }

    @staticmethod
    def risk_alert(message: str) -> Dict:
        """Risk management alert"""
        return {
            'type': 'risk',
            'title': 'Risk Alert',
            'message': message,
            'priority': 'critical'
        }
