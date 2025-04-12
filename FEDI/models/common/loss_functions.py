import torch
import numpy as np
from scnn.sh import isft


def mse_loss(preds: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
    """Calculate mean squared error loss using only the first 45 SH coefficients.

    Args:
        preds: Predicted values. Shape: (batch size, 45).
        targets: Target values. Shape: (batch size, 45).

    Returns:
        Mean squared error.
    """
    preds_45 = preds[:, :45]  # Keep only the first 45 coefficients
    targets_45 = targets[:, :45]  # Keep only the first 45 coefficients

    # Apply inverse Spherical Fourier Transform (ISFT)
    preds_fod = (isft.cpu()[:, :45] @ preds_45.cpu().unsqueeze(-1)).squeeze(-1)
    targets_fod = (isft.cpu()[:, :45] @ targets_45.cpu().unsqueeze(-1)).squeeze(-1)

    # Compute MSE Loss
    loss = torch.mean((preds_fod - targets_fod) ** 2)

    return loss
