/** Proxy API calls to the FastAPI backend so the browser stays same-origin
 *  (no CORS needed). Backend must be running on :8000 (`make api`). */
const nextConfig = {
  async rewrites() {
    return [
      { source: "/api/:path*", destination: "http://localhost:8000/api/:path*" },
      { source: "/health", destination: "http://localhost:8000/health" },
    ];
  },
};

export default nextConfig;
