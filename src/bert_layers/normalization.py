# Copyright 2024 **AUTHORS_TODO**
# License: Apache-2.0

# RMSNorm Implementation: Copyright Meta (from their Llama RMSNorm implementation)
# License: LLAMA 2 COMMUNITY LICENSE AGREEMENT


from typing import Optional
import inspect
import warnings
import torch
import torch.nn as nn

from .configuration_bert import FlexBertConfig


class RMSNorm(nn.Module):
    """Llama2 RMSNorm implementation"""

    def __init__(self, dim: int, eps: float = 1e-6):
        """
        Initialize the RMSNorm normalization layer.

        Args:
            dim (int): The dimension of the input tensor.
            eps (float, optional): A small value added to the denominator for numerical stability. Default is 1e-6.

        Attributes:
            eps (float): A small value added to the denominator for numerical stability.
            weight (nn.Parameter): Learnable scaling parameter.

        """
        super().__init__()
        self.eps = eps
        self.weight = nn.Parameter(torch.ones(dim))

    def _norm(self, x):
        """
        Apply the RMSNorm normalization to the input tensor.

        Args:
            x (torch.Tensor): The input tensor.

        Returns:
            torch.Tensor: The normalized tensor.

        """
        return x * torch.rsqrt(x.pow(2).mean(-1, keepdim=True) + self.eps)

    def forward(self, x):
        """
        Forward pass through the RMSNorm layer.

        Args:
            x (torch.Tensor): The input tensor.

        Returns:
            torch.Tensor: The output tensor after applying RMSNorm.

        """
        output = self._norm(x.float()).type_as(x)
        return output * self.weight


NORM2CLS = {
    "layernorm": nn.LayerNorm,
    "rmsnorm": RMSNorm,
}


def get_norm_layer(config: FlexBertConfig) -> nn.Module:
    try:
        norm_class = NORM2CLS[config.normalization]
        signature = inspect.signature(norm_class)
        if hasattr(config, "norm_kwargs"):
            norm_kwargs = {k: v for k, v in config.norm_kwargs.items() if k in signature.parameters}
        else:
            norm_kwargs = {}
        return norm_class(config.hidden_size, **norm_kwargs)
    except KeyError:
        raise ValueError(f"Invalid normalization layer type: {config.normalization}, must be one of {NORM2CLS.keys()}.")
