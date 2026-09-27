import React from "react";
import { Easing, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { color, font, springs } from "../../theme";

// Rasterized pages of Teresa's packet (1700×2200). Page 8 is the file list with the signature line, so it lands on top.
const PAGES = [1, 2, 3, 4, 5, 6, 7, 8];
const LABELS = ["Index", "Claim form", "Periapical #46", "Bitewing, right", "Bitewing, left", "Perio chart", "Narrative"];
const PAGE_W = 1700;
const PAGE_H = 2200;
const H = 640;
const S = H / PAGE_H;
const W = PAGE_W * S;

// Ophi assembles the request: sheets fly in and fan out, the dentist signs the top one.
export const PacketFan: React.FC<{ start: number; sign: number; stagger?: number; dir?: string; cy?: number }> = ({ start, sign, stagger = 5, dir = "app-v2", cy = 448 }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const cx = 760;
  const n = PAGES.length;
  const sigP = interpolate(f, [sign, sign + 16], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.bezier(0.45, 0, 0.3, 1) });
  const badge = spring({ frame: f - sign - 12, fps, config: springs.overshoot });
  return (
    <div style={{ position: "absolute", inset: 0 }}>
      {PAGES.map((p, i) => {
        const at = start + i * stagger;
        const s = spring({ frame: f - at, fps, config: { damping: 20, stiffness: 150, mass: 0.8 } });
        if (f < at) return null;
        // Fan: spread by index around the stack centre; the last page lands flat on top.
        const k = i - (n - 1) / 2;
        const top = i === n - 1;
        const rot = top ? 0 : k * 4.2;
        const dx = top ? 0 : k * 46;
        const dy = top ? 0 : Math.abs(k) * 8;
        const x = interpolate(s, [0, 1], [1500, cx + dx]);
        const y = interpolate(s, [0, 1], [1250, cy + dy]);
        const r = interpolate(s, [0, 1], [28, rot]);
        return (
          <div
            key={p}
            style={{
              position: "absolute",
              left: x - W / 2,
              top: y - H / 2,
              width: W,
              height: H,
              transform: `rotate(${r}deg)`,
              transformOrigin: "50% 90%",
              background: "#fff",
              borderRadius: 6,
              boxShadow: "0 1px 2px rgba(15,36,29,0.15), 0 16px 40px rgba(15,36,29,0.18)",
              overflow: "hidden",
            }}
          >
            <Img src={staticFile(`${dir}/11b-packet-page-${p}.png`)} style={{ width: W, height: H }} />
            {top && (
              <svg width={W} height={H} viewBox={`0 0 ${PAGE_W} ${PAGE_H}`} style={{ position: "absolute", inset: 0 }}>
                <path
                  d="M 300 1052 C 330 990, 350 985, 356 1040 C 360 1070, 372 990, 404 1000 C 430 1010, 412 1052, 440 1046 C 470 1040, 470 996, 500 1004 C 520 1010, 510 1050, 540 1042 C 580 1030, 600 1000, 650 1030 C 680 1046, 700 1030, 720 1026"
                  fill="none"
                  stroke={color.forest}
                  strokeWidth={9}
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  pathLength={1}
                  strokeDasharray={1}
                  strokeDashoffset={1 - sigP}
                />
              </svg>
            )}
          </div>
        );
      })}
      {/* File chips, right column */}
      <div style={{ position: "absolute", left: 1240, top: cy - 250, display: "flex", flexDirection: "column", gap: 14 }}>
        {LABELS.map((l, i) => {
          const at = start + i * stagger + 6;
          const s = spring({ frame: f - at, fps, config: springs.snappy });
          if (f < at) return null;
          return (
            <div
              key={l}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 14,
                opacity: s,
                transform: `translateX(${(1 - s) * 40}px)`,
                fontFamily: font.sans,
                fontSize: 30,
                color: color.forest,
              }}
            >
              <svg width={30} height={30} viewBox="0 0 30 30">
                <circle cx={15} cy={15} r={14} fill={color.forest} />
                <path d="M8.5 15.5 l4.5 4.5 l8.5 -9" fill="none" stroke={color.ivory} strokeWidth={3} strokeLinecap="round" strokeLinejoin="round" />
              </svg>
              {l}
            </div>
          );
        })}
      </div>
      {/* Signed badge */}
      {f >= sign + 12 && (
        <div
          style={{
            position: "absolute",
            left: 1240,
            top: cy + 170,
            transform: `scale(${badge})`,
            transformOrigin: "0 50%",
            padding: "16px 26px",
            borderRadius: 16,
            background: color.forest,
            color: color.ivory,
            fontFamily: font.sans,
            boxShadow: "0 14px 40px rgba(15,36,29,0.3)",
          }}
        >
          <div style={{ fontSize: 32, fontWeight: 500 }}>Signed · Dr. Priya Lau</div>
          <div style={{ fontSize: 22, opacity: 0.75, marginTop: 4 }}>under the dentist’s licence · ON-48213</div>
        </div>
      )}
    </div>
  );
};
