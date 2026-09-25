import type { NextConfig } from "next";

// The app demo, shared by link only: nothing on the site points here. It runs as its own Vercel
// project (scripts/demo-deploy.sh), which serves every screen under this same slug.
const DEMO_SLUG = "demo-4ajsmu"; // keep in step with SLUG in scripts/demo-deploy.sh
const DEMO_ORIGIN = process.env.DEMO_ORIGIN ?? "https://ophi-demo-nonitgs-projects.vercel.app";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      { source: `/${DEMO_SLUG}/:path*`, destination: `${DEMO_ORIGIN}/${DEMO_SLUG}/:path*` },
    ];
  },
};

export default nextConfig;
