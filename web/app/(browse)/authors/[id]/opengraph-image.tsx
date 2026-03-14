import { ImageResponse } from "next/og";
import { getCatalog } from "@/lib/data";

export const runtime = "nodejs";
export const alt = "Author portrait";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default async function OGImage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const catalog = getCatalog();
  const author = catalog.authors.find((a) => a.id === id);
  if (!author) {
    return new ImageResponse(
      <div style={{ display: "flex", width: "100%", height: "100%", background: "#0a0a0b", alignItems: "center", justifyContent: "center" }}>
        <span style={{ color: "#fff", fontSize: 48 }}>Grand Old Books</span>
      </div>,
      { ...size }
    );
  }
  const portraitUrl = `https://storage.googleapis.com/grandoldbooks-assets${author.image.replace(".webp", ".png")}`;
  const bookCount = catalog.books.filter((b) => b.authorId === author.id && !b.anthologyId).length;

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
      {/* Author portrait */}
      <img
        src={portraitUrl}
        alt=""
        width={300}
        height={300}
        style={{
          borderRadius: "50%",
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
            fontSize: 52,
            fontWeight: 700,
            color: "#ffffff",
            lineHeight: 1.2,
          }}
        >
          {author.name}
        </span>
        <span
          style={{
            fontSize: 28,
            color: "rgba(255,255,255,0.5)",
            marginTop: 12,
          }}
        >
          {author.years}
        </span>
        <span
          style={{
            fontSize: 24,
            color: "rgba(255,255,255,0.4)",
            marginTop: 8,
          }}
        >
          {bookCount} {bookCount === 1 ? "book" : "books"} on Grand Old Books
        </span>
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
