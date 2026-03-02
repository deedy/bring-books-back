"use client";

interface ProgressBarProps {
  percent: number;
  accentColor: string;
}

export default function ProgressBar({ percent, accentColor }: ProgressBarProps) {
  return (
    <div
      className="fixed left-0 right-0 z-50 h-[6px] bg-transparent"
      style={{ top: "env(safe-area-inset-top, 0px)" }}
    >
      <div
        className="h-full transition-[width] duration-300 ease-out"
        style={{
          width: `${Math.min(percent, 100)}%`,
          backgroundColor: accentColor,
        }}
      />
    </div>
  );
}
