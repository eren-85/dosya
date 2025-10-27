"""
Compute Configuration - Intelligent GPU/CPU Selection
Optimized for RTX 4060 8GB with BF16, TF32, and dynamic batch sizing
"""

import os
import torch
from typing import Literal, Optional, Tuple
from dataclasses import dataclass
import logging
import warnings

logger = logging.getLogger(__name__)


@dataclass
class ComputeConfig:
    """Compute configuration for different model types"""

    # Device selection
    device: str  # 'cuda', 'cpu', 'auto'

    # Mixed precision settings
    use_mixed_precision: bool = True
    amp_dtype: torch.dtype = torch.float16  # torch.bfloat16 or torch.float16
    use_tf32: bool = True  # TensorFloat-32 for RTX 30xx/40xx

    # Deep Learning (LSTM, Transformer)
    dl_device: str = 'cuda'
    dl_batch_size: int = 128  # Auto-calculated based on VRAM
    dl_num_workers: int = 2  # 2-4 optimal for Windows (spawn overhead)
    # Note: pin_memory should be set dynamically in DataLoader (True if cuda, False if cpu)
    dl_use_compile: bool = False  # torch.compile (optional, first iter slow)

    # Tree-based ML (XGBoost, LightGBM, CatBoost)
    ml_device: str = 'cpu'  # CPU faster for small-medium datasets
    ml_n_jobs: int = -1
    ml_auto_gpu_threshold: int = 200000  # Use GPU if n_samples > threshold

    # Reinforcement Learning (PPO, Decision Transformer)
    rl_device: str = 'cuda'
    rl_n_envs: int = 8
    rl_cpu_threads: int = 1  # Set torch.set_num_threads(1) for RL (Windows subprocess compatibility)

    # Technical Analysis (pandas-ta, TA-Lib)
    ta_device: str = 'cpu'
    ta_n_jobs: int = -1

    # Backtest Engine
    backtest_device: str = 'cpu'
    backtest_parallel: bool = True
    backtest_n_jobs: int = -1


class ComputeManager:
    """
    Intelligent compute resource manager

    Features:
        - BF16 support for RTX 40xx (better stability than FP16)
        - TF32 optimization for matrix operations
        - Dynamic batch size based on VRAM
        - Conditional GPU for XGBoost on large datasets
        - VRAM monitoring and auto-cleanup
    """

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

        # GPU detection
        self.has_gpu = torch.cuda.is_available()
        self.gpu_name = None
        self.gpu_memory = 0
        self.gpu_memory_gb = 0.0
        self.gpu_compute_capability = (0, 0)

        if self.has_gpu:
            self.gpu_name = torch.cuda.get_device_name(0)
            self.gpu_memory = torch.cuda.get_device_properties(0).total_memory
            # Use GiB (binary) for consistency: 1 GiB = 1024^3 bytes
            # Note: Marketing says "8 GB" but actual is 8 GiB = 8.59 GB
            self.gpu_memory_gb = self.gpu_memory / (1024**3)  # GiB (binary)
            self.gpu_compute_capability = torch.cuda.get_device_capability(0)

        # Create config
        self.config = self._create_config()

        # Apply optimizations if GPU available
        if self.has_gpu and self.config.device == 'cuda':
            self._apply_pytorch_optimizations()

        self._log_setup()

    def _supports_bfloat16(self) -> bool:
        """Check if GPU supports BF16 (Ampere/Ada and newer)"""
        if not self.has_gpu:
            return False

        # Compute capability >= 8.0 supports BF16
        # RTX 30xx (Ampere) = 8.6
        # RTX 40xx (Ada) = 8.9
        major, minor = self.gpu_compute_capability
        return major >= 8

    def _supports_tf32(self) -> bool:
        """Check if GPU supports TF32 (Ampere/Ada and newer)"""
        if not self.has_gpu:
            return False

        # TF32 available on Ampere (SM 8.0) and newer
        major, minor = self.gpu_compute_capability
        return major >= 8

    def _calculate_optimal_batch_size(self, vram_gb: float) -> int:
        """
        Calculate optimal batch size based on VRAM

        Formula: batch_size = 128 * (vram_gb / 8.0)
        Rounded to nearest multiple of 16
        """
        if vram_gb <= 0:
            return 64

        base_batch = 128 * (vram_gb / 8.0)

        # Round to nearest multiple of 16 (GPU efficiency)
        batch_size = int(base_batch // 16 * 16)

        # Clamp to reasonable range
        batch_size = max(16, min(512, batch_size))

        return batch_size

    def _create_config(self) -> ComputeConfig:
        """Create optimal compute configuration"""

        if self.mode == 'cpu':
            # Force CPU mode
            return ComputeConfig(
                device='cpu',
                use_mixed_precision=False,
                dl_device='cpu',
                ml_device='cpu',
                rl_device='cpu',
                ta_device='cpu',
                backtest_device='cpu',
            )

        elif self.mode == 'gpu':
            # Force GPU mode (if available)
            device = 'cuda' if self.has_gpu else 'cpu'

            if not self.has_gpu:
                warnings.warn("GPU mode requested but no GPU available. Falling back to CPU.")
                return self._create_config_cpu()

            # Determine mixed precision dtype
            amp_dtype = torch.bfloat16 if self._supports_bfloat16() else torch.float16

            return ComputeConfig(
                device=device,
                use_mixed_precision=True,
                amp_dtype=amp_dtype,
                use_tf32=self._supports_tf32(),
                dl_device=device,
                dl_batch_size=self._calculate_optimal_batch_size(self.gpu_memory_gb),
                ml_device=device,  # Force GPU for ML too
                rl_device=device,
                ta_device='cpu',  # TA always on CPU
                backtest_device='cpu',  # Backtest always on CPU
            )

        elif self.mode == 'hybrid' or (self.mode == 'auto' and self.has_gpu):
            # HYBRID MODE - RECOMMENDED
            # GPU for DL/RL, CPU for ML/TA/Backtest

            # Determine mixed precision dtype
            amp_dtype = torch.bfloat16 if self._supports_bfloat16() else torch.float16

            return ComputeConfig(
                device='cuda',
                use_mixed_precision=True,
                amp_dtype=amp_dtype,
                use_tf32=self._supports_tf32(),
                dl_device='cuda',
                dl_batch_size=self._calculate_optimal_batch_size(self.gpu_memory_gb),
                ml_device='cpu',  # CPU for tree models (faster on small-medium data)
                ml_auto_gpu_threshold=200000,  # Switch to GPU for >200k samples
                rl_device='cuda',
                ta_device='cpu',
                backtest_device='cpu',
            )

        else:
            # Auto mode without GPU - use CPU
            return self._create_config_cpu()

    def _create_config_cpu(self) -> ComputeConfig:
        """Create CPU-only configuration"""
        return ComputeConfig(
            device='cpu',
            use_mixed_precision=False,
            dl_device='cpu',
            ml_device='cpu',
            rl_device='cpu',
            ta_device='cpu',
            backtest_device='cpu',
        )

    def _apply_pytorch_optimizations(self):
        """Apply PyTorch optimizations for RTX GPUs"""

        # Enable TF32 for faster matmul on Ampere/Ada
        if self.config.use_tf32:
            torch.backends.cuda.matmul.allow_tf32 = True
            torch.backends.cudnn.allow_tf32 = True
            logger.info("✅ TF32 enabled for matrix operations")

        # Set float32 matmul precision (PyTorch 2.x)
        if hasattr(torch, 'set_float32_matmul_precision'):
            torch.set_float32_matmul_precision('high')
            logger.info("✅ Float32 matmul precision set to 'high'")

        # Enable cuDNN benchmark for consistent input sizes
        torch.backends.cudnn.benchmark = True
        logger.info("✅ cuDNN benchmark enabled")

        # Disable cuDNN deterministic (faster training)
        torch.backends.cudnn.deterministic = False

        # RL-specific: Set CPU threads to 1 (Windows SubprocVecEnv compatibility)
        if self.config.rl_device == 'cuda' and self.config.rl_cpu_threads == 1:
            torch.set_num_threads(1)
            logger.info("✅ torch.set_num_threads(1) for RL (Windows subprocess compatibility)")

    def _log_setup(self):
        """Log compute configuration"""
        logger.info(f"\n{'='*60}")
        logger.info(f"🖥️  Compute Mode: {self.mode.upper()}")
        logger.info(f"{'='*60}")

        if self.has_gpu:
            logger.info(f"\n🎮 GPU Information:")
            logger.info(f"   Name: {self.gpu_name}")
            logger.info(f"   VRAM: {self.gpu_memory_gb:.1f} GiB")
            logger.info(f"   Compute Capability: {self.gpu_compute_capability[0]}.{self.gpu_compute_capability[1]}")
            logger.info(f"   CUDA Version: {torch.version.cuda}")
            logger.info(f"   cuDNN Version: {torch.backends.cudnn.version()}")
        else:
            logger.info("\n💻 GPU not available - using CPU only")

        logger.info(f"\n📊 Workload Distribution:")
        logger.info(f"   • Deep Learning (LSTM/Transformer): {self.config.dl_device.upper()}")
        logger.info(f"   • ML Tree Models (XGBoost/CatBoost): {self.config.ml_device.upper()}")
        logger.info(f"   • RL Training (PPO): {self.config.rl_device.upper()}")
        logger.info(f"   • Technical Analysis: {self.config.ta_device.upper()}")
        logger.info(f"   • Backtest Engine: {self.config.backtest_device.upper()}")

        if self.has_gpu and self.config.dl_device == 'cuda':
            logger.info(f"\n⚙️  GPU Settings:")
            logger.info(f"   • Batch Size: {self.config.dl_batch_size}")
            logger.info(f"   • Mixed Precision: {self.config.amp_dtype}")
            logger.info(f"   • TF32 Enabled: {self.config.use_tf32}")

            if self.config.amp_dtype == torch.bfloat16:
                logger.info(f"   • BF16 Support: ✅ (Better stability than FP16)")
            else:
                logger.info(f"   • FP16 Fallback: ⚠️  (GPU doesn't support BF16)")

        if hasattr(self.config, 'ml_auto_gpu_threshold'):
            logger.info(f"\n🌲 Tree Model GPU Threshold:")
            logger.info(f"   • Samples > {self.config.ml_auto_gpu_threshold:,} → GPU")
            logger.info(f"   • Samples ≤ {self.config.ml_auto_gpu_threshold:,} → CPU")

        logger.info(f"{'='*60}\n")

    # ==================== Device Selection API ====================

    def get_torch_device(self, workload: str = 'dl') -> torch.device:
        """
        Get PyTorch device for specific workload

        Args:
            workload: 'dl', 'ml', 'rl', 'ta', 'backtest'

        Returns:
            torch.device
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

    def torch_device(self) -> str:
        """Get primary torch device as string (for compatibility)"""
        return self.config.dl_device

    def amp_dtype(self) -> Optional[torch.dtype]:
        """Get automatic mixed precision dtype"""
        if not self.config.use_mixed_precision:
            return None
        return self.config.amp_dtype

    def suggest_batch_size(self, vram_usage_multiplier: float = 1.0) -> int:
        """
        Suggest batch size with optional multiplier

        Args:
            vram_usage_multiplier: Adjust batch size (0.5 = half VRAM, 2.0 = double)

        Returns:
            Suggested batch size
        """
        base_batch = self.config.dl_batch_size
        adjusted = int(base_batch * vram_usage_multiplier // 16 * 16)
        return max(16, min(512, adjusted))

    # ==================== ML Framework Params ====================

    def get_xgboost_params(self, n_samples: int = 0, n_features: int = 0) -> dict:
        """
        Get XGBoost device parameters with conditional GPU

        Args:
            n_samples: Number of training samples
            n_features: Number of features

        Returns:
            XGBoost parameters dict
        """
        # Use GPU if:
        # 1. GPU mode is forced, OR
        # 2. Large dataset (>200k samples or >200 features)
        use_gpu = (
            self.config.ml_device == 'cuda' or
            (n_samples > self.config.ml_auto_gpu_threshold) or
            (n_features > 200 and n_samples > 50000)
        )

        if use_gpu and self.has_gpu:
            logger.info(f"📊 XGBoost: Using GPU (n_samples={n_samples:,}, n_features={n_features})")
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

    def get_lightgbm_params(self, n_samples: int = 0) -> dict:
        """
        Get LightGBM device parameters

        Note: LightGBM GPU is NOT available via pip on Windows.
        Requires conda or manual compilation.
        Always use CPU for Windows stability.
        """
        # Windows pip LightGBM is CPU-only
        # GPU requires: conda install -c conda-forge lightgbm
        return {
            'device': 'cpu',
            'n_jobs': self.config.ml_n_jobs,
        }

    def get_catboost_params(self, n_samples: int = 0, safe_mode: bool = True) -> dict:
        """
        Get CatBoost device parameters

        Args:
            n_samples: Number of training samples
            safe_mode: If True, use CPU-only (recommended for Windows)
                      If False, try GPU (may fail on some Windows systems)

        Note: CatBoost GPU on Windows can have dependency issues.
        Use safe_mode=True (default) for stability.
        """
        use_gpu = (
            not safe_mode and  # Respect safe mode
            self.config.ml_device == 'cuda' and
            n_samples > self.config.ml_auto_gpu_threshold and
            self.has_gpu
        )

        if use_gpu:
            logger.info(f"📊 CatBoost: Trying GPU (n_samples={n_samples:,})")
            logger.warning("   ⚠️  CatBoost GPU may fail on Windows. Set safe_mode=True if issues occur.")
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
        """Get Stable-Baselines3 device string"""
        return self.config.rl_device

    def xgb_params(self, n_samples: int = 0, n_features: int = 0) -> dict:
        """Shorthand for get_xgboost_params"""
        return self.get_xgboost_params(n_samples, n_features)

    # ==================== Memory Management ====================

    def optimize_memory(self, aggressive: bool = False):
        """
        Optimize GPU memory usage

        Args:
            aggressive: If True, also synchronize and collect garbage
        """
        if self.has_gpu:
            torch.cuda.empty_cache()
            if aggressive:
                torch.cuda.synchronize()
                import gc
                gc.collect()
                logger.debug("🧹 GPU memory cache cleared (aggressive)")
            else:
                logger.debug("🧹 GPU memory cache cleared")

    def reset_peak_memory_stats(self):
        """
        Reset peak memory statistics

        Call at start of each epoch to track per-epoch peak usage
        """
        if self.has_gpu:
            torch.cuda.reset_peak_memory_stats()
            logger.debug("📊 Peak memory stats reset")

    def cleanup_after_training(self):
        """
        Comprehensive cleanup after training/large operation

        Recommended usage:
            - After each training epoch
            - After large model forward/backward passes
            - Before switching models
        """
        if self.has_gpu:
            # Clear cache
            torch.cuda.empty_cache()
            # Synchronize
            torch.cuda.synchronize()
            # Python garbage collection
            import gc
            gc.collect()
            # Reset peak stats for next operation
            torch.cuda.reset_peak_memory_stats()
            logger.debug("🧹 Comprehensive cleanup completed")

    def get_memory_stats(self) -> dict:
        """
        Get detailed GPU memory statistics

        Returns:
            Dict with memory usage in GiB (binary) and percentages
        """
        if not self.has_gpu:
            return {}

        allocated = torch.cuda.memory_allocated(0) / (1024**3)
        reserved = torch.cuda.memory_reserved(0) / (1024**3)
        max_allocated = torch.cuda.max_memory_allocated(0) / (1024**3)
        total = self.gpu_memory_gb

        return {
            'allocated_gib': round(allocated, 2),
            'reserved_gib': round(reserved, 2),
            'max_allocated_gib': round(max_allocated, 2),
            'total_gib': round(total, 1),
            'free_gib': round(total - allocated, 2),
            'utilization_percent': round((allocated / total) * 100, 1),
        }

    def vram_usage_gib(self) -> Tuple[float, float]:
        """
        Get current VRAM usage in GiB (binary)

        Returns:
            (used_gib, reserved_gib)
        """
        if not self.has_gpu:
            return (0.0, 0.0)

        used = torch.cuda.memory_allocated(0) / (1024**3)
        reserved = torch.cuda.memory_reserved(0) / (1024**3)
        return (round(used, 2), round(reserved, 2))

    def log_memory_stats(self):
        """Log current memory statistics"""
        if not self.has_gpu:
            return

        stats = self.get_memory_stats()
        logger.info(f"\n📊 VRAM Usage:")
        logger.info(f"   Allocated: {stats['allocated_gib']:.2f} GiB / {stats['total_gib']:.1f} GiB ({stats['utilization_percent']:.1f}%)")
        logger.info(f"   Reserved: {stats['reserved_gib']:.2f} GiB")
        logger.info(f"   Peak: {stats['max_allocated_gib']:.2f} GiB")
        logger.info(f"   Free: {stats['free_gib']:.2f} GiB")


# ==================== Global Instance ====================

_compute_manager: Optional[ComputeManager] = None


def initialize_compute(mode: Literal['auto', 'cpu', 'gpu', 'hybrid'] = 'auto') -> ComputeManager:
    """
    Initialize global compute manager

    Recommended modes:
        - 'hybrid': Best for RTX 4060 (GPU for DL/RL, CPU for ML/TA/Backtest)
        - 'auto': Auto-detect optimal configuration
        - 'cpu': Force CPU (for testing or no GPU)
        - 'gpu': Force GPU for everything

    Environment variable override: COMPUTE_MODE=hybrid/auto/cpu/gpu

    Returns:
        ComputeManager instance
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
    """Get global compute manager (initialize if needed)"""
    global _compute_manager
    if _compute_manager is None:
        _compute_manager = initialize_compute()
    return _compute_manager


# ==================== Utility Functions ====================

def test_gpu_setup():
    """
    Test GPU setup and print diagnostics

    Usage:
        python -m backend.config.compute_config
    """
    print("\n" + "="*70)
    print("🔧 GPU Setup Test - Sigma Analyst")
    print("="*70)

    print("\n1️⃣  PyTorch Installation:")
    print(f"   PyTorch Version: {torch.__version__}")
    print(f"   CUDA Available: {torch.cuda.is_available()}")

    if torch.cuda.is_available():
        print(f"   CUDA Version: {torch.version.cuda}")
        print(f"   cuDNN Version: {torch.backends.cudnn.version()}")
        print(f"   Device Count: {torch.cuda.device_count()}")
        print(f"   Device Name: {torch.cuda.get_device_name(0)}")

        props = torch.cuda.get_device_properties(0)
        # Use GiB (binary) for consistency with ComputeManager
        vram_gib = props.total_memory / (1024**3)
        print(f"   VRAM: {vram_gib:.1f} GiB ({props.total_memory / 1e9:.1f} GB)")
        print(f"   Compute Capability: {props.major}.{props.minor}")

        # Test BF16 support
        cc_major = props.major
        supports_bf16 = cc_major >= 8
        print(f"   BF16 Support: {'✅ Yes' if supports_bf16 else '❌ No (FP16 fallback)'}")
        print(f"   TF32 Support: {'✅ Yes' if cc_major >= 8 else '❌ No'}")
    else:
        print("   ❌ No CUDA GPU detected!")
        print("\n   💡 To install PyTorch with CUDA:")
        print("      pip install --index-url https://download.pytorch.org/whl/cu124 torch torchvision torchaudio")

    print("\n2️⃣  Compute Manager Test:")
    compute = initialize_compute(mode='hybrid')

    print("\n3️⃣  Memory Test:")
    if torch.cuda.is_available():
        # Allocate small tensor
        x = torch.randn(1000, 1000, device='cuda')
        y = x @ x.T

        stats = compute.get_memory_stats()
        print(f"   Test allocation: {stats['allocated_gib']:.2f} GiB")
        print(f"   Free VRAM: {stats['free_gib']:.2f} GiB")

        del x, y
        compute.optimize_memory()
        print("   ✅ Memory test passed")
    else:
        print("   ⏭️  Skipped (no GPU)")

    print("\n4️⃣  BF16/FP16 Test:")
    if torch.cuda.is_available():
        amp_dtype = compute.amp_dtype()
        print(f"   Using: {amp_dtype}")

        # Test forward pass
        model = torch.nn.Linear(100, 10).cuda()
        x = torch.randn(32, 100, device='cuda')

        with torch.autocast(device_type='cuda', dtype=amp_dtype):
            y = model(x)

        print(f"   ✅ Mixed precision test passed")

        del model, x, y
        compute.optimize_memory()
    else:
        print("   ⏭️  Skipped (no GPU)")

    print("\n5️⃣  Matmul Benchmark (TF32):")
    if torch.cuda.is_available():
        import time

        # Warm-up
        a = torch.randn(1024, 1024, device='cuda')
        b = torch.randn(1024, 1024, device='cuda')
        _ = a @ b
        torch.cuda.synchronize()

        # Benchmark
        a = torch.randn(4096, 4096, device='cuda')
        b = torch.randn(4096, 4096, device='cuda')
        torch.cuda.synchronize()
        t0 = time.time()
        c = a @ b
        torch.cuda.synchronize()
        elapsed_ms = (time.time() - t0) * 1e3

        print(f"   4096x4096 matmul: {elapsed_ms:.1f} ms")
        if elapsed_ms < 100:
            print(f"   ✅ TF32 working (fast)")
        elif elapsed_ms < 200:
            print(f"   ⚠️  Slower than expected (check TF32)")
        else:
            print(f"   ❌ Very slow (TF32 may not be enabled)")

        del a, b, c
        compute.optimize_memory()
    else:
        print("   ⏭️  Skipped (no GPU)")

    print("\n" + "="*70)
    print("✅ Setup test complete!")
    print("="*70 + "\n")


# Run test if executed directly
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    test_gpu_setup()
