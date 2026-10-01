import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { SCENE_OVERLAP } from "../timeline";
import { fonts } from "../theme";
import { Backdrop } from "./Backdrop";

/** Opaque scene layer; later scenes fade in over the tail of the previous one. */
export const SceneFrame: React.FC<{
  fadeIn?: boolean;
  washX?: string;
  washY?: string;
  gridOpacity?: number;
  children: React.ReactNode;
}> = ({ fadeIn = true, washX, washY, gridOpacity, children }) => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill
      style={{
        fontFamily: fonts.sans,
        opacity: fadeIn
          ? interpolate(frame, [0, SCENE_OVERLAP], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })
          : 1,
      }}
    >
      <Backdrop washX={washX} washY={washY} gridOpacity={gridOpacity}>
        {children}
      </Backdrop>
    </AbsoluteFill>
  );
};
