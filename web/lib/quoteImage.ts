/**
 * Generate a quote card image as a Blob using the Canvas API.
 * Includes book cover, quote text, title, author, year, chapter, and watermark.
 */
export async function generateQuoteImage(
  quoteText: string,
  bookTitle: string,
  authorName: string,
  accentColor: string,
  coverImageUrl: string,
  originalYear: number,
  chapterTitle: string,
  shareUrl?: string
): Promise<Blob | null> {
  const canvas = document.createElement("canvas");
  const W = 1200;
  const H = 630;
  canvas.width = W;
  canvas.height = H;
  const ctx = canvas.getContext("2d");
  if (!ctx) return null;

  // Background
  ctx.fillStyle = "#1a1a1a";
  ctx.fillRect(0, 0, W, H);

  // Load and draw book cover on the left
  const coverW = 200;
  const coverPad = 50;
  let textLeftEdge = coverPad; // fallback if cover fails

  try {
    const img = await loadImage(coverImageUrl);
    const aspect = img.height / img.width;
    const coverH = Math.min(coverW * aspect, H - 100);
    const coverX = coverPad;
    const coverY = (H - coverH) / 2;

    // Subtle shadow behind cover
    ctx.shadowColor = "rgba(0,0,0,0.5)";
    ctx.shadowBlur = 20;
    ctx.shadowOffsetX = 4;
    ctx.shadowOffsetY = 4;

    // Rounded rect clip for cover
    roundRect(ctx, coverX, coverY, coverW, coverH, 8);
    ctx.clip();
    ctx.drawImage(img, coverX, coverY, coverW, coverH);

    // Reset clip and shadow
    ctx.restore();
    ctx.save();
    ctx.shadowColor = "transparent";
    ctx.shadowBlur = 0;

    textLeftEdge = coverPad + coverW + 40;
  } catch {
    textLeftEdge = 80;
  }

  const textRightEdge = W - 60;
  const maxWidth = textRightEdge - textLeftEdge;

  // Accent color stripe at top
  ctx.fillStyle = accentColor;
  ctx.fillRect(0, 0, W, 4);

  // --- Layout: reserve space for footer, then fill remaining with quote ---
  // Footer: divider + title + author/chapter + watermark = ~120px from bottom
  const footerTop = H - 120;

  // Opening quote mark — small, inline with the text area
  const openQuoteSize = 48;
  ctx.font = `bold ${openQuoteSize}px Georgia, serif`;
  ctx.fillStyle = accentColor + "60";
  const openQuoteY = 72;
  ctx.fillText("\u201C", textLeftEdge, openQuoteY);

  // Quote text — wrap lines to fill space between open quote and footer
  const textFont = "italic 26px Georgia, serif";
  const lineHeight = 36;
  ctx.font = textFont;
  ctx.fillStyle = "#e5e5e5";

  const words = quoteText.split(/\s+/);
  const lines: string[] = [];
  let currentLine = "";
  for (const word of words) {
    const test = currentLine ? `${currentLine} ${word}` : word;
    if (ctx.measureText(test).width > maxWidth) {
      if (currentLine) lines.push(currentLine);
      currentLine = word;
    } else {
      currentLine = test;
    }
  }
  if (currentLine) lines.push(currentLine);

  // Calculate how many lines fit: from textStartY to footerTop, leaving room for closing quote
  const textStartY = openQuoteY + 30;
  const closeQuoteHeight = 30; // space reserved below last text line for closing quote
  const availableHeight = footerTop - textStartY - closeQuoteHeight - 10;
  const maxLines = Math.max(1, Math.floor(availableHeight / lineHeight));

  if (lines.length > maxLines) {
    lines.length = maxLines;
    lines[maxLines - 1] = lines[maxLines - 1].replace(/\s+\S*$/, "") + "\u2026";
  }

  // Draw text lines
  ctx.font = textFont;
  ctx.fillStyle = "#e5e5e5";
  for (let i = 0; i < lines.length; i++) {
    ctx.fillText(lines[i], textLeftEdge, textStartY + i * lineHeight);
  }

  // Closing quote mark — placed on a new line below the last text line, right-aligned to text end
  const lastLineY = textStartY + (lines.length - 1) * lineHeight;
  const closeQuoteY = lastLineY + lineHeight; // one line below
  ctx.font = `bold ${openQuoteSize}px Georgia, serif`;
  ctx.fillStyle = accentColor + "60";
  // Right-align the closing quote to the end of the last line
  ctx.font = textFont;
  const lastLineW = ctx.measureText(lines[lines.length - 1] || "").width;
  ctx.font = `bold ${openQuoteSize}px Georgia, serif`;
  const closeQuoteW = ctx.measureText("\u201D").width;
  const closeQuoteX = Math.min(textLeftEdge + lastLineW + 6, textRightEdge - closeQuoteW);
  ctx.fillText("\u201D", closeQuoteX, closeQuoteY);

  // --- Footer ---
  // Divider line
  ctx.strokeStyle = accentColor + "40";
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(textLeftEdge, footerTop);
  ctx.lineTo(textRightEdge, footerTop);
  ctx.stroke();

  // Book title
  ctx.font = "bold 20px -apple-system, BlinkMacSystemFont, sans-serif";
  ctx.fillStyle = "#ffffff";
  ctx.fillText(bookTitle, textLeftEdge, footerTop + 32);

  // Author · Year · Chapter
  const metaLine = chapterTitle
    ? `by ${authorName}  \u00B7  ${originalYear}  \u00B7  ${chapterTitle}`
    : `by ${authorName}  \u00B7  ${originalYear}`;
  ctx.font = "14px -apple-system, BlinkMacSystemFont, sans-serif";
  ctx.fillStyle = "#ffffff70";
  // Truncate if too long
  let metaText = metaLine;
  while (ctx.measureText(metaText).width > maxWidth && metaText.length > 20) {
    metaText = metaText.slice(0, -4) + "\u2026";
  }
  ctx.fillText(metaText, textLeftEdge, footerTop + 58);

  // Deep link URL or watermark — bottom-right
  ctx.font = "13px -apple-system, BlinkMacSystemFont, sans-serif";
  ctx.fillStyle = "#ffffff50";
  ctx.textAlign = "right";
  if (shareUrl) {
    // Show the deep link (strip protocol for cleaner look)
    const displayUrl = shareUrl.replace(/^https?:\/\//, "");
    // Truncate if too wide
    let urlText = displayUrl;
    while (ctx.measureText(urlText).width > W - 80 && urlText.length > 20) {
      urlText = urlText.slice(0, -4) + "\u2026";
    }
    ctx.fillText(urlText, W - 40, H - 20);
  } else {
    ctx.fillText("grandoldbooks.com", W - 40, H - 20);
  }
  ctx.textAlign = "left";

  return new Promise((resolve) => {
    canvas.toBlob((blob) => resolve(blob), "image/png");
  });
}

async function loadImage(src: string): Promise<HTMLImageElement> {
  // Fetch as blob to avoid CORS issues with cross-origin redirects (nginx 301 → GCS).
  // Using a blob URL means the Image element loads from a same-origin blob,
  // so the canvas stays un-tainted without needing crossOrigin="anonymous".
  const res = await fetch(src);
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => {
      URL.revokeObjectURL(url);
      resolve(img);
    };
    img.onerror = (e) => {
      URL.revokeObjectURL(url);
      reject(e);
    };
    img.src = url;
  });
}

function roundRect(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  w: number,
  h: number,
  r: number
) {
  ctx.save();
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.lineTo(x + w - r, y);
  ctx.arcTo(x + w, y, x + w, y + r, r);
  ctx.lineTo(x + w, y + h - r);
  ctx.arcTo(x + w, y + h, x + w - r, y + h, r);
  ctx.lineTo(x + r, y + h);
  ctx.arcTo(x, y + h, x, y + h - r, r);
  ctx.lineTo(x, y + r);
  ctx.arcTo(x, y, x + r, y, r);
  ctx.closePath();
}
