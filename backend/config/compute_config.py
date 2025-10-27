"""
Compute Configuration - GPU/CPU Selection
Optimized for RTX 4060 8GB VRAM + Hybrid CPU/GPU usage
"""

import os
import torch
from typing import Literal, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ComputeConfig:
    """Compute configuration for different model types"""

    # Device selection
    device: str  # 'cuda', 'cpu', 'auto'
    use_mixed_precision: bool = True  # FP16 for 2x memory efficiency

    # Deep Learning (LSTM, Transformer)
    dl_device: str = 'cuda'  # 10-50x speedup on GPU
    dl_batch_size: int = 128  # Optimal for 8GB VRAM
    dl_num_workers: int = 4

    # Tree-based ML (XGBoost, LightGBM, CatBoost)
    ml_device: str = 'cpu'  # CPU faster for small-medium datasets
    ml_n_jobs: int = -1  # Use all CPU cores

    # Reinforcement Learning (PPO, Decision Transformer)
    rl_device: str = 'cuda'  # GPU for faster training
    rl_n_envs: int = 8  # Parallel environments

    # Technical Analysis (pandas-ta, TA-Lib)
    ta_device: str = 'cpu'  # NumPy/pandas optimized for CPU
    ta_n_jobs: int = -1

    # Backtest Engine
    backtest_device: str = 'cpu'  # Pandas-based operations
    backtest_parallel: bool = True
    backtest_n_jobs: int = -1


class ComputeManager:
    """Manages compute resources for different workloads"""

    def __init__(self, mode: Literal['auto', 'cpu', 'gpu', 'hybrid'] = 'auto'):
        """
        Initialize compute manager

        Args:
            mode:
                - 'auto': Auto-detect and use optimal configuration
                - 'cpu': Force CPU for all operations
                - 'gpu': Force GPU for all operations (if available)
                - 'hybrid': Use CPU for some, GPU for others (RECOMMENDED)
        """
        self.mode = mode
        self.has_gpu = torch.cuda.is_available()
        self.gpu_name = torch.cuda.get_device_name(0) if self.has_gpu else None
        self.gpu_memory = torch.cuda.get_device_properties(0).total_memory if self.has_gpu else 0
        self.gpu_memory_gb = self.gpu_memory / (1024**3) if self.has_gpu else 0

        self.config = self._create_config()
        self._log_setup()

    def _create_config(self) -> ComputeConfig:
        """Create optimal compute configuration"""

        if self.mode == 'cpu':
            # Force CPU mode
            return ComputeConfig(
                device='cpu',
                dl_device='cpu',
                ml_device='cpu',
                rl_device='cpu',
                ta_device='cpu',
                backtest_device='cpu',
            )

        elif self.mode == 'gpu':
            # Force GPU mode (if available)
            device = 'cuda' if self.has_gpu else 'cpu'
            return ComputeConfig(
                device=device,
                dl_device=device,
                ml_device=device,
                rl_device=device,
                ta_device='cpu',  # TA always on CPU (NumPy/pandas optimized)
                backtest_device='cpu',  # Backtest always on CPU (pandas)
            )

        elif self.mode == 'hybrid' or (self.mode == 'auto' and self.has_gpu):
            # HYBRID MODE - RECOMMENDED for RTX 4060
            # Use GPU for Deep Learning and RL, CPU for everything else

            # Optimize batch size based on VRAM
            if self.gpu_memory_gb >= 8:
                batch_size = 128  # RTX 4060 8GB
            elif self.gpu_memory_gb >= 6:
                batch_size = 64   # RTX 3060 6GB
            else:
                batch_size = 32   # Lower VRAM

            return ComputeConfig(
                device='cuda',
                use_mixed_precision=True,  # FP16 for 2x memory
                dl_device='cuda',
                dl_batch_size=batch_size,
                ml_device='cpu',  # Tree-based models faster on CPU
                rl_device='cuda',
                ta_device='cpu',
                backtest_device='cpu',
            )

        else:
            # Auto mode without GPU - use CPU
            return ComputeConfig(
                device='cpu',
                dl_device='cpu',
                ml_device='cpu',
                rl_device='cpu',
                ta_device='cpu',
                backtest_device='cpu',
            )

    def _log_setup(self):
        """Log compute configuration"""
        logger.info(f"🖥️  Compute Mode: {self.mode.upper()}")

        if self.has_gpu:
            logger.info(f"🎮 GPU Detected: {self.gpu_name}")
            logger.info(f"💾 VRAM: {self.gpu_memory_gb:.1f} GB")
            logger.info(f"⚡ CUDA Version: {torch.version.cuda}")
        else:
            logger.info("💻 GPU not available - using CPU")

        logger.info(f"\n📊 Workload Distribution:")
        logger.info(f"  • Deep Learning (LSTM/Transformer): {self.config.dl_device.upper()}")
        logger.info(f"  • ML Models (XGBoost/CatBoost): {self.config.ml_device.upper()}")
        logger.info(f"  • RL Training (PPO/DT): {self.config.rl_device.upper()}")
        logger.info(f"  • Technical Analysis: {self.config.ta_device.upper()}")
        logger.info(f"  • Backtest Engine: {self.config.backtest_device.upper()}")

        if self.has_gpu and self.config.dl_device == 'cuda':
            logger.info(f"\n⚙️  GPU Settings:")
            logger.info(f"  • Batch Size: {self.config.dl_batch_size}")
            logger.info(f"  • Mixed Precision: {self.config.use_mixed_precision}")

    def get_torch_device(self, workload: str = 'dl') -> torch.device:
        """
        Get PyTorch device for specific workload

        Args:
            workload: 'dl', 'ml', 'rl', 'ta', 'backtest'
        """
        device_map = {
            'dl': self.config.dl_device,
            'ml': self.config.ml_device,
            'rl': self.config.rl_device,
            'ta': self.config.ta_device,
            'backtest': self.config.backtest_device,
        }

        device_str = device_map.get(workload, self.config.device)
        return torch.device(device_str)

    def get_xgboost_params(self) -> dict:
        """Get XGBoost device parameters"""
        if self.config.ml_device == 'cuda' and self.has_gpu:
            return {
                'tree_method': 'gpu_hist',
                'gpu_id': 0,
                'predictor': 'gpu_predictor',
            }
        else:
            return {
                'tree_method': 'hist',
                'n_jobs': self.config.ml_n_jobs,
            }

    def get_lightgbm_params(self) -> dict:
        """Get LightGBM device parameters"""
        if self.config.ml_device == 'cuda' and self.has_gpu:
            return {
                'device': 'gpu',
                'gpu_platform_id': 0,
                'gpu_device_id': 0,
            }
        else:
            return {
                'device': 'cpu',
                'n_jobs': self.config.ml_n_jobs,
            }

    def get_catboost_params(self) -> dict:
        """Get CatBoost device parameters"""
        if self.config.ml_device == 'cuda' and self.has_gpu:
            return {
                'task_type': 'GPU',
                'devices': '0',
            }
        else:
            return {
                'task_type': 'CPU',
                'thread_count': self.config.ml_n_jobs if self.config.ml_n_jobs > 0 else None,
            }

    def get_sb3_device(self) -> str:
        """Get Stable-Baselines3 device"""
        return self.config.rl_device

    def optimize_memory(self):
        """Optimize GPU memory usage"""
        if self.has_gpu:
            torch.cuda.empty_cache()
            # Enable TF32 for better performance on RTX 30xx/40xx
            torch.backends.cuda.matmul.allow_tf32 = True
            torch.backends.cudnn.allow_tf32 = True
            logger.info("🧹 GPU memory optimized")

    def get_memory_stats(self) -> dict:
        """Get GPU memory statistics"""
        if not self.has_gpu:
            return {}

        allocated = torch.cuda.memory_allocated(0) / (1024**3)
        reserved = torch.cuda.memory_reserved(0) / (1024**3)
        total = self.gpu_memory_gb

        return {
            'allocated_gb': allocated,
            'reserved_gb': reserved,
            'total_gb': total,
            'free_gb': total - allocated,
            'utilization_percent': (allocated / total) * 100,
        }


# Global compute manager instance
_compute_manager: Optional[ComputeManager] = None


def initialize_compute(mode: Literal['auto', 'cpu', 'gpu', 'hybrid'] = 'auto') -> ComputeManager:
    """
    Initialize global compute manager

    Recommended modes:
        - 'hybrid': Best for RTX 4060 (GPU for DL/RL, CPU for ML/TA/Backtest)
        - 'auto': Auto-detect optimal configuration
        - 'cpu': Force CPU (for testing or no GPU)
        - 'gpu': Force GPU for everything (may be slower for tree models)

    Environment variable override: COMPUTE_MODE=hybrid/auto/cpu/gpu
    """
    global _compute_manager

    # Check environment variable
    env_mode = os.getenv('COMPUTE_MODE', mode).lower()
    if env_mode not in ['auto', 'cpu', 'gpu', 'hybrid']:
        logger.warning(f"Invalid COMPUTE_MODE={env_mode}, using '{mode}'")
        env_mode = mode

    _compute_manager = ComputeManager(mode=env_mode)
    return _compute_manager


def get_compute() -> ComputeManager:
    """Get global compute manager"""
    global _compute_manager
    if _compute_manager is None:
        _compute_manager = initialize_compute()
    return _compute_manager


# Usage examples
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    print("\n" + "="*60)
    print("Sigma Analyst - Compute Configuration Test")
    print("="*60)

    # Test HYBRID mode (recommended for RTX 4060)
    compute = initialize_compute(mode='hybrid')

    print("\n📋 Configuration Summary:")
    print(f"  Mode: {compute.mode}")
    print(f"  GPU Available: {compute.has_gpu}")
    if compute.has_gpu:
        print(f"  GPU: {compute.gpu_name}")
        print(f"  VRAM: {compute.gpu_memory_gb:.1f} GB")

    print(f"\n🎯 Optimal Settings for Your System:")
    print(f"  Deep Learning Batch Size: {compute.config.dl_batch_size}")
    print(f"  Mixed Precision (FP16): {compute.config.use_mixed_precision}")

    print(f"\n💡 Device Assignment:")
    print(f"  Technical Analysis → {compute.config.ta_device.upper()}")
    print(f"  XGBoost/LightGBM/CatBoost → {compute.config.ml_device.upper()}")
    print(f"  LSTM/Transformer → {compute.config.dl_device.upper()}")
    print(f"  PPO/Decision Transformer → {compute.config.rl_device.upper()}")
    print(f"  Backtest → {compute.config.backtest_device.upper()}")

    if compute.has_gpu:
        print(f"\n📊 GPU Memory:")
        stats = compute.get_memory_stats()
        print(f"  Total: {stats['total_gb']:.1f} GB")
        print(f"  Free: {stats['free_gb']:.1f} GB")
        print(f"  Utilization: {stats['utilization_percent']:.1f}%")
