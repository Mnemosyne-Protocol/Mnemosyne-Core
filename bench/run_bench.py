import argparse, json, os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from bench.mnemo_bench.logfmt import set_log_file
from bench.mnemo_bench.methods.naive_chaining import run_naive_chaining
from bench.mnemo_bench.methods.memory_buffer import run_memory_buffer
from bench.mnemo_bench.methods.self_consistency import run_self_consistency
from bench.mnemo_bench.methods.single_agent_gate import run_single_agent_gate
from bench.mnemo_bench.methods.mnemosyne_fail_closed import run_mnemosyne_pipeline

def generate_synthetic_frames(num_frames):
    frames = []
    for i in range(1, num_frames + 1):
        if i % 15 == 0: # Style Hatası (Scar missing)
            frames.append({"name": f"Frame_{i:03d}.mp4", "style_score": 0.40, "geometry_score": 0.95, "policy_score": 0.95})
        elif i % 15 == 5: # Geometry Hatası (Object permanence)
            frames.append({"name": f"Frame_{i:03d}.mp4", "style_score": 0.95, "geometry_score": 0.40, "policy_score": 0.95})
        elif i % 15 == 10: # Policy Hatası (Brand rule / Violence)
            frames.append({"name": f"Frame_{i:03d}.mp4", "style_score": 0.95, "geometry_score": 0.95, "policy_score": 0.40})
        else: # Kusursuz Kare
            frames.append({"name": f"Frame_{i:03d}.mp4", "style_score": 0.95, "geometry_score": 0.95, "policy_score": 0.95})
    return frames

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--frames", type=int, default=100)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--report", default="bench/out/report.csv")
    parser.add_argument("--trace", default="bench/out/trace.json")
    parser.add_argument("--terminal-log", default="bench/out/terminal_trace.log")
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.report), exist_ok=True)
    set_log_file(args.terminal_log)
    frames = generate_synthetic_frames(args.frames)

    results = {
        "Naive": run_naive_chaining(frames),
        "MemoryBuffer": run_memory_buffer(frames),
        "SelfConsistency": run_self_consistency(frames),
        "SingleAgent": run_single_agent_gate(frames),
        "Mnemosyne": run_mnemosyne_pipeline(frames)
    }

    with open(args.trace, "w") as f: json.dump(results, f, indent=2)
    with open(args.report, "w") as f:
        f.write("Method,Rejects,Resamples,CHR\n")
        for method, stats in results.items():
            chr_rate = stats['hallucinations'] / args.frames
            f.write(f"{method},{stats['rejects']},{stats['resamples']},{chr_rate:.2f}\n")

if __name__ == "__main__":
    main()
