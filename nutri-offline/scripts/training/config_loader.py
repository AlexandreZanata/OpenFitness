"""Load training config with profile merge (quantun-ia style defaults → profile → overrides)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from _paths import ROOT


def load_training_config(
    config_path: Path,
    *,
    profile: str | None = None,
) -> dict[str, Any]:
    """Merge defaults, active profile, and resolve paths relative to nutri-offline ROOT."""
    import yaml

    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Invalid config at {config_path}")

    defaults = dict(raw.get("defaults", raw))
    profiles = raw.get("profiles", {})
    active = profile or os.environ.get("NUTRI_TRAIN_PROFILE") or raw.get("active_profile", "full")
    overrides = profiles.get(active, {}) if active != "full" else profiles.get("full", {})
    merged: dict[str, Any] = {**defaults, **overrides}
    merged["_profile"] = active
    merged["_config_path"] = str(config_path)

    for key in ("train_jsonl", "val_jsonl", "output_dir"):
        value = merged.get(key)
        if value and not Path(value).is_absolute():
            merged[key] = str((ROOT / value).resolve())

    return merged
