/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: false, // Disable strict mode to prevent double-rendering in dev
  // Removed rewrites - using Next.js API routes as proxy instead
  // This is more reliable and provides better error handling
};

module.exports = nextConfig;
