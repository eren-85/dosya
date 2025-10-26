"""
Data sources module
"""

from .base import DataSource, ExchangeDataSource, OnChainDataSource
from .aggregator import DataAggregator

__all__ = [
    "DataSource",
    "ExchangeDataSource",
    "OnChainDataSource",
    "DataAggregator"
]
