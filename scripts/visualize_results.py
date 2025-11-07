"""
Model Training Results Visualizer

Visualizes model training results with beautiful charts:
- Loss curves (train vs validation)
- Accuracy curves
- Feature importance
- Model comparison

Usage:
    python scripts/visualize_results.py
    python scripts/visualize_results.py --symbol BTCUSDT --timeframe 1h
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import argparse
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns

# Set style
sns.set_style("darkgrid")
plt.rcParams['figure.figsize'] = (14, 8)
plt.rcParams['font.size'] = 10

def load_training_logs(log_path):
    """Load training logs from JSON file"""
    try:
        with open(log_path, 'r') as f:
            logs = json.load(f)
        return logs
    except FileNotFoundError:
        print(f"❌ Log file not found: {log_path}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in {log_path}: {e}")
        return None

def plot_loss_curves(logs, output_path="data/models/visualizations/loss_curve.png"):
    """Plot training and validation loss curves"""

    if 'history' not in logs:
        print("⚠️  No training history found in logs")
        return

    history = logs['history']

    fig, ax = plt.subplots(figsize=(10, 6))

    # Plot train loss
    if 'train_loss' in history:
        ax.plot(history['train_loss'], label='Train Loss', linewidth=2, color='#3b82f6')

    # Plot val loss
    if 'val_loss' in history:
        ax.plot(history['val_loss'], label='Validation Loss', linewidth=2, color='#ef4444')

    ax.set_xlabel('Epoch', fontsize=12, fontweight='bold')
    ax.set_ylabel('Loss', fontsize=12, fontweight='bold')
    ax.set_title('Training & Validation Loss', fontsize=14, fontweight='bold')
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)

    # Save
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"✅ Loss curve saved: {output_path}")

def plot_accuracy_curves(logs, output_path="data/models/visualizations/accuracy_curve.png"):
    """Plot training and validation accuracy curves"""

    if 'history' not in logs:
        print("⚠️  No training history found in logs")
        return

    history = logs['history']

    fig, ax = plt.subplots(figsize=(10, 6))

    # Plot train accuracy
    if 'train_acc' in history:
        ax.plot(history['train_acc'], label='Train Accuracy', linewidth=2, color='#10b981')

    # Plot val accuracy
    if 'val_acc' in history:
        ax.plot(history['val_acc'], label='Validation Accuracy', linewidth=2, color='#f59e0b')

    ax.set_xlabel('Epoch', fontsize=12, fontweight='bold')
    ax.set_ylabel('Accuracy (%)', fontsize=12, fontweight='bold')
    ax.set_title('Training & Validation Accuracy', fontsize=14, fontweight='bold')
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)

    # Add baseline (50% for binary classification)
    ax.axhline(y=50, color='gray', linestyle='--', alpha=0.5, label='Baseline (50%)')

    # Save
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"✅ Accuracy curve saved: {output_path}")

def plot_feature_importance(logs, top_n=20, output_path="data/models/visualizations/feature_importance.png"):
    """Plot top N most important features"""

    if 'feature_importance' not in logs:
        print("⚠️  No feature importance found in logs")
        return

    importance = logs['feature_importance']

    # Sort by importance
    sorted_features = sorted(importance.items(), key=lambda x: x[1], reverse=True)[:top_n]

    features, scores = zip(*sorted_features)

    # Create horizontal bar chart
    fig, ax = plt.subplots(figsize=(10, max(8, top_n * 0.4)))

    colors = plt.cm.viridis(scores / max(scores))
    bars = ax.barh(range(len(features)), scores, color=colors)

    ax.set_yticks(range(len(features)))
    ax.set_yticklabels(features, fontsize=10)
    ax.set_xlabel('Importance Score', fontsize=12, fontweight='bold')
    ax.set_title(f'Top {top_n} Most Important Features', fontsize=14, fontweight='bold')
    ax.grid(True, axis='x', alpha=0.3)

    # Add value labels on bars
    for i, (bar, score) in enumerate(zip(bars, scores)):
        ax.text(score, i, f' {score:.4f}', va='center', fontsize=9)

    # Invert y-axis (highest on top)
    ax.invert_yaxis()

    # Save
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"✅ Feature importance saved: {output_path}")

def generate_summary_report(logs, output_path="data/models/visualizations/summary.txt"):
    """Generate text summary of training results"""

    summary = []
    summary.append("="*60)
    summary.append("MODEL TRAINING SUMMARY")
    summary.append("="*60)
    summary.append("")

    # Model info
    if 'model_type' in logs:
        summary.append(f"Model Type: {logs['model_type']}")
    if 'symbol' in logs:
        summary.append(f"Symbol: {logs['symbol']}")
    if 'timeframe' in logs:
        summary.append(f"Timeframe: {logs['timeframe']}")

    summary.append("")

    # Training params
    if 'epochs' in logs:
        summary.append(f"Epochs: {logs['epochs']}")
    if 'device' in logs:
        summary.append(f"Device: {logs['device']}")

    summary.append("")
    summary.append("-"*60)

    # Final metrics
    if 'final_metrics' in logs:
        metrics = logs['final_metrics']
        summary.append("FINAL METRICS:")
        summary.append("")

        for key, value in metrics.items():
            if isinstance(value, float):
                summary.append(f"  {key}: {value:.4f}")
            else:
                summary.append(f"  {key}: {value}")

    summary.append("")
    summary.append("="*60)

    # Save
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        f.write('\n'.join(summary))

    print(f"✅ Summary report saved: {output_path}")

    # Also print to console
    print("\n" + '\n'.join(summary))

def main():
    parser = argparse.ArgumentParser(description='Visualize model training results')
    parser.add_argument('--log-file', type=str, help='Path to training log JSON file')
    parser.add_argument('--symbol', type=str, help='Symbol (e.g., BTCUSDT)')
    parser.add_argument('--timeframe', type=str, help='Timeframe (e.g., 1h)')
    parser.add_argument('--model-type', type=str, default='xgb', help='Model type (xgb, lstm, ppo)')

    args = parser.parse_args()

    # Determine log file path
    if args.log_file:
        log_path = args.log_file
    elif args.symbol and args.timeframe:
        log_path = f"data/models/{args.symbol}_{args.timeframe}_{args.model_type}_training_log.json"
    else:
        # Find most recent log
        models_dir = Path("data/models")
        log_files = list(models_dir.glob("*_training_log.json"))

        if not log_files:
            print("❌ No training log files found in data/models/")
            print("💡 Run model training first or specify --log-file")
            return

        # Use most recent
        log_path = max(log_files, key=lambda p: p.stat().st_mtime)
        print(f"📊 Using most recent log: {log_path.name}")

    # Load logs
    logs = load_training_logs(log_path)

    if not logs:
        return

    print(f"\n{'='*60}")
    print(f"📊 Generating Visualizations")
    print(f"{'='*60}\n")

    # Generate visualizations
    plot_loss_curves(logs)
    plot_accuracy_curves(logs)
    plot_feature_importance(logs, top_n=20)
    generate_summary_report(logs)

    print(f"\n{'='*60}")
    print(f"✅ All visualizations generated!")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
