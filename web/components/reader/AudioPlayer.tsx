"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { createPortal } from "react-dom";
import type { AudioManifest } from "@/lib/types";
import HeadphoneIcon from "@/components/icons/HeadphoneIcon";

interface AudioPlayerProps {
  manifest: AudioManifest;
  chapterId: string;
  bookId: string;
  accentColor: string;
  darkMode: boolean;
  onParagraphRangeChange: (range: [number, number] | null) => void;
  onRequestNextChapter?: () => void;
  synced: boolean;
  onGoToAudio: () => void;
  onPlayFromHere: () => void;
  initialSeekTime?: number;
  onSeekRef?: React.MutableRefObject<((time: number) => void) | null>;
  chapterProgress?: number;
  onToggleBookmark?: () => void;
  programmaticScrollRef?: React.MutableRefObject<boolean>;
  autoplay?: boolean;
  /** Paragraph index where preview gate starts — audio pauses here if set */
  gateParagraphIndex?: number;
  /** URL to sign-in page (shown when gated) */
  signInUrl?: string;
}

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

const SPEEDS = [0.75, 1, 1.25, 1.5, 1.75, 2];

export default function AudioPlayer({
  manifest,
  chapterId,
  bookId,
  accentColor,
  darkMode,
  onParagraphRangeChange,
  onRequestNextChapter,
  synced,
  onGoToAudio,
  onPlayFromHere,
  initialSeekTime = 0,
  onSeekRef,
  chapterProgress = 0,
  onToggleBookmark,
  programmaticScrollRef,
  autoplay,
  gateParagraphIndex,
  signInUrl,
}: AudioPlayerProps) {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isLoaded, setIsLoaded] = useState(false);
  const [isBuffering, setIsBuffering] = useState(false);
  const [hasError, setHasError] = useState(false);
  const retryCountRef = useRef(0);
  const [currentTime, setCurrentTime] = useState(0);
  const didApplyInitialSeek = useRef(false);
  const [duration, setDuration] = useState(0);
  const [speedIndex, setSpeedIndex] = useState(1); // default 1x
  const prevChapterIdRef = useRef(chapterId);
  const wasPlayingRef = useRef(false);
  const [mounted, setMounted] = useState(false);
  const [bookmarkFlash, setBookmarkFlash] = useState(false);
  const bookmarkFlashTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [isGated, setIsGated] = useState(false);
  const didGateRef = useRef(false);

  useEffect(() => setMounted(true), []);

  const chapterAudio = manifest.chapters[chapterId];
  const audioUrl = `/data/audio/${bookId}/${chapterId}.mp3?v=${chapterAudio?.durationSec ?? 0}`;

  // Autoplay on mount when requested via URL param
  const didAutoplay = useRef(false);
  useEffect(() => {
    if (!autoplay || didAutoplay.current) return;
    didAutoplay.current = true;
    const audio = audioRef.current;
    if (!audio) return;
    audio.src = audioUrl;
    audio.load();
    setIsLoaded(true);
    audio.playbackRate = SPEEDS[speedIndex];
    audio.play().catch(() => setIsPlaying(false));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autoplay, audioUrl]);

  // Apply initial seek time when it becomes available (after Zustand hydration)
  useEffect(() => {
    if (didApplyInitialSeek.current || initialSeekTime <= 0) return;
    didApplyInitialSeek.current = true;
    setCurrentTime(initialSeekTime);
    if (audioRef.current && isLoaded) {
      audioRef.current.currentTime = initialSeekTime;
    }
  }, [initialSeekTime, isLoaded]);

  // Expose seek function to parent via ref
  useEffect(() => {
    if (onSeekRef) {
      onSeekRef.current = (time: number) => {
        setCurrentTime(time);
        if (audioRef.current) {
          if (!isLoaded) {
            audioRef.current.src = audioUrl;
            audioRef.current.load();
            setIsLoaded(true);
            audioRef.current.playbackRate = SPEEDS[speedIndex];
          }
          audioRef.current.currentTime = time;
          audioRef.current.play().catch(() => setIsPlaying(false));
        }
      };
    }
    return () => { if (onSeekRef) onSeekRef.current = null; };
  }, [onSeekRef, audioUrl, isLoaded, speedIndex]);

  // Binary search to find the active segment for current time
  const findActiveSegment = useCallback(
    (time: number) => {
      if (!chapterAudio?.segments) return null;
      const segments = chapterAudio.segments;
      let lo = 0;
      let hi = segments.length - 1;
      while (lo <= hi) {
        const mid = Math.floor((lo + hi) / 2);
        const seg = segments[mid];
        if (time < seg.startSec) {
          hi = mid - 1;
        } else if (time >= seg.endSec) {
          lo = mid + 1;
        } else {
          return seg;
        }
      }
      // If no exact match, find the last segment that starts at or before this time
      // (handles zero-duration segments from alignment gaps)
      for (let i = segments.length - 1; i >= 0; i--) {
        if (segments[i].startSec <= time && segments[i].endSec > segments[i].startSec) {
          return segments[i];
        }
      }
      return null;
    },
    [chapterAudio],
  );

  // Handle chapter change
  useEffect(() => {
    if (prevChapterIdRef.current !== chapterId) {
      const wasPlaying = wasPlayingRef.current;
      prevChapterIdRef.current = chapterId;
      setCurrentTime(0);
      setDuration(0);
      setIsLoaded(false);
      setIsBuffering(false);
      setHasError(false);
      setIsGated(false);
      retryCountRef.current = 0;
      didGateRef.current = false;
      onParagraphRangeChange(null);

      if (wasPlaying && audioRef.current) {
        audioRef.current.src = audioUrl;
        audioRef.current.load();
        setIsLoaded(true);
        audioRef.current.play().catch(() => setIsPlaying(false));
      } else {
        setIsPlaying(false);
      }
    }
  }, [chapterId, bookId, onParagraphRangeChange]);

  // Track playing state for chapter transitions
  useEffect(() => {
    wasPlayingRef.current = isPlaying;
  }, [isPlaying]);

  // Time update handler
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    function handleTimeUpdate() {
      const t = audio!.currentTime;
      setCurrentTime(t);
      // Keep play state in sync with actual audio element
      setIsPlaying(!audio!.paused);
      const seg = findActiveSegment(t);
      if (seg) {
        onParagraphRangeChange([seg.paragraphStart, seg.paragraphEnd]);
        // Pause at preview gate
        if (
          gateParagraphIndex != null &&
          seg.paragraphStart >= gateParagraphIndex &&
          !didGateRef.current
        ) {
          didGateRef.current = true;
          audio!.pause();
          setIsGated(true);
        }
      } else {
        onParagraphRangeChange(null);
      }
    }

    function handleLoadedMetadata() {
      setDuration(audio!.duration);
    }

    function handleEnded() {
      setIsPlaying(false);
      onParagraphRangeChange(null);
      onRequestNextChapter?.();
    }

    function handlePlay() { setIsPlaying(true); }
    function handlePause() { setIsPlaying(false); }

    function handleWaiting() { setIsBuffering(true); }
    function handleStalled() { setIsBuffering(true); }
    function handleCanPlay() { setIsBuffering(false); }
    function handlePlaying() {
      setIsBuffering(false);
      setHasError(false);
      retryCountRef.current = 0;
    }
    function handleError() {
      if (retryCountRef.current >= 3) {
        setHasError(true);
        setIsBuffering(false);
        return;
      }
      retryCountRef.current += 1;
      setIsBuffering(true);
      const savedTime = audio!.currentTime;
      const delay = 1000 * 2 ** (retryCountRef.current - 1);
      setTimeout(() => {
        if (!audio) return;
        audio.src = audioUrl;
        audio.load();
        audio.currentTime = savedTime;
        audio.play().catch(() => {});
      }, delay);
    }

    audio.addEventListener("timeupdate", handleTimeUpdate);
    audio.addEventListener("loadedmetadata", handleLoadedMetadata);
    audio.addEventListener("ended", handleEnded);
    audio.addEventListener("play", handlePlay);
    audio.addEventListener("pause", handlePause);
    audio.addEventListener("waiting", handleWaiting);
    audio.addEventListener("stalled", handleStalled);
    audio.addEventListener("canplay", handleCanPlay);
    audio.addEventListener("playing", handlePlaying);
    audio.addEventListener("error", handleError);

    return () => {
      audio.removeEventListener("timeupdate", handleTimeUpdate);
      audio.removeEventListener("loadedmetadata", handleLoadedMetadata);
      audio.removeEventListener("ended", handleEnded);
      audio.removeEventListener("play", handlePlay);
      audio.removeEventListener("pause", handlePause);
      audio.removeEventListener("waiting", handleWaiting);
      audio.removeEventListener("stalled", handleStalled);
      audio.removeEventListener("canplay", handleCanPlay);
      audio.removeEventListener("playing", handlePlaying);
      audio.removeEventListener("error", handleError);
    };
  }, [findActiveSegment, onParagraphRangeChange, onRequestNextChapter, audioUrl]);

  // Media Session API for lock screen controls
  useEffect(() => {
    if (!("mediaSession" in navigator)) return;
    navigator.mediaSession.metadata = new MediaMetadata({
      title: chapterId,
      artist: bookId,
    });
    navigator.mediaSession.setActionHandler("play", () => audioRef.current?.play());
    navigator.mediaSession.setActionHandler("pause", () => audioRef.current?.pause());
    navigator.mediaSession.setActionHandler("seekto", (details) => {
      if (audioRef.current && details.seekTime != null) {
        audioRef.current.currentTime = details.seekTime;
      }
    });
    return () => {
      navigator.mediaSession.setActionHandler("play", null);
      navigator.mediaSession.setActionHandler("pause", null);
      navigator.mediaSession.setActionHandler("seekto", null);
    };
  }, [chapterId, bookId]);

  // Speed change
  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.playbackRate = SPEEDS[speedIndex];
    }
  }, [speedIndex]);

  const handlePlayPause = () => {
    const audio = audioRef.current;
    if (!audio) return;

    // If gated, redirect to sign-in
    if (isGated && signInUrl) {
      window.location.href = signInUrl;
      return;
    }

    // If in error state, tap triggers manual retry
    if (hasError) {
      setHasError(false);
      setIsBuffering(true);
      retryCountRef.current = 0;
      const savedTime = audio.currentTime;
      audio.src = audioUrl;
      audio.load();
      audio.currentTime = savedTime;
      audio.play().catch(() => setIsPlaying(false));
      return;
    }

    if (!isLoaded) {
      audio.src = audioUrl;
      audio.load();
      setIsLoaded(true);
      audio.playbackRate = SPEEDS[speedIndex];
      if (initialSeekTime > 0) {
        audio.currentTime = initialSeekTime;
        setCurrentTime(initialSeekTime);
      }
      audio.play().catch(() => setIsPlaying(false));
    } else if (isPlaying) {
      audio.pause();
    } else {
      audio.play().catch(() => setIsPlaying(false));
    }
  };

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const time = parseFloat(e.target.value);
    setCurrentTime(time);
    if (audioRef.current) {
      audioRef.current.currentTime = time;
    }
  };

  const handleSeekClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!displayDuration) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const pct = Math.max(0, Math.min(1, x / rect.width));
    const time = pct * displayDuration;
    setCurrentTime(time);
    if (audioRef.current) {
      audioRef.current.currentTime = time;
    }
  };

  const scrollToParagraph = (paraIndex: number) => {
    const el = document.querySelector(`[data-paragraph-index="${paraIndex}"]`);
    if (el) {
      if (programmaticScrollRef) programmaticScrollRef.current = true;
      const y = el.getBoundingClientRect().top + window.scrollY - 300;
      window.scrollTo({ top: y, behavior: "smooth" });
      setTimeout(() => { if (programmaticScrollRef) programmaticScrollRef.current = false; }, 800);
    }
  };

  const handleSkipNext = () => {
    const audio = audioRef.current;
    if (!audio || !chapterAudio?.segments) return;
    const segments = chapterAudio.segments;
    for (const seg of segments) {
      // Skip to next segment with a genuinely different time position
      // (skip over zero-duration segments that share the same startSec)
      if (seg.startSec > currentTime + 0.5 && seg.endSec > seg.startSec) {
        audio.currentTime = seg.startSec;
        setCurrentTime(seg.startSec);
        onParagraphRangeChange([seg.paragraphStart, seg.paragraphEnd]);
        scrollToParagraph(seg.paragraphStart);
        return;
      }
    }
    if (segments.length > 0) {
      const last = segments[segments.length - 1];
      audio.currentTime = last.endSec;
    }
  };

  const handleSkipPrev = () => {
    const audio = audioRef.current;
    if (!audio || !chapterAudio?.segments) return;
    const segments = chapterAudio.segments;
    for (let i = segments.length - 1; i >= 0; i--) {
      const seg = segments[i];
      // Skip over zero-duration segments
      if (seg.startSec < currentTime - 1 && seg.endSec > seg.startSec) {
        audio.currentTime = seg.startSec;
        setCurrentTime(seg.startSec);
        onParagraphRangeChange([seg.paragraphStart, seg.paragraphEnd]);
        scrollToParagraph(seg.paragraphStart);
        return;
      }
    }
    audio.currentTime = 0;
    setCurrentTime(0);
    if (segments.length > 0) {
      onParagraphRangeChange([segments[0].paragraphStart, segments[0].paragraphEnd]);
      scrollToParagraph(segments[0].paragraphStart);
    }
  };

  const handleSpeedCycle = () => {
    setSpeedIndex((prev) => (prev + 1) % SPEEDS.length);
  };

  const displayDuration = duration || chapterAudio?.durationSec || 0;
  const progress = displayDuration ? (currentTime / displayDuration) * 100 : 0;

  const bg = darkMode ? "rgba(20,20,20,0.95)" : "rgba(255,255,255,0.95)";
  const textMuted = darkMode ? "rgba(255,255,255,0.5)" : "rgba(0,0,0,0.5)";
  const textMain = darkMode ? "rgba(255,255,255,0.8)" : "rgba(0,0,0,0.8)";
  const trackBg = darkMode ? "rgba(255,255,255,0.12)" : "rgba(0,0,0,0.12)";
  const hoverBg = darkMode ? "rgba(255,255,255,0.1)" : "rgba(0,0,0,0.08)";
  const progressBarColor = darkMode ? "rgba(255,255,255,0.25)" : "rgba(0,0,0,0.2)";

  const bar = (
    <div
      style={{
        position: "fixed",
        bottom: 0,
        left: 0,
        right: 0,
        zIndex: 2147483646,
        overflow: "hidden",
      }}
    >
      {/* Chapter reading progress bar — above the player chrome */}
      <div style={{ height: 6, background: "transparent" }}>
        <div
          style={{
            height: "100%",
            width: `${Math.min(chapterProgress, 100)}%`,
            background: progressBarColor,
            transition: "width 0.2s ease-out",
          }}
        />
      </div>
      <div
        style={{
          paddingBottom: "env(safe-area-inset-bottom)",
          background: bg,
          backdropFilter: "blur(20px)",
          WebkitBackdropFilter: "blur(20px)",
          boxShadow: "0 -2px 20px rgba(0,0,0,0.15)",
        }}
      >
      {/* Seek track with paragraph markers */}
      <div
        onClick={handleSeekClick}
        onMouseDown={(e) => {
          // Enable drag-to-seek
          const track = e.currentTarget;
          const handleMove = (ev: MouseEvent) => {
            if (!displayDuration) return;
            const rect = track.getBoundingClientRect();
            const x = ev.clientX - rect.left;
            const pct = Math.max(0, Math.min(1, x / rect.width));
            const time = pct * displayDuration;
            setCurrentTime(time);
            if (audioRef.current) audioRef.current.currentTime = time;
          };
          const handleUp = () => {
            document.removeEventListener("mousemove", handleMove);
            document.removeEventListener("mouseup", handleUp);
          };
          document.addEventListener("mousemove", handleMove);
          document.addEventListener("mouseup", handleUp);
        }}
        className="audio-seek-track"
        style={{ background: "transparent", position: "relative", cursor: "pointer", paddingTop: 0, paddingBottom: 4 }}
      >
        {/* Track background */}
        <div className="audio-seek-rail" style={{ background: trackBg, borderRadius: 2, position: "relative" }}>
          {/* Progress fill */}
          <div
            style={{
              height: "100%",
              width: `${progress}%`,
              background: accentColor,
              borderRadius: 2,
              transition: "width 0.25s linear",
              position: "absolute",
              top: 0,
              left: 0,
            }}
          />
          {/* Scrubber thumb */}
          <div
            className="audio-seek-thumb"
            style={{
              position: "absolute",
              left: `${progress}%`,
              top: "50%",
              transform: "translate(-50%, -50%)",
              width: 12,
              height: 12,
              borderRadius: "50%",
              background: accentColor,
              boxShadow: "0 1px 4px rgba(0,0,0,0.3)",
              transition: "width 0.15s, height 0.15s, opacity 0.15s, left 0.25s linear",
              pointerEvents: "none",
            }}
          />
          {/* Paragraph segment markers */}
          {displayDuration > 0 && chapterAudio?.segments?.map((seg, i) => {
            if (i === 0) return null; // skip first marker (start of track)
            const pct = (seg.startSec / displayDuration) * 100;
            return (
              <div
                key={i}
                style={{
                  position: "absolute",
                  left: `${pct}%`,
                  top: -1,
                  width: 2,
                  height: "calc(100% + 2px)",
                  background: darkMode ? "rgba(255,255,255,0.3)" : "rgba(0,0,0,0.25)",
                  borderRadius: 1,
                  transform: "translateX(-1px)",
                }}
              />
            );
          })}
        </div>
      </div>

      <div
        style={{
          maxWidth: 896,
          margin: "0 auto",
          padding: "0 16px",
          height: 52,
          display: "flex",
          alignItems: "center",
          gap: 8,
        }}
      >
        {/* Skip previous */}
        <button
          onClick={handleSkipPrev}
          style={{
            flexShrink: 0, width: 28, height: 28, display: "flex", alignItems: "center",
            justifyContent: "center", borderRadius: 6, border: "none",
            background: "transparent", color: textMain, cursor: "pointer",
          }}
          onMouseEnter={(e) => (e.currentTarget.style.background = hoverBg)}
          onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
          aria-label="Previous paragraph"
          title="Previous paragraph"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
            <rect x="4" y="5" width="3" height="14" rx="1" />
            <polygon points="20,5 10,12 20,19" />
          </svg>
        </button>

        {/* Play/Pause */}
        <button
          onClick={handlePlayPause}
          style={{
            flexShrink: 0, width: 36, height: 36, display: "flex", alignItems: "center",
            justifyContent: "center", borderRadius: "50%", border: "none",
            background: hasError ? "rgba(220,60,60,0.15)" : accentColor,
            color: hasError ? "rgba(220,60,60,0.9)" : "#fff", cursor: "pointer",
            transition: "opacity 0.15s, background 0.15s",
          }}
          onMouseEnter={(e) => (e.currentTarget.style.opacity = "0.85")}
          onMouseLeave={(e) => (e.currentTarget.style.opacity = "1")}
          aria-label={hasError ? "Retry" : isPlaying ? "Pause" : "Play"}
          title={hasError ? "Tap to retry" : isPlaying ? "Pause" : "Play"}
        >
          {isBuffering && !hasError ? (
            <div className="audio-spinner" style={{ width: 16, height: 16, border: "2px solid rgba(255,255,255,0.3)", borderTopColor: "#fff", borderRadius: "50%" }} />
          ) : isPlaying ? (
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <rect x="6" y="4" width="4" height="16" rx="1" />
              <rect x="14" y="4" width="4" height="16" rx="1" />
            </svg>
          ) : (
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <polygon points="7,4 21,12 7,20" />
            </svg>
          )}
        </button>

        {/* Skip next */}
        <button
          onClick={handleSkipNext}
          style={{
            flexShrink: 0, width: 28, height: 28, display: "flex", alignItems: "center",
            justifyContent: "center", borderRadius: 6, border: "none",
            background: "transparent", color: textMain, cursor: "pointer",
          }}
          onMouseEnter={(e) => (e.currentTarget.style.background = hoverBg)}
          onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
          aria-label="Next paragraph"
          title="Next paragraph"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
            <polygon points="4,5 14,12 4,19" />
            <rect x="17" y="5" width="3" height="14" rx="1" />
          </svg>
        </button>

        {/* Spacer */}
        <div style={{ flex: 1 }} />

        {/* Time + status */}
        <span style={{ fontSize: 11, fontVariantNumeric: "tabular-nums", color: textMuted }}>
          {formatTime(currentTime)} / {formatTime(displayDuration)}
          {isBuffering && !hasError && !isGated && <span style={{ marginLeft: 6, color: textMuted }}>Buffering...</span>}
          {hasError && !isGated && <span style={{ marginLeft: 6, color: "rgba(220,60,60,0.8)" }}>Tap play to retry</span>}
          {isGated && signInUrl && (
            <a
              href={signInUrl}
              style={{
                marginLeft: 8, fontSize: 11, fontWeight: 600,
                color: "#22c55e", textDecoration: "none",
              }}
            >
              Sign in to keep listening
            </a>
          )}
        </span>

        {/* Bookmark */}
        {onToggleBookmark && (
          <button
            onClick={() => {
              onToggleBookmark();
              if (bookmarkFlashTimer.current) clearTimeout(bookmarkFlashTimer.current);
              setBookmarkFlash(true);
              bookmarkFlashTimer.current = setTimeout(() => setBookmarkFlash(false), 400);
            }}
            style={{
              flexShrink: 0, width: 28, height: 28, display: "flex", alignItems: "center",
              justifyContent: "center", borderRadius: 6, border: "none",
              background: "transparent", color: textMain, cursor: "pointer",
            }}
            onMouseEnter={(e) => (e.currentTarget.style.background = hoverBg)}
            onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
            aria-label="Set bookmark"
            title="Bookmark current position"
          >
            <svg width="14" height="14" viewBox="0 0 24 24"
              fill={bookmarkFlash ? "currentColor" : "none"}
              stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"
              style={{ transition: "fill 0.15s ease" }}
            >
              <path d="M19 21l-7-5-7 5V5a2 2 0 012-2h10a2 2 0 012 2z" />
            </svg>
          </button>
        )}

        {/* Sync controls */}
        {synced ? (
          /* Synced state — just show a highlighted track icon */
          <div
            style={{
              flexShrink: 0, width: 28, height: 28, display: "flex", alignItems: "center",
              justifyContent: "center", borderRadius: 6,
              background: `${accentColor}20`, color: accentColor,
            }}
            title="Text and audio in sync"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" />
              <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" />
            </svg>
          </div>
        ) : (
          /* Unsynced — show two re-sync buttons */
          <div style={{ display: "flex", gap: 2, flexShrink: 0 }}>
            {/* Go to audio position */}
            <button
              onClick={onGoToAudio}
              style={{
                width: 28, height: 28, display: "flex", alignItems: "center",
                justifyContent: "center", borderRadius: 6, border: "none",
                background: "transparent", color: accentColor, cursor: "pointer",
              }}
              onMouseEnter={(e) => (e.currentTarget.style.background = hoverBg)}
              onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
              aria-label="Go to audio position"
              title="Scroll to where audio is playing"
            >
              <HeadphoneIcon size={14} />
            </button>
            {/* Play from current text position */}
            <button
              onClick={onPlayFromHere}
              style={{
                width: 28, height: 28, display: "flex", alignItems: "center",
                justifyContent: "center", borderRadius: 6, border: "none",
                background: "transparent", color: progressBarColor, cursor: "pointer",
              }}
              onMouseEnter={(e) => (e.currentTarget.style.background = hoverBg)}
              onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
              aria-label="Play from current text position"
              title="Play audio from where you're reading"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <line x1="4" y1="6" x2="20" y2="6" />
                <line x1="4" y1="10" x2="20" y2="10" />
                <line x1="4" y1="14" x2="14" y2="14" />
                <line x1="4" y1="18" x2="16" y2="18" />
              </svg>
            </button>
          </div>
        )}

        {/* Speed */}
        <button
          onClick={handleSpeedCycle}
          style={{
            flexShrink: 0, padding: "2px 6px", borderRadius: 4, border: "none",
            background: "transparent", color: textMuted, fontSize: 11, fontWeight: 600,
            fontVariantNumeric: "tabular-nums", cursor: "pointer", minWidth: 32,
            textAlign: "center",
          }}
          onMouseEnter={(e) => (e.currentTarget.style.background = hoverBg)}
          onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
          aria-label={`Playback speed: ${SPEEDS[speedIndex]}x`}
          title={`Playback speed: ${SPEEDS[speedIndex]}x`}
        >
          {SPEEDS[speedIndex]}x
        </button>
      </div>

      <audio ref={audioRef} preload="none" />
      <style>{`
        .audio-seek-track { height: 4px; }
        .audio-seek-rail { height: 4px; }
        .audio-seek-thumb { opacity: 0; }
        .audio-seek-track:hover .audio-seek-rail { height: 6px; }
        .audio-seek-track:hover .audio-seek-thumb { opacity: 1; }
        @media (min-width: 640px) {
          .audio-seek-track { height: 4px; }
          .audio-seek-rail { height: 4px; }
          .audio-seek-thumb { opacity: 0; }
          .audio-seek-track:hover .audio-seek-rail { height: 6px; }
          .audio-seek-track:hover .audio-seek-thumb { opacity: 1; width: 14px !important; height: 14px !important; }
        }
        @keyframes audio-spin { to { transform: rotate(360deg); } }
        .audio-spinner { animation: audio-spin 0.8s linear infinite; }
      `}</style>
      </div>
    </div>
  );

  if (!mounted) return <audio ref={audioRef} preload="none" />;

  return createPortal(bar, document.body);
}
