import React from "react";
import { Img, staticFile } from "remotion";

export type Crop = { x: number; y: number; w: number; h: number };

/** Shows a region of a source image scaled to cover a fixed box. */
export const CropImage: React.FC<{
  src: string;
  srcW: number;
  srcH: number;
  crop: Crop;
  width: number;
  height: number;
  zoom?: number;
  style?: React.CSSProperties;
}> = ({ src, srcW, srcH, crop, width, height, zoom = 1, style }) => {
  const scale = Math.max(width / crop.w, height / crop.h) * zoom;
  const cx = crop.x + crop.w / 2;
  const cy = crop.y + crop.h / 2;
  return (
    <div style={{ position: "relative", width, height, overflow: "hidden", ...style }}>
      <Img
        src={staticFile(src)}
        style={{
          position: "absolute",
          width: srcW * scale,
          height: srcH * scale,
          left: width / 2 - cx * scale,
          top: height / 2 - cy * scale,
          maxWidth: "none",
        }}
      />
    </div>
  );
};
