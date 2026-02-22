def run_single_agent_gate(frames):
    drift_count = sum(1 for f in frames if f.get('style_score', 1.0) < 0.85)
    return {"rejects": drift_count, "resamples": drift_count, "hallucinations": 0}
