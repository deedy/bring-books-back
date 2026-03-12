"use client";

import { useEffect } from "react";
import { setHeaderBack } from "@/lib/headerContext";

/**
 * Sets the header back button dynamically based on how the user arrived.
 * - From the reader (/read/...) → "Back to reading"
 * - Otherwise → book title (links to book page)
 */
export default function GlossaryHeaderBack({
  bookId,
  bookTitle,
}: {
  bookId: string;
  bookTitle: string;
}) {
  useEffect(() => {
    let label = bookTitle;
    let href = `/books/${bookId}`;

    try {
      const ref = document.referrer;
      if (ref) {
        const url = new URL(ref);
        if (url.pathname.startsWith(`/read/${bookId}`)) {
          label = "Back to reading";
          href = `/read/${bookId}`;
        }
      }
    } catch {
      // ignore invalid referrer
    }

    setHeaderBack({ label, href });
    return () => setHeaderBack(null);
  }, [bookId, bookTitle]);

  return null;
}
