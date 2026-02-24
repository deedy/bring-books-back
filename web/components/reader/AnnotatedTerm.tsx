"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { createPortal } from "react-dom";
import { Annotation } from "@/lib/types";

interface AnnotatedTermProps {
  term: string;
  annotation: Annotation;
  darkMode: boolean;
}

const typeColors = {
  character: { light: "rgba(59,130,246,0.5)", dark: "rgba(96,165,250,0.4)", badge: "#3b82f6", label: "Character" },
  proper_noun: { light: "rgba(217,119,6,0.5)", dark: "rgba(251,191,36,0.4)", badge: "#d97706", label: "Place / Term" },
  vocabulary: { light: "rgba(22,163,74,0.5)", dark: "rgba(74,222,128,0.4)", badge: "#16a34a", label: "Vocabulary" },
};

export default function AnnotatedTerm({ term, annotation, darkMode }: AnnotatedTermProps) {
  const [open, setOpen] = useState(false);
  const [pos, setPos] = useState<{ top: number; left: number; arrowLeft: number; above: boolean } | null>(null);
  const spanRef = useRef<HTMLSpanElement>(null);
  const cardRef = useRef<HTMLDivElement>(null);

  const colors = typeColors[annotation.type];
  const underlineColor = darkMode ? colors.dark : colors.light;
  const underlineStyle = annotation.type === "vocabulary" ? "dashed" : "dotted";

  const computePosition = useCallback(() => {
    if (!spanRef.current) return;
    const rect = spanRef.current.getBoundingClientRect();
    const cardWidth = 280;
    const cardHeight = 120; // estimate
    const margin = 8;

    // Center card on the term, clamp to viewport
    let left = rect.left + rect.width / 2 - cardWidth / 2;
    left = Math.max(margin, Math.min(left, window.innerWidth - cardWidth - margin));

    const arrowLeft = rect.left + rect.width / 2 - left;

    // Prefer below, but flip above if not enough space
    const spaceBelow = window.innerHeight - rect.bottom;
    const above = spaceBelow < cardHeight + margin + 8;
    const top = above
      ? rect.top + window.scrollY - cardHeight - 8
      : rect.bottom + window.scrollY + 8;

    setPos({ top, left, arrowLeft, above });
  }, []);

  // Track whether the current interaction is touch-based
  const isTouchRef = useRef(false);

  const handleTouchStart = useCallback(() => {
    isTouchRef.current = true;
  }, []);

  const handleClick = useCallback(() => {
    // On touch: toggle open/close
    if (isTouchRef.current) {
      if (open) {
        setOpen(false);
      } else {
        computePosition();
        setOpen(true);
      }
      return;
    }
    // On mouse click: toggle
    if (open) {
      setOpen(false);
    } else {
      computePosition();
      setOpen(true);
    }
  }, [open, computePosition]);

  const handleMouseEnter = useCallback(() => {
    // Skip hover behavior on touch devices
    if (isTouchRef.current) return;
    computePosition();
    setOpen(true);
  }, [computePosition]);

  const handleMouseLeave = useCallback(() => {
    // Skip hover behavior on touch devices
    if (isTouchRef.current) return;
    setOpen(false);
  }, []);

  // Reset touch flag after a short delay (so mouse events after touch are ignored)
  useEffect(() => {
    if (!isTouchRef.current) return;
    const timer = setTimeout(() => { isTouchRef.current = false; }, 500);
    return () => clearTimeout(timer);
  });

  // Close on outside tap (mobile)
  useEffect(() => {
    if (!open) return;
    const handler = (e: MouseEvent | TouchEvent) => {
      if (
        cardRef.current && !cardRef.current.contains(e.target as Node) &&
        spanRef.current && !spanRef.current.contains(e.target as Node)
      ) {
        setOpen(false);
      }
    };
    // Use a slight delay so the opening tap doesn't immediately close
    const timer = setTimeout(() => {
      document.addEventListener("mousedown", handler);
      document.addEventListener("touchstart", handler);
    }, 10);
    return () => {
      clearTimeout(timer);
      document.removeEventListener("mousedown", handler);
      document.removeEventListener("touchstart", handler);
    };
  }, [open]);

  // Recompute position on scroll/resize while open
  useEffect(() => {
    if (!open) return;
    const recompute = () => computePosition();
    window.addEventListener("scroll", recompute, { passive: true });
    window.addEventListener("resize", recompute);
    return () => {
      window.removeEventListener("scroll", recompute);
      window.removeEventListener("resize", recompute);
    };
  }, [open, computePosition]);

  const card = open && pos && createPortal(
    <div
      ref={cardRef}
      style={{
        position: "absolute",
        top: pos.top,
        left: pos.left,
        width: 280,
        zIndex: 9999,
        fontFamily: "var(--font-serif)",
      }}
    >
      {/* Arrow */}
      <div
        style={{
          position: "absolute",
          [pos.above ? "bottom" : "top"]: -6,
          left: pos.arrowLeft - 6,
          width: 0,
          height: 0,
          borderLeft: "6px solid transparent",
          borderRight: "6px solid transparent",
          [pos.above ? "borderTop" : "borderBottom"]: `6px solid ${darkMode ? "#2a2a2a" : "white"}`,
        }}
      />
      <div
        style={{
          background: darkMode ? "#2a2a2a" : "white",
          border: `1px solid ${darkMode ? "rgba(255,255,255,0.12)" : "rgba(0,0,0,0.1)"}`,
          borderRadius: 8,
          padding: "12px 14px",
          boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
          color: darkMode ? "#e5e5e5" : "#1a1a1a",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
          <span style={{ fontWeight: 600, fontSize: 15 }}>{term}</span>
          <span
            style={{
              fontSize: 10,
              padding: "1px 6px",
              borderRadius: 4,
              background: `${colors.badge}20`,
              color: colors.badge,
              fontWeight: 600,
              letterSpacing: "0.02em",
              textTransform: "uppercase",
              fontFamily: "system-ui, sans-serif",
            }}
          >
            {colors.label}
          </span>
        </div>
        <p style={{ fontSize: 14, lineHeight: 1.5, margin: 0, opacity: 0.85 }}>
          {annotation.description}
        </p>
      </div>
    </div>,
    document.body,
  );

  return (
    <>
      <span
        ref={spanRef}
        onTouchStart={handleTouchStart}
        onClick={handleClick}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        style={{
          borderBottom: `1px ${underlineStyle} ${underlineColor}`,
          cursor: "help",
          transition: "border-color 0.15s",
        }}
      >
        {term}
      </span>
      {card}
    </>
  );
}
