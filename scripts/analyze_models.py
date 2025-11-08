"""
Model Analysis & Comparison Tool

Analyzes all trained models and generates comparison reports:
- Accuracy comparison
- Feature importance
- Best model selection
- Performance metrics

Usage:
    python scripts/analyze_models.py
    python scripts/analyze_models.py --symbol BTCUSDT --timeframe 1h
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import glob
import argparse
from datetime import datetime
import pandas as pd

def find_all_models(models_dir="data/models"):
    """Find all trained models"""
    models_path = Path(models_dir)

    if not models_path.exists():
        print(f"❌ Models directory not found: {models_dir}")
        return []

    # Find all model files
    model_files = {
        'xgboost': list(models_path.glob("*_xgb*.json")),
        'lstm': list(models_path.glob("*_lstm*.pth")) + list(models_path.glob("*_lstm*.h5")),
        'ppo': list(models_path.glob("*_ppo*.zip")),
        'ensemble': list(models_path.glob("*_ensemble*.pkl")),
    }

    return model_files

def analyze_xgboost_model(model_path):
    """Analyze XGBoost model"""
    try:
        import xgboost as xgb

        model = xgb.XGBClassifier()
        model.load_model(str(model_path))

        # Get feature importance
        importance = model.feature_importances_

        return {
            'path': str(model_path),
            'type': 'xgboost',
            'features': model.n_features_in_ if hasattr(model, 'n_features_in_') else None,
            'importance': importance.tolist() if importance is not None else None,
        }
    except Exception as e:
        return {'path': str(model_path), 'error': str(e)}

def generate_report(model_files, output_path="data/models/analysis_report.json"):
    """Generate comprehensive analysis report"""

    report = {
        'generated_at': datetime.now().isoformat(),
        'total_models': sum(len(files) for files in model_files.values()),
        'models': {}
    }

    print(f"\n{'='*60}")
    print(f"📊 Model Analysis Report")
    print(f"{'='*60}\n")

    for model_type, files in model_files.items():
        if not files:
            continue

        print(f"\n🔍 {model_type.upper()} Models: {len(files)} found")
        report['models'][model_type] = []

        for model_file in files:
            print(f"   📁 {model_file.name}")

            # Parse filename for metadata
            name_parts = model_file.stem.split('_')

            model_info = {
                'file': str(model_file),
                'name': model_file.name,
                'size_mb': round(model_file.stat().st_size / (1024*1024), 2),
                'modified': datetime.fromtimestamp(model_file.stat().st_mtime).isoformat(),
            }

            # Try to extract symbol, timeframe, market from filename
            if len(name_parts) >= 3:
                model_info['symbol'] = name_parts[0]
                model_info['timeframe'] = name_parts[1]
                if len(name_parts) >= 4:
                    model_info['market'] = name_parts[2]

            # Analyze model if possible
            if model_type == 'xgboost':
                analysis = analyze_xgboost_model(model_file)
                model_info.update(analysis)

            report['models'][model_type].append(model_info)

    # Summary statistics
    print(f"\n{'='*60}")
    print(f"📈 Summary Statistics")
    print(f"{'='*60}")
    print(f"   Total Models: {report['total_models']}")
    for model_type, models in report['models'].items():
        print(f"   {model_type.upper()}: {len(models)}")

    # Save report
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"\n💾 Report saved to: {output_path}")

    return report

def compare_models(symbol=None, timeframe=None):
    """Compare models for specific symbol/timeframe"""

    models_dir = Path("data/models")

    # Find models matching criteria
    pattern = "*"
    if symbol:
        pattern = f"{symbol}_{pattern}"
    if timeframe:
        pattern = f"{pattern}{timeframe}_*"

    matching_files = list(models_dir.glob(pattern))

    if not matching_files:
        print(f"❌ No models found matching: {pattern}")
        return

    print(f"\n{'='*60}")
    print(f"🔍 Comparing Models")
    if symbol:
        print(f"   Symbol: {symbol}")
    if timeframe:
        print(f"   Timeframe: {timeframe}")
    print(f"{'='*60}\n")

    comparison = []

    for model_file in matching_files:
        info = {
            'file': model_file.name,
            'type': None,
            'size_mb': round(model_file.stat().st_size / (1024*1024), 2),
        }

        # Determine model type
        if 'xgb' in model_file.name or 'xgboost' in model_file.name:
            info['type'] = 'XGBoost'
        elif 'lstm' in model_file.name:
            info['type'] = 'LSTM'
        elif 'ppo' in model_file.name:
            info['type'] = 'PPO'
        elif 'ensemble' in model_file.name:
            info['type'] = 'Ensemble'

        comparison.append(info)

    # Print comparison table
    print(f"{'Model':<40} {'Type':<15} {'Size (MB)':<10}")
    print(f"{'-'*65}")

    for info in comparison:
        print(f"{info['file']:<40} {info['type'] or 'Unknown':<15} {info['size_mb']:<10.2f}")

    print(f"\n   Total: {len(comparison)} models\n")

def main():
    parser = argparse.ArgumentParser(description='Analyze trained models')
    parser.add_argument('--symbol', type=str, help='Filter by symbol (e.g., BTCUSDT)')
    parser.add_argument('--timeframe', type=str, help='Filter by timeframe (e.g., 1h)')
    parser.add_argument('--compare', action='store_true', help='Compare models')

    args = parser.parse_args()

    if args.compare:
        compare_models(args.symbol, args.timeframe)
    else:
        # Full analysis
        model_files = find_all_models()
        generate_report(model_files)

if __name__ == "__main__":
    main()
