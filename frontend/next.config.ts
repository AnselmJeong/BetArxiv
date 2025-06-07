import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'standalone', // Enable standalone build for Docker
};

export default nextConfig;
