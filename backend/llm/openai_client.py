"""
OpenAI Client for Market Analysis

Features:
- GPT-4o, GPT-4-turbo, GPT-4o-mini support
- Streaming responses
- JSON mode for structured output
- Function calling
- Rate limiting handling
- Fallback to Anthropic if needed
"""

import os
import json
import logging
from typing import Optional, Dict, List, Any, Union
from datetime import datetime

try:
    from openai import OpenAI, OpenAIError, RateLimitError
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    OpenAI = None
    OpenAIError = Exception
    RateLimitError = Exception

logger = logging.getLogger(__name__)


class OpenAIClient:
    """
    OpenAI API client for market analysis

    Handles:
    - Market analysis generation
    - Technical indicator interpretation
    - Trading signal generation
    - Risk assessment
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        max_tokens: int = 4000,
    ):
        """
        Initialize OpenAI client

        Args:
            api_key: OpenAI API key (default: from env)
            model: Model name (gpt-4o, gpt-4-turbo, gpt-4o-mini)
            temperature: Sampling temperature (0.0 - 2.0)
            max_tokens: Maximum response tokens
        """
        if not OPENAI_AVAILABLE:
            raise ImportError("openai package not installed. Run: pip install openai")

        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenAI API key not found. Please add OPENAI_API_KEY to your .env file. "
                "Example: OPENAI_API_KEY=sk-proj-..."
            )

        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

        # Initialize client
        self.client = OpenAI(api_key=self.api_key)

        logger.info(f"✅ OpenAI client initialized (model: {self.model})")

    def analyze_market(
        self,
        symbol: str,
        timeframe: str,
        market_data: Dict[str, Any],
        technical_indicators: Dict[str, Any],
        on_chain_data: Optional[Dict[str, Any]] = None,
        additional_context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate comprehensive market analysis

        Args:
            symbol: Trading pair (e.g., "BTCUSDT")
            timeframe: Analysis timeframe (e.g., "1H", "4H", "1D")
            market_data: OHLCV data, volume, etc.
            technical_indicators: RSI, MACD, Moving Averages, etc.
            on_chain_data: Optional on-chain metrics
            additional_context: Optional additional context

        Returns:
            dict: Analysis results
        """
        logger.info(f"🤖 Analyzing {symbol} ({timeframe}) with OpenAI {self.model}")

        # Build analysis prompt
        prompt = self._build_analysis_prompt(
            symbol=symbol,
            timeframe=timeframe,
            market_data=market_data,
            technical_indicators=technical_indicators,
            on_chain_data=on_chain_data,
            additional_context=additional_context,
        )

        try:
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt()
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"}  # Structured JSON output
            )

            # Parse response
            content = response.choices[0].message.content
            result = json.loads(content)

            # Add metadata
            result["metadata"] = {
                "model": self.model,
                "timestamp": datetime.utcnow().isoformat(),
                "symbol": symbol,
                "timeframe": timeframe,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }
            }

            logger.info(f"✅ Analysis completed ({response.usage.total_tokens} tokens)")
            return result

        except RateLimitError as e:
            logger.error(f"❌ Rate limit exceeded: {e}")
            return {
                "status": "error",
                "error": "rate_limit",
                "message": (
                    "OpenAI rate limit exceeded. This usually means:\n"
                    "1. Your API key has exceeded free tier limits\n"
                    "2. You need to add payment method to OpenAI account\n"
                    "3. Or wait a few minutes and try again\n\n"
                    f"Error details: {str(e)}"
                ),
                "timestamp": datetime.utcnow().isoformat()
            }
        except OpenAIError as e:
            error_msg = str(e)
            # Check if it's an authentication error
            if "authentication" in error_msg.lower() or "api_key" in error_msg.lower():
                message = (
                    "OpenAI API authentication failed. Please check:\n"
                    "1. Your .env file exists in the project root\n"
                    "2. OPENAI_API_KEY is set correctly (starts with 'sk-')\n"
                    "3. The API key is valid and not expired\n\n"
                    f"Error details: {error_msg}"
                )
            else:
                message = f"OpenAI API error: {error_msg}"

            logger.error(f"❌ OpenAI API error: {e}")
            return {
                "status": "error",
                "error": "api_error",
                "message": message,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            return {
                "status": "error",
                "error": "unknown",
                "message": f"Unexpected error during analysis: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }

    def _get_system_prompt(self) -> str:
        """
        Get system prompt for market analysis

        Returns:
            str: System prompt
        """
        return """You are Sigma Analyst, an expert AI cryptocurrency market analyst with deep knowledge of:

**Technical Analysis:**
- 200+ technical indicators (RSI, MACD, Bollinger Bands, Ichimoku, etc.)
- Smart Money Concepts (Order Blocks, Fair Value Gaps, Kill Zones)
- ICT (Inner Circle Trader) methodology
- Market microstructure (CVD, OI, Funding Rate)
- Harmonic patterns and Fibonacci analysis

**On-Chain Analysis:**
- Exchange netflows (whale movements)
- Stablecoin inflows/outflows
- Active addresses and network activity
- Miner behavior and hash rate
- Derivatives metrics (Open Interest, Liquidations)

**Market Psychology:**
- Fear & Greed Index interpretation
- Sentiment analysis
- Crowd behavior patterns
- Market cycles and phases

**Your Role:**
- Provide objective, data-driven analysis
- Identify high-probability trading setups
- Calculate risk/reward ratios
- Suggest entry/exit points with stop-loss levels
- Explain reasoning clearly for educational purposes

**Output Format (JSON):**
{
  "market_bias": "bullish" | "bearish" | "neutral",
  "confidence": 0-100,
  "summary": "Brief 2-3 sentence summary",
  "technical_analysis": {
    "trend": "description",
    "support_levels": [numbers],
    "resistance_levels": [numbers],
    "key_indicators": {"RSI": value, "MACD": "signal", ...}
  },
  "smart_money": {
    "order_blocks": [...],
    "fair_value_gaps": [...],
    "kill_zone": "London/NY/Asia"
  },
  "on_chain_insights": {
    "whale_activity": "description",
    "exchange_flows": "description"
  },
  "trading_signal": {
    "action": "LONG" | "SHORT" | "WAIT",
    "entry_price": number,
    "stop_loss": number,
    "take_profit_1": number,
    "take_profit_2": number,
    "risk_reward_ratio": number
  },
  "risk_assessment": {
    "level": "low" | "medium" | "high",
    "factors": ["list", "of", "risks"]
  },
  "conclusion": "Final recommendation and rationale"
}

**Important:**
- Be honest about uncertainty
- Don't guarantee outcomes
- Prioritize risk management
- Educate the user on WHY, not just WHAT
- Use clear, professional language"""

    def _build_analysis_prompt(
        self,
        symbol: str,
        timeframe: str,
        market_data: Dict[str, Any],
        technical_indicators: Dict[str, Any],
        on_chain_data: Optional[Dict[str, Any]],
        additional_context: Optional[str],
    ) -> str:
        """
        Build analysis prompt from market data

        Args:
            symbol: Trading pair
            timeframe: Timeframe
            market_data: Market data
            technical_indicators: Technical indicators
            on_chain_data: On-chain data
            additional_context: Additional context

        Returns:
            str: Analysis prompt
        """
        prompt_parts = [
            f"**Symbol:** {symbol}",
            f"**Timeframe:** {timeframe}",
            f"**Analysis Date:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
            "",
            "**Market Data:**",
            f"```json\n{json.dumps(market_data, indent=2)}\n```",
            "",
            "**Technical Indicators:**",
            f"```json\n{json.dumps(technical_indicators, indent=2)}\n```",
        ]

        if on_chain_data:
            prompt_parts.extend([
                "",
                "**On-Chain Data:**",
                f"```json\n{json.dumps(on_chain_data, indent=2)}\n```",
            ])

        if additional_context:
            prompt_parts.extend([
                "",
                "**Additional Context:**",
                additional_context,
            ])

        prompt_parts.extend([
            "",
            "**Task:**",
            "Provide a comprehensive market analysis in JSON format as specified in the system prompt.",
            "Focus on actionable insights and clear risk management guidance.",
        ])

        return "\n".join(prompt_parts)

    def quick_analysis(
        self,
        symbol: str,
        current_price: float,
        indicators: Dict[str, float],
        question: Optional[str] = None,
    ) -> str:
        """
        Get a quick text analysis (non-structured)

        Args:
            symbol: Trading pair
            current_price: Current price
            indicators: Key indicators
            question: Optional specific question

        Returns:
            str: Analysis text
        """
        logger.info(f"🤖 Quick analysis for {symbol}")

        prompt = f"""Quick market analysis for {symbol}:

Current Price: ${current_price:,.2f}

Key Indicators:
{json.dumps(indicators, indent=2)}
"""

        if question:
            prompt += f"\n\nSpecific Question: {question}"

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a concise cryptocurrency market analyst. Provide brief, actionable insights."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.5,
                max_tokens=500,
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"❌ Quick analysis failed: {e}")
            return f"Error: {str(e)}"


# ============================================
# Singleton instance
# ============================================

_openai_client: Optional[OpenAIClient] = None


def get_openai_client(
    api_key: Optional[str] = None,
    model: Optional[str] = None,
) -> OpenAIClient:
    """
    Get or create OpenAI client singleton

    Args:
        api_key: Optional API key override
        model: Optional model override

    Returns:
        OpenAIClient: Client instance
    """
    global _openai_client

    if _openai_client is None:
        model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        _openai_client = OpenAIClient(api_key=api_key, model=model)

    return _openai_client
