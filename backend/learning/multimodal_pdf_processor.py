"""
Multimodal PDF Processor
Extracts text, images, and creates knowledge base from trading PDFs

Stack:
- PyMuPDF (fitz) for PDF processing
- PaddleOCR for scanned pages
- Text-Image matching for pattern recognition
"""

import fitz  # PyMuPDF
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import json
from datetime import datetime
import base64
from io import BytesIO
from PIL import Image


class MultimodalPDFProcessor:
    """
    Process trading PDFs to extract:
    - Text content (strategies, rules, psychology)
    - Chart images (patterns, examples)
    - Text-Image relationships ("Figure 3 shows...")
    """

    def __init__(self, output_dir: str = "./data/knowledge"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories
        self.charts_dir = self.output_dir / "charts"
        self.charts_dir.mkdir(exist_ok=True)

        self.texts_dir = self.output_dir / "texts"
        self.texts_dir.mkdir(exist_ok=True)

        # Knowledge base
        self.knowledge_base = []

    def process_pdf(
        self,
        pdf_path: str,
        max_pages: Optional[int] = None,
        extract_images: bool = True,
        use_ocr: bool = False
    ) -> Dict:
        """
        Process PDF and extract all content

        Args:
            pdf_path: Path to PDF file
            max_pages: Maximum pages to process (None = all)
            extract_images: Extract chart images
            use_ocr: Use OCR for scanned pages

        Returns:
            {
                'pages_processed': int,
                'text_chunks': int,
                'images_extracted': int,
                'patterns_found': List[str]
            }
        """
        print(f"📖 Processing PDF: {pdf_path}")

        pdf = fitz.open(pdf_path)
        total_pages = len(pdf)
        pages_to_process = min(total_pages, max_pages) if max_pages else total_pages

        print(f"   Total pages: {total_pages}")
        print(f"   Processing: {pages_to_process} pages")

        stats = {
            'pages_processed': 0,
            'text_chunks': 0,
            'images_extracted': 0,
            'patterns_found': []
        }

        for page_num in range(pages_to_process):
            page = pdf[page_num]

            # Extract text
            text = page.get_text()

            # If minimal text and OCR enabled, use OCR
            if len(text.strip()) < 50 and use_ocr:
                text = self._ocr_page(page)

            # Extract images
            images = []
            if extract_images:
                images = self._extract_images(page, page_num)
                stats['images_extracted'] += len(images)

            # Find pattern references in text
            patterns = self._find_pattern_references(text)
            stats['patterns_found'].extend(patterns)

            # Create knowledge entry
            if text.strip() or images:
                entry = self._create_knowledge_entry(
                    page_num=page_num,
                    text=text,
                    images=images,
                    patterns=patterns
                )
                self.knowledge_base.append(entry)
                stats['text_chunks'] += 1

            stats['pages_processed'] += 1

            # Progress
            if (page_num + 1) % 50 == 0:
                print(f"   Processed {page_num + 1}/{pages_to_process} pages...")

        pdf.close()

        # Save knowledge base
        self._save_knowledge_base()

        print(f"\n✅ Processing complete!")
        print(f"   Pages: {stats['pages_processed']}")
        print(f"   Text chunks: {stats['text_chunks']}")
        print(f"   Images: {stats['images_extracted']}")
        print(f"   Unique patterns: {len(set(stats['patterns_found']))}")

        return stats

    def _extract_images(self, page, page_num: int) -> List[Dict]:
        """Extract images from page and save them"""
        images = []
        image_list = page.get_images()

        for img_index, img_info in enumerate(image_list):
            try:
                xref = img_info[0]
                base_image = page.parent.extract_image(xref)

                # Save image
                image_filename = f"page_{page_num + 1}_img_{img_index + 1}.png"
                image_path = self.charts_dir / image_filename

                with open(image_path, 'wb') as img_file:
                    img_file.write(base_image["image"])

                images.append({
                    'filename': image_filename,
                    'path': str(image_path),
                    'index': img_index,
                    'format': base_image.get("ext", "png"),
                    'width': base_image.get("width", 0),
                    'height': base_image.get("height", 0)
                })

            except Exception as e:
                print(f"      ⚠️  Error extracting image {img_index} from page {page_num + 1}: {e}")

        return images

    def _ocr_page(self, page) -> str:
        """Use PaddleOCR on scanned page"""
        try:
            from paddleocr import PaddleOCR

            # Convert page to image
            pix = page.get_pixmap()
            img_bytes = pix.tobytes("png")
            img = Image.open(BytesIO(img_bytes))

            # OCR
            ocr = PaddleOCR(use_angle_cls=True, lang='en', use_gpu=False)
            result = ocr.ocr(img_bytes)

            # Extract text
            text = ""
            if result and result[0]:
                for line in result[0]:
                    text += line[1][0] + "\n"

            return text

        except Exception as e:
            print(f"      ⚠️  OCR failed: {e}")
            return ""

    def _find_pattern_references(self, text: str) -> List[str]:
        """Find chart pattern names in text"""
        patterns = [
            'head and shoulders', 'double top', 'double bottom',
            'triangle', 'wedge', 'flag', 'pennant',
            'ascending triangle', 'descending triangle',
            'bullish', 'bearish', 'reversal', 'continuation',
            'support', 'resistance', 'breakout', 'breakdown',
            'cup and handle', 'rounding bottom', 'rounding top',
            'gap', 'island reversal', 'engulfing'
        ]

        found = []
        text_lower = text.lower()

        for pattern in patterns:
            if pattern in text_lower:
                found.append(pattern)

        return list(set(found))  # Unique

    def _create_knowledge_entry(
        self,
        page_num: int,
        text: str,
        images: List[Dict],
        patterns: List[str]
    ) -> Dict:
        """Create structured knowledge entry"""
        return {
            'page': page_num + 1,
            'text': text.strip(),
            'text_length': len(text.strip()),
            'images': images,
            'patterns_mentioned': patterns,
            'timestamp': datetime.now().isoformat()
        }

    def _save_knowledge_base(self):
        """Save knowledge base to JSON"""
        kb_path = self.output_dir / "knowledge_base.json"

        with open(kb_path, 'w', encoding='utf-8') as f:
            json.dump(self.knowledge_base, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Knowledge base saved: {kb_path}")

    def get_pattern_examples(self, pattern_name: str) -> List[Dict]:
        """Query knowledge base for specific pattern examples"""
        results = []

        for entry in self.knowledge_base:
            if pattern_name.lower() in [p.lower() for p in entry['patterns_mentioned']]:
                results.append(entry)

        return results

    def get_charts_by_page(self, page_num: int) -> List[str]:
        """Get all chart images from a specific page"""
        for entry in self.knowledge_base:
            if entry['page'] == page_num:
                return [img['path'] for img in entry['images']]
        return []


if __name__ == "__main__":
    # Test with 1.pdf
    processor = MultimodalPDFProcessor(output_dir="./data/knowledge")

    # Process first 100 pages as test
    stats = processor.process_pdf(
        pdf_path="/home/user/dosya/1.pdf",
        max_pages=100,  # Test with 100 pages first
        extract_images=True,
        use_ocr=False  # Enable if needed
    )

    print(f"\n📊 Stats: {stats}")

    # Example: Find head and shoulders patterns
    hs_examples = processor.get_pattern_examples("head and shoulders")
    print(f"\n🔍 Found {len(hs_examples)} pages mentioning 'head and shoulders'")
