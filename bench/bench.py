from __future__ import annotations
import argparse, time, json, csv, os
from benchkit.suite import SyntheticSuiteConfig, generate_sequence
from benchkit.metrics import summarize_trace
from benchkit.methods import (
    run_naive_chaining, run_memory_buffer, run_self_consistency,
    run_single_agent_gate, run_mnemosyne_fail_closed
)

METHODS = [
    ("naive_chaining", run_naive_chaining),
    ("memory_buffer", run_memory_buffer),
    ("self_consistency", run_self_consistency),
    ("single_agent_gate", run_single_agent_gate),
    ("mnemosyne_fail_closed", run_mnemosyne_fail_closed),
]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--frames", type=int, default=200)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--drift-rate", type=float, default=0.35)
    ap.add_argument("--drift-amp", type=float, default=0.45)
    ap.add_argument("--good-amp", type=float, default=0.05)
    ap.add_argument("--delta-threshold", type=float, default=0.18)
    ap.add_argument("--policy-threshold", type=float, default=0.90)
    ap.add_argument("--selfcons-n", type=int, default=5)
    ap.add_argument("--max-resamples", type=int, default=6)
    ap.add_argument("--report", type=str, default="out/report.csv")
    ap.add_argument("--trace-json", type=str, default="out/trace.json")
    args = ap.parse_args()

    cfg = SyntheticSuiteConfig(
        frames=args.frames, seed=args.seed,
        drift_rate=args.drift_rate, drift_amp=args.drift_amp, good_amp=args.good_amp,
        delta_threshold=args.delta_threshold, policy_threshold=args.policy_threshold,
        selfcons_n=args.selfcons_n, max_resamples=args.max_resamples,
    )
    seq = generate_sequence(cfg)

    rows = []
    all_traces = {}
    for name, fn in METHODS:
        t0 = time.time()
        trace = fn(seq, cfg)
        elapsed = time.time() - t0
        summary = summarize_trace(trace, elapsed_s=elapsed, frames=args.frames)
        summary["method"] = name
        rows.append(summary)
        all_traces[name] = trace

    os.makedirs(os.path.dirname(args.report), exist_ok=True)
    with open(args.report, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    os.makedirs(os.path.dirname(args.trace_json), exist_ok=True)
    with open(args.trace_json, "w", encoding="utf-8") as f:
        json.dump({"config": cfg.__dict__, "traces": all_traces}, f, ensure_ascii=False, indent=2)

    print("Wrote:", args.report)
    print("Wrote:", args.trace_json)
    for r in rows:
        print(f"- {r['method']}: CHR={r['chr']:.3f} reject_rate={r['reject_rate']:.3f} "
              f"resamples/frame={r['resamples_per_frame']:.2f} latency_ms/frame={r['latency_ms_per_frame']:.2f}")

if __name__ == "__main__":
    main()
