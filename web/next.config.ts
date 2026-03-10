import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  images: {
    unoptimized: true,
  },
  async rewrites() {
    return [
      {
        source: "/data/images/:path*",
        destination: "https://storage.googleapis.com/grandoldbooks-assets/data/images/:path*",
      },
    ];
  },
};

export default nextConfig;
