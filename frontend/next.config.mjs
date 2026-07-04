/** Proxy API calls to the FastAPI backend so the browser stays same-origin
 *  (no CORS needed). BACKEND_URL is set by docker-compose (http://backend:8000);
 *  defaults to localhost:8000 for `make api` + `make frontend` development. */
const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

const nextConfig = {
  // Generative-CAD runs iterate the model and can take minutes;
  // don't let the proxy 504 them.
  experimental: { proxyTimeout: 600_000 },
  async rewrites() {
    return [
      { source: "/api/:path*", destination: `${BACKEND_URL}/api/:path*` },
      { source: "/health", destination: `${BACKEND_URL}/health` },
    ];
  },
};

export default nextConfig;
