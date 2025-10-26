"""
Claude Reasoning API integration for final decision-making
Combines ML predictions, RL suggestions, and RAG context
"""

from typing import Dict, List, Optional
from datetime import datetime
import json
from anthropic import Anthropic
from ..core.config import settings


class ClaudeReasoningEngine:
    """
    Claude API integration for sophisticated market reasoning
    Takes ML/RL outputs and produces final analysis
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.anthropic_api_key
        self.client = Anthropic(api_key=self.api_key) if self.api_key else None

    def analyze_market(
        self,
        market_data: Dict,
        ml_predictions: Dict,
        rl_recommendation: Dict,
        rag_context: str,
        mode: str = "oneshot"
    ) -> Dict:
        """
        Comprehensive market analysis using Claude

        Args:
            market_data: Current market state (price, indicators, etc.)
            ml_predictions: Ensemble, LSTM, Transformer predictions
            rl_recommendation: RL agent recommendation
            rag_context: Context from PDF knowledge base
            mode: 'oneshot' or 'monitor'

        Returns:
            {
                'market_pulse': {...},
                'scenarios': [...],
                'recommendation': {...},
                'reasoning': str
            }
        """

        if not self.client:
            # Fallback if no API key
            return self._fallback_analysis(market_data, ml_predictions, rl_recommendation)

        # Construct prompt
        prompt = self._build_analysis_prompt(
            market_data, ml_predictions, rl_recommendation, rag_context, mode
        )

        try:
            # Call Claude API
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",  # Latest Claude
                max_tokens=4096,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3  # Lower temperature for consistency
            )

            # Parse response
            response_text = message.content[0].text

            # Extract JSON from response
            analysis = self._parse_claude_response(response_text)

            return analysis

        except Exception as e:
            print(f"Error calling Claude API: {e}")
            return self._fallback_analysis(market_data, ml_predictions, rl_recommendation)

    def _build_analysis_prompt(
        self,
        market_data: Dict,
        ml_predictions: Dict,
        rl_recommendation: Dict,
        rag_context: str,
        mode: str
    ) -> str:
        """Build comprehensive prompt for Claude"""

        prompt = f"""
You are **Sigma Analyst**, a multi-role AI financial analyst with expertise in:
- Senior Crypto Market Analyst
- Market Intelligence Officer
- Behavioral Finance Specialist
- Financial News Reporter

**IMPORTANT**: This is NOT a trading bot. Provide analysis and insights for informed decision-making.

## Current Market Data (UTC: {datetime.utcnow().isoformat()})
```json
{json.dumps(market_data, indent=2)}
```

## ML Model Predictions
```json
{json.dumps(ml_predictions, indent=2)}
```

## RL Agent Recommendation
```json
{json.dumps(rl_recommendation, indent=2)}
```

## Knowledge Base Context
{rag_context}

---

**Task**: Provide a comprehensive market analysis in the following JSON format:

```json
{{
  "meta": {{
    "generated_at_utc": "<ISO timestamp>",
    "mode": "{mode}",
    "confidence": 0.0-1.0
  }},
  "market_pulse": {{
    "sentiment": "bullish|neutral|bearish",
    "confidence": 0.0-1.0,
    "volatility_regime": "low|normal|elevated",
    "key_observation": "1-2 sentence summary"
  }},
  "scenarios": [
    {{
      "name": "bull",
      "prob": 0.0-1.0,
      "trigger": "clear condition",
      "invalidation": "clear level/condition",
      "targets": [price1, price2]
    }},
    {{
      "name": "base",
      "prob": 0.0-1.0,
      "trigger": "...",
      "invalidation": "...",
      "targets": [...]
    }},
    {{
      "name": "bear",
      "prob": 0.0-1.0,
      "trigger": "...",
      "invalidation": "...",
      "targets": [...]
    }}
  ],
  "recommendation": {{
    "action": "LONG|SHORT|HOLD|CLOSE",
    "confidence": 0.0-1.0,
    "entry_zone": [low, high],
    "stop_loss": price,
    "take_profit": [tp1, tp2],
    "risk_reward_ratio": float,
    "position_size_pct": 0.0-1.0
  }},
  "reasoning": "Detailed explanation combining ML predictions, RL recommendation, technical analysis, and knowledge base insights. Be concise but thorough (3-5 paragraphs).",
  "alerts": ["Any critical warnings or observations"],
  "risk": {{
    "leverage_risk": "low|medium|high",
    "liquidity_risk": "low|medium|high",
    "volatility_risk": "low|medium|high"
  }},
  "disclaimer": "This analysis is for informational purposes only. Not financial advice."
}}
```

**Guidelines**:
1. Be objective and data-driven
2. Clearly state assumptions
3. Provide actionable insights
4. Include invalidation levels for scenarios
5. Consider market context (Kill Zones, order blocks, etc.)
6. Use knowledge base context to inform analysis
7. Acknowledge model limitations
"""

        return prompt

    def _parse_claude_response(self, response_text: str) -> Dict:
        """Parse Claude's JSON response"""
        try:
            # Extract JSON from response (Claude might wrap in ```json```)
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1

            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                return json.loads(json_str)
            else:
                raise ValueError("No JSON found in response")

        except Exception as e:
            print(f"Error parsing Claude response: {e}")
            # Return structured fallback
            return {
                'error': 'Failed to parse response',
                'raw_response': response_text[:500]
            }

    def _fallback_analysis(
        self,
        market_data: Dict,
        ml_predictions: Dict,
        rl_recommendation: Dict
    ) -> Dict:
        """Fallback analysis if Claude API unavailable"""

        # Simple rule-based analysis
        avg_ml_prediction = sum(
            pred for pred in ml_predictions.values() if isinstance(pred, (int, float))
        ) / max(len(ml_predictions), 1)

        sentiment = "bullish" if avg_ml_prediction > 0 else ("bearish" if avg_ml_prediction < 0 else "neutral")

        return {
            'meta': {
                'generated_at_utc': datetime.utcnow().isoformat(),
                'mode': 'fallback',
                'confidence': 0.5
            },
            'market_pulse': {
                'sentiment': sentiment,
                'confidence': 0.6,
                'volatility_regime': 'normal',
                'key_observation': 'Fallback analysis - Claude API not available'
            },
            'scenarios': [
                {
                    'name': 'base',
                    'prob': 1.0,
                    'trigger': 'Current price action',
                    'invalidation': 'N/A',
                    'targets': [market_data.get('price', 0) * 1.05]
                }
            ],
            'recommendation': rl_recommendation,
            'reasoning': 'Analysis based on ML ensemble and RL agent only. Claude reasoning unavailable.',
            'alerts': ['Claude API unavailable - using fallback analysis'],
            'risk': {
                'leverage_risk': 'medium',
                'liquidity_risk': 'medium',
                'volatility_risk': 'medium'
            },
            'disclaimer': 'This is a fallback analysis. Not financial advice.'
        }
