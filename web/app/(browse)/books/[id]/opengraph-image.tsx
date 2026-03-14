import { ImageResponse } from "next/og";
import { getCatalog } from "@/lib/data";

export const runtime = "nodejs";
export const alt = "Book cover";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default async function OGImage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const catalog = getCatalog();
  const book = catalog.books.find((b) => b.id === id);
  if (!book) {
    return new ImageResponse(
      <div style={{ display: "flex", width: "100%", height: "100%", background: "#0a0a0b", alignItems: "center", justifyContent: "center" }}>
        <span style={{ color: "#fff", fontSize: 48 }}>Grand Old Books</span>
      </div>,
      { ...size }
    );
  }
  const author = catalog.authors.find((a) => a.id === book.authorId);
  const coverUrl = `https://storage.googleapis.com/grandoldbooks-assets${book.coverImage.replace(".webp", ".png")}`;

  return new ImageResponse(
    <div
      style={{
        display: "flex",
        width: "100%",
        height: "100%",
        background: "linear-gradient(135deg, #0a0a0b 0%, #1a1a2e 100%)",
        padding: 60,
        alignItems: "center",
        gap: 60,
      }}
    >
      {/* Book cover */}
      <img
        src={coverUrl}
        alt=""
        width={280}
        height={420}
        style={{
          borderRadius: 12,
          objectFit: "cover",
          boxShadow: "0 8px 30px rgba(0,0,0,0.5)",
        }}
      />
      {/* Text */}
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          flex: 1,
          justifyContent: "center",
        }}
      >
        <span
          style={{
            fontSize: 48,
            fontWeight: 700,
            color: "#ffffff",
            lineHeight: 1.2,
            overflow: "hidden",
            textOverflow: "ellipsis",
          }}
        >
          {book.title}
        </span>
        {author && (
          <span
            style={{
              fontSize: 28,
              color: "rgba(255,255,255,0.6)",
              marginTop: 16,
            }}
          >
            by {author.name}
          </span>
        )}
        {book.subtitle && (
          <span
            style={{
              fontSize: 22,
              color: "rgba(255,255,255,0.4)",
              marginTop: 12,
            }}
          >
            {book.subtitle}
          </span>
        )}
        <span
          style={{
            fontSize: 20,
            color: "rgba(255,255,255,0.3)",
            marginTop: 32,
          }}
        >
          Grand Old Books
        </span>
      </div>
    </div>,
    { ...size }
  );
}
