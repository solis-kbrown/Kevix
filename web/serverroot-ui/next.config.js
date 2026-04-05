/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  // Use 'export' only when building for static deployment (STATIC_EXPORT=1)
  ...(process.env.STATIC_EXPORT === '1' ? {
    output: 'export',
    trailingSlash: true,
    images: { unoptimized: true },
  } : {}),
  async rewrites() {
    // rewrites only work in server mode (not static export)
    if (process.env.STATIC_EXPORT === '1') return [];
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:5001/api/:path*',
      },
    ];
  },
}

module.exports = nextConfig