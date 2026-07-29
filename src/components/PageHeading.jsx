import React from "react";
import { COLORS, FONTS } from "../theme";

export default function PageHeading({ eyebrow, title, subtitle }) {
  return (
    <>
      <p className="text-xs uppercase tracking-widest mb-2.5" style={{ fontFamily: FONTS.mono, color: COLORS.signal, letterSpacing: "0.14em" }}>
        {eyebrow}
      </p>
      <h1 className="font-bold m-0 mb-2" style={{ fontFamily: FONTS.display, fontSize: 44, letterSpacing: "-0.01em" }}>
        {title}
      </h1>
      <p className="mb-10 max-w-lg leading-relaxed" style={{ color: COLORS.slate, fontSize: 15 }}>
        {subtitle}
      </p>
    </>
  );
}
