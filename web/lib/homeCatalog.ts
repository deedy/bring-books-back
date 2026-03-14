import type { Book } from "@/lib/types";

export type HomeSortField = "default" | "recent" | "year" | "length" | "popularity";
export type HomeSortDir = "asc" | "desc";

export interface HomeSection {
  id:
    | "epics-worlds"
    | "russian-classics"
    | "love-memory"
    | "society-family"
    | "mystery-conscience"
    | "ideas-journeys";
  title: string;
  description?: string;
  books: Book[];
}

export type HomeBrowseModel =
  | { mode: "sectioned"; sections: HomeSection[]; flatBooks: Book[] }
  | { mode: "flat"; books: Book[] };

interface BuildHomeBrowseModelOptions {
  books: Book[];
  langFilter: string;
  sortField: HomeSortField;
  sortDir: HomeSortDir;
}

const MIN_SECTION_BOOKS = 2;

const SECTION_META: Array<Pick<HomeSection, "id" | "title" | "description"> & { bookIds: string[] }> = [
  {
    id: "epics-worlds",
    title: "Epics, Myths & Sacred Worlds",
    description: "Foundational epics, sacred texts, fables, and world-building classics.",
    bookIds: [
      "mahabharata",
      "ramayana",
      "bhagavad-gita",
      "bible",
      "quran",
      "panchatantra",
      "vedas",
      "ponniyin-selvan",
      "chandrakanta",
    ],
  },
  {
    id: "russian-classics",
    title: "Russian Classics",
    description: "Towering novels of love, war, guilt, and redemption from Russia's golden age.",
    bookIds: [
      "war-and-peace",
      "anna-karenina",
      "crime-and-punishment",
      "brothers-karamazov",
    ],
  },
  {
    id: "love-memory",
    title: "Love, Memory & Longing",
    description: "Romance, heartbreak, recollection, and intimate emotional lives.",
    bookIds: [
      "devdas",
      "mrinalini",
      "ghare-baire",
      "maitreyi",
      "na-hanyate",
    ],
  },
  {
    id: "society-family",
    title: "Society, Family & the Village",
    description: "Books about households, communities, custom, and social change.",
    bookIds: [
      "pather-panchali",
      "godan",
      "samskara",
      "matira-manisha",
      "shyamchi-aai",
      "kayar",
      "alaler-gharer-dulal",
      "sarasvatichandra",
    ],
  },
  {
    id: "mystery-conscience",
    title: "Mystery, Crime & Conscience",
    description: "Detective stories, criminal minds, and novels of moral pressure.",
    bookIds: [
      "feluda",
      "byomkesh",
    ],
  },
  {
    id: "ideas-journeys",
    title: "Ideas, Journeys & the Nation",
    description: "Intellectual quests, spiritual searching, travel, and public thought.",
    bookIds: [
      "discovery-of-india",
      "autobiography-of-a-yogi",
      "baeesween-sadi",
      "barrister-parvateesam",
    ],
  },
];

function compareTitle(left: Book, right: Book): number {
  return left.title.localeCompare(right.title);
}

function compareAddedDesc(left: Book, right: Book): number {
  return (right.addedDate ?? "").localeCompare(left.addedDate ?? "");
}

function compareWordCountAsc(left: Book, right: Book): number {
  return left.wordCount - right.wordCount;
}

function compareYear(left: Book, right: Book): number {
  return left.originalYear - right.originalYear;
}

function comparePopularityDesc(left: Book, right: Book): number {
  return (right.popularity ?? 50) - (left.popularity ?? 50);
}

const CURATED_BOOK_TO_THEME = new Map(
  SECTION_META.flatMap((section) => section.bookIds.map((bookId) => [bookId, section.id] as const))
);

function hasGenre(book: Book, ...genres: string[]): boolean {
  return genres.some((genre) => book.genre.includes(genre));
}

function inferThemeId(book: Book): HomeSection["id"] {
  if (book.originalLanguage === "Russian") {
    return "russian-classics";
  }

  if (
    hasGenre(
      book,
      "Epic Poetry",
      "Mythology",
      "Scripture",
      "Sacred Text",
      "Spirituality",
      "Commentary",
      "Fables",
      "Folklore",
      "Fantasy",
      "Adventure",
      "Epic",
    )
  ) {
    return "epics-worlds";
  }

  if (
    hasGenre(
      book,
      "Romance",
      "Autobiographical Fiction",
      "Memoir",
      "Tragedy",
    )
  ) {
    return "love-memory";
  }

  if (
    hasGenre(
      book,
      "Detective Fiction",
      "Mystery",
      "Psychological Fiction",
      "Philosophical Fiction",
    )
  ) {
    // Social Novels go to society-family, not mystery
    if (hasGenre(book, "Social Novel")) return "society-family";
    return "mystery-conscience";
  }

  if (
    hasGenre(
      book,
      "History",
      "Autobiography",
      "Philosophy",
      "Science Fiction",
      "Utopian Fiction",
      "Satirical Fiction",
      "Comedy",
      "Political Novel",
    )
  ) {
    return "ideas-journeys";
  }

  return "society-family";
}

function compareFlatBooks(left: Book, right: Book, field: "year" | "length", dir: HomeSortDir): number {
  const primary =
    field === "year"
      ? compareYear(left, right)
      : compareWordCountAsc(left, right);
  if (primary !== 0) return dir === "asc" ? primary : -primary;

  const byAdded = compareAddedDesc(left, right);
  if (byAdded !== 0) return byAdded;

  return compareTitle(left, right);
}

function sortSectionBooks(
  sectionMeta: Pick<HomeSection, "id"> & { bookIds: string[] },
  books: Book[],
): Book[] {
  const sorted = [...books];
  const order = new Map(sectionMeta.bookIds.map((bookId, index) => [bookId, index]));

  sorted.sort((left, right) => {
    const leftIndex = order.get(left.id);
    const rightIndex = order.get(right.id);
    if (leftIndex != null || rightIndex != null) {
      if (leftIndex == null) return 1;
      if (rightIndex == null) return -1;
      if (leftIndex !== rightIndex) return leftIndex - rightIndex;
    }

    const byYear = compareYear(left, right);
    if (byYear !== 0) return byYear;

    const byAdded = compareAddedDesc(left, right);
    if (byAdded !== 0) return byAdded;

    return compareTitle(left, right);
  });

  return sorted;
}

export function buildHomeBrowseModel({
  books,
  langFilter,
  sortField,
  sortDir,
}: BuildHomeBrowseModelOptions): HomeBrowseModel {
  const filteredBooks =
    langFilter === "all"
      ? books
      : books.filter((book) => book.originalLanguage === langFilter);

  if (sortField === "recent") {
    const flatBooks = [...filteredBooks].sort((left, right) => {
      const byAdded = compareAddedDesc(left, right);
      if (byAdded !== 0) return sortDir === "asc" ? byAdded : -byAdded;
      return compareTitle(left, right);
    });
    return { mode: "flat", books: flatBooks };
  }

  if (sortField === "popularity") {
    const flatBooks = [...filteredBooks].sort((left, right) => {
      const primary = comparePopularityDesc(left, right);
      if (primary !== 0) return sortDir === "asc" ? -primary : primary;
      return compareTitle(left, right);
    });
    return { mode: "flat", books: flatBooks };
  }

  if (sortField === "year" || sortField === "length") {
    const flatBooks = [...filteredBooks].sort((left, right) =>
      compareFlatBooks(left, right, sortField, sortDir)
    );
    return { mode: "flat", books: flatBooks };
  }

  const grouped: Record<HomeSection["id"], Book[]> = {
    "epics-worlds": [],
    "russian-classics": [],
    "love-memory": [],
    "society-family": [],
    "mystery-conscience": [],
    "ideas-journeys": [],
  };

  for (const book of filteredBooks) {
    const sectionId = CURATED_BOOK_TO_THEME.get(book.id) ?? inferThemeId(book);
    grouped[sectionId].push(book);
  }

  const sections = SECTION_META
    .map((meta) => ({
      ...meta,
      books: sortSectionBooks(meta, grouped[meta.id]),
    }))
    .filter((section) => section.books.length > 0);

  const flatBooks = sections.flatMap((section) => section.books);
  const hasSparseSection =
    sections.length <= 1 || sections.some((section) => section.books.length < MIN_SECTION_BOOKS);

  if (hasSparseSection) {
    return { mode: "flat", books: flatBooks };
  }

  return {
    mode: "sectioned",
    sections,
    flatBooks,
  };
}
