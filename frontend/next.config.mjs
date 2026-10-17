/** @type {import('next').NextConfig} */

const backend = process.env.BACKEND_PROXY_ORIGIN;

const config = {
  reactStrictMode: true,
  poweredByHeader: false,

  async rewrites() {
    if (!backend) return [];

    return [
      {
        source: "/api/:path*",
        destination: `${backend}/api/:path*`,
      },
      {
        source: "/samples/:path*",
        destination: `${backend}/samples/:path*`,
      },
    ];
  },
};

export default config;