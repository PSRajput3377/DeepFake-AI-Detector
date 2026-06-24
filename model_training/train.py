"""Train the DeepFake detector on pre-extracted face crops.

Usage::

    python train.py --data processed_faces --epochs 30 --batch-size 4
    python train.py --data processed_sdfvd processed_ffpp --epochs 40 --batch-size 8

Important defaults:

* The ResNeXt backbone is **frozen** for the first 3 epochs (warm-up the
  classifier), then ``layer4`` is unfrozen for the rest of training.
* AdamW + cosine LR schedule with warmup.
* Stratified train/val split (80/20) on the *video* level — preventing
  leakage between train and val clips of the same video.
* Best checkpoint (highest val accuracy) saved to
  ``checkpoints/best.pt`` along with the training config and metrics.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import time
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader
from tqdm import tqdm

from _paths import DeepFakeDetector, ModelConfig
from dataset import LABEL_TO_INDEX, FaceClipsDataset, discover_clips_many
from transforms import eval_transform, train_transform


# ─── Device ───────────────────────────────────────────────────────────
def _autodetect_device() -> str:
    """Pick the best available device: cuda → mps (Apple Silicon) → cpu."""
    if torch.cuda.is_available():
        return "cuda"
    if getattr(torch.backends, "mps", None) is not None and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


# ─── Reproducibility ──────────────────────────────────────────────────
def seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


# ─── Splitting ────────────────────────────────────────────────────────
def stratified_split(
    clips: List[Tuple[Path, int]],
    val_frac: float,
    seed: int,
) -> Tuple[List[Tuple[Path, int]], List[Tuple[Path, int]]]:
    rng = random.Random(seed)
    by_label: Dict[int, List[Tuple[Path, int]]] = defaultdict(list)
    for c in clips:
        by_label[c[1]].append(c)
    train, val = [], []
    for items in by_label.values():
        rng.shuffle(items)
        cut = max(1, int(round(len(items) * val_frac)))
        val.extend(items[:cut])
        train.extend(items[cut:])
    rng.shuffle(train)
    rng.shuffle(val)
    return train, val


# ─── Optimizer / scheduler helpers ────────────────────────────────────
def cosine_with_warmup(optimizer, total_steps: int, warmup_steps: int):
    def lr_lambda(step: int) -> float:
        if step < warmup_steps:
            return step / max(1, warmup_steps)
        progress = (step - warmup_steps) / max(1, total_steps - warmup_steps)
        return 0.5 * (1 + math.cos(math.pi * progress))

    return torch.optim.lr_scheduler.LambdaLR(optimizer, lr_lambda)


def build_optimizer(model: nn.Module, lr_head: float, lr_backbone: float, weight_decay: float):
    head_params, backbone_params = [], []
    for name, p in model.named_parameters():
        if not p.requires_grad:
            continue
        if name.startswith("backbone"):
            backbone_params.append(p)
        else:
            head_params.append(p)
    return torch.optim.AdamW(
        [
            {"params": head_params, "lr": lr_head, "weight_decay": weight_decay},
            {"params": backbone_params, "lr": lr_backbone, "weight_decay": weight_decay},
        ]
    )


# ─── Metrics ──────────────────────────────────────────────────────────
@torch.no_grad()
def evaluate(model, loader, device) -> Dict[str, float]:
    model.eval()
    correct = total = 0
    losses = []
    criterion = nn.CrossEntropyLoss()
    tp = fp = fn = tn = 0
    for clips, labels in tqdm(loader, desc="val", leave=False):
        clips = clips.to(device, non_blocking=True)
        labels = labels.to(device, non_blocking=True)
        logits = model(clips)
        loss = criterion(logits, labels)
        losses.append(loss.item())
        preds = logits.argmax(dim=1)
        correct += (preds == labels).sum().item()
        total += labels.numel()
        # Class 0 = fake (the "positive" class for forensic precision).
        tp += int(((preds == 0) & (labels == 0)).sum())
        fp += int(((preds == 0) & (labels == 1)).sum())
        fn += int(((preds == 1) & (labels == 0)).sum())
        tn += int(((preds == 1) & (labels == 1)).sum())

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    tpr = tp / (tp + fn) if (tp + fn) else 0.0
    tnr = tn / (tn + fp) if (tn + fp) else 0.0
    balanced_acc = 0.5 * (tpr + tnr)
    return {
        "loss": float(np.mean(losses)) if losses else 0.0,
        "accuracy": correct / max(1, total),
        "balanced_accuracy": balanced_acc,
        "precision_fake": precision,
        "recall_fake": recall,
        "f1_fake": f1,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
    }


def _metric_value(metrics: Dict[str, float], name: str) -> float:
    """Higher is better for all supported checkpoint metrics."""
    if name == "loss":
        return -metrics["loss"]
    if name == "balanced_accuracy":
        return metrics["balanced_accuracy"]
    if name == "f1_fake":
        return metrics["f1_fake"]
    return metrics["accuracy"]


def _mixup_batch(
    clips: torch.Tensor,
    labels: torch.Tensor,
    alpha: float,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, float]:
    """Beta-mixup on clip tensors. Returns mixed clips, labels_a, labels_b, lam."""
    if alpha <= 0 or clips.size(0) < 2:
        return clips, labels, labels, 1.0
    lam = float(np.random.beta(alpha, alpha))
    perm = torch.randperm(clips.size(0), device=clips.device)
    mixed = lam * clips + (1.0 - lam) * clips[perm]
    return mixed, labels, labels[perm], lam


# ─── Main ─────────────────────────────────────────────────────────────
def main() -> int:
    parser = argparse.ArgumentParser(description="Train DeepFake detector.")
    parser.add_argument(
        "--data",
        nargs="+",
        type=Path,
        required=True,
        help="One or more preprocessed directories (each with real/ and fake/ clip folders). "
        "Multiple roots are merged — e.g. SDFVD + FaceForensics++ crops.",
    )
    parser.add_argument("--out", type=Path, default=Path("checkpoints"))
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--sequence-length", type=int, default=20)
    parser.add_argument("--clips-per-video", type=int, default=4,
                        help="Random window samples per video per epoch (data multiplier).")
    parser.add_argument("--val-frac", type=float, default=0.25,
                        help="Fraction held out for validation (video-level stratified).")
    parser.add_argument("--metric", type=str, default="f1_fake",
                        choices=("f1_fake", "balanced_accuracy", "accuracy", "loss"),
                        help="Metric used to pick best.pt (f1_fake is best for small val sets).")
    parser.add_argument("--mixup-alpha", type=float, default=0.15,
                        help="Mixup strength (0 = off). Helps regularize tiny datasets.")
    parser.add_argument("--label-smoothing", type=float, default=0.1,
                        help="Cross-entropy label smoothing.")
    parser.add_argument("--frame-drop-prob", type=float, default=0.12,
                        help="Temporal frame dropout probability during training.")
    parser.add_argument("--strong-aug", action="store_true", default=True,
                        help="Stronger color/erase augmentations (default on).")
    parser.add_argument("--no-strong-aug", action="store_false", dest="strong_aug",
                        help="Disable strong augmentations.")
    parser.add_argument("--lr-head", type=float, default=1e-4,
                        help="Head learning rate (lower = less overfitting on small data).")
    parser.add_argument("--lr-backbone", type=float, default=3e-5)
    parser.add_argument("--weight-decay", type=float, default=5e-4)
    parser.add_argument("--warmup-frozen", type=int, default=3,
                        help="Epochs with the ResNeXt backbone fully frozen.")
    parser.add_argument("--patience", type=int, default=8,
                        help="Early-stopping patience on val accuracy.")
    parser.add_argument("--num-workers", type=int, default=2)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--device", type=str, default=None)
    parser.add_argument("--no-pretrained", action="store_true",
                        help="Train ResNeXt from scratch (NOT recommended).")
    parser.add_argument("--freeze-backbone", action="store_true",
                        help="Keep the ResNeXt backbone fully frozen for the entire "
                             "run (5-10x faster on CPU; recommended for small datasets).")
    parser.add_argument("--small-head", action="store_true",
                        help="Use a much smaller LSTM+MobileViT head (~500K params "
                             "instead of ~6.8M). Strongly recommended when the dataset "
                             "has < 500 videos — prevents catastrophic overfitting.")
    parser.add_argument("--dropout", type=float, default=None,
                        help="Override head dropout (default 0.4, or 0.55 with --small-head).")
    args = parser.parse_args()

    seed_everything(args.seed)
    args.out.mkdir(parents=True, exist_ok=True)

    device = args.device or _autodetect_device()
    print(f"[info] device = {device}")

    clips = discover_clips_many(args.data)
    if not clips:
        roots = ", ".join(str(p) for p in args.data)
        raise SystemExit(f"no clips found under: {roots}")

    print(f"[info] loaded {len(clips)} clips from {len(args.data)} root(s)")

    # Stratified split on the video level.
    train_clips, val_clips = stratified_split(clips, args.val_frac, args.seed)
    n_train_real = sum(1 for _, y in train_clips if y == LABEL_TO_INDEX["real"])
    n_train_fake = len(train_clips) - n_train_real
    n_val_real = sum(1 for _, y in val_clips if y == LABEL_TO_INDEX["real"])
    n_val_fake = len(val_clips) - n_val_real
    print(
        f"[info] train: {len(train_clips)}  (real={n_train_real}, fake={n_train_fake}) | "
        f"val: {len(val_clips)}  (real={n_val_real}, fake={n_val_fake})"
    )

    train_ds = FaceClipsDataset(
        train_clips,
        sequence_length=args.sequence_length,
        transform=train_transform(strong=args.strong_aug),
        train=True,
        clips_per_video=args.clips_per_video,
        frame_drop_prob=args.frame_drop_prob,
    )
    val_ds = FaceClipsDataset(
        val_clips,
        sequence_length=args.sequence_length,
        transform=eval_transform(),
        train=False,
        clips_per_video=1,
    )
    pin = device == "cuda"
    train_loader = DataLoader(
        train_ds, batch_size=args.batch_size, shuffle=True,
        num_workers=args.num_workers, pin_memory=pin, drop_last=True,
    )
    val_loader = DataLoader(
        val_ds, batch_size=max(2, args.batch_size), shuffle=False,
        num_workers=args.num_workers, pin_memory=pin,
    )

    cfg = ModelConfig(
        sequence_length=args.sequence_length,
        backbone_pretrained=not args.no_pretrained,
    )
    if args.small_head:
        cfg.proj_dim = 128
        cfg.lstm_hidden = 64
        cfg.transformer_layers = 1
        cfg.transformer_heads = 4
        cfg.transformer_ff = 256
        cfg.dropout = 0.6
        print("[info] --small-head enabled: tiny LSTM+MobileViT head for small datasets")
    if args.dropout is not None:
        cfg.dropout = args.dropout
    model = DeepFakeDetector(cfg).to(device)
    model.freeze_backbone(True)  # warmup phase
    # Frozen backbone stays in eval() so BatchNorm running stats don't drift.
    model.backbone.eval()
    print(f"[info] trainable params: "
          f"{sum(p.numel() for p in model.parameters() if p.requires_grad):,}")
    if args.freeze_backbone:
        print("[info] --freeze-backbone enabled: ResNeXt stays frozen for the entire run")

    # Class-weighted loss in case of imbalance.
    class_counts = torch.tensor(
        [n_train_fake or 1, n_train_real or 1], dtype=torch.float32
    )
    class_weight = (class_counts.sum() / (2 * class_counts)).to(device)
    criterion = nn.CrossEntropyLoss(
        weight=class_weight, label_smoothing=args.label_smoothing
    )

    optimizer = build_optimizer(
        model, lr_head=args.lr_head, lr_backbone=args.lr_backbone,
        weight_decay=args.weight_decay,
    )
    steps_per_epoch = max(1, len(train_loader))
    scheduler = cosine_with_warmup(
        optimizer,
        total_steps=args.epochs * steps_per_epoch,
        warmup_steps=max(1, steps_per_epoch),
    )
    scaler = torch.amp.GradScaler("cuda", enabled=device == "cuda")

    history: List[dict] = []
    best_score = -1.0
    best_acc = -1.0
    epochs_without_improve = 0
    # MPS autocast can be unstable on some PyTorch builds; CUDA always uses AMP.
    use_amp = device == "cuda"
    amp_device = "cuda"
    print(f"[info] checkpoint metric = {args.metric}  mixup_alpha = {args.mixup_alpha}")
    started = time.time()

    for epoch in range(1, args.epochs + 1):
        if not args.freeze_backbone and epoch == args.warmup_frozen + 1:
            print(f"[info] epoch {epoch}: unfreezing ResNeXt layer4")
            model.unfreeze_last_block()
            optimizer = build_optimizer(
                model, lr_head=args.lr_head, lr_backbone=args.lr_backbone,
                weight_decay=args.weight_decay,
            )
            remaining = (args.epochs - epoch + 1) * steps_per_epoch
            scheduler = cosine_with_warmup(
                optimizer,
                total_steps=remaining,
                warmup_steps=max(1, steps_per_epoch // 2),
            )

        model.train()
        # Frozen layers always stay in eval mode (no BN drift from tiny batches).
        for module in model.backbone.modules():
            for p in module.parameters(recurse=False):
                if not p.requires_grad:
                    module.eval()
                    break
        running, n = 0.0, 0
        correct = 0
        bar = tqdm(train_loader, desc=f"epoch {epoch:02d}/{args.epochs}")
        for clips, labels in bar:
            clips = clips.to(device, non_blocking=True)
            labels = labels.to(device, non_blocking=True)
            optimizer.zero_grad(set_to_none=True)
            clips_m, la, lb, lam = _mixup_batch(clips, labels, args.mixup_alpha)
            with torch.amp.autocast(device_type=amp_device, enabled=use_amp):
                logits = model(clips_m)
                if lam < 1.0:
                    loss = lam * criterion(logits, la) + (1.0 - lam) * criterion(logits, lb)
                else:
                    loss = criterion(logits, labels)
            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            scaler.step(optimizer)
            scaler.update()
            scheduler.step()

            running += loss.item() * labels.size(0)
            n += labels.size(0)
            correct += (logits.argmax(dim=1) == labels).sum().item()
            bar.set_postfix(
                loss=f"{running / max(1, n):.4f}",
                acc=f"{correct / max(1, n):.3f}",
                lr=f"{scheduler.get_last_lr()[0]:.2e}",
            )

        train_loss = running / max(1, n)
        train_acc = correct / max(1, n)
        val_metrics = evaluate(model, val_loader, device)

        score = _metric_value(val_metrics, args.metric)
        epoch_log = {
            "epoch": epoch,
            "train_loss": train_loss,
            "train_acc": train_acc,
            "val_loss": val_metrics["loss"],
            "val_acc": val_metrics["accuracy"],
            "val_balanced_acc": val_metrics["balanced_accuracy"],
            "val_precision_fake": val_metrics["precision_fake"],
            "val_recall_fake": val_metrics["recall_fake"],
            "val_f1_fake": val_metrics["f1_fake"],
            "val_metric_score": score,
            "lr": scheduler.get_last_lr()[0],
        }
        history.append(epoch_log)
        print(
            f"[epoch {epoch:02d}] train_loss={train_loss:.4f} train_acc={train_acc:.3f} | "
            f"val_loss={val_metrics['loss']:.4f} val_acc={val_metrics['accuracy']:.3f} "
            f"bal_acc={val_metrics['balanced_accuracy']:.3f} "
            f"P/R/F1(fake)={val_metrics['precision_fake']:.3f}/"
            f"{val_metrics['recall_fake']:.3f}/{val_metrics['f1_fake']:.3f} "
            f"[{args.metric}={score:.3f}]"
        )

        # Save latest + best.
        torch.save(
            {"state_dict": model.state_dict(), "config": asdict(cfg), "epoch": epoch,
             "val_metrics": val_metrics},
            args.out / "latest.pt",
        )
        if val_metrics["accuracy"] > best_acc:
            best_acc = val_metrics["accuracy"]
        if score > best_score:
            best_score = score
            epochs_without_improve = 0
            torch.save(
                {
                    "state_dict": model.state_dict(),
                    "config": asdict(cfg),
                    "epoch": epoch,
                    "val_accuracy": val_metrics["accuracy"],
                    "val_balanced_accuracy": val_metrics["balanced_accuracy"],
                    "val_precision_fake": val_metrics["precision_fake"],
                    "val_recall_fake": val_metrics["recall_fake"],
                    "val_f1_fake": val_metrics["f1_fake"],
                    "checkpoint_metric": args.metric,
                    "checkpoint_score": score,
                    "args": vars(args)
                    | {"data": [str(p) for p in args.data], "out": str(args.out)},
                },
                args.out / "best.pt",
            )
            print(
                f"[info] new best {args.metric}={score:.3f} "
                f"(val_acc={val_metrics['accuracy']:.3f}) → saved {args.out / 'best.pt'}"
            )
        else:
            epochs_without_improve += 1
            if epochs_without_improve >= args.patience:
                print(f"[info] early stopping (no improvement for {args.patience} epochs)")
                break

    elapsed = time.time() - started
    summary = {
        "best_val_accuracy": best_acc,
        "best_checkpoint_score": best_score,
        "checkpoint_metric": args.metric,
        "epochs_run": len(history),
        "elapsed_seconds": elapsed,
        "history": history,
        "config": asdict(cfg),
        "args": vars(args) | {"data": [str(p) for p in args.data], "out": str(args.out)},
    }
    with open(args.out / "history.json", "w") as f:
        json.dump(summary, f, indent=2, default=str)
    print(
        f"[done] best val_acc={best_acc:.3f}  best {args.metric}={best_score:.3f}  "
        f"({elapsed/60:.1f} min, {len(history)} epochs)  "
        f"summary → {args.out / 'history.json'}"
    )
    if best_acc < 0.70:
        big = len(clips) >= 800
        if not big:
            print(
                "[warn] Validation accuracy is still below 70%. The training set is small — "
                "the model often fails on out-of-distribution web videos. Mix in "
                "FaceForensics++ crops (see preprocess --layout ffplusplus) with train.py "
                "--data dir1 dir2, or set DEEPFAKE_USE_PRETRAINED_HF=1 on the backend."
            )
        else:
            print(
                "[warn] Validation accuracy is still below 70% despite a larger dataset. "
                "Try more epochs, tuning --lr-head / --freeze-backbone, or check label balance."
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
