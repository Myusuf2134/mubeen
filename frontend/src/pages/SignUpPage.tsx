import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { signupApi, loginApi, AuthApiError } from "@/api/auth";
import { useAuth } from "@/context/AuthContext";

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
      className="mt-1.5 text-[11px] font-medium text-red-400"
    >
      {message}
    </motion.p>
  );
}

function validateEmail(v: string): string {
  if (!v.trim()) return "Email is required";
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v.trim())) return "Enter a valid email address";
  return "";
}

function validatePassword(v: string): string {
  if (!v) return "Password is required";
  if (v.length < 12) return "Password must be at least 12 characters";
  return "";
}

export function SignUpPage() {
  const navigate = useNavigate();
  const { storeToken } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
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
      await signupApi(email, password);
      const { access_token } = await loginApi(email, password);
      storeToken(access_token);
      navigate("/register-masjid", { replace: true });
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

  const inputBase =
    "w-full rounded-[14px] bg-white/[0.05] px-4 py-3 text-step--1 text-ink " +
    "placeholder-ink-muted transition-colors duration-150 " +
    "focus:outline-none focus:ring-1";

  return (
    <div className="relative min-h-screen flex items-center justify-center px-5 py-12">

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

      {/* Dot grid texture */}
      <div className="pointer-events-none fixed inset-0 dot-grid opacity-30" aria-hidden="true" />

      {/* Card */}
      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
        className="relative w-full max-w-[440px]"
      >
        <div
          className="glass rounded-card-xl overflow-hidden"
          style={{ borderColor: "rgba(94,234,212,0.12)" }}
        >
          {/* Top gradient accent line */}
          <div
            className="h-px w-full"
            style={{
              background:
                "linear-gradient(90deg, transparent 0%, rgba(94,234,212,0.5) 30%, rgba(212,176,106,0.4) 70%, transparent 100%)",
            }}
            aria-hidden="true"
          />

          <div className="px-8 py-9">
            {/* Brand lockup */}
            <div className="mb-8 flex flex-col items-center text-center">
              <div className="mb-3 flex items-center gap-3">
                <div
                  className="flex h-11 w-11 items-center justify-center rounded-icon font-sora text-xl font-black"
                  style={{
                    background: "linear-gradient(135deg, #5eead4 0%, #0d9488 100%)",
                    color: "#06120f",
                    boxShadow:
                      "0 0 28px rgba(94,234,212,0.25), 0 4px 12px rgba(0,0,0,0.4)",
                  }}
                  aria-hidden="true"
                >
                  M
                </div>
                <span
                  className="font-sora font-black heading-shimmer"
                  style={{ fontSize: "var(--step-3)" }}
                >
                  Mubeen
                </span>
              </div>
              <p className="kicker">Operator Portal</p>
            </div>

            <h1
              className="mb-1 font-sora font-bold text-ink"
              style={{ fontSize: "var(--step-2)" }}
            >
              Create your account
            </h1>
            <p className="mb-7 text-step--1 text-ink-muted">
              Set up your operator account — no masjid required yet.
            </p>

            <form onSubmit={handleSubmit} noValidate>
              {/* Email */}
              <div className="mb-5">
                <label
                  htmlFor="signup-email"
                  className="mb-1.5 block text-step--1 font-medium text-ink-dim"
                >
                  Email
                </label>
                <input
                  id="signup-email"
                  type="email"
                  autoComplete="email"
                  value={email}
                  onChange={(e) => {
                    setEmail(e.target.value);
                    if (emailError) setEmailError("");
                    if (formError) setFormError("");
                  }}
                  onBlur={() => { if (email) setEmailError(validateEmail(email)); }}
                  placeholder="imam@masjid.com"
                  className={
                    inputBase +
                    (emailError
                      ? " border border-red-400/60 focus:border-red-400/80 focus:ring-red-400/20"
                      : " border border-white/10 focus:border-mint/50 focus:ring-mint/20")
                  }
                  aria-invalid={emailError ? "true" : "false"}
                  aria-describedby={emailError ? "signup-email-error" : undefined}
                />
                <AnimatePresence>
                  {emailError && (
                    <span id="signup-email-error">
                      <FieldError message={emailError} />
                    </span>
                  )}
                </AnimatePresence>
              </div>

              {/* Password */}
              <div className="mb-6">
                <label
                  htmlFor="signup-password"
                  className="mb-1.5 block text-step--1 font-medium text-ink-dim"
                >
                  Password
                </label>
                <div className="relative">
                  <input
                    id="signup-password"
                    type={showPassword ? "text" : "password"}
                    autoComplete="new-password"
                    value={password}
                    onChange={(e) => {
                      setPassword(e.target.value);
                      if (passwordError) setPasswordError("");
                      if (formError) setFormError("");
                    }}
                    onBlur={() => { if (password) setPasswordError(validatePassword(password)); }}
                    placeholder="12+ characters"
                    className={
                      inputBase +
                      " pr-11" +
                      (passwordError
                        ? " border border-red-400/60 focus:border-red-400/80 focus:ring-red-400/20"
                        : " border border-white/10 focus:border-mint/50 focus:ring-mint/20")
                    }
                    aria-invalid={passwordError ? "true" : "false"}
                    aria-describedby={
                      passwordError ? "signup-password-error" : "signup-password-hint"
                    }
                  />
                  <button
                    type="button"
                    onClick={() => { setShowPassword((v) => !v); }}
                    aria-label={showPassword ? "Hide password" : "Show password"}
                    className="absolute right-3.5 top-1/2 -translate-y-1/2 text-ink-muted hover:text-ink-dim transition-colors duration-150 focus:outline-none focus-visible:ring-2 focus-visible:ring-mint rounded-sm"
                  >
                    <EyeIcon open={showPassword} />
                  </button>
                </div>
                <AnimatePresence>
                  {passwordError ? (
                    <span id="signup-password-error">
                      <FieldError message={passwordError} />
                    </span>
                  ) : (
                    <p id="signup-password-hint" className="mt-1.5 text-[11px] text-ink-muted">
                      Minimum 12 characters
                    </p>
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
                    className="mb-5 flex items-start gap-2.5 rounded-[12px] bg-red-400/10 border border-red-400/25 px-3.5 py-3"
                  >
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 20 20"
                      fill="currentColor"
                      className="mt-0.5 h-4 w-4 flex-shrink-0 text-red-400"
                      aria-hidden="true"
                    >
                      <path
                        fillRule="evenodd"
                        d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-5a.75.75 0 01.75.75v4.5a.75.75 0 01-1.5 0v-4.5A.75.75 0 0110 5zm0 10a1 1 0 100-2 1 1 0 000 2z"
                        clipRule="evenodd"
                      />
                    </svg>
                    <p className="text-[13px] text-red-300">{formError}</p>
                  </motion.div>
                )}
              </AnimatePresence>

              <button
                type="submit"
                disabled={loading}
                className="btn-primary w-full justify-center py-3 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <>
                    <svg
                      className="h-4 w-4 animate-spin"
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
                    Creating account…
                  </>
                ) : (
                  "Create account"
                )}
              </button>
            </form>

            <p className="mt-6 text-center text-step--1 text-ink-muted">
              Already have an account?{" "}
              <Link
                to="/login"
                className="font-semibold text-mint hover:text-mint-dim transition-colors duration-150 focus:outline-none focus-visible:underline"
              >
                Sign in →
              </Link>
            </p>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
