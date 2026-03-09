/**
 * Pre-deploy validation checks.
 * Run: npx tsx scripts/validate.ts
 * Called automatically via npm test (after vitest).
 *
 * Checks:
 * 1. Every book in catalog has addedDate
 * 2. Every non-anthology book has chapters data
 * 3. Every book has a cover image
 * 4. Every non-anthology book has a hero image
 * 5. Sitemap exists and is not empty
 * 6. Every book/author in catalog has a sitemap entry
 * 7. manifest.json exists
 */

import fs from "fs";
import path from "path";

const PUBLIC = path.join(__dirname, "..", "public");
const DATA = path.join(PUBLIC, "data");
const SERVER_DATA = path.join(__dirname, "..", "server-data");

let errors: string[] = [];
let warnings: string[] = [];

function loadJson(p: string) {
  return JSON.parse(fs.readFileSync(p, "utf-8"));
}

function main() {
  console.log("Running pre-deploy validation...\n");

  // Load catalog
  const catalog = loadJson(path.join(DATA, "catalog.json"));
  const books = catalog.books;
  const authors = catalog.authors;

  // 1. Every book has addedDate
  const missingDate = books.filter((b: any) => !b.addedDate);
  if (missingDate.length > 0) {
    errors.push(`${missingDate.length} books missing addedDate: ${missingDate.slice(0, 5).map((b: any) => b.id).join(", ")}${missingDate.length > 5 ? "..." : ""}`);
  }

  // 2. Every non-anthology book has chapters data
  for (const book of books) {
    if (book.type === "anthology") continue;

    // Check server-data first, fall back to public data
    const serverPath = path.join(SERVER_DATA, "books", book.id, "chapters.json");
    const publicPath = path.join(DATA, "books", book.id, "chapters.json");
    if (!fs.existsSync(serverPath) && !fs.existsSync(publicPath)) {
      errors.push(`Book "${book.id}" missing chapters.json`);
    }
  }

  // 3. Every book has a cover image (webp)
  for (const book of books) {
    if (book.anthologyId) continue; // sub-stories use parent cover
    const coverPath = path.join(PUBLIC, book.coverImage.replace(/^\//, ""));
    if (!fs.existsSync(coverPath)) {
      warnings.push(`Book "${book.id}" cover image not found: ${book.coverImage}`);
    }
  }

  // 4. Every non-anthology top-level book has a hero image
  for (const book of books) {
    if (book.type === "anthology" || book.anthologyId) continue;
    const heroPath = path.join(PUBLIC, "data", "images", "heroes", `${book.id}.webp`);
    if (!fs.existsSync(heroPath)) {
      warnings.push(`Book "${book.id}" missing hero image`);
    }
  }

  // 5. Sitemap exists and has entries
  const sitemapPath = path.join(PUBLIC, "sitemap.xml");
  if (!fs.existsSync(sitemapPath)) {
    errors.push("sitemap.xml not found — run: npx tsx scripts/generate-sitemap.ts");
  } else {
    const sitemap = fs.readFileSync(sitemapPath, "utf-8");
    const urlCount = (sitemap.match(/<url>/g) || []).length;
    if (urlCount === 0) {
      errors.push("sitemap.xml is empty");
    }

    // 6. Spot-check: every top-level book and author has a sitemap entry
    for (const book of books) {
      if (!sitemap.includes(`/books/${book.id}</loc>`)) {
        errors.push(`Book "${book.id}" missing from sitemap`);
      }
    }
    for (const author of authors) {
      if (!sitemap.includes(`/authors/${author.id}</loc>`)) {
        errors.push(`Author "${author.id}" missing from sitemap`);
      }
    }
  }

  // 7. manifest.json exists
  if (!fs.existsSync(path.join(PUBLIC, "manifest.json"))) {
    warnings.push("manifest.json not found");
  }

  // Report
  if (warnings.length > 0) {
    console.log(`⚠  ${warnings.length} warning(s):`);
    warnings.forEach((w) => console.log(`   ${w}`));
    console.log();
  }

  if (errors.length > 0) {
    console.log(`✗  ${errors.length} error(s):`);
    errors.forEach((e) => console.log(`   ${e}`));
    console.log("\nValidation FAILED.");
    process.exit(1);
  }

  console.log(`✓  All checks passed (${books.length} books, ${authors.length} authors)`);
}

main();
