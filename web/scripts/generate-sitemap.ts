/**
 * Generate sitemap.xml from catalog data.
 * Run: npx tsx scripts/generate-sitemap.ts
 * Called automatically via npm prebuild hook.
 */

import fs from "fs";
import path from "path";

const BASE = "https://grandoldbooks.com";
const DATA_DIR = path.join(__dirname, "..", "public", "data");

function slugify(text: string): string {
  return text.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "");
}

function chapterPath(ch: { title: string; number: number; part: number | null; partName: string | null }, seqIdx: number): string {
  if (ch.part != null && ch.partName) {
    return `${ch.part}/${slugify(ch.partName)}/${ch.number}/${slugify(ch.title)}`;
  }
  return `${seqIdx}/${slugify(ch.title)}`;
}

function loadJson(filePath: string) {
  return JSON.parse(fs.readFileSync(filePath, "utf-8"));
}

function main() {
  const catalog = loadJson(path.join(DATA_DIR, "catalog.json"));
  const urls: { loc: string; priority: number }[] = [];

  // Static pages
  urls.push({ loc: "/", priority: 1.0 });
  urls.push({ loc: "/about", priority: 0.7 });
  urls.push({ loc: "/privacy", priority: 0.3 });

  // Author pages
  for (const author of catalog.authors) {
    urls.push({ loc: `/authors/${author.id}`, priority: 0.7 });
  }

  // Book pages
  for (const book of catalog.books) {
    urls.push({ loc: `/books/${book.id}`, priority: 0.8 });

    // Glossary
    const annPath = path.join(DATA_DIR, "books", book.id, "annotations.json");
    if (fs.existsSync(annPath)) {
      urls.push({ loc: `/books/${book.id}/glossary`, priority: 0.5 });
    }

    // Reader chapter URLs (skip anthologies)
    if (book.type === "anthology") continue;
    const chaptersPath = path.join(DATA_DIR, "books", book.id, "chapters.json");
    if (!fs.existsSync(chaptersPath)) continue;
    const { chapters } = loadJson(chaptersPath);
    chapters.forEach((ch: any, idx: number) => {
      urls.push({ loc: `/read/${book.id}/${chapterPath(ch, idx + 1)}`, priority: 0.6 });
    });
  }

  const today = new Date().toISOString().slice(0, 10);
  const xml = [
    '<?xml version="1.0" encoding="UTF-8"?>',
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ...urls.map(({ loc, priority }) =>
      `  <url>\n    <loc>${BASE}${loc}</loc>\n    <lastmod>${today}</lastmod>\n    <priority>${priority.toFixed(1)}</priority>\n  </url>`
    ),
    "</urlset>",
    "",
  ].join("\n");

  const outPath = path.join(__dirname, "..", "public", "sitemap.xml");
  fs.writeFileSync(outPath, xml);
  console.log(`Generated sitemap.xml with ${urls.length} URLs`);
}

main();
