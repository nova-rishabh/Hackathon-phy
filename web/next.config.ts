import type { NextConfig } from "next";
const nextConfig: NextConfig = {
  typescript: { ignoreBuildErrors: true },
  eslint: { ignoreDuringBuilds: true },
  async redirects() {
    return [
      { source: "/claims", destination: "/check", permanent: false },
      { source: "/citizen", destination: "/ask", permanent: false },
      { source: "/stories", destination: "/", permanent: false },
      { source: "/flags", destination: "/", permanent: false },
      { source: "/report", destination: "/trust", permanent: false },
    ];
  },
};
export default nextConfig;
