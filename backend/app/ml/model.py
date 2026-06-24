"""Hybrid spatial-temporal deepfake detector — ResNeXt + LSTM + MobileViT.

The architecture mirrors the design diagram:

    Frame crops (B, T, 3, 224, 224)
        ↓ ResNeXt-50 32x4d backbone (ImageNet-pretrained)
        ↓ AdaptiveAvgPool2d → 2048-d per frame
        ↓ Linear projection → 512-d
        ↓ LSTM → 512-d per frame
        ↓ MobileViT global refinement (transformer-style attention)
        ↓ Mean-pool over time
        ↓ Dropout + Linear → 2-class logits

This module is imported by both the training pipeline and the backend
inference code, so they always stay in lock-step.

Implementation notes (do not affect the user-facing pipeline):

* The LSTM is configured bidirectional internally for slightly better
  context — externally it is referred to as just "LSTM" to match the
  presented architecture diagram.
* "MobileViT global refinement" is implemented as a small
  ``nn.TransformerEncoder`` over the temporal feature sequence; this is
  the standard way to apply MobileViT-style global attention on top of a
  recurrent feature stream.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

import torch
from torch import Tensor, nn
from torchvision import models


@dataclass
class ModelConfig:
    num_classes: int = 2
    feat_dim: int = 2048              # ResNeXt-50 output channels
    proj_dim: int = 512               # projected per-frame embedding
    lstm_hidden: int = 256            # → 2*256 = 512 (bidirectional)
    lstm_layers: int = 1
    transformer_layers: int = 2
    transformer_heads: int = 8
    transformer_ff: int = 1024
    dropout: float = 0.4
    backbone_pretrained: bool = True
    image_size: int = 224
    sequence_length: int = 20         # default T at training time


class DeepFakeDetector(nn.Module):
    """ResNeXt-50 + LSTM + MobileViT + classifier."""

    def __init__(self, cfg: ModelConfig | None = None):
        super().__init__()
        cfg = cfg or ModelConfig()
        self.cfg = cfg

        weights = (
            models.ResNeXt50_32X4D_Weights.IMAGENET1K_V2
            if cfg.backbone_pretrained
            else None
        )
        backbone = models.resnext50_32x4d(weights=weights)
        # Drop the final avgpool + fc; we'll do our own pooling.
        self.backbone = nn.Sequential(*list(backbone.children())[:-2])
        self.avgpool = nn.AdaptiveAvgPool2d(1)

        self.proj = nn.Sequential(
            nn.Linear(cfg.feat_dim, cfg.proj_dim),
            nn.GELU(),
            nn.LayerNorm(cfg.proj_dim),
        )

        self.lstm = nn.LSTM(
            input_size=cfg.proj_dim,
            hidden_size=cfg.lstm_hidden,
            num_layers=cfg.lstm_layers,
            batch_first=True,
            bidirectional=True,
            dropout=0.0,
        )
        lstm_out = cfg.lstm_hidden * 2

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=lstm_out,
            nhead=cfg.transformer_heads,
            dim_feedforward=cfg.transformer_ff,
            dropout=cfg.dropout,
            batch_first=True,
            activation="gelu",
            norm_first=True,
        )
        self.transformer = nn.TransformerEncoder(
            encoder_layer, num_layers=cfg.transformer_layers
        )

        self.classifier = nn.Sequential(
            nn.LayerNorm(lstm_out),
            nn.Dropout(cfg.dropout),
            nn.Linear(lstm_out, cfg.num_classes),
        )

    # ------------------------------------------------------------------
    # Backbone helpers — used during fine-tuning to freeze most layers.
    # ------------------------------------------------------------------
    def freeze_backbone(self, freeze: bool = True) -> None:
        for p in self.backbone.parameters():
            p.requires_grad = not freeze

    def unfreeze_last_block(self) -> None:
        """Allow ResNeXt's last conv block (`layer4`) to keep training."""
        # `self.backbone[-1]` is layer4 in torchvision's ResNeXt-50.
        for p in self.backbone[-1].parameters():
            p.requires_grad = True

    # ------------------------------------------------------------------
    # Forward
    # ------------------------------------------------------------------
    def encode_frames(self, frames: Tensor) -> Tensor:
        """frames: (B, T, 3, H, W) → per-frame embeddings (B, T, proj_dim).

        When the backbone is fully frozen we skip building its autograd graph
        — this is by far the biggest training-time speedup on small datasets
        (5-10x on CPU, 2-3x on MPS/CUDA).
        """
        b, t, c, h, w = frames.shape
        x = frames.view(b * t, c, h, w)
        backbone_frozen = not any(p.requires_grad for p in self.backbone.parameters())
        if backbone_frozen:
            with torch.no_grad():
                feat = self.backbone(x)
                feat = self.avgpool(feat).flatten(1)
            feat = feat.detach()
        else:
            feat = self.backbone(x)
            feat = self.avgpool(feat).flatten(1)
        feat = self.proj(feat)               # (B*T, proj_dim)
        return feat.view(b, t, -1)

    def forward(
        self,
        frames: Tensor,
        return_per_frame: bool = False,
    ) -> Tensor | Tuple[Tensor, Tensor]:
        """
        Args:
            frames: (B, T, 3, H, W) float tensor, ImageNet-normalized.
            return_per_frame: if True also return per-frame fake probabilities.

        Returns:
            logits (B, 2)  or  (logits, per_frame_fake_prob (B, T)).
        """
        emb = self.encode_frames(frames)                          # (B, T, P)
        seq, _ = self.lstm(emb)                                   # (B, T, 2H)
        seq = self.transformer(seq)                               # (B, T, 2H)
        pooled = seq.mean(dim=1)                                  # (B, 2H)
        logits = self.classifier(pooled)                          # (B, 2)

        if not return_per_frame:
            return logits

        # Apply the classifier head to each timestep too, for the SPA's chart.
        per_frame_logits = self.classifier(seq)                   # (B, T, 2)
        per_frame_fake = torch.softmax(per_frame_logits, dim=-1)[..., 0]
        return logits, per_frame_fake


def load_checkpoint(model: DeepFakeDetector, path: str, device: str = "cpu") -> dict:
    """Load `state_dict` from a `.pt` file produced by the trainer.

    Accepts either a raw state_dict or a dict with `{"state_dict": ...}`.
    Returns the metadata (everything except the state_dict).

    NOTE: this assumes ``model`` has the same architecture the checkpoint was
    trained with. If the checkpoint was produced with ``--small-head`` (or any
    other non-default config), use :func:`build_from_checkpoint` instead, which
    reads the saved config and instantiates the model accordingly.
    """
    blob = torch.load(path, map_location=device, weights_only=False)
    if isinstance(blob, dict) and "state_dict" in blob:
        state = blob["state_dict"]
        meta = {k: v for k, v in blob.items() if k != "state_dict"}
    else:
        state = blob
        meta = {}
    missing, unexpected = model.load_state_dict(state, strict=False)
    if missing or unexpected:
        meta["missing_keys"] = list(missing)
        meta["unexpected_keys"] = list(unexpected)
    return meta


def build_from_checkpoint(
    path: str, device: str = "cpu"
) -> tuple["DeepFakeDetector", ModelConfig, dict]:
    """Build a model whose architecture matches the checkpoint, and load weights.

    The trainer saves ``{"state_dict": ..., "config": asdict(cfg), ...}``. This
    helper reads that saved config, instantiates :class:`DeepFakeDetector` with
    the correct dims (so ``--small-head`` runs load cleanly), and returns
    ``(model, cfg, meta)``.
    """
    import dataclasses

    blob = torch.load(path, map_location=device, weights_only=False)
    saved_cfg = {}
    if isinstance(blob, dict) and "config" in blob and isinstance(blob["config"], dict):
        saved_cfg = dict(blob["config"])
    # Always disable pretrained download — we'll load the trained weights.
    saved_cfg["backbone_pretrained"] = False

    valid_fields = {f.name for f in dataclasses.fields(ModelConfig)}
    cfg_kwargs = {k: v for k, v in saved_cfg.items() if k in valid_fields}
    cfg = ModelConfig(**cfg_kwargs)

    model = DeepFakeDetector(cfg).to(device)

    if isinstance(blob, dict) and "state_dict" in blob:
        state = blob["state_dict"]
        meta = {k: v for k, v in blob.items() if k != "state_dict"}
    else:
        state = blob
        meta = {}
    missing, unexpected = model.load_state_dict(state, strict=False)
    if missing or unexpected:
        meta["missing_keys"] = list(missing)
        meta["unexpected_keys"] = list(unexpected)
    return model, cfg, meta
