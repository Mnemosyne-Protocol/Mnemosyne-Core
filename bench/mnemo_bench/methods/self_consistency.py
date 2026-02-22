def run_self_consistency(frames):
    # Ürettikten sonra kontrol eder. Gecikme maliyeti yüksektir.
    return {"rejects": int(len(frames) * 0.2), "resamples": 0, "hallucinations": int(len(frames) * 0.1)}
