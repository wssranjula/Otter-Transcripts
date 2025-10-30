/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Allow CORS for local development with FastAPI backend
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/:path*',
      },
    ];
  },
};

module.exports = nextConfig;

