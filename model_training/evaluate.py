"""Compute final metrics + confusion matrix on the val split.

Usage::

    python evaluate.py --data processed_faces --weights checkpoints/best.pt
    python evaluate.py --data crops_a crops_b --weights checkpoints/best.pt
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

import numpy as np
import torch
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from torch.utils.data import DataLoader
from tqdm import tqdm

from _paths import DeepFakeDetector, ModelConfig, load_checkpoint  # noqa: F401
from app.ml.model import build_from_checkpoint
from dataset import INDEX_TO_LABEL, FaceClipsDataset, discover_clips_many
from train import stratified_split
from transforms import eval_transform


def plot_confusion(cm, out_path: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(4.2, 4.0))
    im = ax.imshow(cm, cmap="Blues")
    ax.set_xticks([0, 1], ["fake", "real"])
    ax.set_yticks([0, 1], ["fake", "real"])
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_title("Confusion matrix")
    for (i, j), v in np.ndenumerate(cm):
        ax.text(j, i, str(v), ha="center", va="center", color="black", fontsize=14)
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    print(f"[info] confusion matrix → {out_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate a trained deepfake detector.")
    parser.add_argument(
        "--data",
        nargs="+",
        type=Path,
        required=True,
        help="Pre-extracted face folder(s); multiple merged for val split.",
    )
    parser.add_argument("--weights", type=Path, required=True)
    parser.add_argument("--sequence-length", type=int, default=20)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--num-workers", type=int, default=2)
    parser.add_argument("--val-frac", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", type=Path, default=Path("eval_results"))
    args = parser.parse_args()

    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)

    args.out.mkdir(parents=True, exist_ok=True)
    device = "cuda" if torch.cuda.is_available() else "cpu"

    clips = discover_clips_many(args.data)
    if not clips:
        raise SystemExit(f"no clips under: {', '.join(str(p) for p in args.data)}")
    _, val_clips = stratified_split(clips, args.val_frac, args.seed)
    print(f"[info] evaluating on {len(val_clips)} val clips")

    ds = FaceClipsDataset(
        val_clips,
        sequence_length=args.sequence_length,
        transform=eval_transform(),
        train=False,
    )
    loader = DataLoader(
        ds, batch_size=args.batch_size, shuffle=False, num_workers=args.num_workers
    )

    # Build the model from the checkpoint's saved config so `--small-head`
    # runs (and any other non-default architecture) load cleanly.
    model, cfg, meta = build_from_checkpoint(str(args.weights), device=device)
    model.eval()
    print(
        f"[info] loaded {args.weights} (epoch={meta.get('epoch')}, "
        f"proj_dim={cfg.proj_dim}, lstm_hidden={cfg.lstm_hidden})"
    )

    all_preds, all_labels, all_fake_probs = [], [], []
    with torch.no_grad():
        for clips, labels in tqdm(loader, desc="eval"):
            clips = clips.to(device)
            logits = model(clips)
            probs = torch.softmax(logits, dim=1)
            all_fake_probs.extend(probs[:, 0].cpu().tolist())
            all_preds.extend(logits.argmax(dim=1).cpu().tolist())
            all_labels.extend(labels.tolist())

    y_true = np.array(all_labels)
    y_pred = np.array(all_preds)
    y_score = np.array(all_fake_probs)

    metrics = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision_fake": float(precision_score(y_true, y_pred, pos_label=0, zero_division=0)),
        "recall_fake": float(recall_score(y_true, y_pred, pos_label=0, zero_division=0)),
        "f1_fake": float(f1_score(y_true, y_pred, pos_label=0, zero_division=0)),
        "precision_real": float(precision_score(y_true, y_pred, pos_label=1, zero_division=0)),
        "recall_real": float(recall_score(y_true, y_pred, pos_label=1, zero_division=0)),
        "f1_real": float(f1_score(y_true, y_pred, pos_label=1, zero_division=0)),
        "support": {INDEX_TO_LABEL[k]: int((y_true == k).sum()) for k in (0, 1)},
    }
    if len(set(y_true)) == 2:
        metrics["roc_auc_fake"] = float(roc_auc_score((y_true == 0).astype(int), y_score))

    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    metrics["confusion_matrix"] = {
        "labels": ["fake", "real"],
        "matrix": cm.tolist(),
    }

    out_metrics = args.out / "metrics.json"
    with open(out_metrics, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"[info] metrics → {out_metrics}")

    plot_confusion(cm, args.out / "confusion_matrix.png")

    print()
    print("───── Final metrics ─────")
    print(f"Accuracy        : {metrics['accuracy']:.3f}")
    print(f"Precision (fake): {metrics['precision_fake']:.3f}")
    print(f"Recall    (fake): {metrics['recall_fake']:.3f}")
    print(f"F1        (fake): {metrics['f1_fake']:.3f}")
    if "roc_auc_fake" in metrics:
        print(f"ROC-AUC   (fake): {metrics['roc_auc_fake']:.3f}")
    print(f"Confusion matrix:\n{cm}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
