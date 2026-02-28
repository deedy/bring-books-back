"use client";

import { useEffect } from "react";
import { trackEvent } from "@/lib/analytics";

export default function BookOpenTracker({ bookId }: { bookId: string }) {
  useEffect(() => {
    trackEvent("book_open", { book_id: bookId });
  }, [bookId]);
  return null;
}
