"""Training run metrics analysis for Phase 5 post-train gate."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_training_run(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def find_latest_training_run(log_dir: Path) -> Path | None:
    candidates = sorted(log_dir.glob("training-run-*.json"))
    full_runs = []
    for path in candidates:
        try:
            payload = load_training_run(path)
        except (json.JSONDecodeError, OSError):
            continue
        profile = payload.get("profile")
        max_steps = payload.get("config", {}).get("max_steps")
        if profile == "ci" or (max_steps is not None and int(max_steps) <= 2):
            continue
        full_runs.append(path)
    return full_runs[-1] if full_runs else None


def extract_loss_series(history: list[dict[str, Any]]) -> tuple[list[float], list[float]]:
    train_losses = [float(entry["loss"]) for entry in history if "loss" in entry]
    eval_losses = [float(entry["eval_loss"]) for entry in history if "eval_loss" in entry]
    return train_losses, eval_losses


def check_loss_stable(
    history: list[dict[str, Any]],
    *,
    max_final_train_loss: float = 0.5,
    max_eval_loss: float = 0.35,
    max_late_train_spike_ratio: float = 2.0,
) -> dict[str, Any]:
    """GIVEN training log history WHEN analyzed THEN detect divergence or unstable loss."""
    train_losses, eval_losses = extract_loss_series(history)

    if len(train_losses) < 10:
        return {
            "pass": False,
            "reason": "insufficient train loss steps",
            "train_steps": len(train_losses),
            "eval_steps": len(eval_losses),
        }

    final_train = train_losses[-1]
    final_eval = eval_losses[-1] if eval_losses else None

    reasons: list[str] = []
    if final_train > max_final_train_loss:
        reasons.append(f"final train loss {final_train:.4f} > {max_final_train_loss}")
    if final_eval is not None and final_eval > max_eval_loss:
        reasons.append(f"final eval loss {final_eval:.4f} > {max_eval_loss}")

    # Late-epoch regression: last 10% mean vs prior 10%
    window = max(1, len(train_losses) // 10)
    late = train_losses[-window:]
    prior = train_losses[-2 * window : -window]
    late_mean = sum(late) / len(late)
    prior_mean = sum(prior) / len(prior) if prior else late_mean
    if prior and late_mean > prior_mean * 1.5:
        reasons.append(f"late train loss regression {late_mean:.4f} vs {prior_mean:.4f}")

    # Spike within the final third of training (not initial high loss)
    tail_start = max(0, (len(train_losses) * 2) // 3)
    tail = train_losses[tail_start:]
    tail_min = min(tail)
    tail_max = max(tail)
    tail_spike = tail_max / tail_min if tail_min > 0 else float("inf")
    if tail_spike > max_late_train_spike_ratio:
        reasons.append(f"late train loss spike ratio {tail_spike:.2f} > {max_late_train_spike_ratio}")

    if len(eval_losses) >= 2:
        if eval_losses[-1] > eval_losses[-2] * 1.25:
            reasons.append(
                f"eval loss increased {eval_losses[-2]:.4f} -> {eval_losses[-1]:.4f}"
            )

    return {
        "pass": not reasons,
        "reasons": reasons,
        "final_train_loss": round(final_train, 4),
        "final_eval_loss": round(final_eval, 4) if final_eval is not None else None,
        "late_train_mean": round(late_mean, 4),
        "prior_train_mean": round(prior_mean, 4),
        "late_train_spike_ratio": round(tail_spike, 2),
        "train_steps": len(train_losses),
        "eval_steps": len(eval_losses),
    }
