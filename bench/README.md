# Mnemosyne v1.6 — Benchmarks & Baselines (Starter Kit)

Minimal, reproducible benchmark harness to address research-rigor feedback.

## Run
```bash
python3 bench.py --frames 200 --seed 42 --drift-rate 0.35 --delta-threshold 0.18 --report out/report.csv
```

## Output
- `out/report.csv` summary table
- `out/trace.json` per-method traces

## Methods
- naive_chaining
- memory_buffer
- self_consistency
- single_agent_gate
- mnemosyne_fail_closed (product-of-constraints + localized resampling)
