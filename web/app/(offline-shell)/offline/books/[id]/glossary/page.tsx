"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import GlossaryContent from "@/components/GlossaryContent";
import { buildGlossaryPreviewData } from "@/lib/bookDetails";
import { loadOfflinePayload } from "@/lib/offline";
import { buildOfflineReadUrl } from "@/lib/offlineUtils";
import type { OfflineBookPayload } from "@/lib/types";

export default function OfflineGlossaryPage() {
  const params = useParams<{ id: string }>();
  const bookId = params.id;
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

  const terms = useMemo(
    () => buildGlossaryPreviewData(payload?.bookAnnotations, payload?.chapters ?? []).glossaryTerms,
    [payload],
  );

  if (status === "loading") {
    return (
      <div className="max-w-4xl mx-auto px-6 py-12 text-white/50">Loading offline glossary…</div>
    );
  }

  if (!payload) {
    return (
      <div className="max-w-4xl mx-auto px-6 py-12">
        <p className="text-white/60">This offline book is not stored on this device.</p>
      </div>
    );
  }

  if (!payload.bookAnnotations) {
    return (
      <div className="max-w-4xl mx-auto px-6 py-12">
        <p className="text-white/60">No glossary available for this book.</p>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-6 py-12">
      <div className="mb-8">
        <Link
          href={buildOfflineReadUrl(bookId)}
          scroll={false}
          className="inline-flex items-center gap-1.5 text-sm text-white/40 hover:text-white/70 transition-colors"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="15 18 9 12 15 6" />
          </svg>
          Back to reading
        </Link>
      </div>

      <h1 className="text-3xl font-bold text-white mb-2">Glossary</h1>
      <p className="text-white/50 text-sm mb-10">
        {terms.length} entries from {payload.title}
      </p>

      <GlossaryContent terms={terms} />
    </div>
  );
}
