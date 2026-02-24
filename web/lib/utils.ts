const WPM = 230;

/** Format word count as reading time, e.g. "4h 52min" or "3 min" */
export function readingTime(wordCount: number): string {
  const totalMin = Math.max(1, Math.round(wordCount / WPM));
  if (totalMin < 60) return `${totalMin} min`;
  const h = Math.floor(totalMin / 60);
  const m = totalMin % 60;
  return m > 0 ? `${h}h ${m}min` : `${h}h`;
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
  ch: { title: string; number: number; part: number | null; partName: string | null },
  sequentialIndex: number,
): string {
  if (ch.part != null && ch.partName) {
    return `${ch.part}/${slugify(ch.partName)}/${ch.number}/${slugify(ch.title)}`;
  }
  return `${sequentialIndex}/${slugify(ch.title)}`;
}
