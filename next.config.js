/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  async rewrites() {
    return [
      {
        source: '/api/streamlit/:path*',
        destination: 'http://localhost:8502/:path*',
      },
    ]
  },
}

module.exports = nextConfig
