def run_single_agent_gate(frames):
    # Sadece tek bir modaliteyi (örn: sadece stili) kontrol eder.
    return {"rejects": int(len(frames) * 0.1), "resamples": int(len(frames) * 0.1), "hallucinations": int(len(frames) * 0.05)}
