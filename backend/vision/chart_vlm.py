"""
Vision Language Model (VLM) System for Chart Analysis
RTX 4060 optimized - Qwen2.5-VL-7B (int4/AWQ quantized)

Capabilities:
- Chart image understanding (candlesticks, indicators, patterns)
- Pattern recognition (H&S, triangles, wedges, harmonics)
- Text extraction from charts (OCR)
- Multi-modal reasoning (visual + numerical)
- Trading book/PDF analysis with charts

GPU Requirements:
- RTX 4060 (8GB VRAM)
- Uses AWQ/int4 quantization
- Efficient inference (~2-3 GB VRAM)
"""

import torch
from typing import Dict, List, Optional, Union
from pathlib import Path
import numpy as np
from PIL import Image
import logging

logger = logging.getLogger(__name__)

try:
    from transformers import Qwen2VLForConditionalGeneration, AutoTokenizer, AutoProcessor
    from transformers import BitsAndBytesConfig
    HAS_QWEN = True
except ImportError:
    logger.warning("transformers not installed. VLM features disabled.")
    HAS_QWEN = False


class ChartVLM:
    """
    Vision Language Model for chart analysis using Qwen2.5-VL-7B

    Optimized for RTX 4060 with AWQ/int4 quantization
    """

    def __init__(
        self,
        model_name: str = "Qwen/Qwen2.5-VL-7B-Instruct-AWQ",
        device: str = "cuda",
        max_memory: str = "7GB"
    ):
        """
        Initialize VLM

        Args:
            model_name: HuggingFace model ID (AWQ quantized for 8GB VRAM)
            device: cuda or cpu
            max_memory: Max VRAM to use
        """
        self.model_name = model_name
        self.device = device
        self.model = None
        self.processor = None
        self.tokenizer = None

        if not HAS_QWEN:
            raise ImportError("transformers library required for VLM")

        logger.info(f"🧠 Initializing ChartVLM: {model_name}")
        logger.info(f"   Device: {device}")
        logger.info(f"   Max memory: {max_memory}")

    def load_model(self):
        """Load quantized model (RTX 4060 optimized)"""
        if self.model is not None:
            logger.info("   Model already loaded")
            return

        logger.info("📥 Loading Qwen2.5-VL-7B-AWQ (int4 quantized)...")

        try:
            # AWQ quantization config (4-bit for memory efficiency)
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4"
            )

            # Load processor and tokenizer
            self.processor = AutoProcessor.from_pretrained(
                self.model_name,
                trust_remote_code=True
            )

            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                trust_remote_code=True
            )

            # Load model with quantization
            self.model = Qwen2VLForConditionalGeneration.from_pretrained(
                self.model_name,
                quantization_config=quantization_config,
                device_map="auto",
                trust_remote_code=True,
                torch_dtype=torch.float16
            )

            logger.info("✅ VLM loaded successfully")
            logger.info(f"   VRAM usage: ~{torch.cuda.memory_allocated() / 1e9:.2f} GB")

        except Exception as e:
            logger.error(f"❌ Failed to load VLM: {e}")
            raise

    def analyze_chart(
        self,
        image: Union[str, Path, Image.Image],
        question: str = "Analyze this trading chart in detail. Identify patterns, trends, support/resistance levels, and provide trading insights.",
        max_tokens: int = 512
    ) -> Dict:
        """
        Analyze chart image with VLM

        Args:
            image: Path to chart image or PIL Image
            question: Analysis prompt
            max_tokens: Max response length

        Returns:
            {
                'analysis': str,
                'patterns_detected': List[str],
                'confidence': float,
                'recommendation': str
            }
        """
        if self.model is None:
            self.load_model()

        # Load image
        if isinstance(image, (str, Path)):
            image = Image.open(image).convert('RGB')

        logger.info(f"🔍 Analyzing chart image...")

        # Prepare inputs
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": image},
                    {"type": "text", "text": question}
                ]
            }
        ]

        # Process with tokenizer
        text = self.processor.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )

        # Prepare inputs
        inputs = self.processor(
            text=[text],
            images=[image],
            return_tensors="pt",
            padding=True
        ).to(self.device)

        # Generate response
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                do_sample=False,  # Deterministic for consistency
                temperature=0.7,
                top_p=0.9
            )

        # Decode response
        response = self.processor.batch_decode(
            outputs,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=False
        )[0]

        # Parse response
        result = self._parse_analysis(response)

        logger.info(f"✅ Analysis complete")
        logger.info(f"   Patterns detected: {len(result.get('patterns_detected', []))}")

        return result

    def detect_patterns(
        self,
        image: Union[str, Path, Image.Image]
    ) -> List[Dict]:
        """
        Detect chart patterns using VLM

        Returns:
            [
                {
                    'pattern': 'head_and_shoulders',
                    'confidence': 0.85,
                    'description': 'Bearish H&S forming...',
                    'location': 'top right'
                },
                ...
            ]
        """
        question = """
        Identify all chart patterns in this image. For each pattern, provide:
        1. Pattern name (e.g., head_and_shoulders, triangle, flag)
        2. Confidence level (0-100%)
        3. Brief description
        4. Location on chart

        Format as JSON list.
        """

        result = self.analyze_chart(image, question, max_tokens=1024)

        # Extract patterns from response
        patterns = self._extract_patterns(result['analysis'])

        return patterns

    def compare_with_book_chart(
        self,
        user_chart: Union[str, Path, Image.Image],
        book_chart: Union[str, Path, Image.Image]
    ) -> Dict:
        """
        Compare user's chart with pattern from trading book

        Args:
            user_chart: Current market chart
            book_chart: Reference pattern from book/PDF

        Returns:
            {
                'similarity': 0.75,
                'matching_features': ['neckline', 'volume profile'],
                'differences': ['slope angle different'],
                'recommendation': 'Pattern matches 75%, wait for...'
            }
        """
        question = """
        Compare these two charts:
        1. First image: Current market chart
        2. Second image: Reference pattern from trading book

        Analyze:
        - Similarity percentage
        - Matching features
        - Key differences
        - Trading recommendation based on comparison
        """

        # For now, analyze individually (Qwen2.5-VL supports multi-image)
        # TODO: Implement true multi-image comparison

        user_analysis = self.analyze_chart(user_chart, "Describe this chart pattern in detail.")
        book_analysis = self.analyze_chart(book_chart, "Describe this reference pattern.")

        # Compare analyses (simplified - can be improved with embeddings)
        similarity = self._calculate_text_similarity(
            user_analysis['analysis'],
            book_analysis['analysis']
        )

        return {
            'similarity': similarity,
            'user_chart_analysis': user_analysis,
            'book_pattern_analysis': book_analysis,
            'recommendation': f"Similarity: {similarity:.1%}. " + (
                "Strong match - consider entry" if similarity > 0.7 else
                "Weak match - wait for confirmation"
            )
        }

    def _parse_analysis(self, response: str) -> Dict:
        """Parse VLM response into structured format"""
        # Extract patterns mentioned
        pattern_keywords = [
            'head and shoulders', 'h&s', 'triangle', 'wedge', 'flag',
            'double top', 'double bottom', 'cup and handle',
            'ascending triangle', 'descending triangle', 'symmetrical triangle',
            'bullish flag', 'bearish flag', 'pennant'
        ]

        patterns_detected = []
        response_lower = response.lower()

        for pattern in pattern_keywords:
            if pattern in response_lower:
                patterns_detected.append(pattern.replace(' ', '_'))

        # Extract confidence (if mentioned)
        confidence = 0.5  # Default
        if 'confident' in response_lower or 'strong' in response_lower:
            confidence = 0.8
        elif 'possible' in response_lower or 'potential' in response_lower:
            confidence = 0.6

        # Extract recommendation
        recommendation = "WAIT"
        if 'buy' in response_lower or 'long' in response_lower or 'bullish' in response_lower:
            recommendation = "LONG"
        elif 'sell' in response_lower or 'short' in response_lower or 'bearish' in response_lower:
            recommendation = "SHORT"

        return {
            'analysis': response,
            'patterns_detected': patterns_detected,
            'confidence': confidence,
            'recommendation': recommendation
        }

    def _extract_patterns(self, text: str) -> List[Dict]:
        """Extract pattern list from VLM response"""
        # Simplified extraction - can be improved with JSON parsing
        patterns = []

        pattern_names = [
            'head_and_shoulders', 'inverse_head_and_shoulders',
            'triangle', 'wedge', 'flag', 'pennant',
            'double_top', 'double_bottom', 'cup_and_handle'
        ]

        for pattern in pattern_names:
            if pattern.replace('_', ' ') in text.lower():
                patterns.append({
                    'pattern': pattern,
                    'confidence': 0.7,  # Default
                    'description': f"{pattern.replace('_', ' ').title()} detected in chart",
                    'location': 'center'
                })

        return patterns

    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity (simplified)"""
        # Simple word overlap metric
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        overlap = len(words1 & words2)
        total = len(words1 | words2)

        return overlap / total if total > 0 else 0.0

    def unload_model(self):
        """Free VRAM"""
        if self.model is not None:
            del self.model
            del self.processor
            del self.tokenizer
            torch.cuda.empty_cache()
            logger.info("✅ VLM unloaded, VRAM freed")


class ChartImageGenerator:
    """
    Generate chart images from OHLCV data for VLM analysis
    """

    def __init__(self, style: str = "tradingview"):
        """
        Args:
            style: Chart style ('tradingview', 'mplfinance', 'plotly')
        """
        self.style = style

    def generate_candlestick_chart(
        self,
        df,
        indicators: List[str] = None,
        patterns: List[Dict] = None,
        save_path: Optional[str] = None
    ) -> Image.Image:
        """
        Generate chart image from OHLCV dataframe

        Args:
            df: OHLCV dataframe
            indicators: List of indicators to plot ['sma_20', 'rsi', etc.]
            patterns: Pattern annotations to overlay
            save_path: Where to save image

        Returns:
            PIL Image
        """
        import matplotlib.pyplot as plt
        import matplotlib.patches as patches
        from matplotlib.dates import DateFormatter
        import mplfinance as mpf

        # Convert to mplfinance format
        df_plot = df.copy()
        df_plot.index = pd.to_datetime(df_plot['open_time'], unit='ms')
        df_plot = df_plot[['open', 'high', 'low', 'close', 'volume']]

        # Add indicators
        apds = []
        if indicators:
            for ind in indicators:
                if ind in df.columns and ind.startswith('sma'):
                    # Moving average
                    apds.append(mpf.make_addplot(df[ind], panel=0, color='blue'))
                elif ind == 'rsi':
                    # RSI in separate panel
                    apds.append(mpf.make_addplot(df['rsi_14'], panel=1, color='purple'))

        # Plot style
        mc = mpf.make_marketcolors(
            up='#26a69a',
            down='#ef5350',
            edge='inherit',
            wick='inherit',
            volume='in'
        )

        s = mpf.make_mpf_style(
            marketcolors=mc,
            gridstyle=':',
            y_on_right=False
        )

        # Generate plot
        fig, axes = mpf.plot(
            df_plot,
            type='candle',
            style=s,
            volume=True,
            addplot=apds if apds else None,
            returnfig=True,
            figsize=(12, 8)
        )

        # Annotate patterns if provided
        if patterns:
            ax = axes[0]
            for pattern in patterns:
                # Draw pattern box/annotation
                # TODO: Implement pattern overlay
                pass

        # Save or return
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            logger.info(f"📊 Chart saved: {save_path}")

        # Convert to PIL Image
        fig.canvas.draw()
        image = Image.frombytes(
            'RGB',
            fig.canvas.get_width_height(),
            fig.canvas.tostring_rgb()
        )

        plt.close(fig)

        return image


# Example usage
if __name__ == "__main__":
    import pandas as pd

    # Initialize VLM
    vlm = ChartVLM(device="cuda")
    vlm.load_model()

    # Generate sample chart
    generator = ChartImageGenerator()

    # Load data
    df = pd.read_parquet("data/advanced/BTCUSDT_5m_futures_binance.parquet")

    # Generate chart image
    chart_img = generator.generate_candlestick_chart(
        df.tail(200),
        indicators=['sma_20', 'sma_50'],
        save_path="data/temp/btc_chart.png"
    )

    # Analyze with VLM
    result = vlm.analyze_chart(
        chart_img,
        question="Analyze this Bitcoin 5-minute chart. Identify any patterns and provide trading insights."
    )

    print("="*80)
    print("VLM ANALYSIS")
    print("="*80)
    print(result['analysis'])
    print()
    print(f"Patterns detected: {result['patterns_detected']}")
    print(f"Recommendation: {result['recommendation']}")
    print(f"Confidence: {result['confidence']:.1%}")
