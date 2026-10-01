import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { CAPTIONS, CaptionEntry, SceneId } from "../timeline";
import { colors, fonts } from "../theme";

/** Renders a caption string where *word* marks emphasis. */
const CaptionText: React.FC<{ text: string }> = ({ text }) => (
  <>
    {text.split("*").map((part, i) =>
      i % 2 === 1 ? (
        <span key={i} style={{ position: "relative", color: colors.primary, fontWeight: 700, isolation: "isolate" }}>
          {part}
          <span
            style={{
              position: "absolute",
              left: "-2%",
              right: "-2%",
              bottom: "0.05em",
              height: "0.32em",
              borderRadius: 999,
              background: colors.infoBg,
              zIndex: -1,
            }}
          />
        </span>
      ) : (
        <span key={i}>{part}</span>
      ),
    )}
  </>
);

/**
 * Subtitle track driven by timeline.json. Each caption is a short phrase so the
 * line never fills the bottom of the frame.
 */
export const CaptionTrack: React.FC<{ hideIn?: SceneId[]; bottom?: number; fontSize?: number }> = ({
  hideIn = [],
  bottom = 64,
  fontSize = 44,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const ms = (frame / fps) * 1000;
  const active: CaptionEntry | undefined = CAPTIONS.find(
    (c) => ms >= c.startMs && ms < c.endMs && !hideIn.includes(c.sceneId),
  );
  if (!active) return null;

  const startF = (active.startMs / 1000) * fps;
  const endF = (active.endMs / 1000) * fps;
  const opacity = interpolate(frame, [startF, startF + 4, endF - 3, endF], [0, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const lift = interpolate(frame, [startF, startF + 6], [8, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", pointerEvents: "none" }}>
      <div
        style={{
          marginBottom: bottom,
          opacity,
          translate: `0px ${lift}px`,
          display: "flex",
          alignItems: "center",
          gap: 18,
          padding: "14px 34px 16px 26px",
          borderRadius: 18,
          background: "#ffffffee",
          border: `1.5px solid ${colors.borderSoft}`,
          boxShadow: "0 18px 40px -26px #00009155",
          fontFamily: fonts.sans,
          fontSize,
          fontWeight: 500,
          lineHeight: 1.35,
          color: colors.heading,
          letterSpacing: "0.02em",
          whiteSpace: "nowrap",
        }}
      >
        <div style={{ display: "flex", flexDirection: "column", gap: 5 }}>
          <div style={{ width: 5, height: fontSize * 0.42, borderRadius: 3, background: colors.primary }} />
          <div style={{ width: 5, height: fontSize * 0.2, borderRadius: 3, background: colors.accent }} />
        </div>
        <span>
          <CaptionText text={active.text} />
        </span>
      </div>
    </AbsoluteFill>
  );
};
