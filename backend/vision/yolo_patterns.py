"""
YOLOv8 Pattern Detection for Chart Analysis
RTX 4060 optimized - YOLOv8n/s (lightweight)

Detects:
- Head & Shoulders (bullish/bearish)
- Triangles (ascending, descending, symmetrical)
- Wedges (rising, falling)
- Flags & Pennants
- Double tops/bottoms
- Cup & Handle
- Harmonic patterns (Gartley, Butterfly, Bat, Crab)

Training:
- Train on labeled chart images
- Use data augmentation
- Export to ONNX for fast inference
"""

import torch
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import numpy as np
from PIL import Image
import logging

logger = logging.getLogger(__name__)

try:
    from ultralytics import YOLO
    HAS_YOLO = True
except ImportError:
    logger.warning("ultralytics not installed. YOLO features disabled.")
    HAS_YOLO = False


class ChartPatternDetector:
    """
    YOLOv8-based chart pattern detection

    Pattern Classes:
        0: head_and_shoulders
        1: inverse_head_and_shoulders
        2: ascending_triangle
        3: descending_triangle
        4: symmetrical_triangle
        5: rising_wedge
        6: falling_wedge
        7: bull_flag
        8: bear_flag
        9: pennant
        10: double_top
        11: double_bottom
        12: cup_and_handle
        13: gartley (harmonic)
        14: butterfly (harmonic)
        15: bat (harmonic)
        16: crab (harmonic)
    """

    PATTERN_CLASSES = [
        'head_and_shoulders',
        'inverse_head_and_shoulders',
        'ascending_triangle',
        'descending_triangle',
        'symmetrical_triangle',
        'rising_wedge',
        'falling_wedge',
        'bull_flag',
        'bear_flag',
        'pennant',
        'double_top',
        'double_bottom',
        'cup_and_handle',
        'gartley',
        'butterfly',
        'bat',
        'crab'
    ]

    def __init__(
        self,
        model_path: str = "models/yolov8_patterns.pt",
        device: str = "cuda",
        confidence_threshold: float = 0.5
    ):
        """
        Initialize YOLO detector

        Args:
            model_path: Path to trained YOLOv8 model
            device: cuda or cpu
            confidence_threshold: Min confidence for detections
        """
        self.model_path = Path(model_path)
        self.device = device
        self.confidence_threshold = confidence_threshold
        self.model = None

        if not HAS_YOLO:
            raise ImportError("ultralytics library required for YOLO")

        logger.info(f"📊 Initializing YOLOv8 Pattern Detector")
        logger.info(f"   Model: {model_path}")
        logger.info(f"   Device: {device}")
        logger.info(f"   Confidence threshold: {confidence_threshold}")

    def load_model(self):
        """Load YOLO model"""
        if self.model is not None:
            logger.info("   Model already loaded")
            return

        if not self.model_path.exists():
            logger.warning(f"⚠️  Model not found: {self.model_path}")
            logger.warning("   Using pretrained YOLOv8n. Train custom model for best results.")
            # Use base YOLOv8n (will need training on patterns)
            self.model = YOLO('yolov8n.pt')
        else:
            logger.info(f"📥 Loading trained pattern detector...")
            self.model = YOLO(str(self.model_path))

        # Move to device
        self.model.to(self.device)

        logger.info(f"✅ YOLO model loaded")

    def detect_patterns(
        self,
        image: Union[str, Path, Image.Image, np.ndarray],
        visualize: bool = False
    ) -> List[Dict]:
        """
        Detect patterns in chart image

        Args:
            image: Chart image (path, PIL, or numpy array)
            visualize: Draw bounding boxes on image

        Returns:
            [
                {
                    'pattern': 'head_and_shoulders',
                    'confidence': 0.87,
                    'bbox': [x1, y1, x2, y2],
                    'center': (cx, cy),
                    'area': 12345
                },
                ...
            ]
        """
        if self.model is None:
            self.load_model()

        logger.info(f"🔍 Detecting patterns...")

        # Run inference
        results = self.model.predict(
            image,
            conf=self.confidence_threshold,
            device=self.device,
            verbose=False
        )

        # Parse results
        detections = []

        for result in results:
            boxes = result.boxes

            for i in range(len(boxes)):
                # Get box info
                box = boxes.xyxy[i].cpu().numpy()  # [x1, y1, x2, y2]
                confidence = float(boxes.conf[i].cpu())
                class_id = int(boxes.cls[i].cpu())

                # Pattern name
                pattern_name = self.PATTERN_CLASSES[class_id] if class_id < len(self.PATTERN_CLASSES) else f"class_{class_id}"

                # Calculate center and area
                x1, y1, x2, y2 = box
                center_x = (x1 + x2) / 2
                center_y = (y1 + y2) / 2
                area = (x2 - x1) * (y2 - y1)

                detection = {
                    'pattern': pattern_name,
                    'confidence': confidence,
                    'bbox': [float(x1), float(y1), float(x2), float(y2)],
                    'center': (float(center_x), float(center_y)),
                    'area': float(area)
                }

                detections.append(detection)

        logger.info(f"✅ Detected {len(detections)} patterns")

        # Visualize if requested
        if visualize and detections:
            annotated_img = self._draw_detections(image, detections)
            return detections, annotated_img

        return detections

    def train(
        self,
        data_yaml: str,
        epochs: int = 100,
        imgsz: int = 640,
        batch: int = 16,
        name: str = "pattern_detector"
    ):
        """
        Train YOLO model on pattern dataset

        Args:
            data_yaml: Path to dataset YAML config
            epochs: Training epochs
            imgsz: Image size (640 recommended)
            batch: Batch size (adjust for VRAM)
            name: Experiment name

        Dataset YAML format:
        ```yaml
        path: data/patterns
        train: images/train
        val: images/val

        nc: 17  # Number of classes
        names:
          0: head_and_shoulders
          1: inverse_head_and_shoulders
          ...
        ```
        """
        logger.info("="*80)
        logger.info("🎓 TRAINING YOLO PATTERN DETECTOR")
        logger.info("="*80)
        logger.info(f"Dataset: {data_yaml}")
        logger.info(f"Epochs: {epochs}")
        logger.info(f"Image size: {imgsz}")
        logger.info(f"Batch size: {batch}")
        logger.info("="*80)

        # Initialize model (YOLOv8n for speed on RTX 4060)
        if self.model is None:
            self.model = YOLO('yolov8n.pt')

        # Train
        results = self.model.train(
            data=data_yaml,
            epochs=epochs,
            imgsz=imgsz,
            batch=batch,
            name=name,
            device=self.device,
            patience=20,  # Early stopping
            save=True,
            save_period=10,
            plots=True,
            verbose=True
        )

        logger.info("="*80)
        logger.info("✅ TRAINING COMPLETE")
        logger.info("="*80)
        logger.info(f"Best model: runs/detect/{name}/weights/best.pt")
        logger.info("="*80)

        return results

    def export_onnx(self, output_path: str = "models/yolov8_patterns.onnx"):
        """Export model to ONNX for faster inference"""
        if self.model is None:
            self.load_model()

        logger.info(f"📤 Exporting to ONNX...")

        self.model.export(
            format='onnx',
            simplify=True,
            opset=12
        )

        logger.info(f"✅ ONNX model exported: {output_path}")

    def _draw_detections(self, image, detections: List[Dict]) -> Image.Image:
        """Draw bounding boxes and labels on image"""
        from PIL import ImageDraw, ImageFont

        # Load image
        if isinstance(image, (str, Path)):
            img = Image.open(image).convert('RGB')
        elif isinstance(image, np.ndarray):
            img = Image.fromarray(image)
        else:
            img = image.copy()

        draw = ImageDraw.Draw(img)

        # Try to load font
        try:
            font = ImageFont.truetype("arial.ttf", 16)
        except:
            font = ImageFont.load_default()

        # Color map
        colors = [
            '#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A',
            '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E2'
        ]

        for i, det in enumerate(detections):
            # Get bbox
            x1, y1, x2, y2 = det['bbox']

            # Color
            color = colors[i % len(colors)]

            # Draw box
            draw.rectangle([x1, y1, x2, y2], outline=color, width=3)

            # Draw label
            label = f"{det['pattern']} {det['confidence']:.2f}"
            draw.text((x1, y1 - 20), label, fill=color, font=font)

        return img


class PatternDatasetBuilder:
    """
    Helper to build YOLO training dataset from charts

    Workflow:
    1. Generate chart images from OHLCV data
    2. Manually label patterns (using labelImg or Roboflow)
    3. Split into train/val
    4. Create data.yaml
    """

    def __init__(self, output_dir: str = "data/patterns"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_sample_charts(
        self,
        data_dir: str = "data/advanced",
        num_samples: int = 1000,
        window_size: int = 200
    ):
        """
        Generate chart images from OHLCV data for labeling

        Args:
            data_dir: Directory with parquet files
            num_samples: Number of chart images to generate
            window_size: Number of candles per chart
        """
        import pandas as pd
        import random

        logger.info(f"📊 Generating {num_samples} chart samples...")

        # Get all parquet files
        parquet_files = list(Path(data_dir).glob("*.parquet"))

        if not parquet_files:
            logger.error(f"No parquet files found in {data_dir}")
            return

        images_dir = self.output_dir / "images"
        images_dir.mkdir(exist_ok=True)

        from backend.vision.chart_vlm import ChartImageGenerator
        generator = ChartImageGenerator()

        count = 0

        while count < num_samples:
            # Random file
            parquet_file = random.choice(parquet_files)

            # Load data
            df = pd.read_parquet(parquet_file)

            if len(df) < window_size + 100:
                continue

            # Random window
            start_idx = random.randint(0, len(df) - window_size - 1)
            window_df = df.iloc[start_idx:start_idx + window_size]

            # Generate chart
            img_path = images_dir / f"chart_{count:05d}.png"

            try:
                generator.generate_candlestick_chart(
                    window_df,
                    indicators=['sma_20', 'sma_50'],
                    save_path=str(img_path)
                )

                count += 1

                if count % 100 == 0:
                    logger.info(f"   Generated {count}/{num_samples} charts...")

            except Exception as e:
                logger.warning(f"Failed to generate chart: {e}")
                continue

        logger.info(f"✅ Generated {count} chart images")
        logger.info(f"📁 Saved to: {images_dir}")
        logger.info(f"\n📝 Next steps:")
        logger.info(f"   1. Label patterns using labelImg or Roboflow")
        logger.info(f"   2. Split into train/val")
        logger.info(f"   3. Create data.yaml")
        logger.info(f"   4. Train: detector.train('data.yaml')")

    def create_data_yaml(self, train_images: str, val_images: str):
        """Create YOLO data.yaml config"""
        yaml_content = f"""
# Chart Pattern Detection Dataset

path: {self.output_dir}
train: {train_images}
val: {val_images}

# Number of classes
nc: 17

# Class names
names:
  0: head_and_shoulders
  1: inverse_head_and_shoulders
  2: ascending_triangle
  3: descending_triangle
  4: symmetrical_triangle
  5: rising_wedge
  6: falling_wedge
  7: bull_flag
  8: bear_flag
  9: pennant
  10: double_top
  11: double_bottom
  12: cup_and_handle
  13: gartley
  14: butterfly
  15: bat
  16: crab
"""

        yaml_path = self.output_dir / "data.yaml"
        with open(yaml_path, 'w') as f:
            f.write(yaml_content)

        logger.info(f"✅ Created data.yaml: {yaml_path}")


# Example usage
if __name__ == "__main__":
    # Initialize detector
    detector = ChartPatternDetector(
        model_path="models/yolov8_patterns.pt",
        device="cuda",
        confidence_threshold=0.5
    )

    # Option 1: Detect patterns in existing chart
    detections = detector.detect_patterns(
        "data/temp/btc_chart.png",
        visualize=True
    )

    for det in detections:
        print(f"Pattern: {det['pattern']}")
        print(f"Confidence: {det['confidence']:.2%}")
        print(f"BBox: {det['bbox']}")
        print()

    # Option 2: Train custom model
    # builder = PatternDatasetBuilder()
    # builder.generate_sample_charts(num_samples=1000)
    # # ... label patterns manually ...
    # builder.create_data_yaml("images/train", "images/val")
    # detector.train("data/patterns/data.yaml", epochs=100)
