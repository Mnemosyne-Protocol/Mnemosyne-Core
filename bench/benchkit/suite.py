from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple, Dict, Any
import random

Vec3 = Tuple[float, float, float]

def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))

def jitter(v: Vec3, amp: float, rng: random.Random) -> Vec3:
    return (clamp01(v[0] + rng.uniform(-amp, amp)),
            clamp01(v[1] + rng.uniform(-amp, amp)),
            clamp01(v[2] + rng.uniform(-amp, amp)))

@dataclass
class SyntheticSuiteConfig:
    frames: int = 200
    seed: int = 42
    drift_rate: float = 0.35
    drift_amp: float = 0.45
    good_amp: float = 0.05
    delta_threshold: float = 0.18
    policy_threshold: float = 0.90
    selfcons_n: int = 5
    max_resamples: int = 6

def generate_sequence(cfg: SyntheticSuiteConfig) -> Dict[str, Any]:
    rng = random.Random(cfg.seed)
    baseline: Vec3 = (0.20, 0.75, 0.25)

    frames: List[Dict[str, Any]] = []
    for t in range(cfg.frames):
        drifted = rng.random() < cfg.drift_rate
        style = jitter(baseline, cfg.drift_amp if drifted else cfg.good_amp, rng)
        frames.append({
            "t": t,
            "candidate_style": style,
            "drifted": drifted,
            "baseline": baseline,
            "policy_score": style[1],  # toy policy: keep green high
        })
    return {"baseline": baseline, "frames": frames, "rng_seed": cfg.seed}
