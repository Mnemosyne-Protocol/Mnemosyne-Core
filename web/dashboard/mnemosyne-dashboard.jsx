import { useState, useEffect, useRef, useCallback } from "react";

// ═══════════════════════════════════════════════════════════════
// DASHBOARD SCHEMA — Mirrors Rust/TS Gateway types exactly
// ═══════════════════════════════════════════════════════════════

const FIXED6_SCALE = 1_000_000;
const KS_SEED = "MNEMOSYNE-KS-V3";

const fixed6ToDisplay = (raw) => raw / FIXED6_SCALE;
const formatUsd = (n) =>
  new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
  }).format(n);
const formatHours = (n) => `${n.toFixed(1)} hrs`;

// ═══════════════════════════════════════════════════════════════
// MOCK DATA ENGINE (simulates live Gateway polling)
// ═══════════════════════════════════════════════════════════════

const VERDICTS = ["SEALED", "REJECT_FATAL", "REJECT_RECOVERABLE"];
const CODES = [
  "B-GEO-101",
  "B-EMB-101",
  "B-CLR-101",
  "B-EMI-101",
  "A-PROV-001",
  "C-CTX-201",
];

function generateLedgerEvents(count) {
  const events = [];
  let prevHash = "0".repeat(64);
  for (let i = 1; i <= count; i++) {
    const isAccept = Math.random() > 0.35;
    const kind = isAccept
      ? "acceptance"
      : Math.random() > 0.3
        ? "rejection_recoverable"
        : "rejection_fatal";
    const ts = new Date(
      Date.now() - (count - i) * 47000 + Math.random() * 20000
    ).toISOString();
    const hash = fakeHash(prevHash + i);
    const hoursSaved = isAccept ? 0 : 1.5;
    const costSaved = hoursSaved * 100;
    events.push({
      seq: i,
      timestamp: ts,
      prev_hash: prevHash,
      event_hash: hash,
      kind,
      frame_id: `frm_${hash.slice(0, 8)}`,
      violation_codes: isAccept
        ? []
        : [CODES[Math.floor(Math.random() * CODES.length)]],
      rework_cost: {
        estimated_hours_saved: Math.round(hoursSaved * FIXED6_SCALE),
        estimated_cost_saved_usd: Math.round(costSaved * FIXED6_SCALE),
      },
    });
    prevHash = hash;
  }
  return events;
}

function fakeHash(seed) {
  let h = 0x9f8c4b2a;
  for (let i = 0; i < seed.length; i++) {
    h = (h ^ seed.charCodeAt(i)) * 0x01000193;
    h = h >>> 0;
  }
  return (
    h.toString(16).padStart(8, "0") +
    ((h * 17 + 0xdeadbeef) >>> 0).toString(16).padStart(8, "0") +
    ((h * 31 + 0xcafebabe) >>> 0).toString(16).padStart(8, "0") +
    ((h * 43 + 0xfeedface) >>> 0).toString(16).padStart(8, "0") +
    ((h * 59 + 0xbaadf00d) >>> 0).toString(16).padStart(8, "0") +
    ((h * 67 + 0x8badf00d) >>> 0).toString(16).padStart(8, "0") +
    ((h * 71 + 0xdeadc0de) >>> 0).toString(16).padStart(8, "0") +
    ((h * 79 + 0xc0ffee00) >>> 0).toString(16).padStart(8, "0")
  );
}

function computeRoi(events) {
  let total = 0,
    accepted = 0,
    rejected = 0,
    fatal = 0,
    recoverable = 0;
  let hoursSavedRaw = 0,
    costSavedRaw = 0;
  for (const e of events) {
    total++;
    if (e.kind === "acceptance") {
      accepted++;
    } else {
      rejected++;
      if (e.kind === "rejection_fatal") fatal++;
      else recoverable++;
      hoursSavedRaw += e.rework_cost.estimated_hours_saved;
      costSavedRaw += e.rework_cost.estimated_cost_saved_usd;
    }
  }
  const hoursSaved = fixed6ToDisplay(hoursSavedRaw);
  const costSaved = fixed6ToDisplay(costSavedRaw);
  const platformCost = total * 0.02;
  const netSavings = costSaved - platformCost;
  const roiPct = platformCost > 0 ? (netSavings / platformCost) * 100 : 0;
  const acceptRate = total > 0 ? (accepted / total) * 100 : 0;
  const fatalRate = rejected > 0 ? (fatal / rejected) * 100 : 0;
  return {
    total,
    accepted,
    rejected,
    fatal,
    recoverable,
    hoursSaved,
    costSaved,
    platformCost,
    netSavings,
    roiPct,
    acceptRate,
    fatalRate,
    hoursSavedRaw,
    costSavedRaw,
  };
}

// ═══════════════════════════════════════════════════════════════
// ANIMATED NUMBER COUNTER
// ═══════════════════════════════════════════════════════════════

function AnimatedCounter({ value, format = (v) => v.toFixed(0), duration = 900 }) {
  const [display, setDisplay] = useState(0);
  const ref = useRef(0);
  const frameRef = useRef(null);

  useEffect(() => {
    const start = ref.current;
    const diff = value - start;
    const startTime = performance.now();

    function animate(now) {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      const current = start + diff * eased;
      setDisplay(current);
      ref.current = current;
      if (progress < 1) {
        frameRef.current = requestAnimationFrame(animate);
      }
    }
    frameRef.current = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(frameRef.current);
  }, [value, duration]);

  return <span>{format(display)}</span>;
}

// ═══════════════════════════════════════════════════════════════
// KS VERIFIED BADGE
// ═══════════════════════════════════════════════════════════════

function KsBadge({ small = false }) {
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 4,
        padding: small ? "1px 6px" : "2px 8px",
        background: "rgba(6,182,212,0.12)",
        border: "1px solid rgba(6,182,212,0.3)",
        borderRadius: 3,
        fontSize: small ? 9 : 10,
        fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
        color: "#67e8f9",
        letterSpacing: "0.05em",
        textTransform: "uppercase",
        whiteSpace: "nowrap",
      }}
    >
      <span style={{ color: "#22d3ee" }}>◆</span>
      KS Verified
    </span>
  );
}

// ═══════════════════════════════════════════════════════════════
// ROI COUNTER COMPONENT
// ═══════════════════════════════════════════════════════════════

function RoiCounter({ roi }) {
  const cards = [
    {
      label: "Total USD Saved",
      value: roi.costSaved,
      format: (v) => formatUsd(v),
      color: "#34d399",
      accent: "#059669",
      icon: "↗",
      showBadge: true,
    },
    {
      label: "Hours Reclaimed",
      value: roi.hoursSaved,
      format: (v) => formatHours(v),
      color: "#67e8f9",
      accent: "#0891b2",
      icon: "◷",
      showBadge: true,
    },
    {
      label: "Net ROI",
      value: roi.roiPct,
      format: (v) => `${v.toFixed(0)}%`,
      color: "#fbbf24",
      accent: "#d97706",
      icon: "◈",
      showBadge: false,
    },
    {
      label: "Accept Rate",
      value: roi.acceptRate,
      format: (v) => `${v.toFixed(1)}%`,
      color: roi.acceptRate > 80 ? "#34d399" : "#f87171",
      accent: roi.acceptRate > 80 ? "#059669" : "#dc2626",
      icon: "Ψ",
      showBadge: false,
    },
  ];

  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 16 }}>
      {cards.map((card, i) => (
        <div
          key={i}
          style={{
            background: "linear-gradient(135deg, rgba(15,23,42,0.95), rgba(15,23,42,0.8))",
            border: `1px solid ${card.accent}33`,
            borderRadius: 6,
            padding: "20px 18px 16px",
            position: "relative",
            overflow: "hidden",
          }}
        >
          <div
            style={{
              position: "absolute",
              top: 0,
              left: 0,
              right: 0,
              height: 2,
              background: `linear-gradient(90deg, transparent, ${card.color}, transparent)`,
            }}
          />
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginBottom: 12,
            }}
          >
            <span
              style={{
                fontSize: 11,
                color: "#94a3b8",
                textTransform: "uppercase",
                letterSpacing: "0.08em",
                fontFamily: "'JetBrains Mono', monospace",
              }}
            >
              {card.icon} {card.label}
            </span>
            {card.showBadge && <KsBadge small />}
          </div>
          <div
            style={{
              fontSize: 30,
              fontWeight: 700,
              color: card.color,
              fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
              letterSpacing: "-0.02em",
              lineHeight: 1,
            }}
          >
            <AnimatedCounter value={card.value} format={card.format} />
          </div>
        </div>
      ))}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// FRAME STATISTICS BAR
// ═══════════════════════════════════════════════════════════════

function FrameStats({ roi }) {
  const sealedPct = roi.total > 0 ? (roi.accepted / roi.total) * 100 : 0;
  const fatalPct = roi.total > 0 ? (roi.fatal / roi.total) * 100 : 0;
  const recovPct = roi.total > 0 ? (roi.recoverable / roi.total) * 100 : 0;

  return (
    <div
      style={{
        background: "rgba(15,23,42,0.95)",
        border: "1px solid rgba(51,65,85,0.5)",
        borderRadius: 6,
        padding: "16px 18px",
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 14,
        }}
      >
        <span style={{ fontSize: 11, color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.08em", fontFamily: "'JetBrains Mono', monospace" }}>
          Frame Pipeline · {roi.total.toLocaleString()} processed
        </span>
        <span style={{ fontSize: 10, color: "#64748b", fontFamily: "'JetBrains Mono', monospace" }}>
          Fixed6 raw: hours={roi.hoursSavedRaw} cost={roi.costSavedRaw}
        </span>
      </div>
      <div
        style={{
          display: "flex",
          height: 20,
          borderRadius: 3,
          overflow: "hidden",
          background: "#1e293b",
        }}
      >
        <div
          style={{
            width: `${sealedPct}%`,
            background: "linear-gradient(90deg, #059669, #34d399)",
            transition: "width 0.6s ease",
          }}
        />
        <div
          style={{
            width: `${recovPct}%`,
            background: "linear-gradient(90deg, #d97706, #fbbf24)",
            transition: "width 0.6s ease",
          }}
        />
        <div
          style={{
            width: `${fatalPct}%`,
            background: "linear-gradient(90deg, #dc2626, #f87171)",
            transition: "width 0.6s ease",
          }}
        />
      </div>
      <div
        style={{
          display: "flex",
          gap: 20,
          marginTop: 10,
          fontSize: 11,
          fontFamily: "'JetBrains Mono', monospace",
        }}
      >
        <span style={{ color: "#34d399" }}>● SEALED {roi.accepted}</span>
        <span style={{ color: "#fbbf24" }}>● RECOVERABLE {roi.recoverable}</span>
        <span style={{ color: "#f87171" }}>● FATAL {roi.fatal}</span>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// LEDGER TREE COMPONENT
// ═══════════════════════════════════════════════════════════════

function LedgerTree({ events, showKsDetails }) {
  const visibleEvents = events.slice(-30).reverse();

  return (
    <div
      style={{
        background: "rgba(15,23,42,0.95)",
        border: "1px solid rgba(51,65,85,0.5)",
        borderRadius: 6,
        padding: "16px 0",
        maxHeight: 460,
        overflow: "auto",
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          padding: "0 18px 12px",
          borderBottom: "1px solid rgba(51,65,85,0.3)",
        }}
      >
        <span style={{ fontSize: 11, color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.08em", fontFamily: "'JetBrains Mono', monospace" }}>
          Hash-Chain Explorer · Last {visibleEvents.length} events
        </span>
        <KsBadge />
      </div>
      {visibleEvents.map((event, i) => {
        const isAccept = event.kind === "acceptance";
        const isFatal = event.kind === "rejection_fatal";
        const color = isAccept ? "#34d399" : isFatal ? "#f87171" : "#fbbf24";
        const label = isAccept
          ? "SEALED"
          : isFatal
            ? "REJECT_FATAL"
            : "REJECT_RECOVERABLE";

        return (
          <div key={event.seq} style={{ position: "relative" }}>
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "50px 1fr",
                gap: 0,
                padding: "10px 18px 10px 0",
                borderBottom:
                  i < visibleEvents.length - 1
                    ? "1px solid rgba(51,65,85,0.15)"
                    : "none",
              }}
            >
              {/* Chain link visualization */}
              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  position: "relative",
                }}
              >
                <div
                  style={{
                    width: 10,
                    height: 10,
                    borderRadius: "50%",
                    background: color,
                    border: `2px solid ${color}`,
                    boxShadow: `0 0 8px ${color}44`,
                    zIndex: 1,
                    marginTop: 4,
                  }}
                />
                {i < visibleEvents.length - 1 && (
                  <div
                    style={{
                      position: "absolute",
                      top: 18,
                      width: 1,
                      bottom: -12,
                      background: `linear-gradient(180deg, ${color}66, rgba(51,65,85,0.3))`,
                    }}
                  />
                )}
              </div>

              {/* Event content */}
              <div>
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 8,
                    marginBottom: 4,
                  }}
                >
                  <span
                    style={{
                      fontSize: 10,
                      fontFamily: "'JetBrains Mono', monospace",
                      color: "#64748b",
                    }}
                  >
                    #{event.seq}
                  </span>
                  <span
                    style={{
                      fontSize: 10,
                      fontFamily: "'JetBrains Mono', monospace",
                      padding: "1px 6px",
                      borderRadius: 2,
                      color,
                      background: `${color}15`,
                      border: `1px solid ${color}33`,
                      fontWeight: 600,
                    }}
                  >
                    {label}
                  </span>
                  <span style={{ fontSize: 10, color: "#475569", fontFamily: "'JetBrains Mono', monospace" }}>
                    {event.frame_id}
                  </span>
                  <span
                    style={{
                      marginLeft: "auto",
                      fontSize: 9,
                      color: "#475569",
                      fontFamily: "'JetBrains Mono', monospace",
                    }}
                  >
                    {new Date(event.timestamp).toLocaleTimeString()}
                  </span>
                </div>
                {/* Hash chain */}
                <div
                  style={{
                    fontSize: 9,
                    fontFamily: "'JetBrains Mono', monospace",
                    color: "#334155",
                    display: "flex",
                    flexWrap: "wrap",
                    gap: "2px 12px",
                    lineHeight: 1.6,
                  }}
                >
                  <span>
                    hash:{" "}
                    <span style={{ color: "#67e8f9" }}>
                      {event.event_hash.slice(0, 16)}…
                    </span>
                  </span>
                  <span>
                    prev:{" "}
                    <span style={{ color: "#475569" }}>
                      {event.prev_hash.slice(0, 16)}…
                    </span>
                  </span>
                  {showKsDetails && (
                    <span>
                      salt:{" "}
                      <span style={{ color: "#22d3ee" }}>{KS_SEED}</span>
                    </span>
                  )}
                  {!isAccept && event.violation_codes.length > 0 && (
                    <span>
                      code:{" "}
                      <span style={{ color: "#f87171" }}>
                        {event.violation_codes.join(",")}
                      </span>
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// QUARANTINE OVERLAY — Fail-Closed UI
// ═══════════════════════════════════════════════════════════════

function QuarantineOverlay() {
  const [pulse, setPulse] = useState(false);
  useEffect(() => {
    const iv = setInterval(() => setPulse((p) => !p), 1200);
    return () => clearInterval(iv);
  }, []);

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 9999,
        background: "rgba(2,6,23,0.92)",
        backdropFilter: "grayscale(100%) blur(3px)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        flexDirection: "column",
      }}
    >
      <div
        style={{
          width: 80,
          height: 80,
          borderRadius: "50%",
          border: `3px solid ${pulse ? "#dc2626" : "#7f1d1d"}`,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 36,
          transition: "border-color 0.6s ease",
          marginBottom: 24,
        }}
      >
        🛡️
      </div>
      <div
        style={{
          fontSize: 22,
          fontWeight: 700,
          color: "#f87171",
          fontFamily: "'JetBrains Mono', monospace",
          letterSpacing: "0.1em",
          textTransform: "uppercase",
          marginBottom: 12,
        }}
      >
        QUARANTINE MODE
      </div>
      <div
        style={{
          fontSize: 13,
          color: "#94a3b8",
          maxWidth: 420,
          textAlign: "center",
          lineHeight: 1.7,
          fontFamily: "'JetBrains Mono', monospace",
        }}
      >
        Connection to the Mnemosyne Core lost.
        <br />
        <span style={{ color: "#f87171", fontWeight: 600 }}>
          FAIL-CLOSED: All data is now stale and unverified.
        </span>
        <br />
        Dashboard locked to prevent display of unattested metrics.
      </div>
      <div
        style={{
          marginTop: 28,
          fontSize: 10,
          color: "#475569",
          fontFamily: "'JetBrains Mono', monospace",
        }}
      >
        Reconnecting… Attempting to restore verified data feed.
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// MAIN DASHBOARD
// ═══════════════════════════════════════════════════════════════

export default function MnemosyneDashboard() {
  const [events, setEvents] = useState(() => generateLedgerEvents(85));
  const [roi, setRoi] = useState(() => computeRoi(generateLedgerEvents(85)));
  const [connected, setConnected] = useState(true);
  const [showKsDetails, setShowKsDetails] = useState(true);
  const [lastUpdate, setLastUpdate] = useState(new Date());

  // Simulate live data feed (5s polling)
  useEffect(() => {
    if (!connected) return;
    const iv = setInterval(() => {
      setEvents((prev) => {
        const next = [...prev];
        const newSeq = next.length + 1;
        const prevHash = next.length > 0 ? next[next.length - 1].event_hash : "0".repeat(64);
        const isAccept = Math.random() > 0.33;
        const kind = isAccept
          ? "acceptance"
          : Math.random() > 0.3
            ? "rejection_recoverable"
            : "rejection_fatal";
        const hash = fakeHash(prevHash + newSeq + Date.now());
        next.push({
          seq: newSeq,
          timestamp: new Date().toISOString(),
          prev_hash: prevHash,
          event_hash: hash,
          kind,
          frame_id: `frm_${hash.slice(0, 8)}`,
          violation_codes: isAccept
            ? []
            : [CODES[Math.floor(Math.random() * CODES.length)]],
          rework_cost: {
            estimated_hours_saved: isAccept ? 0 : 1_500_000,
            estimated_cost_saved_usd: isAccept ? 0 : 150_000_000,
          },
        });
        setRoi(computeRoi(next));
        setLastUpdate(new Date());
        return next;
      });
    }, 5000);
    return () => clearInterval(iv);
  }, [connected]);

  return (
    <>
      <link
        href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=DM+Sans:wght@400;500;600;700&display=swap"
        rel="stylesheet"
      />
      {!connected && <QuarantineOverlay />}
      <div
        style={{
          minHeight: "100vh",
          background: "#020617",
          color: "#e2e8f0",
          fontFamily: "'DM Sans', sans-serif",
          padding: "24px 28px",
          position: "relative",
        }}
      >
        {/* Background grain texture */}
        <div
          style={{
            position: "fixed",
            inset: 0,
            opacity: 0.03,
            backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E")`,
            pointerEvents: "none",
            zIndex: 0,
          }}
        />

        {/* Header */}
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start",
            marginBottom: 28,
            position: "relative",
            zIndex: 1,
          }}
        >
          <div>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 12,
                marginBottom: 6,
              }}
            >
              <span
                style={{
                  fontSize: 20,
                  fontWeight: 700,
                  fontFamily: "'JetBrains Mono', monospace",
                  letterSpacing: "-0.02em",
                  color: "#f0fdfa",
                }}
              >
                MNEMOSYNE
              </span>
              <span
                style={{
                  fontSize: 11,
                  padding: "2px 8px",
                  background: "rgba(6,182,212,0.1)",
                  border: "1px solid rgba(6,182,212,0.25)",
                  borderRadius: 3,
                  color: "#67e8f9",
                  fontFamily: "'JetBrains Mono', monospace",
                  fontWeight: 500,
                }}
              >
                v3.0.0
              </span>
              <span
                style={{
                  fontSize: 11,
                  padding: "2px 8px",
                  background: connected ? "rgba(52,211,153,0.1)" : "rgba(248,113,113,0.1)",
                  border: `1px solid ${connected ? "rgba(52,211,153,0.25)" : "rgba(248,113,113,0.25)"}`,
                  borderRadius: 3,
                  color: connected ? "#34d399" : "#f87171",
                  fontFamily: "'JetBrains Mono', monospace",
                  fontWeight: 500,
                }}
              >
                {connected ? "● LIVE" : "● DISCONNECTED"}
              </span>
            </div>
            <div style={{ fontSize: 12, color: "#64748b", fontFamily: "'JetBrains Mono', monospace" }}>
              Executive Rework Dashboard · Fail-Closed Mode Active
            </div>
          </div>
          <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <button
              onClick={() => setShowKsDetails((p) => !p)}
              style={{
                padding: "6px 12px",
                fontSize: 10,
                fontFamily: "'JetBrains Mono', monospace",
                background: showKsDetails ? "rgba(6,182,212,0.15)" : "rgba(51,65,85,0.3)",
                border: `1px solid ${showKsDetails ? "rgba(6,182,212,0.3)" : "rgba(51,65,85,0.3)"}`,
                borderRadius: 4,
                color: showKsDetails ? "#67e8f9" : "#64748b",
                cursor: "pointer",
                textTransform: "uppercase",
                letterSpacing: "0.05em",
              }}
            >
              {showKsDetails ? "◆ KS Layer Visible" : "◇ Show KS Layer"}
            </button>
            <button
              onClick={() => setConnected((p) => !p)}
              style={{
                padding: "6px 12px",
                fontSize: 10,
                fontFamily: "'JetBrains Mono', monospace",
                background: connected ? "rgba(51,65,85,0.3)" : "rgba(248,113,113,0.15)",
                border: `1px solid ${connected ? "rgba(51,65,85,0.3)" : "rgba(248,113,113,0.3)"}`,
                borderRadius: 4,
                color: connected ? "#64748b" : "#f87171",
                cursor: "pointer",
                textTransform: "uppercase",
                letterSpacing: "0.05em",
              }}
            >
              {connected ? "Simulate Disconnect" : "Reconnect"}
            </button>
          </div>
        </div>

        {/* ROI Counters */}
        <div style={{ marginBottom: 20, position: "relative", zIndex: 1 }}>
          <RoiCounter roi={roi} />
        </div>

        {/* Frame Statistics */}
        <div style={{ marginBottom: 20, position: "relative", zIndex: 1 }}>
          <FrameStats roi={roi} />
        </div>

        {/* Two column: Ledger Tree + Audit Details */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 340px",
            gap: 16,
            position: "relative",
            zIndex: 1,
          }}
        >
          <LedgerTree events={events} showKsDetails={showKsDetails} />

          {/* Audit panel */}
          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            {/* Chain integrity */}
            <div
              style={{
                background: "rgba(15,23,42,0.95)",
                border: "1px solid rgba(52,211,153,0.2)",
                borderRadius: 6,
                padding: 18,
              }}
            >
              <div style={{ fontSize: 11, color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.08em", fontFamily: "'JetBrains Mono', monospace", marginBottom: 14 }}>
                Chain Integrity
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 12 }}>
                <div
                  style={{
                    width: 32,
                    height: 32,
                    borderRadius: 6,
                    background: "rgba(52,211,153,0.1)",
                    border: "1px solid rgba(52,211,153,0.25)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontSize: 16,
                  }}
                >
                  ✓
                </div>
                <div>
                  <div style={{ fontSize: 14, fontWeight: 600, color: "#34d399" }}>
                    VALID
                  </div>
                  <div style={{ fontSize: 10, color: "#64748b", fontFamily: "'JetBrains Mono', monospace" }}>
                    {events.length} events, 0 breaks
                  </div>
                </div>
              </div>
              <div style={{ fontSize: 9, color: "#334155", fontFamily: "'JetBrains Mono', monospace", lineHeight: 1.8 }}>
                tip: {events.length > 0 ? events[events.length - 1].event_hash.slice(0, 24) : "—"}…
                <br />
                genesis: {events.length > 0 ? events[0].prev_hash.slice(0, 24) : "—"}…
              </div>
            </div>

            {/* KS Entropy Layer info */}
            <div
              style={{
                background: "rgba(15,23,42,0.95)",
                border: "1px solid rgba(6,182,212,0.2)",
                borderRadius: 6,
                padding: 18,
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
                <span style={{ fontSize: 11, color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.08em", fontFamily: "'JetBrains Mono', monospace" }}>
                  KS Entropy Layer
                </span>
                <KsBadge />
              </div>
              <div style={{ fontSize: 10, color: "#67e8f9", fontFamily: "'JetBrains Mono', monospace", lineHeight: 1.8, marginBottom: 8 }}>
                seed: {KS_SEED}
                <br />
                bytes: {KS_SEED.length}
                <br />
                method: H(KS ‖ data)
                <br />
                scope: domain separation
              </div>
              <div style={{ fontSize: 9, color: "#475569", lineHeight: 1.6, fontStyle: "italic" }}>
                "KS is the seed from which all deterministic proof grows."
              </div>
            </div>

            {/* Billing summary */}
            <div
              style={{
                background: "rgba(15,23,42,0.95)",
                border: "1px solid rgba(51,65,85,0.5)",
                borderRadius: 6,
                padding: 18,
              }}
            >
              <div style={{ fontSize: 11, color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.08em", fontFamily: "'JetBrains Mono', monospace", marginBottom: 14 }}>
                Billing Period
              </div>
              <div style={{ fontSize: 10, fontFamily: "'JetBrains Mono', monospace", lineHeight: 2, color: "#94a3b8" }}>
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <span>Gross savings</span>
                  <span style={{ color: "#34d399" }}>{formatUsd(roi.costSaved)}</span>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <span>Platform cost</span>
                  <span style={{ color: "#fbbf24" }}>{formatUsd(roi.platformCost)}</span>
                </div>
                <div style={{ borderTop: "1px solid rgba(51,65,85,0.3)", display: "flex", justifyContent: "space-between", paddingTop: 4 }}>
                  <span style={{ fontWeight: 600, color: "#e2e8f0" }}>Net savings</span>
                  <span style={{ fontWeight: 700, color: "#34d399" }}>{formatUsd(roi.netSavings)}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div
          style={{
            marginTop: 24,
            padding: "16px 0 0",
            borderTop: "1px solid rgba(51,65,85,0.2)",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            fontSize: 10,
            color: "#334155",
            fontFamily: "'JetBrains Mono', monospace",
            position: "relative",
            zIndex: 1,
          }}
        >
          <span>
            Mnemosyne Labs · Layer-0 Deterministic Governance Protocol
          </span>
          <span>
            Last update: {lastUpdate.toLocaleTimeString()} · FAIL-CLOSED MODE ACTIVE
          </span>
        </div>
      </div>
    </>
  );
}
