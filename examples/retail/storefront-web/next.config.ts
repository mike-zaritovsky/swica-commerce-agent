import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  allowedDevOrigins: ["*"],
  // No Next.js badge over the assistant when it is embedded in a demo.
  devIndicators: false,
};

export default nextConfig;
