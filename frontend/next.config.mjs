/** @type {import('next').NextConfig} */
const nextConfig = {
  /**
   * Security headers applied to every response.
   *
   * The Content-Security-Policy is deliberately restrictive: the app renders
   * server-side and ships no third-party scripts, so `script-src 'self'` and a
   * locked-down `connect-src` are sufficient. `'unsafe-inline'` is required
   * for styles because Next.js injects inline <style> blocks, and for scripts
   * because React Server Components hydrate with an inline payload.
   *
   * Note: `frame-ancestors 'none'` is the modern replacement for
   * X-Frame-Options and is already covered; X-Frame-Options is kept for older
   * user agents.
   */  async headers() {
    const isDevelopment = process.env.NODE_ENV !== "production";

    const contentSecurityPolicy = [
      "default-src 'self'",
      // 'unsafe-eval' is needed only by the dev-mode React refresh runtime.
      `script-src 'self' 'unsafe-inline'${isDevelopment ? " 'unsafe-eval'" : ""}`,
      "style-src 'self' 'unsafe-inline'",
      "img-src 'self' data: blob:",
      "font-src 'self'",
      // The browser only ever talks to its own origin: all API calls are made
      // by the Next.js server, so no external origin is needed here.
      "connect-src 'self'",
      "object-src 'none'",
      "base-uri 'self'",
      "form-action 'self'",
      "frame-ancestors 'none'",
      "upgrade-insecure-requests",
    ].join("; ");

    return [
      {
        source: "/:path*",
        headers: [
          { key: "Content-Security-Policy", value: contentSecurityPolicy },
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "X-Frame-Options", value: "DENY" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          {
            key: "Permissions-Policy",
            value: "camera=(), microphone=(), geolocation=(), interest-cohort=()",
          },
          { key: "Cross-Origin-Opener-Policy", value: "same-origin" },
        ],
      },
    ];
  },
};

export default nextConfig;
