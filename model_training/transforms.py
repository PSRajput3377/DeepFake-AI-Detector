"""Per-frame image augmentations.

Frame-level (rather than clip-level) is fine here because the LSTM /
Transformer learn temporal context anyway, and per-frame jitter actually
acts as a useful regularizer for the spatial backbone.
"""

from __future__ import annotations

from torchvision import transforms

IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)


def train_transform(image_size: int = 224, strong: bool = False):
    """``strong=True`` adds extra jitter for small datasets (SDFVD-scale)."""
    jitter = (
        dict(brightness=0.35, contrast=0.35, saturation=0.35, hue=0.06)
        if strong
        else dict(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.04)
    )
    erase_p = 0.25 if strong else 0.15
    return transforms.Compose(
        [
            transforms.Resize((int(image_size * 1.15), int(image_size * 1.15))),
            transforms.RandomCrop((image_size, image_size)),
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.ColorJitter(**jitter),
            transforms.RandomApply(
                [transforms.GaussianBlur(kernel_size=3, sigma=(0.1, 1.2))], p=0.25
            ),
            transforms.ToTensor(),
            transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
            transforms.RandomErasing(p=erase_p, scale=(0.02, 0.12)),
        ]
    )


def eval_transform(image_size: int = 224):
    return transforms.Compose(
        [
            transforms.Resize((image_size, image_size)),
            transforms.ToTensor(),
            transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
        ]
    )
