"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { createPortal } from "react-dom";
import {
  Fragment,
  type KeyboardEvent as ReactKeyboardEvent,
  type ReactNode,
  useCallback,
  useDeferredValue,
  useEffect,
  useMemo,
  useRef,
  useState,
  useTransition,
} from "react";
import { trackEvent } from "@/lib/analytics";
import {
  normalizeForSearch,
  runSearch,
  type SearchDocument,
  type SearchDocumentKind,
  type SearchImageShape,
  type SearchIndex,
} from "@/lib/search";

type SearchSection = {
  kind: SearchDocumentKind;
  title: string;
  startIndex: number;
  total: number;
  results: SearchDocument[];
};

type DiscoverySection = {
  id: "books" | "authors";
  title: string;
  results: SearchDocument[];
};

const GROUP_ORDER: SearchDocumentKind[] = ["anthology", "book", "author", "chapter", "term"];
const GROUP_TITLES: Record<SearchDocumentKind, string> = {
  anthology: "Anthologies",
  book: "Books",
  author: "Authors",
  chapter: "Chapters",
  term: "Glossary",
};
const GROUP_STEPS: Record<SearchDocumentKind, number> = {
  anthology: 3,
  book: 4,
  author: 3,
  chapter: 5,
  term: 6,
};

function defaultVisibleByKind(): Record<SearchDocumentKind, number> {
  return {
    anthology: GROUP_STEPS.anthology,
    book: GROUP_STEPS.book,
    author: GROUP_STEPS.author,
    chapter: GROUP_STEPS.chapter,
    term: GROUP_STEPS.term,
  };
}

function pickRandomResults(results: SearchDocument[], count: number) {
  const pool = [...results];

  for (let index = pool.length - 1; index > 0; index -= 1) {
    const swapIndex = Math.floor(Math.random() * (index + 1));
    [pool[index], pool[swapIndex]] = [pool[swapIndex], pool[index]];
  }

  return pool.slice(0, count);
}

function buildDiscoverySections(documents: SearchDocument[]): DiscoverySection[] {
  const randomBooks = pickRandomResults(
    documents.filter((document) => document.kind === "book" && !document.anthologyId),
    6,
  );
  const randomAuthors = pickRandomResults(
    documents.filter((document) => document.kind === "author"),
    4,
  );

  const sections: DiscoverySection[] = [
    { id: "books", title: "Books", results: randomBooks },
    { id: "authors", title: "Authors", results: randomAuthors },
  ];

  return sections.filter((section) => section.results.length > 0);
}

let searchIndexPromise: Promise<SearchIndex> | null = null;
let searchDocumentsCache: SearchDocument[] | null = null;
let discoverySectionsCache: DiscoverySection[] | null = null;
const warmedImageUrls = new Set<string>();

function warmImageUrls(urls: Array<string | null | undefined>) {
  if (typeof window === "undefined") return;

  for (const url of urls) {
    if (!url || warmedImageUrls.has(url)) continue;
    warmedImageUrls.add(url);

    const image = new window.Image();
    image.decoding = "async";
    image.src = url;
  }
}

async function loadSearchIndex() {
  if (process.env.NODE_ENV === "development") {
    const response = await fetch("/data/search/index.json", { cache: "no-store" });
    if (!response.ok) {
      throw new Error(`Failed to load search index (${response.status})`);
    }
    return response.json() as Promise<SearchIndex>;
  }

  if (!searchIndexPromise) {
    searchIndexPromise = fetch("/data/search/index.json", { cache: "force-cache" })
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(`Failed to load search index (${response.status})`);
        }
        return response.json() as Promise<SearchIndex>;
      })
      .catch((error) => {
        searchIndexPromise = null;
        throw error;
      });
  }
  return searchIndexPromise;
}

function isTypingTarget(target: EventTarget | null) {
  if (!(target instanceof HTMLElement)) return false;
  const tagName = target.tagName.toLowerCase();
  return (
    tagName === "input" ||
    tagName === "textarea" ||
    tagName === "select" ||
    target.isContentEditable
  );
}

function buildSections(
  results: SearchDocument[],
  visibleByKind: Record<SearchDocumentKind, number>,
): SearchSection[] {
  const grouped: Record<SearchDocumentKind, SearchDocument[]> = {
    anthology: [],
    book: [],
    author: [],
    chapter: [],
    term: [],
  };

  for (const result of results) {
    grouped[result.kind].push(result);
  }

  const sections: SearchSection[] = [];
  let startIndex = 0;

  for (const kind of GROUP_ORDER) {
    if (grouped[kind].length === 0) continue;
    const visibleCount = visibleByKind[kind];
    const visibleResults = grouped[kind].slice(0, visibleCount);
    sections.push({
      kind,
      title: GROUP_TITLES[kind],
      startIndex,
      total: grouped[kind].length,
      results: visibleResults,
    });
    startIndex += visibleResults.length;
  }

  return sections;
}

function resultBadge(result: SearchDocument) {
  switch (result.kind) {
    case "anthology":
      return "Anthology";
    case "book":
      return result.language ? `Book · ${result.language}` : "Book";
    case "author":
      return "Author";
    case "chapter":
      return "Chapter";
    case "term":
      return result.typeLabel ? `Glossary · ${result.typeLabel}` : "Glossary";
  }
}

function escapeRegExp(value: string) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function getHighlightTerms(query: string) {
  return Array.from(
    new Set(
      normalizeForSearch(query)
        .split(" ")
        .filter((term) => term.length >= 2),
    ),
  ).sort((left, right) => right.length - left.length);
}

function highlightText(
  text: string | undefined,
  terms: string[],
  pattern: RegExp | null,
) {
  if (!text) return null;
  if (!pattern || terms.length === 0) return text;

  const parts = text.split(pattern);
  if (parts.length === 1) return text;

  const termSet = new Set(terms);

  return parts.map((part, index) => {
    const normalizedPart = normalizeForSearch(part);
    if (!normalizedPart || !termSet.has(normalizedPart)) {
      return <Fragment key={`${part}-${index}`}>{part}</Fragment>;
    }

    return (
      <mark
        key={`${part}-${index}`}
        className="rounded-sm bg-[#e2c48a]/25 px-[1px] text-[#f7ebcf]"
      >
        {part}
      </mark>
    );
  });
}

function thumbnailClass(shape: SearchImageShape | undefined) {
  switch (shape) {
    case "circle":
      return "h-14 w-14 rounded-full";
    case "landscape":
      return "h-14 w-24 rounded-xl";
    case "cover":
    default:
      return "h-16 w-12 rounded-lg";
  }
}

function SearchThumbnail({ result }: { result: SearchDocument }) {
  if (!result.imageUrl) return null;

  return (
    <div
      className={`relative shrink-0 overflow-hidden bg-white/[0.06] ring-1 ring-white/8 ${thumbnailClass(result.imageShape)}`}
    >
      <img
        src={result.imageUrl}
        alt={result.imageAlt ?? result.title}
        className="h-full w-full object-cover"
        loading="eager"
        fetchPriority="high"
        decoding="async"
      />
    </div>
  );
}

function SearchResultText({
  result,
  highlightedTitle,
  highlightedSubtitle,
  highlightedDescription,
}: {
  result: SearchDocument;
  highlightedTitle: ReactNode;
  highlightedSubtitle: ReactNode;
  highlightedDescription: ReactNode;
}) {
  return (
    <div className="min-w-0">
      <p className="line-clamp-1 text-sm font-medium text-white">
        {highlightedTitle}
      </p>
      {result.subtitle && (
        <p className="line-clamp-1 text-xs text-white/45">
          {highlightedSubtitle}
        </p>
      )}
      {result.description && (
        <p className="mt-1 line-clamp-2 text-xs leading-relaxed text-white/35">
          {highlightedDescription}
        </p>
      )}
    </div>
  );
}

export default function SiteSearch() {
  const pathname = usePathname();
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const deferredQuery = useDeferredValue(query);
  const [documents, setDocuments] = useState<SearchDocument[] | null>(searchDocumentsCache);
  const [results, setResults] = useState<SearchDocument[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [visibleByKind, setVisibleByKind] = useState(defaultVisibleByKind);
  const [discoverySections, setDiscoverySections] = useState<DiscoverySection[]>(
    discoverySectionsCache ?? [],
  );
  const [isPending, startTransition] = useTransition();

  const close = useCallback(() => {
    setOpen(false);
    setQuery("");
    setResults([]);
    setSelectedIndex(0);
    setVisibleByKind(defaultVisibleByKind());
    setError(null);
  }, []);

  useEffect(() => {
    close();
  }, [pathname, close]);

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setOpen(true);
        return;
      }

      if (event.key === "/" && !isTypingTarget(event.target)) {
        event.preventDefault();
        setOpen(true);
        return;
      }

      if (event.key === "Escape") {
        setOpen(false);
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  useEffect(() => {
    if (!open) return;
    trackEvent("search_open");
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    inputRef.current?.focus();
    return () => {
      document.body.style.overflow = previousOverflow;
    };
  }, [open]);

  useEffect(() => {
    if (!open) return;
    if (documents && process.env.NODE_ENV !== "development") return;

    let cancelled = false;

    setLoading(true);
    setError(null);

    loadSearchIndex()
      .then((payload) => {
        if (cancelled) return;
        searchDocumentsCache = payload.documents;
        setDocuments(payload.documents);
      })
      .catch((loadError: unknown) => {
        if (cancelled) return;
        setError(loadError instanceof Error ? loadError.message : "Failed to load search");
      })
      .finally(() => {
        if (cancelled) return;
        setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [open]);

  useEffect(() => {
    if (!documents || discoverySectionsCache) return;
    const sections = buildDiscoverySections(documents);
    discoverySectionsCache = sections;
    warmImageUrls(sections.flatMap((section) => section.results.map((result) => result.imageUrl)));
    setDiscoverySections(sections);
  }, [documents]);

  useEffect(() => {
    if (discoverySections.length === 0) return;
    warmImageUrls(
      discoverySections.flatMap((section) => section.results.map((result) => result.imageUrl)),
    );
  }, [discoverySections]);

  // Eagerly warm the search index on mount (no delay) so the zero state
  // appears instantly when the user presses "/".
  useEffect(() => {
    if (documents) return;

    let cancelled = false;
    loadSearchIndex()
      .then((payload) => {
        if (cancelled) return;
        searchDocumentsCache = payload.documents;
        setDocuments((current) => current ?? payload.documents);
      })
      .catch(() => {
        // Search can stay lazy if background warming fails.
      });

    return () => {
      cancelled = true;
    };
  }, [documents]);

  useEffect(() => {
    if (!documents || deferredQuery.trim().length < 2) {
      setResults([]);
      setSelectedIndex(0);
      setVisibleByKind(defaultVisibleByKind());
      return;
    }

    startTransition(() => {
      setResults(runSearch(documents, deferredQuery));
      setSelectedIndex(0);
      setVisibleByKind(defaultVisibleByKind());
    });
  }, [deferredQuery, documents]);

  const sections = useMemo(
    () => buildSections(results, visibleByKind),
    [results, visibleByKind],
  );
  const visibleResults = useMemo(
    () => sections.flatMap((section) => section.results),
    [sections],
  );
  const highlightTerms = useMemo(() => getHighlightTerms(deferredQuery), [deferredQuery]);
  const highlightPattern = useMemo(
    () =>
      highlightTerms.length > 0
        ? new RegExp(`(${highlightTerms.map((term) => escapeRegExp(term)).join("|")})`, "ig")
        : null,
    [highlightTerms],
  );

  const openResult = useCallback(
    (result: SearchDocument) => {
      trackEvent("search_result_click", {
        kind: result.kind,
        query: deferredQuery.trim(),
      });
      close();
      router.push(result.url);
    },
    [close, deferredQuery, router],
  );

  useEffect(() => {
    warmImageUrls(visibleResults.map((result) => result.imageUrl));
  }, [visibleResults]);

  function handleInputKeyDown(event: ReactKeyboardEvent<HTMLInputElement>) {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setSelectedIndex((current) =>
        visibleResults.length === 0 ? 0 : Math.min(current + 1, visibleResults.length - 1),
      );
      return;
    }

    if (event.key === "ArrowUp") {
      event.preventDefault();
      setSelectedIndex((current) => Math.max(current - 1, 0));
      return;
    }

    if (event.key === "Enter" && visibleResults[selectedIndex]) {
      event.preventDefault();
      openResult(visibleResults[selectedIndex]);
    }
  }

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="inline-flex items-center gap-2 rounded-md border border-white/15 px-2.5 py-1 text-xs font-medium tracking-wide text-white/70 transition-colors hover:bg-white/10"
        aria-label="Search"
      >
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="11" cy="11" r="7" />
          <line x1="21" y1="21" x2="16.65" y2="16.65" />
        </svg>
        <span className="hidden sm:inline">Search</span>
        <span className="hidden md:inline text-white/35">/</span>
      </button>

      {open && createPortal(
        <div
          className="fixed inset-0 z-[70] bg-black/60 backdrop-blur-md px-4 pt-20 pb-4"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) {
              close();
            }
          }}
        >
          <div className="mx-auto max-w-2xl overflow-hidden rounded-2xl border border-white/10 bg-[#101011] shadow-2xl shadow-black/60">
            <div className="flex items-center gap-3 border-b border-white/10 px-4 py-3">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-white/40">
                <circle cx="11" cy="11" r="7" />
                <line x1="21" y1="21" x2="16.65" y2="16.65" />
              </svg>
              <input
                ref={inputRef}
                type="text"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                onKeyDown={handleInputKeyDown}
                placeholder="Search books, authors, chapters, glossary..."
                className="w-full bg-transparent text-sm text-white outline-none placeholder:text-white/30"
              />
              <button
                type="button"
                onClick={close}
                className="inline-flex h-8 w-8 items-center justify-center rounded-md text-white/45 transition-colors hover:bg-white/10 hover:text-white/70 sm:hidden"
                aria-label="Close search"
              >
                <svg
                  width="14"
                  height="14"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>
              <button
                type="button"
                onClick={close}
                className="hidden rounded-md border border-white/10 px-2 py-1 text-[11px] text-white/45 transition-colors hover:bg-white/10 hover:text-white/70 sm:inline-flex"
              >
                Esc
              </button>
            </div>

            <div className="max-h-[70vh] overflow-y-auto px-2 py-2">
              {!documents && !error && (
                <div className="px-3 py-10 text-center text-sm text-white/45">
                  Loading search…
                </div>
              )}

              {error && (
                <div className="px-3 py-10 text-center text-sm text-red-300/80">
                  {error}
                </div>
              )}

              {documents && !error && deferredQuery.trim().length < 2 && (
                <div className="px-1 py-2">
                  <div className="px-3 pb-4 pt-2 text-sm text-white/45">
                    Search across books, authors, chapter titles, and glossary terms.
                  </div>
                  {discoverySections.map((section) => (
                    <section key={section.id} className="pb-3">
                      <h2 className="px-3 py-2 text-[11px] font-semibold uppercase tracking-[0.2em] text-white/35">
                        {section.title}
                      </h2>
                      <div className="space-y-1">
                        {section.results.map((result) => (
                          <Link
                            key={result.id}
                            href={result.url}
                            onClick={close}
                            className="block rounded-xl px-3 py-3 transition-colors hover:bg-white/[0.06]"
                          >
                            <div className="flex items-start justify-between gap-3">
                              <div className="flex min-w-0 items-start gap-3">
                                <SearchThumbnail result={result} />
                                <SearchResultText
                                  result={result}
                                  highlightedTitle={result.title}
                                  highlightedSubtitle={result.subtitle}
                                  highlightedDescription={result.description}
                                />
                              </div>
                              <span className="shrink-0 rounded-full bg-white/[0.07] px-2 py-1 text-[10px] font-medium uppercase tracking-wide text-white/45">
                                {resultBadge(result)}
                              </span>
                            </div>
                          </Link>
                        ))}
                      </div>
                    </section>
                  ))}
                </div>
              )}

              {!loading && !error && deferredQuery.trim().length >= 2 && visibleResults.length === 0 && (
                <div className="px-3 py-10 text-center text-sm text-white/45">
                  No results for <span className="text-white/70">{deferredQuery.trim()}</span>.
                </div>
              )}

              {!error &&
                sections.map((section) => {
                  const hasMore = section.total > section.results.length;
                  const remaining = section.total - section.results.length;

                  return (
                    <section key={section.kind} className="pb-2">
                      <div className="flex items-center justify-between gap-3 px-3 py-2">
                        <h2 className="text-[11px] font-semibold uppercase tracking-[0.2em] text-white/35">
                          {section.title}
                        </h2>
                        <span className="text-[10px] uppercase tracking-wide text-white/25">
                          {section.total}
                        </span>
                      </div>
                      <div className="space-y-1">
                        {section.results.map((result, index) => {
                          const globalIndex = section.startIndex + index;
                          const active = globalIndex === selectedIndex;

                          return (
                            <Link
                              key={result.id}
                              href={result.url}
                              onClick={() => {
                                trackEvent("search_result_click", {
                                  kind: result.kind,
                                  query: deferredQuery.trim(),
                                });
                                close();
                              }}
                              onMouseEnter={() => setSelectedIndex(globalIndex)}
                              className={`block rounded-xl px-3 py-3 transition-colors ${
                                active ? "bg-white/10" : "hover:bg-white/[0.06]"
                              }`}
                            >
                              <div className="flex items-start justify-between gap-3">
                                <div className="flex min-w-0 items-start gap-3">
                                  <SearchThumbnail result={result} />
                                  <SearchResultText
                                    result={result}
                                    highlightedTitle={highlightText(result.title, highlightTerms, highlightPattern)}
                                    highlightedSubtitle={highlightText(result.subtitle, highlightTerms, highlightPattern)}
                                    highlightedDescription={highlightText(result.description, highlightTerms, highlightPattern)}
                                  />
                                </div>
                                <span className="shrink-0 rounded-full bg-white/[0.07] px-2 py-1 text-[10px] font-medium uppercase tracking-wide text-white/45">
                                  {resultBadge(result)}
                                </span>
                              </div>
                            </Link>
                          );
                        })}
                      </div>
                      {hasMore && (
                        <div className="px-3 pt-1">
                          <button
                            type="button"
                            onClick={() =>
                              setVisibleByKind((current) => ({
                                ...current,
                                [section.kind]: current[section.kind] + GROUP_STEPS[section.kind],
                              }))
                            }
                            className="text-[10px] font-medium uppercase tracking-wide text-white/35 transition-colors hover:text-white/65"
                          >
                            +{remaining} more
                          </button>
                        </div>
                      )}
                    </section>
                  );
                })}

              {isPending && visibleResults.length > 0 && (
                <div className="px-3 py-2 text-[11px] text-white/35">
                  Updating…
                </div>
              )}
            </div>
          </div>
        </div>,
        document.body,
      )}
    </>
  );
}
