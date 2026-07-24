import { useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { useAuth } from "@/context/AuthContext";

const STAR_POINTS =
  "50,5 57.65,31.52 81.82,18.18 68.48,42.35 95,50 68.48,57.65 81.82,81.82 " +
  "57.65,68.48 50,95 42.35,68.48 18.18,81.82 31.52,57.65 5,50 31.52,42.35 " +
  "18.18,18.18 42.35,31.52";

export function RegisterMasjidPage() {
  const { isAuthenticated, clearToken } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!isAuthenticated) navigate("/login", { replace: true });
  }, [isAuthenticated, navigate]);

  if (!isAuthenticated) return null;

  function handleSignOut() {
    clearToken();
    navigate("/login", { replace: true });
  }

  return (
    <div className="relative min-h-screen flex flex-col">

      {/* Ambient glow orbs */}
      <div aria-hidden="true" className="pointer-events-none fixed inset-0 overflow-hidden">
        <div
          className="absolute -top-1/4 -right-20 h-[600px] w-[600px] rounded-full"
          style={{ background: "radial-gradient(circle, rgba(94,234,212,0.08) 0%, transparent 65%)" }}
        />
        <div
          className="absolute bottom-0 -left-32 h-[500px] w-[500px] rounded-full"
          style={{ background: "radial-gradient(circle, rgba(212,176,106,0.05) 0%, transparent 65%)" }}
        />
      </div>
      <div className="pointer-events-none fixed inset-0 dot-grid opacity-30" aria-hidden="true" />

      {/* Minimal top nav */}
      <nav className="relative flex items-center justify-between px-6 py-4">
        <Link
          to="/"
          className="flex items-center gap-2.5 focus:outline-none focus-visible:ring-2 focus-visible:ring-mint rounded-sm"
        >
          <div
            className="flex h-8 w-8 items-center justify-center rounded-icon font-sora text-sm font-black"
            style={{
              background: "linear-gradient(135deg, #5eead4 0%, #0d9488 100%)",
              color: "#06120f",
            }}
            aria-hidden="true"
          >
            M
          </div>
          <span className="font-sora font-bold text-step-0 text-ink tracking-sora">
            Mubeen
          </span>
        </Link>

        <button
          type="button"
          onClick={handleSignOut}
          className="btn-ghost text-[11px] px-4 py-2"
        >
          Sign out
        </button>
      </nav>

      {/* Main content */}
      <div
        className="relative flex flex-1 flex-col items-center justify-center px-5 py-16 text-center"
      >
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
          className="w-full max-w-[520px]"
        >
          {/* Decorative star */}
          <svg
            viewBox="0 0 100 100"
            className="mx-auto mb-8 h-16 w-16 opacity-30 star-float"
            aria-hidden="true"
            focusable="false"
          >
            <polygon points={STAR_POINTS} fill="#5eead4" />
          </svg>

          <div
            className="glass rounded-card-xl overflow-hidden"
            style={{ borderColor: "rgba(94,234,212,0.14)" }}
          >
            {/* Top gradient line */}
            <div
              className="h-px w-full"
              style={{
                background:
                  "linear-gradient(90deg, transparent 0%, rgba(94,234,212,0.5) 30%, rgba(212,176,106,0.4) 70%, transparent 100%)",
              }}
              aria-hidden="true"
            />

            <div className="px-8 py-10">
              <p className="kicker mb-4">Account ready</p>

              <h1
                className="mb-3 font-sora font-bold text-ink"
                style={{ fontSize: "var(--step-3)" }}
              >
                Register your masjid
              </h1>

              <p className="mb-8 text-step--1 text-ink-muted leading-relaxed">
                Your operator account is set up. The masjid registration form is
                coming in{" "}
                <span className="font-semibold text-mint">MB-008</span> —
                check back soon to connect your masjid and go live.
              </p>

              {/* Coming-soon pill */}
              <div
                className="inline-flex items-center gap-2 rounded-full border border-mint/20 bg-mint/[0.07] px-4 py-2 text-step--1 font-medium text-mint-dim"
              >
                <span
                  className="h-1.5 w-1.5 rounded-full bg-mint/60 animate-pulse"
                  aria-hidden="true"
                />
                Masjid registration — MB-008
              </div>
            </div>
          </div>

          <Link
            to="/"
            className="mt-6 inline-flex items-center gap-1.5 text-step--1 text-ink-muted hover:text-mint transition-colors duration-150 focus:outline-none focus-visible:ring-2 focus-visible:ring-mint rounded-sm"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 20 20"
              fill="currentColor"
              className="h-3.5 w-3.5"
              aria-hidden="true"
            >
              <path
                fillRule="evenodd"
                d="M17 10a.75.75 0 01-.75.75H5.612l4.158 3.96a.75.75 0 11-1.04 1.08l-5.5-5.25a.75.75 0 010-1.08l5.5-5.25a.75.75 0 111.04 1.08L5.612 9.25H16.25A.75.75 0 0117 10z"
                clipRule="evenodd"
              />
            </svg>
            Back to directory
          </Link>
        </motion.div>
      </div>
    </div>
  );
}
