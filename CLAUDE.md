# PROJECT MNEMOSYNE v3.0.0 — SESSION CONTEXT
# Auto-loaded by Claude Code on every session start.
# Place this file at: /Volumes/MNEMOSYNE-GATE/Vault/repos/Mnemosyne-Core/CLAUDE.md

**DOI:** 10.5281/zenodo.18884426  
**Status:** Alpha-Deployment / Fail-Closed Governance  
**Last verified:** 2026-03-20
**Lead Architect:** Kerem Salman — Mnemosyne Labs, Istanbul

> "Complexity is our moat. Determinism is our product. Proof is our deliverable."
> "We don't guess. We prove."

---

## ⚠️ GROUND RULES FOR CLAUDE

1. **DO NOT HALLUCINATE.** If a file, function, or test result is not listed here, say "I don't have this in context" — do not invent.
2. **Fail-closed mentality.** When in doubt about a technical detail → REJECT / conservative.
3. **Fixed6 always.** Never use IEEE 754 floats for threshold comparisons. All metrics: `i64` with 6 implicit decimal places.
4. **KS always.** Every new SHA-256 hash must use `KS_SEED = "MNEMOSYNE-KS-V3"` prefix: `H(KS_SEED || data)`.
5. **No email without ONAY.** Telegram bot is the Human-in-the-Loop gate. Draft only — never send autonomously.
6. **Preserve the three-layer spec.** Fingerprint / Attestation / Policy — never collapse or merge layers.
7. **Test everything.** Every code artifact must include a self-test that runs without external dependencies.
8. **No Co-Authored-By.** Git commits carry only "Kerem Salman <ks@mnemosynelabs.ai>". 
   Never add Co-Authored-By Claude or Anthropic lines to any commit message.
9. **Runtime Reflection First.** When integrating with DCC tools (UE5, Nuke, Maya, Houdini), 
   NEVER guess or assume API method names. Always instruct the operator to run a reflection 
   query first (e.g., `dir(unreal.MoviePipelinePythonHostExecutor)`) and wait for confirmed 
   output before writing or patching any hook code.

---

## 1. WHAT MNEMOSYNE IS

Mnemosyne is a **Verification Protocol** — the TLS of Generative Media.

- **NOT** an AI generator, NOT a quality scorer, NOT a content moderator.
- Sits **DOWNSTREAM** of any generative model (ComfyUI, SD, Flux, Midjourney, proprietary).
- Does not generate pixels. It **VERIFIES** them.
- Default posture: **REJECT**. An asset passes ONLY if `ψ = 1` (all invariants pass).
- Fail-closed: if the system cannot make a decision → asset is **BLOCKED**.
- Category: **AI Trust Infrastructure** (like Cloudflare/Okta but for generative assets).

---

## 2. CORE ARCHITECTURE — Triple-Layer Spec

### 2.1 Render Fingerprint Spec v1
- Silhouette Hash (alpha/depth binary mask)
- Edge Map Hash (Canny/Sobel)
- Beauty Render (pixel hash + perceptual hash via pHash)
- Material Response Hash (light sweep pass)
- ROI Hashes: `head`, `chest`, `emblem_zone` (per-region exact match)
- Depth Envelope (L2 norm vs. reference)

**Key files:**
- `render_fingerprint_spec.json` → HOW to measure (forensic visual audit)
- `asset.attestation.json` → WHAT was observed (signed evidence)
- `final_gate_policy.yaml` → WHAT is allowed (enforcement brain)

### 2.2 Attestation v2
- Ed25519 signature over canonical payload
- KS-salted SHA-256: `H("MNEMOSYNE-KS-V3" || data)`
- Merkle root binding: `policy_hash + render_hash + context_hash`
- ISO 8601 timestamp, signer identity, schema version

### 2.3 Final Gate Policy v1.0
- 11-step evaluation algorithm (signature → spec → mode → invariants → ψ)
- 3 submission modes: Curated (pixel-exact), Controlled Generative (bounded), Vendor Intake (quarantine)
- 3 signer tiers: Tier A (production/HSM), Tier B (staging), Tier C (diagnostic)
- 15+ classified failure types
- `gate_evaluator.py` — TESTED, all 11 steps pass in **0.08ms**

---

## 3. THE Ψ (PSI) THEOREM

```
ψ(x) = ⋀ᵢ₌₁ⁿ Iᵢ(x)
```

- Boolean conjunction. **One failure → total rejection. No interpolation.**
- Zero short-circuit: ALL invariants run in parallel (rayon). Full violation vector returned.

---

## 4. MOAT TECHNOLOGIES

### 4.1 KS (Knowledge Seed) Entropy Layer
```
KS_SEED = "MNEMOSYNE-KS-V3"   # 15 bytes, ASCII, public
Every hash: H(KS_SEED || data)  # prevents cross-protocol collisions
```
- Defined identically in Rust, Python, TypeScript.
- TESTED: domain separation proof verified (`KS hash ≠ raw hash` for same input).

### 4.2 Fixed6 Deterministic Arithmetic
```
0.720000 → 720_000  (i64)
0.999800 → 999_800  (i64)
1.000000 → 1_000_000 (i64)
SCALE = 1_000_000
```
- No IEEE 754 float ever influences a Gate decision.
- Multiplication via `i128` intermediates, overflow → REJECT.

### 4.3 Render Fingerprint Engine
- Not pixel comparison — **forensic structural analysis**.
- Silhouette geometry, Canny edge maps, material response under controlled light sweeps.
- Per-region-of-interest hashes (`head`, `chest`, `emblem_zone`).

---

## 5. COMPLETED SOURCE CODE — 8 Phases

| Phase | Name | Runtime | Lines | Status |
|-------|------|---------|-------|--------|
| 1 | The Vault | Rust | 2,789 | `gate.rs`, `taxonomy.rs`, `ledger.rs`, `lib.rs` — COMPLETE |
| 2 | The Eyes | Python + PyO3 | 1,483 | FFI bridge, CV extractors, `preflight.py` — COMPLETE |
| 3 | The Gatekeeper | TypeScript | 1,949 | Fastify gateway, auth, billing, circuit breaker — COMPLETE |
| 4 | The Asa | Rust CLI | 2,098 | `mnemosynectl`: verify, sign, audit, roi, doctor — COMPLETE |
| 5 | The Ingress | Python + JS | 1,103 | ComfyUI nodes, metadata sealer, frontend ext — COMPLETE |
| 6 | The Dashboard | React | 985 | ROI counters, ledger tree, quarantine mode — COMPLETE |
| 7 | The Reveal | Markdown | 717 | `README.md`, `WHITEPAPER.md` — COMPLETE |
| 8 | Sovereign Handover | YAML + Python + MD | 1,322+ | `final_gate_policy.yaml`, `gate_evaluator.py` — COMPLETE |
| — | Tests | Python | 396 | 22 Tier-1 tests pass, KS domain separation verified — COMPLETE |
| **TOTAL** | | **4 languages** | **~12,800+** | |

### Key File Locations
```
src/gate.rs                          — Ψ engine, Fixed6, KS_SEED, sha256_bytes(), Evidence Pack
src/taxonomy.rs                      — GovernanceTier A/B/C, RejectClass, 15+ error codes
src/ledger.rs                        — Append-only hash-chained log, ReworkSummary, billing
src/ffi.rs                           — PyO3 bridge: PyGateEngine, quantize_fixed6(), ks_seed()
python/mnemo_workers/preflight.py    — Fixed6 quantization, KS_SEED, RFC 8785
python/mnemo_workers/extractors.py   — Depth, Mask, Embedding, Color, Emissive
python/mnemo_workers/orchestrator.py — FeatureOrchestrator, ExtractionResult
gateway/src/server.ts                — Fastify entrypoint, rate limiting, auth hooks
gateway/src/middleware/auth.ts       — mTLS + JWT, TenantContext injection
gateway/src/bridge/core-bridge.ts   — Circuit breaker (CLOSED/OPEN/HALF_OPEN)
gateway/src/services/billing.ts      — Success Share computation, ROI snapshot
gateway/src/routes/gateway.ts        — 9 routes, Zod validation, fail-closed 503
mnemo-cli/src/main.rs                — Clap v4 CLI: gate, policy, ledger, billing, keygen, doctor
mnemo-cli/src/commands/policy_signer.rs  — RFC 8785 → KS-SHA256 → Ed25519 → .signed_policy
mnemo-cli/src/commands/roi_reporter.rs   — Fixed6 ROI computation from Ledger
comfyui-mnemosyne/mnemosyne_nodes.py    — MnemosyneGateNode (fail-closed)
comfyui-mnemosyne/metadata_sealer.py    — Evidence Pack → PNG tEXt chunks
core/final_gate_policy.yaml             — 476-line enforcement policy (TESTED)
validators/gate_evaluator.py            — 11-step evaluator (TESTED: 0.08ms, all pass)
```

---

## 6. TEST VECTORS — Verification Anchors

> These are PROVEN values. If Claude produces different results, it is hallucinating.

### RFC 8785 Canonical Test Vector
```
Input:     {"emissive_budget":"0.720000","allowed_colors":["#000000","#FFD700"]}
Canonical: {"allowed_colors":["#000000","#FFD700"],"emissive_budget":"0.720000"}
Raw SHA-256: 8d3fd83061563864597b0a898cc2a67c1ca79281005b06aa08e7f73e9dbab2a8
KS SHA-256:  ff9e9429751eea06...  ← MUST differ from raw (domain separation)
```

### Gate Evaluator Test
```
Passing attestation (controlled_generative mode):
→ 11/11 steps PASS
→ ψ = 1
→ Verdict: APPROVED
→ Elapsed: 0.08ms
```

---

## 7. COMMERCIAL STRATEGY

**Positioning:** AI Trust Infrastructure — not AI tool, not content moderation.  
**Analogy:** "Mnemosyne is the TLS for Generative Media."  
**We don't compete with:** Midjourney, Runway, OpenAI — we sit BELOW them.

### Target Decision Makers
| Sector | Companies | Contact Titles |
|--------|-----------|----------------|
| AAA Gaming | Epic Games, Ubisoft, EA, Riot Games, Activision Blizzard | Dir. Pipeline Engineering, Technical Art Director, VP Production |
| VFX | ILM, Weta FX, Framestore, DNEG | Head of Pipeline Technology, Dir. Rendering Systems |
| GenAI | Runway AI, Stability AI, Pika Labs | Head of Infrastructure, Dir. AI Systems |

### Revenue Model
- **Pilot:** $30,000 (7 weeks: Discovery → Integration → Measurement)
- **Enterprise License:** $120,000+/year per pipeline
- **Per-Frame:** $0.03/frame
- **Vendor Network:** $5,000–$20,000/vendor/year

### ROI Benchmark (100 sequences/month AAA studio)
Without Mnemosyne: $150,000/month rework cost (10h × $150/hr × 100 seq)
With Mnemosyne:     $120K/year license
Annual savings:   $1,500,000
ROI: 12.5x

### Funding Ask
- $2.0M Post-Money SAFE, $12M Cap (~16.7% dilution)
- Runway: 18-24 months
- Milestones: Gate v4 + Plugin MVP (Q3 2026), 3 Paid Pilots (Q4 2026), 
- First Enterprise Conversion (Q1 2027), Institutional Seed Ready (Q2 2027)

---

## 8. INFRASTRUCTURE STATUS

### Current Hardware — MNEMOSYNE-NODE-01
- **Machine:** Apple Mac Studio M3 Ultra (28CPU, 60GPU, 96GB RAM, 1TB SSD)
- **OS:** macOS Tahoe 26.3.1
- **Hostname:** MNEMOSYNE-NODE-01 / mnemosyne-node-01
- **Commissioned:** 2026-03-20

### Disk Architecture
- `Macintosh HD` — System volume (APFS)
- `MNEMOSYNE-GATE` — Encrypted APFS volume (FileVault) — source code, whitepapers, pipeline tests
  - `/Volumes/MNEMOSYNE-GATE/Vault/repos/` — all repositories
  - `/Volumes/MNEMOSYNE-GATE/Vault/keys/` — key material
  - `/Volumes/MNEMOSYNE-GATE/Vault/secrets-ref/` — references only, no raw secrets
  - `/Volumes/MNEMOSYNE-GATE/Vault/whitepapers/`
  - `/Volumes/MNEMOSYNE-GATE/Vault/pipeline-tests/`

### LaCie 4TB — Backup Architecture (DEDE-BABA-OĞUL)
- `TM-BACKUP` (1.5TB, APFS Encrypted) — Time Machine, saatlik snapshot
- `CCC-CLONE` (1TB, APFS Encrypted) — CarbonCopy Cloner, bootable clone, haftalık (Pazar 02:00)
- `KS-PROJECTS` (1.5TB, APFS Encrypted) — Aktif proje dosyaları, büyük asset'ler

### Accounts
- `ksadmin` — Admin (sistem müdahalesi, sudo)
- `ks` — Standard User (günlük geliştirme, terminal, üretim)

### Development Stack
| Tool | Version | Location |
|------|---------|----------|
| macOS | Tahoe 26.3.1 | — |
| Homebrew | 5.1.0 | /opt/homebrew |
| Git | 2.53.0 | brew |
| Python | 3.12.9 | pyenv |
| Node.js | 24.14.0 | nvm (LTS) |
| Rust | 1.94.0 | rustup (stable-aarch64-apple-darwin) |
| VS Code | 1.112.0 | /Applications |
| Claude Code | 2.1.80 | npm global |

### VS Code Extensions
- `rust-lang.rust-analyzer`
- `ms-python.python` + `pylance` + `debugpy`
- `charliermarsh.ruff`
- `tamasfe.even-better-toml`
- `usernamehw.errorlens`
- `eamodio.gitlens`
- `ms-vscode.makefile-tools`
- `vadimcn.vscode-lldb`

### SSH
- Key: `ed25519` — `ksadmin@mnemosyne-node-01`
- GitHub: `MNEMOSYNE-NODE-01` (added 2026-03-20)
- Passphrase: Keychain'de saklı

### Agent Architecture (IN PROGRESS)
- **Telegram Bot:** `Mnemosyne_Commander_Bot` — Human-in-the-Loop gate
- **CARDINAL RULE:** NO EMAIL IS SENT WITHOUT TELEGRAM 'ONAY' (approval) FROM KEREM
- **Gmail MCP:** To be connected via Google Cloud API for pilot outreach
- **Flow:** Claude drafts → Telegram sends preview → Kerem approves/rejects → Only then: send

### Pending Tasks
- [ ] Gmail MCP connection (needs Google Cloud API setup)
- [ ] Telegram bot ↔ Claude Code integration
- [ ] `canonical_scene_manifest.json` v1 (closes the trust chain)
- [ ] Pilot outreach: Riot Games (cosmetic pipeline), Ubisoft (vendor intake)
- [ ] Demo video for pilot presentation
- [ ] FAZ 9: Docker, Unreal Engine 5, Ollama, ComfyUI (sonraki aşama)

---

## 9. DOCUMENT REFERENCES

| Document | Location | Status |
|----------|----------|--------|
| Zenodo v2.0 Preprint | 10.5281/zenodo.18869318 | Published |
| Zenodo v3.0 Protocol | 10.5281/zenodo.18884426 | Published |
| GitHub Repository | github.com/Mnemosyne-Protocol/Mnemosyne-Core | Active |
| Website | mnemosynelabs.ai | Live |

---

## 10. LANGUAGE & COMMUNICATION PREFERENCES

- **Conversation language:** Turkish (Türkçe)
- **Technical terms:** Always in English (original form) — e.g., Fixed6, KS_SEED, ψ engine, Fail-Closed, Evidence Pack, Ledger, attestation, pipeline
- **Coding approach:** Proactive, chess-like — anticipate future states, not reactive patching
- **No vibe-coding.** Every decision has a reason. Every function has a test.

---

## FAZ 9A ARCHITECTURAL FREEZE (CLOSED)
- **Topoloji:** Host-native inference (Apple Silicon/Metal) + Dockerized Control Plane
- **İletişim:** Sadece Loopback TCP (127.0.0.1:8765). Docker servisleri dışarıya kapalı.
- **Dil:** Control Plane servisleri (ledger, gate-api) Python.
- **Quarantine Schema v1.1:** Her reject kararı `/quarantine/` altına fail-closed JSON yazar.
  Alanlar: asset_id, timestamp_utc, source_model, source_pipeline, violation_type, decision_reason, psi, hash_canonical, hash_ks, policy_pack_version, gate_version, benchmark_run_id, replay_pointer, operator, admission_decision="QUARANTINE"
  Schema invalid → exception fırlatılır, kayıt yapılmaz.
- **Exit Criteria (Bitiş Şartları):** (1) compose.yaml up — 4 servis healthy
  (2) /submit çalışıyor (host'tan gönderim başarılı)
  (3) Ed25519 imzalı ledger kaydı üretildi
  (4) Schema v1.1 enforced (invalid girişte exception fırlatıyor)
  (5) 100 frame benchmark raporu oluşturuldu.
  
  **FAZ 9A Result:** 100/100 verdicts, 141.45 fps, 7.0ms avg / 6.2ms p50 / 38.9ms p99. Commit: d8f7d69.

---

## FAZ 9B ARCHITECTURAL FREEZE (CLOSED)
**Tema:** Synthetic Stream & Failure Corpus v1
**Primary Rule:** "Mnemosyne is a fail-closed admission layer for policy-bound, high-throughput media pipelines."

**Non-negotiable Constraints:**
- Phase 9A topolojisi ve Loopback TCP (127.0.0.1) iletişimi KESİNLİKLE değiştirilmeyecek.
- Bulut bağımlılığı, RLHF, UE5 eklentisi veya SDK çalışması YOKTUR.
- Quarantine JSON Schema v1.1 katı bir şekilde uygulanmaya devam edecek (violation_type ve decision_reason zorunludur).

**Görev Tanımları (Task Definitions):**
- **TASK 1 (Harness):** Host-native sentetik stream runner yazılacak. 30 FPS sustained, 120/240 FPS burst modları ve deterministik replay desteklenecek.
- **TASK 2 (Ontology):** Reddedilen her asset `/quarantine/` klasörüne v1.1 şemasıyla fail-closed olarak yazılacak. En az 3 farklı `violation_type` üretilecek.
- **TASK 3 (Replay):** Karantinaya alınan kayıtları tekrar `gate-api`'den geçirip kararların tutarlılığını (verdict stability) ölçecek bir replay aracı yazılacak.
- **TASK 4 (Latency):** FAZ 9A'daki yüksek p99 gecikmesinin (spike) nedenlerini (serialization, I/O, vs.) ölçen bir analiz raporu üretilecek.
- **TASK 5 (Report):** Tüm bu sürecin `faz9b_benchmark_report.json` çıktısı alınacak.

**Exit Criteria (Bitiş Şartları):**
ec1_stream_30fps_stable: 30 FPS sentetik akış çökmeden tamamlandı.
ec2_burst_mode_runs: 120/240 FPS burst testleri tamamlandı.
ec3_quarantine_schema_written: Schema v1.1 ile fail-closed loglar yazıldı.
ec4_violation_types_present: En az 3 farklı hata tipi karantinaya düştü.
ec5_replay_reproducible: Replay testleri aynı sonuçları (%100 stable) verdi.
ec6_latency_analysis_written: p99 gecikme analizi markdown olarak üretildi.
ec7_benchmark_report_written: Konsolide FAZ 9B raporu üretildi.
ec8_fail_closed_integrity: Hatalı şemalar reddedildi, sessizce kaydedilmedi.

**FAZ 9B Result:** 510 frames, 29.9/125.3/125.6 fps, 8.8ms avg / 8.9ms p50 / 15.9ms p99. 
306 quarantine records, 4 violation types, replay 100% stable. Commit: def3aef.

---

## FAZ 9B.5 & 9C ARCHITECTURAL FREEZE (CLOSED)
**Tema:** API Contract Freeze & UE5 Export Hook MVP
**Primary Rule:** "Mnemosyne is a fail-closed admission layer for policy-bound, high-throughput media pipelines."

**Platform Notu (ÖNEMLİ):** UE5 henüz M3 Node-01'e kurulu değil. FAZ 9C'de UE5 export çıktısını simüle eden bir Python test harness (mock klasörü) kullanılacak. Gerçek UE5 entegrasyonu FAZ 9D'de yapılacaktır.

**SÖZLEŞME 1: Taxonomy & Schema (v1.1 Frozen)**
Karantina loglarındaki ana kategoriler (`violation_type`) SADECE şunlar olabilir: `GEOMETRY_BREACH`, `POLICY_MODE_VIOLATION`, `SIGNATURE_INVALID`, `SOURCE_INVARIANT_BREACH`.

**TAXONOMY MAPPING (v1.0 → v1.1):** Eski ihlal detayları (`decision_reason` alanına yazılacak) şu ana kategorilere eşlenmiştir:
- emissive_budget → POLICY_MODE_VIOLATION
- ks_mode → POLICY_MODE_VIOLATION  
- signature → SIGNATURE_INVALID
- source_invariant.mesh_topology_hash → SOURCE_INVARIANT_BREACH

**SÖZLEŞME 2: İletişim Protokolü (Locked)**
- UE5 export simülatörü (Python köprüsü), Gate'e SADECE Loopback TCP (127.0.0.1:8765) üzerinden `/submit` endpoint'i ile POST atacaktır. UDS YOK.

**GÖREV TANIMI (FAZ 9C - UE5 Export Hook MVP):**
- Hedef: UE5'ten alınan/simüle edilen bir klasördeki kareleri export sonrasında (Post-Export Hook) Gate'e gönderen basit bir Python köprüsü yazmaktır.
- Çıktı: Tüm kareler geçerse `Mnemosyne_Certified_Passport.json` sidecar dosyası üretilecek. Tek bir kare bile hata verirse (ψ=0), işlem fail-closed olarak duracak ve karantinaya yazılacak.

**Exit Criteria (Bitiş Şartları):**
ec1_contract_frozen: Şema v1.1 ve Taxonomy Mapping kurallara uygun uygulandı.
ec2_ue5_hook_works: Simüle edilmiş export kareleri 127.0.0.1 üzerinden Gate'e başarıyla iletildi.
ec3_certification_produced: Tüm kareler geçerli olduğunda Ed25519 imzalı sidecar JSON üretildi.
ec4_fail_closed_blocked: Hatalı kare bulunduğunda sertifika reddedildi ve karantinaya yazıldı.

**FAZ 9B.5 & 9C Result:** 4/4 Exit Criteria PASS. Taxonomy v1.1 enforced. Simulated UE5 post-export hook via 127.0.0.1:8765 working perfectly. Ed25519 `Mnemosyne_Certified_Passport.json` generated for passing frames. Fail-closed block verified for invalid frames. Commit: 278ea16.

---

## FAZ 9D.1 ARCHITECTURAL FREEZE (CLOSED)
**Tema:** UE5 Bring-Up, Export Surface Discovery & Real Hook Design
**Primary Rule:** "Mnemosyne is a fail-closed admission layer for policy-bound, high-throughput media pipelines."

**Constraints & Assumptions (KIRMIZI ÇİZGİLER):**
- Gate API contract, taxonomy ve schema v1.1 KESİNLİKLE DEĞİŞTİRİLEMEZ. İletişim: Loopback TCP (127.0.0.1:8765).
- BU FAZDA FULL PLUGIN KODLAMASI YOKTUR. Sadece yüzey keşfi, kurulum doğrulaması ve tasarım yapılacaktır.
- **OPERATOR ACTION REQUIRED:** Epic Games Launcher ve UE5 kurulumu manuel GUI işlemleridir. Claude bu işlemleri simüle etmeyecek, operatörden (KS) yapmasını bekleyecek ve ardından disk üzerindeki yolları (paths) doğrulayacaktır.

**Görev Tanımları (Tasks):**
- **TASK 1 (Env):** macOS sürümü, Xcode, disk alanı (300GB+ boş) ve Python gereksinimleri denetlenecek.
- **TASK 2 (Launcher):** Epic Games Launcher kurulum adımları ve doğrulama planı (Operator Action) hazırlanacak.
- **TASK 3 (UE5 Install):** UE5 stabil sürümünün kurulum dizini ve binary yolları doğrulanacak.
- **TASK 4 (Blank Project):** En hafif (minimal) boş proje ayarları tanımlanıp diske kaydedildiği doğrulanacak.
- **TASK 5 (Surface Discovery):** Python Editor Scripting, Editor Utility veya C++ seçenekleri karşılaştırılıp, en düşük riskli MVP yüzeyi seçilecek.
- **TASK 6 (Hook Design):** Seçilen yüzey için gerçek export hook tasarımı yapılacak. `scene_manifest_v1` şeması tanımlanacak.
- **TASK 7 (Summary):** Yapılan keşfin ve tasarımın konsolide JSON ve Markdown özeti çıkarılacak.

**Exit Criteria (Bitiş Şartları):**
ec1_readiness_checked: Ortam hazırlık raporu (blocker'lar dahil) üretildi.
ec2_launcher_plan_written: Launcher kurulum ve doğrulama planı yazıldı.
ec3_ue5_status_written: UE5 kurulum durumu (JSON) doğrulandı.
ec4_blank_project_defined: Boş proje (Blank project) durumu doğrulandı.
ec5_export_surface_ranked: Entegrasyon yüzeyleri karşılaştırıldı ve MVP seçildi.
ec6_real_hook_design_written: Gerçek hook mimari tasarımı dokümante edildi.
ec7_scene_manifest_defined: scene/export manifest v1 dokümanı yazıldı.
ec8_summary_written: FAZ 9D.1 nihai özeti oluşturuldu.

**FAZ 9D.1 Result:** 8/8 Exit Criteria PASS. UE5 5.7.4 confirmed, 
MnemosyneHookMVP.uproject created, Python MoviePipelinePythonHostExecutor 
selected as MVP surface, MnemosyneExecutor hook design documented, 
scene_manifest_v1 frozen. Commit: 670834c.

---

## FAZ 9D.2 ARCHITECTURAL FREEZE (CLOSED)
**Tema:** Real UE5 Hook Implementation — Narrow MVP
**Primary Rule:** "Mnemosyne is a fail-closed admission layer for policy-bound, high-throughput media pipelines."

**Constraints & Assumptions (KIRMIZI ÇİZGİLER):**
- **Yüzey:** SADECE Python `MoviePipelinePythonHostExecutor` kullanılacaktır. C++ plugin kodlaması YOKTUR.
- **İletişim:** SADECE Loopback TCP (127.0.0.1:8765). UDS veya Cloud YOK.
- **Sözleşmeler:** `scene_manifest_v1`, `taxonomy v1.1` ve `quarantine schema v1.1` dondurulmuştur (frozen), değiştirilemez.
- **Proje:** `MnemosyneHookMVP.uproject` referans alınacaktır.

**Görev Tanımları (Tasks):**
- **TASK 1:** Gate stack (Docker & 127.0.0.1:8765) ayakta mı kontrol edilecek.
- **TASK 2:** UE5 Python proje iskeleti (`mnemo_ue5_executor.py`, `init_unreal.py`) oluşturulacak.
- **TASK 3:** Export anında deterministik `scene_manifest_v1` üretilecek.
- **TASK 4:** UE5 export çıktısı Gate API'ye POST edilecek.
- **TASK 5:** Geçerse (PASS) `Mnemosyne_Certified_Passport.json` üretilecek, kalırsa (FAIL) anında fail-closed durdurulacak.
- **TASK 6:** Operatör için minimum UE5 test workflow'u dokümante edilecek.
- **TASK 7:** 1 PASS ve 1 FAIL kanıt dosyası üretilip test edilecek.

**Exit Criteria (Bitiş Şartları):**
ec1_gate_live: Gate API'nin ayakta olduğu doğrulandı.
ec2_executor_integrated: Python hook projeye entegre edildi.
ec3_manifest_generated: Gerçek bir export'tan scene_manifest_v1 üretildi.
ec4_gate_submission_works: UE5'ten Gate'e başarıyla POST atıldı.
ec5_passport_on_pass: PASS durumunda Passport üretildi.
ec6_fail_closed_on_reject: FAIL durumunda süreç durduruldu ve passport reddedildi.
ec7_artifacts_written: PASS/FAIL kanıt logları ve rapor yazıldı.
ec8_scope_preserved: C++'a kayılmadı, mimari sınırlar korundu.

**FAZ 9D.2 Result:** 8/8 Exit Criteria PASS. Real UE5 Python executor (MoviePipelinePythonHostExecutor) implemented. 
Live POST to 127.0.0.1:8765 verified. Pass run produced Ed25519 Mnemosyne_Certified_Passport.json. Fail run triggered fail-closed block. 
Ed25519 Certified Passport produced on PASS, fail-closed verified on REJECT. 
Commit: b31d4ab.

