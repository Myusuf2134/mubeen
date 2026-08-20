import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { loginApi, AuthApiError } from "@/api/auth";
import { useAuth } from "@/context/AuthContext";
import { MubeenLogo } from "@/components/MubeenLogo";

function EyeIcon({ open }: { open: boolean }) {
  return open ? (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.5}
      className="h-4 w-4"
      aria-hidden="true"
    >
      <path strokeLinecap="round" strokeLinejoin="round"
        d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
      <path strokeLinecap="round" strokeLinejoin="round"
        d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
    </svg>
  ) : (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.5}
      className="h-4 w-4"
      aria-hidden="true"
    >
      <path strokeLinecap="round" strokeLinejoin="round"
        d="M3.98 8.223A10.477 10.477 0 001.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 10-4.243-4.243m4.242 4.242L9.88 9.88" />
    </svg>
  );
}

function FieldError({ message }: { message: string }) {
  return (
    <motion.p
      role="alert"
      initial={{ opacity: 0, y: -4 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.16 }}
      className="mt-1.5 text-xs font-medium text-red-500"
    >
      {message}
    </motion.p>
  );
}

function validateEmail(v: string): string {
  if (!v.trim()) return "Email is required";
  return "";
}

function validatePassword(v: string): string {
  if (!v) return "Password is required";
  return "";
}

export function LoginPage() {
  const navigate = useNavigate();
  const { storeToken } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [keepSignedIn, setKeepSignedIn] = useState(false);
  const [emailError, setEmailError] = useState("");
  const [passwordError, setPasswordError] = useState("");
  const [formError, setFormError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const ev = validateEmail(email);
    const pv = validatePassword(password);
    setEmailError(ev);
    setPasswordError(pv);
    setFormError("");
    if (ev || pv) return;

    setLoading(true);
    try {
      const { access_token } = await loginApi(email, password);
      storeToken(access_token);
      void navigate("/operator", { replace: true });
    } catch (err) {
      if (err instanceof AuthApiError) {
        if (err.field === "email") setEmailError(err.message);
        else if (err.field === "password") setPasswordError(err.message);
        else setFormError(err.message);
      } else {
        setFormError("Something went wrong. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex h-screen overflow-hidden">
      {/* LEFT PANEL — Warm cream background, branding, quote, gradient+pattern footer */}
      <div
        className="w-2/5 flex flex-col overflow-hidden"
        style={{ backgroundColor: "#e8dcc8" }}
      >
        {/* Top section: Logo, headline, quote */}
        <div className="flex-1 flex flex-col justify-start px-12 pt-12 pb-8 overflow-y-auto">
          {/* Logo + MUBEEN */}
          <div className="flex items-center gap-4 mb-12">
            <MubeenLogo size={56} />
            <span
              className="font-sora font-black"
              style={{ fontSize: "var(--step-2)", color: "#1a1a1a", letterSpacing: "-0.02em" }}
            >
              MUBEEN
            </span>
          </div>

          {/* Headline — serif */}
          <h1
            className="font-amiri font-bold mb-8 leading-tight"
            style={{ fontSize: "var(--step-3)", color: "#1a1a1a", maxWidth: "320px" }}
          >
            Connecting communities through technology.
          </h1>

          {/* Gold diamond divider */}
          <div className="mb-8">
            <div className="text-2xl" style={{ color: "#d4a574" }}>◆</div>
          </div>

          {/* Quote */}
          <blockquote
            className="font-amiri italic text-sm leading-relaxed"
            style={{ color: "#4a4a4a", maxWidth: "300px" }}
          >
            <p className="mb-2">
              "And cooperate in righteousness and piety."
            </p>
            <p style={{ fontSize: "var(--step--1)", opacity: 0.8 }}>
              — Quran 5:2
            </p>
          </blockquote>
        </div>

        {/* Bottom section: Gradient + Islamic pattern overlay */}
        <div
          className="relative h-2/5 flex-shrink-0 overflow-hidden"
          style={{
            background: "linear-gradient(180deg, #e8dcc8 0%, #c9a574 100%)",
          }}
        >
          {/* Islamic star pattern overlay — reuse from tv-display */}
          <svg
            aria-hidden="true"
            className="absolute inset-0 w-full h-full"
            viewBox="0 0 200 200"
            preserveAspectRatio="xMidYMid slice"
            style={{ opacity: 0.12 }}
          >
            <defs>
              <pattern id="login-islamic-stars" x="0" y="0" width="50" height="50" patternUnits="userSpaceOnUse">
                {/* 8-pointed star */}
                <path d="M25 5 L30 20 L45 25 L30 30 L25 45 L20 30 L5 25 L20 20 Z" fill="#1a1a1a" />
                {/* Inner diamond */}
                <path d="M25 25 L35 25 L25 35 L15 25 Z" fill="#1a1a1a" />
              </pattern>
            </defs>
            <rect width="200" height="200" fill="url(#login-islamic-stars)" />
          </svg>
        </div>
      </div>

      {/* RIGHT PANEL — White background, login form */}
      <div className="w-3/5 bg-white flex items-center justify-center px-12 overflow-y-auto">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
          className="w-full max-w-sm"
        >
          {/* Tab switcher — Sign in / Create account */}
          <div className="mb-10 flex items-center gap-2">
            <button
              type="button"
              disabled
              className="px-4 py-2 rounded-full font-medium transition-all duration-150"
              style={{
                fontSize: "var(--step--1)",
                color: "#ffffff",
                backgroundColor: "#2d8659",
                cursor: "default",
              }}
            >
              Sign in
            </button>
            <Link
              to="/signup"
              className="px-4 py-2 rounded-full font-medium transition-colors duration-150"
              style={{
                fontSize: "var(--step--1)",
                color: "#666666",
                backgroundColor: "transparent",
                border: "1px solid #e5e7eb",
              }}
            >
              Create account
            </Link>
          </div>

          {/* Welcome heading */}
          <h2
            className="font-amiri font-bold mb-2"
            style={{ fontSize: "var(--step-2)", color: "#1a1a1a" }}
          >
            Welcome back
          </h2>

          {/* Subheading */}
          <p
            className="mb-8 text-sm"
            style={{ color: "#666666" }}
          >
            Sign in to your Mubeen account
          </p>

          {/* Form */}
          <form onSubmit={(e) => { void handleSubmit(e); }} noValidate>
            {/* Email field */}
            <div className="mb-6">
              <label
                htmlFor="login-email"
                className="block mb-2 font-medium"
                style={{ fontSize: "var(--step--1)", color: "#1a1a1a" }}
              >
                Email
              </label>
              <input
                id="login-email"
                type="email"
                autoComplete="email"
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value);
                  if (emailError) setEmailError("");
                  if (formError) setFormError("");
                }}
                placeholder="you@example.com"
                className="w-full px-4 py-3 rounded-lg border transition-colors duration-150 focus:outline-none"
                style={{
                  borderColor: emailError ? "#ef4444" : "#d1d5db",
                  backgroundColor: "#ffffff",
                  color: "#1a1a1a",
                  fontSize: "var(--step--1)",
                }}
                aria-invalid={emailError ? "true" : "false"}
                aria-describedby={emailError ? "login-email-error" : undefined}
              />
              <AnimatePresence>
                {emailError && (
                  <span id="login-email-error">
                    <FieldError message={emailError} />
                  </span>
                )}
              </AnimatePresence>
            </div>

            {/* Password field */}
            <div className="mb-7">
              <div className="flex items-center justify-between mb-2">
                <label
                  htmlFor="login-password"
                  className="block font-medium"
                  style={{ fontSize: "var(--step--1)", color: "#1a1a1a" }}
                >
                  Password
                </label>
                <Link
                  to="/forgot-password"
                  className="text-xs font-medium transition-colors duration-150"
                  style={{ color: "#2d8659" }}
                >
                  Forgot?
                </Link>
              </div>
              <div className="relative">
                <input
                  id="login-password"
                  type={showPassword ? "text" : "password"}
                  autoComplete="current-password"
                  value={password}
                  onChange={(e) => {
                    setPassword(e.target.value);
                    if (passwordError) setPasswordError("");
                    if (formError) setFormError("");
                  }}
                  placeholder="Enter your password"
                  className="w-full px-4 py-3 rounded-lg border transition-colors duration-150 focus:outline-none"
                  style={{
                    borderColor: passwordError ? "#ef4444" : "#d1d5db",
                    backgroundColor: "#ffffff",
                    color: "#1a1a1a",
                    fontSize: "var(--step--1)",
                    paddingRight: "2.5rem",
                  }}
                  aria-invalid={passwordError ? "true" : "false"}
                  aria-describedby={passwordError ? "login-password-error" : undefined}
                />
                <button
                  type="button"
                  onClick={() => { setShowPassword((v) => !v); }}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700 transition-colors focus:outline-none"
                >
                  <EyeIcon open={showPassword} />
                </button>
              </div>
              <AnimatePresence>
                {passwordError && (
                  <span id="login-password-error">
                    <FieldError message={passwordError} />
                  </span>
                )}
              </AnimatePresence>
            </div>

            {/* Form-level error */}
            <AnimatePresence>
              {formError && (
                <motion.div
                  role="alert"
                  initial={{ opacity: 0, y: -6 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.18 }}
                  className="mb-5 flex items-start gap-2.5 rounded-lg px-3.5 py-3"
                  style={{
                    backgroundColor: "rgba(239, 68, 68, 0.1)",
                    border: "1px solid rgba(239, 68, 68, 0.3)",
                  }}
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 20 20"
                    fill="currentColor"
                    className="mt-0.5 h-4 w-4 flex-shrink-0"
                    aria-hidden="true"
                    style={{ color: "#ef4444" }}
                  >
                    <path
                      fillRule="evenodd"
                      d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-5a.75.75 0 01.75.75v4.5a.75.75 0 01-1.5 0v-4.5A.75.75 0 0110 5zm0 10a1 1 0 100-2 1 1 0 000 2z"
                      clipRule="evenodd"
                    />
                  </svg>
                  <p className="text-xs font-medium" style={{ color: "#ef4444" }}>{formError}</p>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Keep me signed in — Checkbox */}
            <div className="mb-7 flex items-center gap-2.5">
              <input
                id="login-keep-signed-in"
                type="checkbox"
                checked={keepSignedIn}
                onChange={(e) => setKeepSignedIn(e.target.checked)}
                className="w-4 h-4 rounded"
                style={{
                  borderColor: "#d1d5db",
                  cursor: "pointer",
                  accentColor: "#2d8659",
                }}
                aria-label="Keep me signed in"
              />
              <label
                htmlFor="login-keep-signed-in"
                className="text-sm font-medium transition-colors duration-150 cursor-pointer"
                style={{ color: "#666666" }}
              >
                Keep me signed in
              </label>
            </div>

            {/* Sign In button — Dark green */}
            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 rounded-lg font-semibold text-center text-white transition-all duration-150 disabled:opacity-50 disabled:cursor-not-allowed"
              style={{
                backgroundColor: "#2d8659",
              }}
              onMouseEnter={(e) => !loading && (e.currentTarget.style.backgroundColor = "#1f5c3f")}
              onMouseLeave={(e) => !loading && (e.currentTarget.style.backgroundColor = "#2d8659")}
            >
              {loading ? (
                <>
                  <svg
                    className="inline-block h-4 w-4 animate-spin mr-2"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                    aria-hidden="true"
                  >
                    <circle
                      className="opacity-25"
                      cx="12" cy="12" r="10"
                      stroke="currentColor" strokeWidth="4"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                    />
                  </svg>
                  Signing in…
                </>
              ) : (
                "Sign In"
              )}
            </button>
          </form>

          {/* Divider */}
          <div className="flex items-center my-6">
            <div className="flex-1 h-px" style={{ backgroundColor: "#e5e7eb" }} />
            <span className="px-3 text-xs" style={{ color: "#999999" }}>or continue with</span>
            <div className="flex-1 h-px" style={{ backgroundColor: "#e5e7eb" }} />
          </div>

          {/* OAuth buttons (NOT included — not implemented in backend) */}

          {/* Sign up link */}
          <p className="text-center text-sm" style={{ color: "#666666" }}>
            Don&apos;t have an account?{" "}
            <Link
              to="/signup"
              className="font-semibold transition-colors duration-150 focus:outline-none focus-visible:underline"
              style={{ color: "#2d8659" }}
            >
              Sign up
            </Link>
          </p>
        </motion.div>
      </div>
    </div>
  );
}
