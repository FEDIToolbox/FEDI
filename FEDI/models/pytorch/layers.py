import math
import torch


class SphConv(torch.nn.Module):
    def __init__(self, c_in: int, c_out: int, l_max: int = 8):
        super().__init__()
        self.l_max = l_max
        self.expansion_mask = self._create_expansion_mask()
        
        # Add residual connection capability
        self.residual = (c_in == c_out)
        
        # Enhanced weight initialization
        self.weights = torch.nn.Parameter(
            torch.empty(c_out, c_in, (l_max//2)+1)
        )
        # torch.nn.init.xavier_uniform_(self.weights, gain=torch.nn.init.calculate_gain('relu'))
        torch.nn.init.kaiming_uniform_(self.weights, a=0.01)
        
        # Learnable scale factor with initialization
        self.scale = torch.nn.Parameter(torch.tensor(math.sqrt(4 * math.pi)))
        
    def _create_expansion_mask(self):
        mask = []
        for l in range(0, self.l_max+1, 2):
            mask += [l//2] * (2*l + 1)  # Expand weights per degree
        return torch.tensor(mask)
    
    def forward(self, x):
        expanded_weights = self.weights[:, :, self.expansion_mask]
        out = torch.einsum('bci,oci->boi', x, expanded_weights) * self.scale
        return out + x if self.residual else out  # Residual connection