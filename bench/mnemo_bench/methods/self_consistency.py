def run_self_consistency(frames):
    drift_count = sum(1 for f in frames if f.get('style_score', 1.0) < 0.85 or f.get('geometry_score', 1.0) < 0.90 or f.get('policy_score', 1.0) < 0.90)
    return {"rejects": drift_count, "resamples": 0, "hallucinations": drift_count // 2}
