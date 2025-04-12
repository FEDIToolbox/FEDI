
import math
import torch
import torch.nn as nn
import healpy as hp
import numpy as np

from .sh import spherical_harmonic
from .layers import SphConv
from .sh import ls, sft, isft

import torch.nn.functional as F

class MLPModel(torch.nn.Module):
    """A simple multi-layer perceptron model."""

    def __init__(self, n_in: int, n_out: int):
        """Initialize the model layers.

        Args:
            n_in (int): Number of input features.
            n_out (int): Number of output units.
        """
        super().__init__()
        self.fc1 = torch.nn.Linear(n_in, 256)
        self.bn1 = torch.nn.BatchNorm1d(256)
        self.fc2 = torch.nn.Linear(256, 256)
        self.bn2 = torch.nn.BatchNorm1d(256)
        self.fc3 = torch.nn.Linear(256, 256)
        self.bn3 = torch.nn.BatchNorm1d(256)
        self.fc4 = torch.nn.Linear(256, n_out)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Make a forward pass.

        Args:
            x: Input signals.

        Returns:
            Signals after passing through the network.
        """

        x = self.fc1(x)
        x = self.bn1(x)
        x = torch.nn.functional.relu(x)
        x = self.fc2(x)
        x = self.bn2(x)
        x = torch.nn.functional.relu(x)
        x = self.fc3(x)
        x = self.bn3(x)
        x = torch.nn.functional.relu(x)
        x = self.fc4(x)
        return x
        

class SphericalCNN_FOD_Neonatal(torch.nn.Module):
    def __init__(self, c_in: int, n_out: int):
        super().__init__()
        self.register_buffer("ls", ls)
        self.register_buffer("sft", sft)
        self.register_buffer("isft", isft)

        # Shell-specific processing
        self.conv_shell1 = SphConv(1, 16)
        self.conv_shell2 = SphConv(1, 16)
        self.conv_shell3 = SphConv(1, 16)

        # Attention-based fusion
        self.shell_attention = ShellAttention()

        # Encoder
        self.conv2 = SphConv(48, 32)
        self.conv3 = SphConv(32, 64)
        self.conv3a = SphConv(64, 64)
        # Decoder
        self.conv4 = SphConv(64, 32)
        self.conv4a = SphConv(32, 32)
        self.conv5 = SphConv(32, 16)
        self.conv6 = SphConv(16, 1)

        # FC layers
        self.fc1 = torch.nn.Linear(128, 128)
        self.bn1 = torch.nn.BatchNorm1d(128)
        self.fc2 = torch.nn.Linear(128, 128)
        self.bn2 = torch.nn.BatchNorm1d(128)
        self.fc3 = torch.nn.Linear(128, n_out)

    def nonlinearity(self, x: torch.Tensor) -> torch.Tensor:
        return (
            self.sft
            @ torch.nn.functional.leaky_relu(
                self.isft @ x.unsqueeze(-1),
                negative_slope=0.1,
            )
        ).squeeze(-1)

    def global_pooling(self, x: torch.Tensor) -> torch.Tensor:
        return torch.mean(self.isft @ x.unsqueeze(-1), dim=2).squeeze(-1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Process shells with attention fusion
        x_shell1 = self.conv_shell1(x[:, 0:1, :])
        x_shell2 = self.conv_shell2(x[:, 1:2, :])
        x_shell3 = self.conv_shell3(x[:, 2:3, :])
        
        # Attention-based fusion instead of simple concatenation
        x = self.shell_attention([x_shell1, x_shell2, x_shell3])

        # Deeper encoder
        x = self.conv2(x)
        x1 = self.nonlinearity(x)
        x = self.conv3(x1)
        x = self.conv3a(x)  
        x2 = self.nonlinearity(x)

        # Deeper decoder
        x = self.conv4(x2)
        x = self.conv4a(x) 
        x3 = self.nonlinearity(x)
        x = self.conv5(x3)
        x = self.nonlinearity(x)

        odfs_sh = self.conv6(x).squeeze(1)[:, 0:45]

        # FC network
        x = torch.cat([self.global_pooling(x1), 
                      self.global_pooling(x2),
                      self.global_pooling(x3)], dim=1)
        
        x = torch.nn.functional.relu(self.bn1(self.fc1(x)))
        x = torch.nn.functional.relu(self.bn2(self.fc2(x)))
        odfs_sh += self.fc3(x)

        return odfs_sh


class ShellAttention(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.attention_net = torch.nn.Sequential(
            torch.nn.Linear(48, 24),
            torch.nn.LeakyReLU(0.1),
            torch.nn.Linear(24, 3),
            torch.nn.Softmax(dim=-1)
        )
        
    def forward(self, shells):
        # shells: list of [batch, 16, coefficients]
        concat = torch.cat([s.mean(-1) for s in shells], dim=-1)
        weights = self.attention_net(concat)
        
        # Apply attention weights
        weighted = []
        for i, shell in enumerate(shells):
            weighted.append(shell * weights[:, i].view(-1, 1, 1))
            
        return torch.cat(weighted, dim=1)