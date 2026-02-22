import time
import sys
import re

# Benchmark sırasında terminal_trace.log dosyasına da yazabilmek için global bir dosya tutucu
_log_file = None

def set_log_file(filepath):
    global _log_file
    _log_file = open(filepath, "w", encoding="utf-8")

def _write_log(level, message, color_code):
    timestamp = time.strftime("%H:%M:%S")
    
    # 1. Terminale renkli bas
    console_out = f"\033[{color_code}m[{timestamp}] [{level}] {message}\033[0m"
    print(console_out)
    
    # 2. Eğer dosya ayarlandıysa, renk kodlarını (ANSI) temizleyip dosyaya yaz (CTO'lar için)
    if _log_file:
        clean_msg = re.sub(r'\x1b\[[0-9;]*m', '', console_out)
        _log_file.write(clean_msg + "\n")
        _log_file.flush()

# --- STANDART FORMAT FONKSİYONLARI ---

def log_info(msg):
    _write_log("INFO", msg, "94")

def log_push_state(memory_id):
    _write_log("PUSH_STATE", f"Loading Story Bible -> Memory Snapshot (ID: {memory_id})", "94")

def log_incoming(frame_name):
    _write_log("INCOMING", f"{frame_name} received. Extracting CLIP embeddings...", "97")

def log_verify(status_line):
    _write_log("VERIFY", status_line, "92")

def log_reject(reason="Continuity \u03a8 = 0. Gate failed closed."):
    _write_log("REJECT", reason, "1;31")

def log_rollback():
    _write_log("ROLLBACK", "Triggering localized re-sampling (Algorithm 1)...", "93")

def log_resample():
    _write_log("RE-SAMPLE", "Injecting constraint weights to model prompt...", "93")

def log_accept():
    _write_log("ACCEPT", "Continuity \u03a8 = 1. State persisted.", "1;32")