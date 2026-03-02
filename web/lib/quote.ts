export interface QuotePosition {
  paragraphIndex: number;
  startOffset: number;
  endOffset: number;
}

/**
 * Encode a quote position into a URL hash string.
 * Format: q=p{paragraphIndex}.{startOffset}-{endOffset}
 */
export function encodeQuoteHash(
  paragraphIndex: number,
  startOffset: number,
  endOffset: number
): string {
  return `q=p${paragraphIndex}.${startOffset}-${endOffset}`;
}

/**
 * Decode a hash string into a QuotePosition, or null if invalid.
 */
export function decodeQuoteHash(hash: string): QuotePosition | null {
  const cleaned = hash.replace(/^#/, "");
  const match = cleaned.match(/^q=p(\d+)\.(\d+)-(\d+)$/);
  if (!match) return null;
  return {
    paragraphIndex: parseInt(match[1], 10),
    startOffset: parseInt(match[2], 10),
    endOffset: parseInt(match[3], 10),
  };
}

/**
 * Build a full share URL from the current page location + quote position.
 */
export function buildShareUrl(
  paragraphIndex: number,
  startOffset: number,
  endOffset: number
): string {
  const base = window.location.origin + window.location.pathname;
  return `${base}#${encodeQuoteHash(paragraphIndex, startOffset, endOffset)}`;
}

/**
 * Get the character offset of a point within a container's textContent.
 * Uses Range.toString() which correctly handles both Text and Element containers.
 */
function getTextOffset(container: Element, node: Node, offset: number): number {
  const r = document.createRange();
  r.selectNodeContents(container);
  r.setEnd(node, offset);
  return r.toString().length;
}

/** Walk up from a node to find the nearest [data-p] paragraph element. */
function findParagraph(node: Node | null): HTMLElement | null {
  while (node) {
    if (node instanceof HTMLElement && node.hasAttribute("data-p")) {
      return node;
    }
    node = node.parentElement;
  }
  return null;
}

/**
 * Extract the selected text and its quote position from the current Selection.
 * Works when the selection is within a single [data-p] paragraph, or spans
 * across paragraphs (falls back to the starting paragraph).
 */
export function getSelectionQuote(): {
  text: string;
  paragraphIndex: number;
  startOffset: number;
  endOffset: number;
} | null {
  const sel = window.getSelection();
  if (!sel || sel.isCollapsed || !sel.rangeCount) return null;

  const range = sel.getRangeAt(0);
  const text = sel.toString().trim();
  if (!text || text.length < 10) return null;

  const anchorPara = findParagraph(range.startContainer);
  if (!anchorPara) return null;

  const endPara = findParagraph(range.endContainer);

  const paragraphIndex = parseInt(anchorPara.getAttribute("data-p")!, 10);
  const startOffset = getTextOffset(anchorPara, range.startContainer, range.startOffset);

  if (endPara === anchorPara) {
    // Same paragraph — encode exact range
    const endOffset = getTextOffset(anchorPara, range.endContainer, range.endOffset);
    return { text, paragraphIndex, startOffset, endOffset };
  }

  // Cross-paragraph selection — encode from start offset to end of paragraph
  const paraTextLen = anchorPara.textContent?.length ?? 0;
  return { text, paragraphIndex, startOffset, endOffset: paraTextLen };
}
