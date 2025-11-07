/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable experimental features if needed
  experimental: {
    // Enable if using app directory features
  },

  // Image optimization settings
  images: {
    domains: ['localhost'], // Add your production domain here
    unoptimized: process.env.NODE_ENV === 'development', // Disable optimization in dev for faster builds
  },

  // Headers for security
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'Referrer-Policy',
            value: 'origin-when-cross-origin',
          },
        ],
      },
    ]
  },

  // Redirects and rewrites if needed
  async rewrites() {
    return [
      // Add any API rewrites if needed for local development
    ]
  },
}

module.exports = nextConfig
