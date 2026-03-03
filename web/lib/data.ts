import fs from "fs";
import path from "path";
import { Catalog, ChaptersData, BookMeta, AnnotationsData, AnthologyData, OriginalChaptersData } from "./types";

export { slugify } from "./utils";


const dataDir = path.join(process.cwd(), "public", "data");

export function getCatalog(): Catalog {
  const data = fs.readFileSync(path.join(dataDir, "catalog.json"), "utf-8");
  return JSON.parse(data);
}

export function getBookMeta(bookId: string): BookMeta {
  const data = fs.readFileSync(
    path.join(dataDir, "books", bookId, "meta.json"),
    "utf-8"
  );
  return JSON.parse(data);
}

export function getChapters(bookId: string): ChaptersData {
  const data = fs.readFileSync(
    path.join(dataDir, "books", bookId, "chapters.json"),
    "utf-8"
  );
  return JSON.parse(data);
}

export function getAnnotations(bookId: string): AnnotationsData | null {
  const filePath = path.join(dataDir, "books", bookId, "annotations.json");
  if (!fs.existsSync(filePath)) return null;
  const data = fs.readFileSync(filePath, "utf-8");
  return JSON.parse(data);
}

export function getAnthologyData(bookId: string): AnthologyData | null {
  const filePath = path.join(dataDir, "books", bookId, "anthology.json");
  if (!fs.existsSync(filePath)) return null;
  const data = fs.readFileSync(filePath, "utf-8");
  return JSON.parse(data);
}

export function getOriginalChapters(bookId: string): OriginalChaptersData | null {
  const filePath = path.join(dataDir, "books", bookId, "chapters_original.json");
  if (!fs.existsSync(filePath)) return null;
  const data = fs.readFileSync(filePath, "utf-8");
  return JSON.parse(data);
}
