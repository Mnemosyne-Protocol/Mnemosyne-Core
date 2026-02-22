from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple, Literal
import math

Vec3 = Tuple[float, float, float]
Decision = Literal["ACCEPT", "REJECT"]

def l2(a: Vec3, b: Vec3) -> float:
    return math.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2 + (a[2]-b[2])**2)

@dataclass(frozen=True)
class AgentResult:
    name: str
    decision: Decision
    score: float
    threshold: float
    reason: str

@dataclass
class StyleVerifier:
    delta_threshold: float
    def verify(self, cand: Vec3, baseline: Vec3) -> AgentResult:
        d = l2(cand, baseline)
        if d > self.delta_threshold:
            return AgentResult("StyleVerifier", "REJECT", d, self.delta_threshold, f"δ={d:.3f} > {self.delta_threshold:.3f}")
        return AgentResult("StyleVerifier", "ACCEPT", d, self.delta_threshold, f"δ={d:.3f} ≤ {self.delta_threshold:.3f}")

@dataclass
class PolicyGuard:
    policy_threshold: float
    def verify(self, score: float) -> AgentResult:
        if score < self.policy_threshold:
            return AgentResult("PolicyGuard", "REJECT", score, self.policy_threshold, f"score={score:.3f} < {self.policy_threshold:.3f}")
        return AgentResult("PolicyGuard", "ACCEPT", score, self.policy_threshold, f"score={score:.3f} ≥ {self.policy_threshold:.3f}")
