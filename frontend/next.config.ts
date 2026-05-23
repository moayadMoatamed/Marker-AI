import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "export",
  distDir: "out",
  images: { unoptimized: true },
  async rewrites() {
    return [
      // In dev, proxy /api/* and /runs/* to the Python backend
      ...(process.env.NODE_ENV === "development"
        ? [
            {
              source: "/api/:path*",
              destination: "http://localhost:8001/api/:path*",
            },
            {
              source: "/runs/:path*",
              destination: "http://localhost:8001/runs/:path*",
            },
          ]
        : []),
    ];
  },
};

export default nextConfig;
