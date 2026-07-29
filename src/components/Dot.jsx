import React from "react";
import { COLORS } from "../theme";

export default function Dot({ color }) {
  return <span className="inline-block rounded-full flex-shrink-0" style={{ width: 6, height: 6, background: color || COLORS.good }} />;
}
