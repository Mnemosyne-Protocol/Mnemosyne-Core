from __future__ import annotations
from typing import List, Dict, Any

def summarize_trace(trace: List[Dict[str, Any]], elapsed_s: float, frames: int) -> Dict[str, Any]:
    total = max(1, frames)
    chr = sum(1 for e in trace if e.get("chr_violation")) / total
    reject_rate = sum(1 for e in trace if e.get("rejects", 0) > 0) / total
    resamples_per_frame = sum(e.get("rejects", 0) for e in trace) / total
    latency_ms_per_frame = (elapsed_s * 1000.0) / total
    hard_stop_frames = sum(1 for e in trace if not e.get("accepted", True))
    total_rejects = sum(e.get("rejects", 0) for e in trace)
    return {
        "chr": chr,
        "reject_rate": reject_rate,
        "resamples_per_frame": resamples_per_frame,
        "latency_ms_per_frame": latency_ms_per_frame,
        "hard_stop_frames": hard_stop_frames,
        "total_rejects": total_rejects,
    }
