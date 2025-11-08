"""
Debug script to check data files and identify issues
"""
import sys
from pathlib import Path
import pandas as pd
import numpy as np

def check_data_file(filepath):
    """Check a single data file for issues"""
    print(f"\n{'='*80}")
    print(f"📂 Checking: {filepath}")
    print(f"{'='*80}")

    try:
        # Load data
        df = pd.read_parquet(filepath)
        print(f"✅ Loaded successfully: {len(df)} rows, {len(df.columns)} columns")

        # Check basic columns
        required = ['open', 'high', 'low', 'close', 'volume']
        missing = [col for col in required if col not in df.columns]
        if missing:
            print(f"❌ Missing required columns: {missing}")
        else:
            print(f"✅ All required columns present")

        # Check data types
        print(f"\n📊 Data Types:")
        print(df.dtypes.value_counts())

        # Check numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        print(f"\n✅ Numeric columns: {len(numeric_cols)}")

        # Check datetime columns
        datetime_cols = df.select_dtypes(include=['datetime64']).columns.tolist()
        print(f"📅 Datetime columns: {len(datetime_cols)}")
        if datetime_cols:
            print(f"   {datetime_cols}")

        # Check object columns
        object_cols = df.select_dtypes(include=['object']).columns.tolist()
        print(f"🔤 Object columns: {len(object_cols)}")
        if object_cols:
            print(f"   {object_cols[:10]}..." if len(object_cols) > 10 else f"   {object_cols}")

        # Check for NaN
        nan_cols = df.columns[df.isna().any()].tolist()
        if nan_cols:
            print(f"\n⚠️  Columns with NaN: {len(nan_cols)}")
            for col in nan_cols[:5]:
                nan_count = df[col].isna().sum()
                print(f"   {col}: {nan_count} NaN values ({nan_count/len(df)*100:.1f}%)")

        # Try feature selection (same as training scripts)
        excluded_cols = ['open', 'high', 'low', 'close', 'volume', 'open_time', 'close_time', 'timestamp', 'target']
        feature_cols = [
            col for col in df.columns
            if col not in excluded_cols
            and pd.api.types.is_numeric_dtype(df[col])
        ]
        print(f"\n✅ Would use {len(feature_cols)} features for training")

        if not feature_cols:
            print("❌ ERROR: No numeric features found! All columns excluded or non-numeric")
            print("\nAll columns:")
            for col in df.columns:
                print(f"  - {col}: {df[col].dtype}")

        return True

    except Exception as e:
        print(f"❌ ERROR loading file: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Check data files in advanced directory"""
    data_dir = Path("data/advanced")

    if not data_dir.exists():
        print(f"❌ Data directory not found: {data_dir}")
        return 1

    # Find all parquet files
    parquet_files = list(data_dir.glob("**/*.parquet"))

    if not parquet_files:
        print(f"❌ No parquet files found in {data_dir}")
        return 1

    print(f"Found {len(parquet_files)} parquet files")

    # Check first few files
    success_count = 0
    for i, filepath in enumerate(parquet_files[:5], 1):
        if check_data_file(filepath):
            success_count += 1

    print(f"\n{'='*80}")
    print(f"✅ Successfully checked {success_count}/{min(5, len(parquet_files))} files")
    print(f"{'='*80}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
