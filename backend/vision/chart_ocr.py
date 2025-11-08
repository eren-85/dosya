"""
Chart OCR System using PaddleOCR
Extracts text from chart images (prices, indicators, annotations)

Optimized for CPU (Windows compatible)
Multi-language support (EN, TR, etc.)

Use Cases:
- Extract price labels from charts
- Read indicator values
- Parse chart annotations
- Extract text from trading book screenshots
"""

from typing import List, Dict, Tuple, Union, Optional
from pathlib import Path
import numpy as np
from PIL import Image
import logging

logger = logging.getLogger(__name__)

try:
    from paddleocr import PaddleOCR
    HAS_PADDLE = True
except ImportError:
    logger.warning("paddleocr not installed. OCR features disabled.")
    HAS_PADDLE = False


class ChartOCR:
    """
    OCR system for extracting text from chart images

    Uses PaddleOCR (CPU-optimized, multi-language)
    """

    def __init__(
        self,
        lang: str = 'en',
        use_gpu: bool = False,
        show_log: bool = False
    ):
        """
        Initialize OCR

        Args:
            lang: Language code ('en', 'tr', 'ch', etc.)
            use_gpu: Use GPU (False recommended for Windows compatibility)
            show_log: Show PaddleOCR logs
        """
        self.lang = lang
        self.use_gpu = use_gpu
        self.ocr = None

        if not HAS_PADDLE:
            raise ImportError("paddleocr library required for OCR")

        logger.info(f"📝 Initializing PaddleOCR")
        logger.info(f"   Language: {lang}")
        logger.info(f"   Device: {'GPU' if use_gpu else 'CPU'}")

        # Initialize PaddleOCR
        self.ocr = PaddleOCR(
            use_angle_cls=True,
            lang=lang,
            use_gpu=use_gpu,
            show_log=show_log
        )

        logger.info("✅ OCR initialized")

    def extract_text(
        self,
        image: Union[str, Path, Image.Image, np.ndarray],
        confidence_threshold: float = 0.5
    ) -> List[Dict]:
        """
        Extract text from chart image

        Args:
            image: Image (path, PIL, or numpy)
            confidence_threshold: Min confidence for text detection

        Returns:
            [
                {
                    'text': 'BTC/USDT 67,234.50',
                    'confidence': 0.95,
                    'bbox': [[x1,y1], [x2,y2], [x3,y3], [x4,y4]],
                    'position': 'top_left'
                },
                ...
            ]
        """
        logger.info(f"📝 Extracting text from image...")

        # Convert to numpy if needed
        if isinstance(image, (str, Path)):
            img = np.array(Image.open(image).convert('RGB'))
        elif isinstance(image, Image.Image):
            img = np.array(image.convert('RGB'))
        else:
            img = image

        # Run OCR
        result = self.ocr.ocr(img, cls=True)

        # Parse results
        texts = []

        if result and result[0]:
            for line in result[0]:
                # line format: [bbox, (text, confidence)]
                bbox = line[0]
                text_info = line[1]
                text = text_info[0]
                confidence = text_info[1]

                if confidence >= confidence_threshold:
                    # Calculate position
                    position = self._get_text_position(bbox, img.shape)

                    texts.append({
                        'text': text,
                        'confidence': float(confidence),
                        'bbox': [[float(x), float(y)] for x, y in bbox],
                        'position': position
                    })

        logger.info(f"✅ Extracted {len(texts)} text elements")

        return texts

    def extract_prices(
        self,
        image: Union[str, Path, Image.Image, np.ndarray]
    ) -> List[Dict]:
        """
        Extract price values from chart

        Returns:
            [
                {
                    'price': 67234.50,
                    'formatted': '67,234.50',
                    'confidence': 0.95,
                    'position': 'right_axis'
                },
                ...
            ]
        """
        texts = self.extract_text(image)

        prices = []

        for item in texts:
            text = item['text']

            # Try to parse as price
            price_val = self._parse_price(text)

            if price_val is not None:
                prices.append({
                    'price': price_val,
                    'formatted': text,
                    'confidence': item['confidence'],
                    'position': item['position']
                })

        logger.info(f"💰 Extracted {len(prices)} price values")

        return prices

    def extract_indicators(
        self,
        image: Union[str, Path, Image.Image, np.ndarray]
    ) -> Dict[str, float]:
        """
        Extract indicator values from chart

        Returns:
            {
                'RSI': 67.5,
                'MACD': 123.4,
                'Volume': 1234567.0
            }
        """
        texts = self.extract_text(image)

        indicators = {}

        # Known indicator keywords
        indicator_keywords = [
            'RSI', 'MACD', 'MA', 'EMA', 'SMA',
            'Volume', 'Vol', 'ATR', 'Stoch', 'BB'
        ]

        for item in texts:
            text = item['text']

            # Check for indicator names
            for keyword in indicator_keywords:
                if keyword.upper() in text.upper():
                    # Try to extract numeric value
                    value = self._extract_number(text)

                    if value is not None:
                        indicators[keyword] = value

        logger.info(f"📊 Extracted {len(indicators)} indicator values")

        return indicators

    def _parse_price(self, text: str) -> Optional[float]:
        """Parse price from text"""
        import re

        # Remove common symbols
        text = text.replace(',', '').replace('$', '').replace('₺', '').replace('€', '')

        # Try to find number
        match = re.search(r'[\d,]+\.?\d*', text)

        if match:
            try:
                return float(match.group().replace(',', ''))
            except:
                pass

        return None

    def _extract_number(self, text: str) -> Optional[float]:
        """Extract numeric value from text"""
        import re

        # Find number pattern
        match = re.search(r'-?[\d,]+\.?\d*', text)

        if match:
            try:
                return float(match.group().replace(',', ''))
            except:
                pass

        return None

    def _get_text_position(self, bbox: List[List[float]], img_shape: Tuple) -> str:
        """Determine text position on image"""
        height, width = img_shape[:2]

        # Get center of bbox
        center_x = sum(p[0] for p in bbox) / 4
        center_y = sum(p[1] for p in bbox) / 4

        # Divide image into regions
        x_region = 'left' if center_x < width / 3 else ('center' if center_x < 2 * width / 3 else 'right')
        y_region = 'top' if center_y < height / 3 else ('middle' if center_y < 2 * height / 3 else 'bottom')

        return f"{y_region}_{x_region}"


class LayoutAnalyzer:
    """
    Layout analysis for PDFs and chart images
    Uses LayoutParser + PubLayNet detector
    """

    def __init__(self, model: str = "lp://PubLayNet/faster_rcnn_R_50_FPN_3x/config"):
        """
        Initialize layout analyzer

        Args:
            model: LayoutParser model ID
        """
        self.model_name = model
        self.model = None

        logger.info(f"📄 Initializing LayoutParser")
        logger.info(f"   Model: {model}")

        try:
            import layoutparser as lp
            self.lp = lp
            HAS_LAYOUT = True
        except ImportError:
            logger.warning("layoutparser not installed. Layout analysis disabled.")
            HAS_LAYOUT = False
            return

        # Load model
        self.model = lp.Detectron2LayoutModel(
            model,
            extra_config=["MODEL.ROI_HEADS.SCORE_THRESH_TEST", 0.8],
            label_map={0: "Text", 1: "Title", 2: "List", 3: "Table", 4: "Figure"}
        )

        logger.info("✅ LayoutParser initialized")

    def analyze_page(
        self,
        image: Union[str, Path, Image.Image, np.ndarray]
    ) -> Dict:
        """
        Analyze page layout (PDF page or chart image)

        Returns:
            {
                'text_blocks': [...],
                'titles': [...],
                'figures': [...],  # Charts!
                'tables': [...]
            }
        """
        if self.model is None:
            raise RuntimeError("LayoutParser not initialized")

        logger.info(f"📄 Analyzing page layout...")

        # Convert to numpy
        if isinstance(image, (str, Path)):
            img = np.array(Image.open(image).convert('RGB'))
        elif isinstance(image, Image.Image):
            img = np.array(image.convert('RGB'))
        else:
            img = image

        # Detect layout
        layout = self.model.detect(img)

        # Group by type
        result = {
            'text_blocks': [],
            'titles': [],
            'figures': [],
            'tables': [],
            'lists': []
        }

        for block in layout:
            block_info = {
                'bbox': [
                    float(block.block.x_1),
                    float(block.block.y_1),
                    float(block.block.x_2),
                    float(block.block.y_2)
                ],
                'confidence': float(block.score),
                'type': block.type
            }

            if block.type == 'Text':
                result['text_blocks'].append(block_info)
            elif block.type == 'Title':
                result['titles'].append(block_info)
            elif block.type == 'Figure':
                result['figures'].append(block_info)
            elif block.type == 'Table':
                result['tables'].append(block_info)
            elif block.type == 'List':
                result['lists'].append(block_info)

        logger.info(f"✅ Layout analysis complete")
        logger.info(f"   Text blocks: {len(result['text_blocks'])}")
        logger.info(f"   Titles: {len(result['titles'])}")
        logger.info(f"   Figures: {len(result['figures'])}")
        logger.info(f"   Tables: {len(result['tables'])}")

        return result

    def extract_charts_from_pdf(
        self,
        pdf_path: str,
        page_range: Optional[Tuple[int, int]] = None
    ) -> List[Dict]:
        """
        Extract chart images from PDF (trading books)

        Args:
            pdf_path: Path to PDF file
            page_range: (start, end) page numbers (None = all pages)

        Returns:
            [
                {
                    'page': 5,
                    'chart_image': PIL.Image,
                    'bbox': [x1, y1, x2, y2],
                    'caption': 'Head and Shoulders pattern'
                },
                ...
            ]
        """
        import pdf2image

        logger.info(f"📖 Extracting charts from PDF: {pdf_path}")

        # Convert PDF to images
        if page_range:
            images = pdf2image.convert_from_path(
                pdf_path,
                first_page=page_range[0],
                last_page=page_range[1]
            )
        else:
            images = pdf2image.convert_from_path(pdf_path)

        charts = []

        for page_num, page_img in enumerate(images, start=1):
            # Analyze layout
            layout = self.analyze_page(page_img)

            # Extract figure regions (charts)
            for figure in layout['figures']:
                x1, y1, x2, y2 = figure['bbox']

                # Crop chart region
                chart_img = page_img.crop((x1, y1, x2, y2))

                charts.append({
                    'page': page_num,
                    'chart_image': chart_img,
                    'bbox': figure['bbox'],
                    'confidence': figure['confidence'],
                    'caption': None  # Can be extracted with OCR
                })

        logger.info(f"✅ Extracted {len(charts)} charts from {len(images)} pages")

        return charts


# Example usage
if __name__ == "__main__":
    # Initialize OCR
    ocr = ChartOCR(lang='en', use_gpu=False)

    # Extract text from chart
    texts = ocr.extract_text("data/temp/btc_chart.png")

    for text in texts:
        print(f"Text: {text['text']}")
        print(f"Confidence: {text['confidence']:.2%}")
        print(f"Position: {text['position']}")
        print()

    # Extract prices
    prices = ocr.extract_prices("data/temp/btc_chart.png")

    for price in prices:
        print(f"Price: ${price['price']:,.2f}")
        print(f"Position: {price['position']}")
        print()

    # Extract indicators
    indicators = ocr.extract_indicators("data/temp/btc_chart.png")
    print("Indicators:", indicators)

    # Layout analysis
    # analyzer = LayoutAnalyzer()
    # charts = analyzer.extract_charts_from_pdf("data/books/technical_analysis.pdf")
