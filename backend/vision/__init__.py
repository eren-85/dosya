"""
Vision Module - Multi-Modal Chart Analysis
RTX 4060 optimized

Components:
- ChartVLM: Qwen2.5-VL-7B for visual reasoning
- ChartPatternDetector: YOLOv8 for pattern detection
- ChartOCR: PaddleOCR for text extraction
- LayoutAnalyzer: PDF layout analysis

Usage:
    from backend.vision import ChartVLM, ChartPatternDetector, ChartOCR
"""

from .chart_vlm import ChartVLM, ChartImageGenerator
from .yolo_patterns import ChartPatternDetector, PatternDatasetBuilder
from .chart_ocr import ChartOCR, LayoutAnalyzer

__all__ = [
    'ChartVLM',
    'ChartImageGenerator',
    'ChartPatternDetector',
    'PatternDatasetBuilder',
    'ChartOCR',
    'LayoutAnalyzer',
]
