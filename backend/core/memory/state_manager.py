"""
State persistence and checkpoint management
"""

from typing import Dict, Optional, Any
from datetime import datetime
import torch
import json
import os
from pathlib import Path
from ...core.config import settings


class StateManager:
    """
    Agent state persistence and checkpoint management
    """

    def __init__(self, checkpoint_dir: Optional[str] = None):
        self.checkpoint_dir = checkpoint_dir or settings.checkpoints_dir
        Path(self.checkpoint_dir).mkdir(parents=True, exist_ok=True)

    def save_checkpoint(
        self,
        checkpoint_id: str,
        agent_state: Dict[str, Any],
        model_state: Optional[Dict[str, Any]] = None,
        optimizer_state: Optional[Dict[str, Any]] = None,
        metrics: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Save agent checkpoint

        Args:
            checkpoint_id: Unique checkpoint identifier
            agent_state: Agent's internal state
            model_state: Model weights (state_dict)
            optimizer_state: Optimizer state
            metrics: Performance metrics
            metadata: Additional metadata

        Returns:
            Path to saved checkpoint
        """

        checkpoint = {
            'checkpoint_id': checkpoint_id,
            'timestamp': datetime.now().isoformat(),
            'agent_state': agent_state,
            'metrics': metrics or {},
            'metadata': metadata or {}
        }

        # Save model and optimizer separately (large binary data)
        checkpoint_path = os.path.join(self.checkpoint_dir, f"{checkpoint_id}.pt")

        if model_state or optimizer_state:
            torch_checkpoint = {}
            if model_state:
                torch_checkpoint['model_state'] = model_state
            if optimizer_state:
                torch_checkpoint['optimizer_state'] = optimizer_state

            torch.save(torch_checkpoint, checkpoint_path)

        # Save JSON metadata
        metadata_path = os.path.join(self.checkpoint_dir, f"{checkpoint_id}_meta.json")
        with open(metadata_path, 'w') as f:
            json.dump(checkpoint, f, indent=2)

        print(f"✅ Checkpoint saved: {checkpoint_id}")
        return checkpoint_path

    def load_checkpoint(self, checkpoint_id: str) -> Dict[str, Any]:
        """
        Load checkpoint

        Returns:
            {
                'agent_state': {...},
                'model_state': {...},
                'optimizer_state': {...},
                'metrics': {...},
                'metadata': {...}
            }
        """

        # Load metadata
        metadata_path = os.path.join(self.checkpoint_dir, f"{checkpoint_id}_meta.json")
        if not os.path.exists(metadata_path):
            raise FileNotFoundError(f"Checkpoint {checkpoint_id} not found")

        with open(metadata_path, 'r') as f:
            checkpoint = json.load(f)

        # Load PyTorch checkpoint if exists
        checkpoint_path = os.path.join(self.checkpoint_dir, f"{checkpoint_id}.pt")
        if os.path.exists(checkpoint_path):
            torch_checkpoint = torch.load(checkpoint_path, map_location='cpu')
            checkpoint['model_state'] = torch_checkpoint.get('model_state')
            checkpoint['optimizer_state'] = torch_checkpoint.get('optimizer_state')
        else:
            checkpoint['model_state'] = None
            checkpoint['optimizer_state'] = None

        print(f"✅ Checkpoint loaded: {checkpoint_id}")
        return checkpoint

    def list_checkpoints(self) -> list[Dict[str, Any]]:
        """List all available checkpoints"""
        checkpoints = []

        for file in os.listdir(self.checkpoint_dir):
            if file.endswith('_meta.json'):
                checkpoint_id = file.replace('_meta.json', '')
                metadata_path = os.path.join(self.checkpoint_dir, file)

                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)

                checkpoints.append({
                    'checkpoint_id': checkpoint_id,
                    'timestamp': metadata['timestamp'],
                    'metrics': metadata.get('metrics', {})
                })

        # Sort by timestamp (newest first)
        checkpoints.sort(key=lambda x: x['timestamp'], reverse=True)
        return checkpoints

    def delete_checkpoint(self, checkpoint_id: str):
        """Delete checkpoint"""
        metadata_path = os.path.join(self.checkpoint_dir, f"{checkpoint_id}_meta.json")
        checkpoint_path = os.path.join(self.checkpoint_dir, f"{checkpoint_id}.pt")

        if os.path.exists(metadata_path):
            os.remove(metadata_path)

        if os.path.exists(checkpoint_path):
            os.remove(checkpoint_path)

        print(f"✅ Checkpoint deleted: {checkpoint_id}")

    def get_best_checkpoint(self, metric: str = 'sharpe_ratio') -> Optional[str]:
        """Get checkpoint with best performance on given metric"""
        checkpoints = self.list_checkpoints()

        if not checkpoints:
            return None

        # Find checkpoint with highest metric value
        best = max(checkpoints, key=lambda x: x['metrics'].get(metric, float('-inf')))
        return best['checkpoint_id']

    def save_agent_snapshot(self, agent_state: Dict[str, Any]) -> str:
        """
        Quick snapshot save (no model weights)
        Useful for monitoring mode state persistence
        """
        snapshot_id = f"snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        snapshot_path = os.path.join(self.checkpoint_dir, f"{snapshot_id}.json")

        snapshot = {
            'snapshot_id': snapshot_id,
            'timestamp': datetime.now().isoformat(),
            'agent_state': agent_state
        }

        with open(snapshot_path, 'w') as f:
            json.dump(snapshot, f, indent=2)

        return snapshot_id

    def load_latest_snapshot(self) -> Optional[Dict[str, Any]]:
        """Load most recent snapshot"""
        snapshots = [
            f for f in os.listdir(self.checkpoint_dir)
            if f.startswith('snapshot_') and f.endswith('.json')
        ]

        if not snapshots:
            return None

        latest = sorted(snapshots)[-1]
        snapshot_path = os.path.join(self.checkpoint_dir, latest)

        with open(snapshot_path, 'r') as f:
            snapshot = json.load(f)

        return snapshot
