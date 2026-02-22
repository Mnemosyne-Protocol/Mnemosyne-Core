def run_memory_buffer(frames):
    halls = sum(1 for f in frames if f.get('style_score', 1.0) < 0.85)
    return {"rejects": 0, "resamples": 0, "hallucinations": halls}
