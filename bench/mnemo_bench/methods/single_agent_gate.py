def run_single_agent_gate(frames):
    style_drifts = sum(1 for f in frames if f.get('style_score', 1.0) < 0.85)
    # Stili geçip, Geometri veya Policy'den patlayanlar Halüsinasyondur!
    missed_drifts = sum(1 for f in frames if f.get('style_score', 1.0) >= 0.85 and (f.get('geometry_score', 1.0) < 0.90 or f.get('policy_score', 1.0) < 0.90))
    return {"rejects": style_drifts, "resamples": style_drifts, "hallucinations": missed_drifts}
