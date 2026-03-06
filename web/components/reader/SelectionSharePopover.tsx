"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { getSelectionQuote, buildShareUrl } from "@/lib/quote";
import { generateQuoteImage } from "@/lib/quoteImage";

interface SelectionSharePopoverProps {
  accentColor: string;
  bookTitle: string;
  authorName: string;
  coverImage: string;
  originalYear: number;
  chapterTitle: string;
  containerRef: React.RefObject<HTMLElement | null>;
}

export default function SelectionSharePopover({
  accentColor,
  bookTitle,
  authorName,
  coverImage,
  originalYear,
  chapterTitle,
  containerRef,
}: SelectionSharePopoverProps) {
  const [visible, setVisible] = useState(false);
  const [pos, setPos] = useState({ x: 0, y: 0, flip: false });
  const [copied, setCopied] = useState<"text" | "link" | null>(null);
  const quoteRef = useRef<ReturnType<typeof getSelectionQuote>>(null);
  const popoverRef = useRef<HTMLDivElement>(null);
  const hideTimer = useRef<ReturnType<typeof setTimeout>>(undefined);

  const dismiss = useCallback(() => {
    setVisible(false);
    setCopied(null);
    quoteRef.current = null;
  }, []);

  const handleSelectionChange = useCallback(() => {
    const quote = getSelectionQuote();
    if (!quote) {
      return;
    }
    quoteRef.current = quote;

    const sel = window.getSelection();
    if (!sel || !sel.rangeCount) return;
    const range = sel.getRangeAt(0);
    const rect = range.getBoundingClientRect();

    const x = rect.left + rect.width / 2;
    const flip = rect.top < 80;
    const y = flip ? rect.bottom + 8 : rect.top - 8;

    setPos({ x, y, flip });
    setVisible(true);
    setCopied(null);
  }, []);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const onMouseUp = () => {
      clearTimeout(hideTimer.current);
      hideTimer.current = setTimeout(handleSelectionChange, 10);
    };

    const onMouseDown = (e: MouseEvent) => {
      if (popoverRef.current && !popoverRef.current.contains(e.target as Node)) {
        dismiss();
      }
    };

    const onScroll = () => dismiss();

    container.addEventListener("mouseup", onMouseUp);
    container.addEventListener("touchend", onMouseUp);
    document.addEventListener("mousedown", onMouseDown);
    window.addEventListener("scroll", onScroll, { passive: true });

    return () => {
      container.removeEventListener("mouseup", onMouseUp);
      container.removeEventListener("touchend", onMouseUp);
      document.removeEventListener("mousedown", onMouseDown);
      window.removeEventListener("scroll", onScroll);
      clearTimeout(hideTimer.current);
    };
  }, [containerRef, handleSelectionChange, dismiss]);

  const handleCopyText = useCallback(async () => {
    const q = quoteRef.current;
    if (!q) return;
    const text = `\u201C${q.text}\u201D\n\u2014 ${bookTitle}`;
    await navigator.clipboard.writeText(text);
    setCopied("text");
    setTimeout(dismiss, 1200);
  }, [bookTitle, dismiss]);

  const handleShareLink = useCallback(async () => {
    const q = quoteRef.current;
    if (!q) return;
    const url = buildShareUrl(q.paragraphIndex, q.startOffset, q.endOffset);

    // Generate quote card image
    let file: File | undefined;
    try {
      const blob = await generateQuoteImage(
        q.text, bookTitle, authorName, accentColor, coverImage, originalYear, chapterTitle
      );
      if (blob) {
        file = new File([blob], "quote.png", { type: "image/png" });
      }
    } catch {
      // Continue without image
    }

    // Use native share API if available — it properly handles file + URL together
    if (navigator.share) {
      try {
        const shareData: ShareData = {
          text: `\u201C${q.text.slice(0, 200)}${q.text.length > 200 ? "\u2026" : ""}\u201D\n\u2014 ${bookTitle}`,
          url,
        };
        if (file && navigator.canShare?.({ files: [file] })) {
          shareData.files = [file];
        }
        await navigator.share(shareData);
        dismiss();
        return;
      } catch {
        // User cancelled or share failed — fall back to clipboard
      }
    }

    // Fallback: copy image to clipboard + URL as text
    if (file) {
      try {
        await navigator.clipboard.write([
          new ClipboardItem({
            "image/png": file,
            "text/plain": new Blob([url], { type: "text/plain" }),
          }),
        ]);
        setCopied("link");
        setTimeout(dismiss, 1200);
        return;
      } catch {
        // Fall through
      }
    }

    await navigator.clipboard.writeText(url);
    setCopied("link");
    setTimeout(dismiss, 1200);
  }, [bookTitle, authorName, accentColor, coverImage, originalYear, chapterTitle, dismiss]);

  if (!visible) return null;

  return (
    <div
      ref={popoverRef}
      className="fixed z-[100] pointer-events-auto animate-in fade-in zoom-in-95 duration-150"
      style={{
        left: pos.x,
        top: pos.flip ? pos.y : undefined,
        bottom: pos.flip ? undefined : `calc(100vh - ${pos.y}px)`,
        transform: "translateX(-50%)",
      }}
    >
      <div
        className="flex items-center gap-0.5 px-1.5 py-1 rounded-xl shadow-2xl"
        style={{ backgroundColor: accentColor }}
      >
        <button
          onClick={handleCopyText}
          className="px-3 py-1.5 text-[13px] font-medium text-white rounded-lg hover:bg-white/20 transition-colors whitespace-nowrap"
        >
          {copied === "text" ? "Copied!" : "Copy Text"}
        </button>
        <div className="w-px h-4 bg-white/30" />
        <button
          onClick={handleShareLink}
          className="px-3 py-1.5 text-[13px] font-medium text-white rounded-lg hover:bg-white/20 transition-colors whitespace-nowrap"
        >
          {copied === "link" ? "Copied!" : "Share Link"}
        </button>
      </div>
      {/* Arrow */}
      <div
        className="absolute left-1/2 -translate-x-1/2"
        style={{
          [pos.flip ? "top" : "bottom"]: "-5px",
          width: 0,
          height: 0,
          borderLeft: "6px solid transparent",
          borderRight: "6px solid transparent",
          ...(pos.flip
            ? { borderBottom: `6px solid ${accentColor}` }
            : { borderTop: `6px solid ${accentColor}` }),
          transform: `translateX(-50%) ${pos.flip ? "rotate(180deg)" : ""}`,
        }}
      />
    </div>
  );
}
