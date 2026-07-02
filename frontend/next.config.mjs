/** Proxy API calls to the FastAPI backend so the browser stays same-origin
 *  (no CORS needed). Backend must be running on :8000 (`make api`). */
const nextConfig = {
  // Generative-CAD runs iterate the model up to 3x and can take ~5 min;
  // don't let the dev proxy 504 them.
  experimental: { proxyTimeout: 600_000 },
  async rewrites() {
    return [
      { source: "/api/:path*", destination: "http://localhost:8000/api/:path*" },
      { source: "/health", destination: "http://localhost:8000/health" },
    ];
  },
};

export default nextConfig;
