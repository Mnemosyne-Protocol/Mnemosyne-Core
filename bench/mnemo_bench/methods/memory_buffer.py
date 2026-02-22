def run_memory_buffer(frames):
    # RAG tabanlı hafıza. Bağlam penceresi dolunca ipuçlarını kaçırır.
    return {"rejects": 0, "resamples": 0, "hallucinations": int(len(frames) * 0.4)}
