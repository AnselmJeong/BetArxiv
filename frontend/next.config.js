/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*', // FastAPI 서버 주소
      },
    ];
  },
};

module.exports = nextConfig; 