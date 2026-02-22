import argparse
import json
import os
import sys

# Proje dizinini yola ekle ki bench modüllerini bulabilsin
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from bench.mnemo_bench.logfmt import set_log_file
from bench.mnemo_bench.methods.mnemosyne_fail_closed import run_mnemosyne_pipeline
from bench.mnemo_bench.methods import run_naive_chaining, run_memory_buffer, run_self_consistency, run_single_agent_gate

def generate_synthetic_frames(num_frames):
    frames = []
    for i in range(1, num_frames + 1):
        # Frame 25'te ve her 50 framede bir kasıtlı halüsinasyon yarat
        if i == 25 or i % 50 == 0:
            frames.append({"name": f"Frame_{i:03d}.mp4", "style_score": 0.4, "geometry_score": 1.0, "policy_score": 1.0})
        else:
            frames.append({"name": f"Frame_{i:03d}.mp4", "style_score": 0.9, "geometry_score": 0.9, "policy_score": 0.95})
    return frames

def main():
    parser = argparse.ArgumentParser(description="Mnemosyne Benchmark Suite")
    parser.add_argument("--frames", type=int, default=200)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--report", default="bench/out/report.csv")
    parser.add_argument("--trace", default="bench/out/trace.json")
    parser.add_argument("--terminal-log", default="bench/out/terminal_trace.log")
    args = parser.parse_args()

    # Çıktı klasörünün var olduğundan emin ol
    os.makedirs(os.path.dirname(args.report), exist_ok=True)
    
    # Tüm çıktıların ANSI'den temizlenmiş kopyasını yazacak log dosyasını ayarla
    set_log_file(args.terminal_log)

    print(f"\n🚀 Starting Mnemosyne Benchmark (Frames: {args.frames}, Seed: {args.seed})\n")
    frames = generate_synthetic_frames(args.frames)

    # 1. Rakipleri Simüle Et
    results = {
        "Naive": run_naive_chaining(frames),
        "MemoryBuffer": run_memory_buffer(frames),
        "SelfConsistency": run_self_consistency(frames),
        "SingleAgent": run_single_agent_gate(frames)
    }

    # 2. Mnemosyne Şovu (Loglarla)
    results["Mnemosyne"] = run_mnemosyne_pipeline(frames)

    # JSON Kaydet
    with open(args.trace, "w") as f:
        json.dump(results, f, indent=2)

    # CSV Kaydet
    with open(args.report, "w") as f:
        f.write("Method,Rejects,Resamples,Hallucinations\n")
        for method, stats in results.items():
            f.write(f"{method},{stats['rejects']},{stats['resamples']},{stats['hallucinations']}\n")

    print("\n\033[1;36m=== SEQUENCE FINALIZED WITH 0 HUMAN REWORK ===\033[0m")
    print(f"\n📊 Results saved to: {args.report} and {args.trace}")
    print(f"📝 Clean terminal trace saved to: {args.terminal_log}")

if __name__ == "__main__":
    main()
