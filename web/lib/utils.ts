import type { Book } from "@/lib/types";

const WPM = 230;
/** How many days a book is considered "new" after its addedDate. */
const NEW_BOOK_DAYS = 14;

/** Return IDs of books added within the last NEW_BOOK_DAYS days. */
export function getNewBookIds(books: Book[]): Set<string> {
  const cutoff = new Date();
  cutoff.setDate(cutoff.getDate() - NEW_BOOK_DAYS);
  const cutoffStr = cutoff.toISOString().slice(0, 10); // YYYY-MM-DD
  return new Set(
    books.filter((b) => b.addedDate && b.addedDate >= cutoffStr).map((b) => b.id)
  );
}

/** Format word count as reading time, e.g. "4½h" or "3 min" */
export function readingTime(wordCount: number): string {
  const totalMin = Math.max(1, Math.round(wordCount / WPM));
  if (totalMin < 60) return `${totalMin} min`;
  const h = totalMin / 60;
  // Over 10h: round to nearest hour
  if (h >= 10) return `${Math.round(h)}h`;
  // Over 2h: round to nearest half hour
  if (h >= 2) {
    const rounded = Math.round(h * 2) / 2;
    return rounded % 1 === 0 ? `${rounded}h` : `${Math.floor(rounded)}½h`;
  }
  // Under 2h: show hours and minutes
  const wholeH = Math.floor(h);
  const m = totalMin % 60;
  return m > 0 ? `${wholeH}h ${m}min` : `${wholeH}h`;
}

/** Format word count as exact reading time, e.g. "2 hrs 35 min" or "52 min" — no rounding. */
export function readingTimeExact(wordCount: number): string {
  const totalMin = Math.max(1, Math.round(wordCount / WPM));
  if (totalMin < 60) return `${totalMin} min`;
  const h = Math.floor(totalMin / 60);
  const m = totalMin % 60;
  return m > 0 ? `${h} hrs ${m} min` : `${h} hrs`;
}

/** Format word count as exact reading time in HH:MM, e.g. "2:35" or "0:12" */
export function readingTimeClock(wordCount: number): string {
  const totalMin = Math.max(1, Math.round(wordCount / WPM));
  const h = Math.floor(totalMin / 60);
  const m = totalMin % 60;
  return `${h}:${String(m).padStart(2, "0")}`;
}

/** Estimate page count (standard ~250 words per page). */
export function pageCount(wordCount: number): number {
  return Math.round(wordCount / 250);
}

/** Format year or year range, e.g. "1965" or "1965–1992" */
function formatYear(year: number): string {
  if (year < 0) return `${Math.abs(year)} BC`;
  return String(year);
}

export function displayYear(originalYear: number, yearEnd?: number): string {
  if (yearEnd && yearEnd !== originalYear) return `${formatYear(originalYear)}\u2013${formatYear(yearEnd)}`;
  return formatYear(originalYear);
}

export function slugify(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/(^-|-$)/g, "");
}

/**
 * URL path segments for a chapter (relative to /read/{bookId}/).
 * - Part books:    {partNum}/{partSlug}/{chapterNum}/{chapterSlug}
 * - Non-part books: {sequentialIndex}/{chapterSlug}
 */
export function chapterPath(
  ch: { title: string; slugTitle?: string; number: number; part: number | null; partName: string | null },
  sequentialIndex: number,
): string {
  const titleForSlug = ch.slugTitle ?? ch.title;
  if (ch.part != null && ch.partName) {
    return `${ch.part}/${slugify(ch.partName)}/${ch.number}/${slugify(titleForSlug)}`;
  }
  return `${sequentialIndex}/${slugify(titleForSlug)}`;
}
