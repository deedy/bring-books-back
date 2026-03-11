"use client";

import { useParams, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

import ReaderLoader from "@/components/reader/ReaderLoader";
import { loadOfflinePayload } from "@/lib/offline";
import { resolveOfflineTargetChapterIndex } from "@/lib/offlineUtils";
import type { OfflineBookPayload } from "@/lib/types";

export default function OfflineReadPage() {
  const params = useParams<{ id: string }>();
  const searchParams = useSearchParams();
  const bookId = params.id;
  const target = searchParams.get("target");
  const [payload, setPayload] = useState<OfflineBookPayload | null>(null);
  const [status, setStatus] = useState<"loading" | "ready" | "missing">("loading");

  useEffect(() => {
    let cancelled = false;
    loadOfflinePayload(bookId).then((data) => {
      if (cancelled) return;
      setPayload(data);
      setStatus(data ? "ready" : "missing");
    });
    return () => {
      cancelled = true;
    };
  }, [bookId]);

  if (status === "loading") {
    return (
      <div className="fixed inset-0 bg-[#1a1a1a] flex items-center justify-center text-white/50">
        Loading offline reader…
      </div>
    );
  }

  if (!payload) {
    return (
      <div className="fixed inset-0 bg-[#1a1a1a] flex items-center justify-center px-6 text-center">
        <div>
          <h1 className="text-2xl font-bold text-white">Offline reader unavailable</h1>
          <p className="text-white/50 mt-3">
            This book has not been downloaded on this device.
          </p>
        </div>
      </div>
    );
  }

  const initialChapter = resolveOfflineTargetChapterIndex(payload.chapters, target) + 1;

  return (
    <ReaderLoader
      accentColor={payload.accentColor}
      annotations={payload.annotations}
      authorName={payload.authorName}
      bookId={payload.bookId}
      bookTitle={payload.title}
      chapters={payload.chapters}
      coverImage={payload.coverImage}
      initialChapter={initialChapter}
      isAuthenticated={true}
      isOriginalActive={payload.isOriginalActive}
      offlineMode={true}
      originalScript={payload.originalScript}
      originalYear={payload.originalYear}
      resumeTarget={null}
      totalChapters={payload.totalChapters}
    />
  );
}
