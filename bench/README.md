# 📊 Mnemosyne Benchmark Suite (v1.6 Ready)

This suite runs the comparative analysis between standard Generative AI orchestration methods (Naive, Memory Buffer, Self-Consistency) and the **Mnemosyne Fail-Closed Protocol**.

## Core Metrics Evaluated
1. **CHR (Continuity Hallucination Rate):** Percentage of final rendered frames containing continuity errors.
2. **Rejects & Resamples:** Operational overhead metrics mapping directly to compute/latency costs.

## Quick Start (Standard Execution)
To run the benchmark and generate the comparative CSV report along with the clean terminal trace:

```bash
python3 bench/run_bench.py --frames 100 --seed 42 --report bench/out/report.csv --trace bench/out/trace.json --terminal-log bench/out/terminal_trace.log
git add bench/README.md
git commit -m "bench: write terminal_trace.log in demo_orchestrator format and add README"
git push
python3 bench/run_bench.py --frames 100 --seed 42 --report bench/out/report.csv --trace bench/out/trace.json --terminal-log bench/out/terminal_trace.log
f
python3 bench/run_bench.py --frames 100 --seed 42 --report bench/out/report.csv --trace bench/out/trace.json --terminal-log bench/out/terminal_trace.log
# 1. AJANLARI KALİBRE EDİYORUZ (CTO Standartları: 0.90, 0.85, 0.90)
cat << 'EOF' > bench/mnemo_bench/agents/agent_geometry.py
class AgentGeometry:
    name = "Agent_Geometry"
    @staticmethod
    def verify(frame_metadata, memory_snapshot):
        if frame_metadata.get("geometry_score", 1.0) >= 0.90:
            return True, "PASS"
        return False, "FAIL (Geometry mismatch)"
