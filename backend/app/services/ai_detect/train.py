"""
Training pipeline for the AI/human/plagiarism classifier.

Reads a CSV with columns ``text,label`` (label ∈ {human, ai, plagiarised}),
extracts features, fits a StandardScaler+LogReg pipeline, and writes it to
the configured model path with a 5-fold CV accuracy report.

Usage:
    uv run python -m app.services.ai_detect.train \\
        --csv backend/data/ai_train.csv \\
        --out backend/app/ml_models/ai_classifier.joblib
"""

from __future__ import annotations

import argparse
import csv
import logging
import sys
from pathlib import Path

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from .features import extract_features

logger = logging.getLogger(__name__)

CLASSES = ("human", "ai", "plagiarised")


def _load_csv(path: Path) -> tuple[list[str], list[str]]:
    texts: list[str] = []
    labels: list[str] = []
    with path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            t = (row.get("text") or "").strip()
            label = (row.get("label") or "").strip().lower()
            if not t or label not in CLASSES:
                continue
            texts.append(t)
            labels.append(label)
    return texts, labels


def train(csv_path: Path, out_path: Path, max_examples: int | None = None) -> float:
    """Fit the pipeline and persist it. Returns the 5-fold CV accuracy."""
    texts, labels = _load_csv(csv_path)
    if not texts:
        raise ValueError(f"No usable rows in {csv_path}")

    if max_examples is not None and len(texts) > max_examples:
        idx = np.random.default_rng(42).permutation(len(texts))[:max_examples]
        texts = [texts[i] for i in idx]
        labels = [labels[i] for i in idx]

    logger.info("Extracting features from %d documents...", len(texts))
    X = np.stack([extract_features(t).to_array() for t in texts], axis=0)  # noqa: N806
    y = np.array(labels)

    pipe = Pipeline(
        [
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(max_iter=1000, multi_class="auto")),
        ]
    )

    cv = StratifiedKFold(n_splits=min(5, len(set(y))), shuffle=True, random_state=42)
    scores = cross_val_score(pipe, X, y, cv=cv, scoring="accuracy")
    mean_acc = float(np.mean(scores))
    logger.info("CV accuracy: %.3f ± %.3f", mean_acc, float(np.std(scores)))

    pipe.fit(X, y)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipe, out_path)
    logger.info("Wrote %s", out_path)
    return mean_acc


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(description="Train AI/human/plagiarism classifier")
    parser.add_argument("--csv", type=Path, required=True, help="Path to labelled CSV")
    parser.add_argument("--out", type=Path, required=True, help="Where to write the .joblib model")
    parser.add_argument("--max", type=int, default=None, help="Cap on examples used")
    args = parser.parse_args(argv)
    train(args.csv, args.out, max_examples=args.max)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
