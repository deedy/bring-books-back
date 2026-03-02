const STORAGE_KEY = 'offline-books';

export function registerSW() {
  if (typeof window === 'undefined' || !('serviceWorker' in navigator)) return;
  navigator.serviceWorker.register('/sw.js').catch(() => {});
}

function getSWRegistration(): Promise<ServiceWorker | null> {
  return navigator.serviceWorker.ready.then((reg) => reg.active);
}

export function isDownloaded(bookId: string): boolean {
  if (typeof window === 'undefined') return false;
  const stored = localStorage.getItem(STORAGE_KEY);
  if (!stored) return false;
  const books: string[] = JSON.parse(stored);
  return books.includes(bookId);
}

export function getDownloadedBooks(): string[] {
  if (typeof window === 'undefined') return [];
  const stored = localStorage.getItem(STORAGE_KEY);
  return stored ? JSON.parse(stored) : [];
}

function markDownloaded(bookId: string) {
  const books = getDownloadedBooks();
  if (!books.includes(bookId)) {
    books.push(bookId);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(books));
  }
}

function unmarkDownloaded(bookId: string) {
  const books = getDownloadedBooks().filter((id) => id !== bookId);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(books));
}

/** Build the full list of URLs to cache for a book */
async function buildBookUrls(bookId: string): Promise<string[]> {
  const base = `/data/books/${bookId}`;
  const urls: string[] = [];

  // JSON data files
  urls.push(`${base}/chapters.json`);
  urls.push(`${base}/meta.json`);
  urls.push(`${base}/annotations.json`);

  // Cover and hero images
  urls.push(`/data/images/covers/${bookId}.webp`);
  urls.push(`/data/images/heroes/${bookId}.webp`);

  // Chapter images — fetch chapters.json to discover them
  const chaptersRes = await fetch(`${base}/chapters.json`);
  if (chaptersRes.ok) {
    const chaptersData = await chaptersRes.json();
    for (const ch of chaptersData.chapters) {
      if (ch.image) urls.push(ch.image);
    }
  }

  // Character portrait images — fetch annotations.json to discover them
  try {
    const annoRes = await fetch(`${base}/annotations.json`);
    if (annoRes.ok) {
      const annoData = await annoRes.json();
      for (const entry of Object.values(annoData.glossary)) {
        const e = entry as { image?: string };
        if (e.image) urls.push(e.image);
      }
    }
  } catch {
    // annotations may not exist for all books
  }

  return urls;
}

export async function downloadBook(
  bookId: string,
  onProgress: (percent: number) => void
): Promise<void> {
  const sw = await getSWRegistration();
  if (!sw) throw new Error('Service worker not available');

  const urls = await buildBookUrls(bookId);

  return new Promise((resolve, reject) => {
    const handler = (event: MessageEvent) => {
      const { data } = event;
      if (data.bookId !== bookId) return;

      if (data.type === 'PROGRESS') {
        onProgress(Math.round((data.done / data.total) * 100));
      }
      if (data.type === 'COMPLETE') {
        navigator.serviceWorker.removeEventListener('message', handler);
        markDownloaded(bookId);
        resolve();
      }
    };

    navigator.serviceWorker.addEventListener('message', handler);

    const timeout = setTimeout(() => {
      navigator.serviceWorker.removeEventListener('message', handler);
      reject(new Error('Download timed out'));
    }, 5 * 60 * 1000);

    // Override resolve to also clear timeout
    const origResolve = resolve;
    resolve = ((val: void) => {
      clearTimeout(timeout);
      origResolve(val);
    }) as typeof resolve;

    sw.postMessage({ type: 'CACHE_BOOK', bookId, urls });
  });
}

export async function removeBook(bookId: string): Promise<void> {
  const sw = await getSWRegistration();
  if (!sw) return;

  return new Promise((resolve) => {
    const handler = (event: MessageEvent) => {
      if (event.data.type === 'DELETED' && event.data.bookId === bookId) {
        navigator.serviceWorker.removeEventListener('message', handler);
        unmarkDownloaded(bookId);
        resolve();
      }
    };
    navigator.serviceWorker.addEventListener('message', handler);
    sw.postMessage({ type: 'DELETE_BOOK', bookId });
  });
}
