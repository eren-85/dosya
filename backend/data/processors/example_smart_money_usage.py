"""
Example usage of Smart Money Indicators
"""

import pandas as pd
import numpy as np
from smart_money_indicators import SmartMoneyIndicators


def create_sample_data(n_candles: int = 1000) -> pd.DataFrame:
    """Create sample OHLC data for testing"""
    dates = pd.date_range(start='2024-01-01', periods=n_candles, freq='1H')

    # Generate random walk price data
    np.random.seed(42)
    close_prices = 50000 + np.cumsum(np.random.randn(n_candles) * 100)

    df = pd.DataFrame({
        'open': close_prices + np.random.randn(n_candles) * 50,
        'high': close_prices + np.abs(np.random.randn(n_candles) * 100),
        'low': close_prices - np.abs(np.random.randn(n_candles) * 100),
        'close': close_prices,
    }, index=dates)

    # Ensure high >= close, low <= close
    df['high'] = df[['high', 'close', 'open']].max(axis=1)
    df['low'] = df[['low', 'close', 'open']].min(axis=1)

    return df


def main():
    """Example of applying all indicators"""
    print("Creating sample data...")
    df = create_sample_data(1000)

    print(f"Data shape: {df.shape}")
    print(f"Date range: {df.index[0]} to {df.index[-1]}")
    print()

    # Apply all indicators
    print("Applying Smart Money indicators...")
    indicators = SmartMoneyIndicators()
    df_with_indicators = indicators.apply_all(df)

    print("Indicators applied successfully!")
    print()

    # Print summary
    print("=" * 60)
    print("INDICATOR SUMMARY")
    print("=" * 60)

    bullish_ob = df_with_indicators['bullish_ob'].sum()
    bearish_ob = df_with_indicators['bearish_ob'].sum()
    print(f"Bullish Order Blocks: {bullish_ob}")
    print(f"Bearish Order Blocks: {bearish_ob}")
    print()

    bullish_fvg = df_with_indicators['bullish_fvg'].sum()
    bearish_fvg = df_with_indicators['bearish_fvg'].sum()
    print(f"Bullish Fair Value Gaps: {bullish_fvg}")
    print(f"Bearish Fair Value Gaps: {bearish_fvg}")
    print()

    high_sweeps = df_with_indicators['high_sweep'].sum()
    low_sweeps = df_with_indicators['low_sweep'].sum()
    print(f"High Liquidity Sweeps: {high_sweeps}")
    print(f"Low Liquidity Sweeps: {low_sweeps}")
    print()

    bullish_bos = df_with_indicators['bullish_bos'].sum()
    bearish_bos = df_with_indicators['bearish_bos'].sum()
    print(f"Bullish Break of Structure: {bullish_bos}")
    print(f"Bearish Break of Structure: {bearish_bos}")
    print()

    if 'asian_killzone' in df_with_indicators.columns:
        asian_pct = (df_with_indicators['asian_killzone'].sum() / len(df_with_indicators)) * 100
        london_pct = (df_with_indicators['london_killzone'].sum() / len(df_with_indicators)) * 100
        ny_pct = (df_with_indicators['ny_killzone'].sum() / len(df_with_indicators)) * 100

        print(f"Asian Kill Zone: {asian_pct:.1f}% of candles")
        print(f"London Kill Zone: {london_pct:.1f}% of candles")
        print(f"New York Kill Zone: {ny_pct:.1f}% of candles")
        print()

    print("=" * 60)
    print()

    # Show recent signals
    print("Last 10 signals:")
    recent = df_with_indicators[
        (df_with_indicators['bullish_ob']) |
        (df_with_indicators['bearish_ob']) |
        (df_with_indicators['bullish_fvg']) |
        (df_with_indicators['bearish_fvg']) |
        (df_with_indicators['high_sweep']) |
        (df_with_indicators['low_sweep'])
    ].tail(10)

    for idx, row in recent.iterrows():
        signals = []
        if row['bullish_ob']:
            signals.append('Bullish OB')
        if row['bearish_ob']:
            signals.append('Bearish OB')
        if row['bullish_fvg']:
            signals.append('Bullish FVG')
        if row['bearish_fvg']:
            signals.append('Bearish FVG')
        if row['high_sweep']:
            signals.append('High Sweep')
        if row['low_sweep']:
            signals.append('Low Sweep')

        print(f"{idx.strftime('%Y-%m-%d %H:%M')} - {', '.join(signals)}")

    print()
    print("Example completed successfully!")


if __name__ == '__main__':
    main()
