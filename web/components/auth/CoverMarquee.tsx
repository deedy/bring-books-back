"use client";

interface CoverMarqueeProps {
  books: { cover: string; title: string }[];
}

export default function CoverMarquee({ books }: CoverMarqueeProps) {
  const duplicated = [...books, ...books];

  return (
    <div
      style={{
        overflow: "hidden",
        maskImage:
          "linear-gradient(to right, transparent 0%, black 10%, black 90%, transparent 100%)",
        WebkitMaskImage:
          "linear-gradient(to right, transparent 0%, black 10%, black 90%, transparent 100%)",
      }}
    >
      <style>{`
        @keyframes marquee-scroll {
          0% { transform: translateX(0); }
          100% { transform: translateX(-50%); }
        }
        .marquee-track {
          display: flex;
          gap: 16px;
          width: max-content;
          animation: marquee-scroll 35s linear infinite;
        }
      `}</style>
      <div className="marquee-track">
        {duplicated.map((book, i) => (
          <div
            key={i}
            className="marquee-item"
            style={{ flexShrink: 0, textAlign: "center" }}
          >
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={book.cover}
              alt=""
              className="marquee-cover"
              style={{
                borderRadius: "8px",
                objectFit: "cover",
                opacity: 0.65,
              }}
            />
            <p
              className="marquee-title"
              style={{
                marginTop: "6px",
                lineHeight: "1.3",
                color: "rgba(255,255,255,0.35)",
                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "nowrap",
                fontFamily: "var(--font-serif)",
              }}
            >
              {book.title}
            </p>
          </div>
        ))}
      </div>
      <style>{`
        .marquee-item { width: 110px; }
        .marquee-cover { height: 160px; width: 110px; }
        .marquee-title { font-size: 10px; }
        @media (min-width: 768px) {
          .marquee-item { width: 130px; }
          .marquee-cover { height: 190px; width: 130px; }
          .marquee-title { font-size: 11px; }
        }
      `}</style>
    </div>
  );
}
