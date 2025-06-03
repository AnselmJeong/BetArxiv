import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/:path*', // Remove /api prefix when forwarding to backend
      },
    ];
  },
};

export default nextConfig;
