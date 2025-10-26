"""
Feature engineering for ML models
Prepares features from raw OHLCV + indicators
"""

from typing import List, Dict, Optional, Tuple
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, RobustScaler
from .technical_indicators import TechnicalIndicators


class FeatureEngineer:
    """
    Feature engineering pipeline for ML models
    """

    def __init__(self, scaling_method: str = 'robust'):
        """
        Args:
            scaling_method: 'standard', 'robust', or 'minmax'
        """
        self.scaling_method = scaling_method
        self.scaler = self._get_scaler(scaling_method)
        self.feature_names: List[str] = []
        self._fitted = False

    def _get_scaler(self, method: str):
        """Get appropriate scaler"""
        if method == 'standard':
            return StandardScaler()
        elif method == 'robust':
            return RobustScaler()
        else:
            from sklearn.preprocessing import MinMaxScaler
            return MinMaxScaler()

    def create_features(
        self,
        df: pd.DataFrame,
        add_indicators: bool = True,
        add_lagged_features: bool = True,
        add_rolling_stats: bool = True
    ) -> pd.DataFrame:
        """
        Create comprehensive feature set

        Args:
            df: Raw OHLCV DataFrame
            add_indicators: Add technical indicators
            add_lagged_features: Add lagged price/volume
            add_rolling_stats: Add rolling statistics

        Returns:
            DataFrame with engineered features
        """
        df = df.copy()

        # Add technical indicators
        if add_indicators:
            df = TechnicalIndicators.add_all_indicators(df)

        # Add lagged features
        if add_lagged_features:
            df = self._add_lagged_features(df)

        # Add rolling statistics
        if add_rolling_stats:
            df = self._add_rolling_stats(df)

        # Add time-based features
        df = self._add_time_features(df)

        # Add interaction features
        df = self._add_interaction_features(df)

        # Remove infinite values and NaNs
        df = self._clean_features(df)

        return df

    def _add_lagged_features(self, df: pd.DataFrame, lags: List[int] = None) -> pd.DataFrame:
        """Add lagged features for time series"""
        if lags is None:
            lags = [1, 2, 3, 5, 10, 20]

        # Lag important features
        features_to_lag = ['close', 'volume', 'rsi_14', 'macd_12_26_9', 'atr']

        for feature in features_to_lag:
            if feature in df.columns:
                for lag in lags:
                    df[f'{feature}_lag_{lag}'] = df[feature].shift(lag)

        return df

    def _add_rolling_stats(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add rolling window statistics"""

        windows = [5, 10, 20, 50]

        for window in windows:
            # Rolling mean and std
            df[f'close_rolling_mean_{window}'] = df['close'].rolling(window).mean()
            df[f'close_rolling_std_{window}'] = df['close'].rolling(window).std()

            # Rolling z-score
            df[f'close_zscore_{window}'] = (
                (df['close'] - df[f'close_rolling_mean_{window}']) /
                (df[f'close_rolling_std_{window}'] + 1e-10)
            )

            # Rolling min/max
            df[f'close_rolling_min_{window}'] = df['close'].rolling(window).min()
            df[f'close_rolling_max_{window}'] = df['close'].rolling(window).max()

            # Position in range
            df[f'close_pct_of_range_{window}'] = (
                (df['close'] - df[f'close_rolling_min_{window}']) /
                (df[f'close_rolling_max_{window}'] - df[f'close_rolling_min_{window}'] + 1e-10)
            )

            # Volume statistics
            df[f'volume_rolling_mean_{window}'] = df['volume'].rolling(window).mean()
            df[f'volume_spike_{window}'] = df['volume'] / (df[f'volume_rolling_mean_{window}'] + 1e-10)

        return df

    def _add_time_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add time-based cyclical features"""

        if 'time' not in df.columns and df.index.name == 'time':
            df = df.reset_index()

        if 'time' in df.columns:
            # Extract time components
            df['hour'] = pd.to_datetime(df['time']).dt.hour
            df['day_of_week'] = pd.to_datetime(df['time']).dt.dayofweek
            df['day_of_month'] = pd.to_datetime(df['time']).dt.day
            df['month'] = pd.to_datetime(df['time']).dt.month

            # Cyclical encoding (sine/cosine for periodicity)
            df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
            df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)

            df['dow_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
            df['dow_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)

            # ICT Kill Zones (UTC time)
            df['london_killzone'] = ((df['hour'] >= 2) & (df['hour'] < 5)).astype(int)
            df['new_york_killzone'] = ((df['hour'] >= 13) & (df['hour'] < 16)).astype(int)
            df['asia_killzone'] = ((df['hour'] >= 20) | (df['hour'] < 2)).astype(int)

        return df

    def _add_interaction_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add interaction features between indicators"""

        # RSI * Volume (momentum + volume confirmation)
        if 'rsi_14' in df.columns and 'volume' in df.columns:
            df['rsi_volume_interaction'] = df['rsi_14'] * np.log1p(df['volume'])

        # Bollinger Bands width * ATR (volatility clustering)
        if 'BBU_20_2.0' in df.columns and 'BBL_20_2.0' in df.columns and 'atr' in df.columns:
            df['bb_width'] = df['BBU_20_2.0'] - df['BBL_20_2.0']
            df['volatility_cluster'] = df['bb_width'] * df['atr']

        # MACD * RSI (momentum confluence)
        if 'MACD_12_26_9' in df.columns and 'rsi_14' in df.columns:
            df['macd_rsi_interaction'] = df['MACD_12_26_9'] * (df['rsi_14'] - 50) / 50

        # Price distance from MA * Volume
        if 'sma_20' in df.columns:
            df['distance_ma_volume'] = (df['close'] / df['sma_20'] - 1) * np.log1p(df['volume'])

        return df

    def _clean_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean features - handle inf, NaN"""

        # Replace infinite values with NaN
        df = df.replace([np.inf, -np.inf], np.nan)

        # Forward fill then backward fill NaNs
        df = df.fillna(method='ffill').fillna(method='bfill')

        # If still NaN, fill with 0
        df = df.fillna(0)

        return df

    def select_features_for_ml(self, df: pd.DataFrame, exclude_cols: List[str] = None) -> Tuple[pd.DataFrame, List[str]]:
        """
        Select numerical features suitable for ML

        Args:
            df: DataFrame with all features
            exclude_cols: Columns to exclude

        Returns:
            (features_df, feature_names)
        """
        if exclude_cols is None:
            exclude_cols = [
                'time', 'timestamp', 'symbol', 'timeframe', 'source',
                'volatility_regime',  # categorical
                'open', 'high', 'low', 'close', 'volume'  # raw OHLCV (keep derived features)
            ]

        # Select numerical columns
        numerical_cols = df.select_dtypes(include=[np.number]).columns.tolist()

        # Exclude specified columns
        feature_cols = [col for col in numerical_cols if col not in exclude_cols]

        # Store feature names
        self.feature_names = feature_cols

        return df[feature_cols], feature_cols

    def fit_scaler(self, X: pd.DataFrame):
        """Fit scaler on training data"""
        self.scaler.fit(X)
        self._fitted = True

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """Transform features using fitted scaler"""
        if not self._fitted:
            raise ValueError("Scaler not fitted. Call fit_scaler() first.")

        X_scaled = self.scaler.transform(X)
        return pd.DataFrame(X_scaled, columns=X.columns, index=X.index)

    def fit_transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """Fit scaler and transform"""
        self.fit_scaler(X)
        return self.transform(X)

    def create_target_variables(
        self,
        df: pd.DataFrame,
        target_type: str = 'returns',
        horizon: int = 1
    ) -> pd.DataFrame:
        """
        Create target variables for supervised learning

        Args:
            df: DataFrame with OHLCV
            target_type: 'returns', 'direction', 'volatility', 'range'
            horizon: Prediction horizon (number of periods ahead)

        Returns:
            DataFrame with target variables
        """
        df = df.copy()

        if target_type == 'returns':
            # Future returns
            df['target_return'] = df['close'].pct_change(horizon).shift(-horizon)

        elif target_type == 'direction':
            # Binary: 1 if price goes up, 0 if down
            df['target_direction'] = (df['close'].shift(-horizon) > df['close']).astype(int)

        elif target_type == 'volatility':
            # Future volatility (realized vol over next N periods)
            df['target_volatility'] = df['close'].pct_change().shift(-horizon).rolling(horizon).std()

        elif target_type == 'range':
            # Future price range
            df['target_high'] = df['high'].rolling(horizon).max().shift(-horizon)
            df['target_low'] = df['low'].rolling(horizon).min().shift(-horizon)
            df['target_range'] = df['target_high'] - df['target_low']

        return df

    def feature_importance_analysis(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        method: str = 'mutual_info'
    ) -> pd.DataFrame:
        """
        Analyze feature importance

        Args:
            X: Features
            y: Target
            method: 'mutual_info', 'correlation', or 'permutation'

        Returns:
            DataFrame with feature importance scores
        """
        from sklearn.feature_selection import mutual_info_regression

        if method == 'mutual_info':
            scores = mutual_info_regression(X, y, random_state=42)
            importance_df = pd.DataFrame({
                'feature': X.columns,
                'importance': scores
            }).sort_values('importance', ascending=False)

        elif method == 'correlation':
            correlations = X.corrwith(y).abs()
            importance_df = pd.DataFrame({
                'feature': correlations.index,
                'importance': correlations.values
            }).sort_values('importance', ascending=False)

        return importance_df

    def remove_highly_correlated_features(
        self,
        X: pd.DataFrame,
        threshold: float = 0.95
    ) -> Tuple[pd.DataFrame, List[str]]:
        """
        Remove highly correlated features

        Args:
            X: Features DataFrame
            threshold: Correlation threshold (0-1)

        Returns:
            (reduced_df, removed_features)
        """
        corr_matrix = X.corr().abs()

        # Upper triangle of correlation matrix
        upper = corr_matrix.where(
            np.triu(np.ones(corr_matrix.shape), k=1).astype(bool)
        )

        # Find features with correlation greater than threshold
        to_drop = [column for column in upper.columns if any(upper[column] > threshold)]

        X_reduced = X.drop(columns=to_drop)

        print(f"✅ Removed {len(to_drop)} highly correlated features (threshold={threshold})")

        return X_reduced, to_drop

    def create_ml_dataset(
        self,
        df: pd.DataFrame,
        target_type: str = 'returns',
        horizon: int = 1,
        train_size: float = 0.8,
        scale: bool = True
    ) -> Dict[str, pd.DataFrame]:
        """
        Create ready-to-use ML dataset

        Returns:
            {
                'X_train': ...,
                'X_test': ...,
                'y_train': ...,
                'y_test': ...,
                'feature_names': [...]
            }
        """

        # Create features
        df_features = self.create_features(df)

        # Create target
        df_features = self.create_target_variables(df_features, target_type, horizon)

        # Remove rows with NaN target
        df_features = df_features.dropna(subset=[f'target_{target_type}'])

        # Select features
        X, feature_names = self.select_features_for_ml(df_features)

        # Target
        y = df_features[f'target_{target_type}']

        # Train/test split (time-based)
        split_idx = int(len(X) * train_size)

        X_train = X.iloc[:split_idx]
        X_test = X.iloc[split_idx:]
        y_train = y.iloc[:split_idx]
        y_test = y.iloc[split_idx:]

        # Scale features
        if scale:
            self.fit_scaler(X_train)
            X_train = self.transform(X_train)
            X_test = self.transform(X_test)

        return {
            'X_train': X_train,
            'X_test': X_test,
            'y_train': y_train,
            'y_test': y_test,
            'feature_names': feature_names
        }
