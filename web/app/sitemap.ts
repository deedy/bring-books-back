import type { MetadataRoute } from "next";
import { getCatalog, getChapters } from "@/lib/data";
import { chapterPath } from "@/lib/utils";

const BASE = "https://grandoldbooks.com";

export default function sitemap(): MetadataRoute.Sitemap {
  const catalog = getCatalog();
  const entries: MetadataRoute.Sitemap = [];

  // Home page
  entries.push({ url: BASE, changeFrequency: "daily", priority: 1.0 });

  // Book pages
  for (const book of catalog.books) {
    entries.push({
      url: `${BASE}/books/${book.id}`,
      lastModified: book.addedDate ?? undefined,
      changeFrequency: "weekly",
      priority: 0.8,
    });
  }

  // Author pages (filter out "Various")
  for (const author of catalog.authors) {
    if (author.name === "Various") continue;
    entries.push({
      url: `${BASE}/authors/${author.id}`,
      changeFrequency: "monthly",
      priority: 0.6,
    });
  }

  // Chapter pages for non-anthology books
  for (const book of catalog.books) {
    if (book.type === "anthology") continue;
    try {
      const chaptersData = getChapters(book.id);
      for (let i = 0; i < chaptersData.chapters.length; i++) {
        const ch = chaptersData.chapters[i];
        const path = chapterPath(ch, i + 1);
        entries.push({
          url: `${BASE}/read/${book.id}/${path}`,
          lastModified: book.addedDate ?? undefined,
          changeFrequency: "monthly",
          priority: 0.5,
        });
      }
    } catch {
      // Skip books without chapters data
    }
  }

  return entries;
}
