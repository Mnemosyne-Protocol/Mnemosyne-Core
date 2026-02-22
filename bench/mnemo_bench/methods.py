from __future__ import annotations
from typing import Dict, Any, List
import random, time

from .suite import SyntheticSuiteConfig, jitter, Vec3
from .agents import StyleVerifier, PolicyGuard

def _event(t: int, accepted: bool, rejects: int, chr_violation: bool, latency_ms: float, details: Dict[str, Any]):
    return {"t": t, "accepted": accepted, "rejects": rejects, "chr_violation": chr_violation, "latency_ms": latency_ms, "details": details}

def _violates_any(cand: Vec3, baseline: Vec3, policy: float, cfg: SyntheticSuiteConfig) -> bool:
    sv = StyleVerifier(cfg.delta_threshold).verify(cand, baseline)
    pg = PolicyGuard(cfg.policy_threshold).verify(policy)
    return not (sv.decision == "ACCEPT" and pg.decision == "ACCEPT")

def run_naive_chaining(seq: Dict[str, Any], cfg: SyntheticSuiteConfig) -> List[Dict[str, Any]]:
    out=[]
    for fr in seq["frames"]:
        t=fr["t"]; cand=fr["candidate_style"]; base=fr["baseline"]; pol=fr["policy_score"]
        out.append(_event(t, True, 0, _violates_any(cand, base, pol, cfg), 0.0, {"cand": cand, "policy": pol}))
    return out

def run_memory_buffer(seq: Dict[str, Any], cfg: SyntheticSuiteConfig) -> List[Dict[str, Any]]:
    out=[]; memory=seq["baseline"]
    for fr in seq["frames"]:
        t=fr["t"]; cand=fr["candidate_style"]; pol=fr["policy_score"]
        out.append(_event(t, True, 0, _violates_any(cand, memory, pol, cfg), 0.0, {"cand": cand, "memory": memory, "policy": pol}))
        memory=cand
    return out

def run_self_consistency(seq: Dict[str, Any], cfg: SyntheticSuiteConfig) -> List[Dict[str, Any]]:
    rng = random.Random(cfg.seed + 999)
    out=[]; base=seq["baseline"]; sv=StyleVerifier(cfg.delta_threshold)
    for fr in seq["frames"]:
        t=fr["t"]
        best=None; best_d=1e9
        for _ in range(max(1, cfg.selfcons_n)):
            sample = jitter(fr["candidate_style"], cfg.good_amp, rng)
            d = sv.verify(sample, base).score
            if d < best_d:
                best, best_d = sample, d
        pol = best[1]
        out.append(_event(t, True, 0, _violates_any(best, base, pol, cfg), 0.0, {"chosen": best, "delta": best_d}))
    return out

def run_single_agent_gate(seq: Dict[str, Any], cfg: SyntheticSuiteConfig) -> List[Dict[str, Any]]:
    rng = random.Random(cfg.seed + 123)
    out=[]; base=seq["baseline"]; sv=StyleVerifier(cfg.delta_threshold)
    for fr in seq["frames"]:
        t=fr["t"]; cand=fr["candidate_style"]; rejects=0; start=time.time()
        while True:
            r = sv.verify(cand, base)
            if r.decision == "ACCEPT":
                pol=cand[1]
                out.append(_event(t, True, rejects, _violates_any(cand, base, pol, cfg), (time.time()-start)*1000, {"chosen": cand, "style": r.reason}))
                break
            rejects += 1
            if rejects > cfg.max_resamples:
                out.append(_event(t, False, rejects, True, (time.time()-start)*1000, {"hard_stop": True, "style": r.reason}))
                break
            cand = jitter(base, cfg.good_amp, rng)
    return out

def run_mnemosyne_fail_closed(seq: Dict[str, Any], cfg: SyntheticSuiteConfig) -> List[Dict[str, Any]]:
    rng = random.Random(cfg.seed + 777)
    out=[]; base=seq["baseline"]; sv=StyleVerifier(cfg.delta_threshold); pg=PolicyGuard(cfg.policy_threshold)
    for fr in seq["frames"]:
        t=fr["t"]; cand=fr["candidate_style"]; rejects=0; start=time.time()
        while True:
            pol=cand[1]
            r1=sv.verify(cand, base); r2=pg.verify(pol)
            gate_ok = (r1.decision=="ACCEPT") and (r2.decision=="ACCEPT")
            if gate_ok:
                out.append(_event(t, True, rejects, False, (time.time()-start)*1000, {"chosen": cand, "style": r1.reason, "policy": r2.reason}))
                break
            rejects += 1
            if rejects > cfg.max_resamples:
                out.append(_event(t, False, rejects, True, (time.time()-start)*1000, {"hard_stop": True, "style": r1.reason, "policy": r2.reason}))
                break
            cand = jitter(base, cfg.good_amp, rng)
    return out
