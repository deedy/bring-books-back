import "server-only";

import fs from "fs";
import path from "path";
import { Catalog, ChaptersData, BookMeta, AnnotationsData, AnthologyData, OriginalChaptersData } from "./types";

export { slugify } from "./utils";


const publicDataDir = path.join(process.cwd(), "public", "data");
const serverDataDir = path.join(process.cwd(), "server-data");

export function getCatalog(): Catalog {
  const data = fs.readFileSync(path.join(publicDataDir, "catalog.json"), "utf-8");
  return JSON.parse(data);
}

export function getBookMeta(bookId: string): BookMeta {
  const data = fs.readFileSync(
    path.join(publicDataDir, "books", bookId, "meta.json"),
    "utf-8"
  );
  return JSON.parse(data);
}

export function getChapters(bookId: string): ChaptersData {
  const data = fs.readFileSync(
    path.join(serverDataDir, "books", bookId, "chapters.json"),
    "utf-8"
  );
  return JSON.parse(data);
}

export function getAnnotations(bookId: string): AnnotationsData | null {
  const filePath = path.join(publicDataDir, "books", bookId, "annotations.json");
  if (!fs.existsSync(filePath)) return null;
  const data = fs.readFileSync(filePath, "utf-8");
  return JSON.parse(data);
}

export function getAnthologyData(bookId: string): AnthologyData | null {
  const filePath = path.join(publicDataDir, "books", bookId, "anthology.json");
  if (!fs.existsSync(filePath)) return null;
  const data = fs.readFileSync(filePath, "utf-8");
  return JSON.parse(data);
}

export function getOriginalChapters(bookId: string): OriginalChaptersData | null {
  const filePath = path.join(serverDataDir, "books", bookId, "chapters_original.json");
  if (!fs.existsSync(filePath)) return null;
  const data = fs.readFileSync(filePath, "utf-8");
  return JSON.parse(data);
}

export function getModernChapters(bookId: string): OriginalChaptersData | null {
  const filePath = path.join(serverDataDir, "books", bookId, "chapters_modern.json");
  if (!fs.existsSync(filePath)) return null;
  const data = fs.readFileSync(filePath, "utf-8");
  return JSON.parse(data);
}

export function getKidChapters(bookId: string): OriginalChaptersData | null {
  const filePath = path.join(serverDataDir, "books", bookId, "chapters_kid.json");
  if (!fs.existsSync(filePath)) return null;
  const data = fs.readFileSync(filePath, "utf-8");
  return JSON.parse(data);
}
