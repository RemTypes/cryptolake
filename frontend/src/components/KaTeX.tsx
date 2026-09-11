"use client";

import React, { useMemo } from "react";
import katex from "katex";

interface KaTeXProps {
  math: string;
  block?: boolean;
  className?: string;
}

export const KaTeX: React.FC<KaTeXProps> = ({ math, block = false, className = "" }) => {
  const html = useMemo(() => {
    try {
      return katex.renderToString(math, {
        displayMode: block,
        throwOnError: false,
      });
    } catch {
      return math;
    }
  }, [math, block]);

  return (
    <span
      className={className}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
};
