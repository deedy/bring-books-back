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
