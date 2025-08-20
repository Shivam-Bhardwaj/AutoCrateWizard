/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    appDir: true,
  },
  images: {
    domains: [],
  },
  env: {
    AUTOCRATE_VERSION: '12.1.4-web',
    NODE_ENV: process.env.NODE_ENV,
  },
}

module.exports = nextConfig