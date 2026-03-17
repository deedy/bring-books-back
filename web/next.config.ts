import type { NextConfig } from "next";

const isProd = process.env.NODE_ENV === "production";

const nextConfig: NextConfig = {
  output: "standalone",
  devIndicators: false,
  experimental: {
    staleTimes: {
      dynamic: 0,
      static: 0,
    },
  },
  images: {
    unoptimized: true,
  },
  async redirects() {
    if (!isProd) return [];
    return [
      {
        source: "/data/images/:path*",
        destination: "https://storage.googleapis.com/grandoldbooks-assets/data/images/:path*",
        permanent: true,
      },
      {
        source: "/data/audio/:path*",
        destination: "https://storage.googleapis.com/grandoldbooks-assets/data/audio/:path*",
        permanent: true,
      },
    ];
  },
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          { key: "X-Frame-Options", value: "DENY" },
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation()" },
        ],
      },
      {
        source: "/_next/static/:path*",
        headers: [
          { key: "Cache-Control", value: "public, max-age=31536000, immutable" },
        ],
      },
      {
        source: "/data/:path*",
        headers: [
          { key: "Cache-Control", value: "public, max-age=86400, s-maxage=2592000" },
        ],
      },
    ];
  },
};

export default nextConfig;
