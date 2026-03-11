"use client";

import { useEffect } from "react";

import { getDownloadedBook } from "@/lib/offline";
import {
  buildOfflineBookUrl,
  buildOfflineGlossaryUrl,
  buildOfflineReadUrl,
} from "@/lib/offlineUtils";

interface OfflineRouteRedirectProps {
  bookId: string;
  kind: "book" | "glossary" | "read";
  target?: string;
}

export default function OfflineRouteRedirect({
  bookId,
  kind,
  target,
}: OfflineRouteRedirectProps) {
  useEffect(() => {
    if (typeof window === "undefined" || navigator.onLine) return;
    if (!getDownloadedBook(bookId)) return;

    const destination =
      kind === "book"
        ? buildOfflineBookUrl(bookId)
        : kind === "glossary"
          ? buildOfflineGlossaryUrl(bookId, window.location.search)
          : buildOfflineReadUrl(bookId, target);

    if (window.location.pathname + window.location.search === destination) return;
    window.location.replace(destination);
  }, [bookId, kind, target]);

  return null;
}
