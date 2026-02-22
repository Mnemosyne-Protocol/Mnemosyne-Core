def run_naive_chaining(frames):
    halls = sum(1 for f in frames if f.get('style_score', 1.0) < 0.85 or f.get('geometry_score', 1.0) < 0.90 or f.get('policy_score', 1.0) < 0.90)
    return {"rejects": 0, "resamples": 0, "hallucinations": halls}
