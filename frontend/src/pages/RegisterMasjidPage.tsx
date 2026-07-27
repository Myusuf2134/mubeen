import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import { useAuth } from "@/context/AuthContext";
import { MasjidApiError, registerMasjidApi } from "@/api/masjids";

// ── Constants ─────────────────────────────────────────────────────────────────

const CALC_METHODS = [
  { value: "ISNA",                    label: "ISNA — North America" },
  { value: "MWL",                     label: "Muslim World League" },
  { value: "UMM_AL_QURA",            label: "Umm al-Qura (Makkah)" },
  { value: "EGYPT",                   label: "Egyptian General Authority" },
  { value: "KARACHI",                 label: "Karachi — Univ. of Islamic Sciences" },
  { value: "DUBAI",                   label: "Dubai" },
  { value: "KUWAIT",                  label: "Kuwait" },
  { value: "QATAR",                   label: "Qatar" },
  { value: "SINGAPORE",               label: "Singapore" },
  { value: "MOON_SIGHTING_COMMITTEE", label: "Moon Sighting Committee" },
];

const TZ_GROUPS: Array<{ group: string; zones: Array<{ value: string; label: string }> }> = [
  {
    group: "United States",
    zones: [
      { value: "America/New_York",             label: "Eastern Time (ET)" },
      { value: "America/Chicago",              label: "Central Time (CT)" },
      { value: "America/Denver",               label: "Mountain Time (MT)" },
      { value: "America/Los_Angeles",          label: "Pacific Time (PT)" },
      { value: "America/Phoenix",              label: "Arizona (no DST)" },
      { value: "America/Anchorage",            label: "Alaska (AKT)" },
      { value: "Pacific/Honolulu",             label: "Hawaii (HST)" },
      { value: "America/Indiana/Indianapolis", label: "Indiana — Eastern" },
    ],
  },
  {
    group: "Canada",
    zones: [
      { value: "America/Toronto",   label: "Toronto (Eastern)" },
      { value: "America/Winnipeg",  label: "Winnipeg (Central)" },
      { value: "America/Edmonton",  label: "Edmonton (Mountain)" },
      { value: "America/Vancouver", label: "Vancouver (Pacific)" },
      { value: "America/Halifax",   label: "Halifax (Atlantic)" },
    ],
  },
  {
    group: "Europe",
    zones: [
      { value: "Europe/London",    label: "London (GMT/BST)" },
      { value: "Europe/Paris",     label: "Paris (CET/CEST)" },
      { value: "Europe/Amsterdam", label: "Amsterdam (CET)" },
      { value: "Europe/Berlin",    label: "Berlin (CET)" },
      { value: "Europe/Stockholm", label: "Stockholm (CET)" },
      { value: "Europe/Rome",      label: "Rome (CET)" },
      { value: "Europe/Madrid",    label: "Madrid (CET)" },
      { value: "Europe/Istanbul",  label: "Istanbul (TRT)" },
      { value: "Europe/Helsinki",  label: "Helsinki (EET)" },
    ],
  },
  {
    group: "Middle East",
    zones: [
      { value: "Asia/Dubai",     label: "Dubai (GST)" },
      { value: "Asia/Riyadh",    label: "Riyadh (AST)" },
      { value: "Asia/Kuwait",    label: "Kuwait (AST)" },
      { value: "Asia/Qatar",     label: "Qatar (AST)" },
      { value: "Asia/Bahrain",   label: "Bahrain (AST)" },
      { value: "Asia/Muscat",    label: "Muscat (GST)" },
      { value: "Asia/Beirut",    label: "Beirut (EET)" },
      { value: "Asia/Amman",     label: "Amman (EET)" },
      { value: "Asia/Jerusalem", label: "Jerusalem" },
      { value: "Asia/Baghdad",   label: "Baghdad (+3)" },
      { value: "Asia/Tehran",    label: "Tehran (IRST)" },
    ],
  },
  {
    group: "South & Southeast Asia",
    zones: [
      { value: "Asia/Karachi",      label: "Karachi (PKT)" },
      { value: "Asia/Kabul",        label: "Kabul (AFT)" },
      { value: "Asia/Kolkata",      label: "Kolkata / Mumbai (IST)" },
      { value: "Asia/Dhaka",        label: "Dhaka (BST)" },
      { value: "Asia/Colombo",      label: "Colombo (IST)" },
      { value: "Asia/Kuala_Lumpur", label: "Kuala Lumpur (MYT)" },
      { value: "Asia/Singapore",    label: "Singapore (SGT)" },
      { value: "Asia/Jakarta",      label: "Jakarta (WIB)" },
      { value: "Asia/Baku",         label: "Baku (AZT)" },
      { value: "Asia/Tashkent",     label: "Tashkent (UZT)" },
    ],
  },
  {
    group: "Africa",
    zones: [
      { value: "Africa/Cairo",      label: "Cairo (EET)" },
      { value: "Africa/Casablanca", label: "Casablanca (WET)" },
      { value: "Africa/Nairobi",    label: "Nairobi (EAT)" },
      { value: "Africa/Lagos",      label: "Lagos (WAT)" },
      { value: "Africa/Abidjan",    label: "Abidjan (GMT)" },
    ],
  },
  {
    group: "Australia & Pacific",
    zones: [
      { value: "Australia/Sydney",    label: "Sydney (AEST/AEDT)" },
      { value: "Australia/Melbourne", label: "Melbourne (AEST/AEDT)" },
      { value: "Australia/Brisbane",  label: "Brisbane (AEST)" },
      { value: "Australia/Adelaide",  label: "Adelaide (ACST/ACDT)" },
      { value: "Australia/Perth",     label: "Perth (AWST)" },
      { value: "Pacific/Auckland",    label: "Auckland (NZST/NZDT)" },
    ],
  },
];

const ALL_TZ_VALUES = new Set(TZ_GROUPS.flatMap((g) => g.zones.map((z) => z.value)));

const BROWSER_TZ = (() => {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone ?? "America/New_York";
  } catch {
    return "America/New_York";
  }
})();

// ── Helpers ───────────────────────────────────────────────────────────────────

function decodeJWTMasjidId(token: string): string | null {
  try {
    const b64url = token.split(".")[1] ?? "";
    const b64 = b64url.replace(/-/g, "+").replace(/_/g, "/");
    const padded = b64.padEnd(b64.length + ((4 - (b64.length % 4)) % 4), "=");
    const payload = JSON.parse(atob(padded)) as Record<string, unknown>;
    return typeof payload.masjid_id === "string" ? payload.masjid_id : null;
  } catch {
    return null;
  }
}

// ── Sub-components ────────────────────────────────────────────────────────────

function FieldError({ message, id }: { message: string; id?: string }) {
  return (
    <motion.p
      id={id}
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

function SectionDivider({ label }: { label: string }) {
  return (
    <div className="my-6 flex items-center gap-3" aria-hidden="true">
      <div className="h-px flex-1" style={{ background: "rgba(94,234,212,0.10)" }} />
      <span className="text-[10px] font-semibold uppercase tracking-caps text-mint/50">
        {label}
      </span>
      <div className="h-px flex-1" style={{ background: "rgba(94,234,212,0.10)" }} />
    </div>
  );
}

function SelectChevron() {
  return (
    <div className="pointer-events-none absolute inset-y-0 right-3.5 flex items-center">
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 20 20"
        fill="currentColor"
        className="h-4 w-4 text-ink-muted"
        aria-hidden="true"
      >
        <path
          fillRule="evenodd"
          d="M5.22 8.22a.75.75 0 011.06 0L10 11.94l3.72-3.72a.75.75 0 111.06 1.06l-4.25 4.25a.75.75 0 01-1.06 0L5.22 9.28a.75.75 0 010-1.06z"
          clipRule="evenodd"
        />
      </svg>
    </div>
  );
}

function Spinner({ className = "h-4 w-4" }: { className?: string }) {
  return (
    <svg
      className={`animate-spin ${className}`}
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
      aria-hidden="true"
    >
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
      />
    </svg>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

export function RegisterMasjidPage() {
  const { isAuthenticated, token, storeToken, clearToken } = useAuth();
  const navigate = useNavigate();

  // Auth guard + redirect if operator already has a masjid
  useEffect(() => {
    if (!isAuthenticated) {
      navigate("/login", { replace: true });
      return;
    }
    if (token) {
      const masjidId = decodeJWTMasjidId(token);
      if (masjidId) navigate(`/masjid/${masjidId}`, { replace: true });
    }
  }, [isAuthenticated, token, navigate]);

  // ── Form state ─────────────────────────────────────────────────────────────
  const [name, setName] = useState("");
  const [addressLine, setAddressLine] = useState("");
  const [city, setCity] = useState("");
  const [stateFld, setStateFld] = useState("");
  const [country, setCountry] = useState("US");
  const [lat, setLat] = useState("");
  const [lon, setLon] = useState("");
  const [calcMethod, setCalcMethod] = useState("ISNA");
  const [timezone, setTimezone] = useState(BROWSER_TZ);
  const [phone, setPhone] = useState("");
  const [website, setWebsite] = useState("");

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [formError, setFormError] = useState("");
  const [loading, setLoading] = useState(false);
  const [geoLoading, setGeoLoading] = useState(false);
  const [geoError, setGeoError] = useState("");

  function clearFieldError(field: string) {
    setErrors((prev) => {
      if (!prev[field]) return prev;
      const next = { ...prev };
      delete next[field];
      return next;
    });
  }

  function validate(): Record<string, string> {
    const e: Record<string, string> = {};
    if (!name.trim()) e.name = "Masjid name is required";
    if (!addressLine.trim()) e.address_line = "Street address is required";
    if (!city.trim()) e.city = "City is required";
    if (!stateFld.trim()) e.state = "State / region is required";
    const latNum = parseFloat(lat);
    if (!lat || isNaN(latNum) || latNum < -90 || latNum > 90)
      e.lat = "Enter a valid latitude (−90 to 90)";
    const lonNum = parseFloat(lon);
    if (!lon || isNaN(lonNum) || lonNum < -180 || lonNum > 180)
      e.lon = "Enter a valid longitude (−180 to 180)";
    if (!timezone) e.timezone = "Timezone is required";
    return e;
  }

  function handleUseMyLocation() {
    if (!navigator.geolocation) {
      setGeoError("Geolocation is not supported by your browser.");
      return;
    }
    setGeoLoading(true);
    setGeoError("");
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setLat(pos.coords.latitude.toFixed(6));
        setLon(pos.coords.longitude.toFixed(6));
        clearFieldError("lat");
        clearFieldError("lon");
        setGeoLoading(false);
      },
      () => {
        setGeoError("Location access denied — enter coordinates manually.");
        setGeoLoading(false);
      },
      { timeout: 8000 },
    );
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const errs = validate();
    setErrors(errs);
    setFormError("");
    if (Object.keys(errs).length > 0) return;

    setLoading(true);
    try {
      const data = await registerMasjidApi(
        {
          name: name.trim(),
          address_line: addressLine.trim(),
          city: city.trim(),
          state: stateFld.trim(),
          country: country.trim() || "US",
          lat: parseFloat(lat),
          lon: parseFloat(lon),
          calculation_method: calcMethod,
          timezone,
          phone: phone.trim() || undefined,
          website: website.trim() || undefined,
        },
        token!,
      );
      storeToken(data.access_token);
      navigate(`/masjid/${data.id}`, { replace: true });
    } catch (err) {
      if (err instanceof MasjidApiError) {
        if (err.field === "name") {
          setErrors((prev) => ({ ...prev, name: err.message }));
        } else if (err.field === "timezone") {
          setErrors((prev) => ({ ...prev, timezone: err.message }));
        } else {
          setFormError(err.message);
        }
      } else {
        setFormError("Something went wrong. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  }

  if (!isAuthenticated) return null;

  function handleSignOut() {
    clearToken();
    navigate("/login", { replace: true });
  }

  const inputBase =
    "w-full rounded-[14px] bg-white/[0.05] px-4 py-3 text-step--1 text-ink " +
    "placeholder-ink-muted transition-colors duration-150 " +
    "focus:outline-none focus:ring-1";
  const selectBase =
    "w-full rounded-[14px] bg-white/[0.05] px-4 py-3 pr-10 text-step--1 text-ink " +
    "transition-colors duration-150 appearance-none cursor-pointer " +
    "focus:outline-none focus:ring-1 [color-scheme:dark]";
  const normalBorder = " border border-white/10 focus:border-mint/50 focus:ring-mint/20";
  const errorBorder  = " border border-red-400/60 focus:border-red-400/80 focus:ring-red-400/20";

  const inputCls  = (f: string) => inputBase  + (errors[f] ? errorBorder : normalBorder);
  const selectCls = (f: string) => selectBase + (errors[f] ? errorBorder : normalBorder);

  const browserTzNotInList = !ALL_TZ_VALUES.has(BROWSER_TZ);

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

      {/* Nav */}
      <nav className="relative flex items-center justify-between px-6 py-4">
        <Link
          to="/"
          className="flex items-center gap-2.5 focus:outline-none focus-visible:ring-2 focus-visible:ring-mint rounded-sm"
        >
          <div
            className="flex h-8 w-8 items-center justify-center rounded-icon font-sora text-sm font-black"
            style={{ background: "linear-gradient(135deg, #5eead4 0%, #0d9488 100%)", color: "#06120f" }}
            aria-hidden="true"
          >
            M
          </div>
          <span className="font-sora font-bold text-step-0 text-ink tracking-sora">Mubeen</span>
        </Link>
        <button type="button" onClick={handleSignOut} className="btn-ghost text-[11px] px-4 py-2">
          Sign out
        </button>
      </nav>

      {/* Content */}
      <div className="relative flex flex-1 flex-col items-center px-5 py-8 pb-16">
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
          className="w-full max-w-[640px]"
        >
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

            <div className="px-8 py-9">
              {/* Header */}
              <p className="kicker mb-3">Step 2 of 2</p>
              <h1
                className="mb-2 font-sora font-bold text-ink"
                style={{ fontSize: "var(--step-3)" }}
              >
                Register your masjid
              </h1>
              <p className="mb-8 text-step--1 text-ink-muted leading-relaxed">
                Fill in the details below. You can update them any time from your dashboard.
              </p>

              <form onSubmit={handleSubmit} noValidate>

                {/* ── Identity ────────────────────────────────────────── */}

                <div className="mb-5">
                  <label htmlFor="rm-name" className="mb-1.5 block text-step--1 font-medium text-ink-dim">
                    Masjid name{" "}
                    <span className="text-red-400/70" aria-hidden="true">*</span>
                  </label>
                  <input
                    id="rm-name"
                    type="text"
                    autoComplete="organization"
                    value={name}
                    onChange={(e) => { setName(e.target.value); clearFieldError("name"); setFormError(""); }}
                    placeholder="Masjid Al-Huda"
                    className={inputCls("name")}
                    aria-invalid={errors.name ? "true" : "false"}
                    aria-describedby={errors.name ? "rm-name-err" : undefined}
                  />
                  <AnimatePresence>
                    {errors.name && <span id="rm-name-err"><FieldError message={errors.name} /></span>}
                  </AnimatePresence>
                </div>

                <div className="mb-5">
                  <label htmlFor="rm-addr" className="mb-1.5 block text-step--1 font-medium text-ink-dim">
                    Street address{" "}
                    <span className="text-red-400/70" aria-hidden="true">*</span>
                  </label>
                  <input
                    id="rm-addr"
                    type="text"
                    autoComplete="street-address"
                    value={addressLine}
                    onChange={(e) => { setAddressLine(e.target.value); clearFieldError("address_line"); }}
                    placeholder="789 Olentangy River Rd"
                    className={inputCls("address_line")}
                    aria-invalid={errors.address_line ? "true" : "false"}
                    aria-describedby={errors.address_line ? "rm-addr-err" : undefined}
                  />
                  <AnimatePresence>
                    {errors.address_line && <span id="rm-addr-err"><FieldError message={errors.address_line} /></span>}
                  </AnimatePresence>
                </div>

                {/* City + State */}
                <div className="mb-5 grid grid-cols-[1fr_1fr] gap-4">
                  <div>
                    <label htmlFor="rm-city" className="mb-1.5 block text-step--1 font-medium text-ink-dim">
                      City <span className="text-red-400/70" aria-hidden="true">*</span>
                    </label>
                    <input
                      id="rm-city"
                      type="text"
                      autoComplete="address-level2"
                      value={city}
                      onChange={(e) => { setCity(e.target.value); clearFieldError("city"); }}
                      placeholder="Columbus"
                      className={inputCls("city")}
                      aria-invalid={errors.city ? "true" : "false"}
                      aria-describedby={errors.city ? "rm-city-err" : undefined}
                    />
                    <AnimatePresence>
                      {errors.city && <span id="rm-city-err"><FieldError message={errors.city} /></span>}
                    </AnimatePresence>
                  </div>
                  <div>
                    <label htmlFor="rm-state" className="mb-1.5 block text-step--1 font-medium text-ink-dim">
                      State <span className="text-red-400/70" aria-hidden="true">*</span>
                    </label>
                    <input
                      id="rm-state"
                      type="text"
                      autoComplete="address-level1"
                      value={stateFld}
                      onChange={(e) => { setStateFld(e.target.value); clearFieldError("state"); }}
                      placeholder="OH"
                      className={inputCls("state")}
                      aria-invalid={errors.state ? "true" : "false"}
                      aria-describedby={errors.state ? "rm-state-err" : undefined}
                    />
                    <AnimatePresence>
                      {errors.state && <span id="rm-state-err"><FieldError message={errors.state} /></span>}
                    </AnimatePresence>
                  </div>
                </div>

                <div className="mb-5">
                  <label htmlFor="rm-country" className="mb-1.5 block text-step--1 font-medium text-ink-dim">
                    Country
                  </label>
                  <input
                    id="rm-country"
                    type="text"
                    autoComplete="country"
                    maxLength={2}
                    value={country}
                    onChange={(e) => setCountry(e.target.value.toUpperCase())}
                    placeholder="US"
                    className={inputBase + normalBorder + " uppercase max-w-[100px]"}
                  />
                  <p className="mt-1.5 text-[11px] text-ink-muted">ISO 3166-1 alpha-2 (e.g. US, CA, GB)</p>
                </div>

                {/* ── Location ─────────────────────────────────────────── */}
                <SectionDivider label="Location" />

                <div className="mb-3 grid grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="rm-lat" className="mb-1.5 block text-step--1 font-medium text-ink-dim">
                      Latitude <span className="text-red-400/70" aria-hidden="true">*</span>
                    </label>
                    <input
                      id="rm-lat"
                      type="number"
                      step="any"
                      min="-90"
                      max="90"
                      value={lat}
                      onChange={(e) => { setLat(e.target.value); clearFieldError("lat"); }}
                      placeholder="40.002"
                      className={inputCls("lat")}
                      aria-invalid={errors.lat ? "true" : "false"}
                      aria-describedby={errors.lat ? "rm-lat-err" : undefined}
                    />
                    <AnimatePresence>
                      {errors.lat && <span id="rm-lat-err"><FieldError message={errors.lat} /></span>}
                    </AnimatePresence>
                  </div>
                  <div>
                    <label htmlFor="rm-lon" className="mb-1.5 block text-step--1 font-medium text-ink-dim">
                      Longitude <span className="text-red-400/70" aria-hidden="true">*</span>
                    </label>
                    <input
                      id="rm-lon"
                      type="number"
                      step="any"
                      min="-180"
                      max="180"
                      value={lon}
                      onChange={(e) => { setLon(e.target.value); clearFieldError("lon"); }}
                      placeholder="-83.015"
                      className={inputCls("lon")}
                      aria-invalid={errors.lon ? "true" : "false"}
                      aria-describedby={errors.lon ? "rm-lon-err" : undefined}
                    />
                    <AnimatePresence>
                      {errors.lon && <span id="rm-lon-err"><FieldError message={errors.lon} /></span>}
                    </AnimatePresence>
                  </div>
                </div>

                {/* Geolocation helper */}
                <div className="mb-6 flex flex-wrap items-center gap-x-3 gap-y-1.5">
                  <button
                    type="button"
                    onClick={handleUseMyLocation}
                    disabled={geoLoading}
                    className="inline-flex items-center gap-1.5 rounded-full border border-white/10 bg-white/[0.04] px-3 py-1.5 text-[11px] font-medium text-ink-muted hover:border-mint/30 hover:text-mint-dim transition-colors duration-150 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus-visible:ring-2 focus-visible:ring-mint"
                  >
                    {geoLoading ? (
                      <><Spinner className="h-3 w-3" />Detecting…</>
                    ) : (
                      <>
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="h-3 w-3" aria-hidden="true">
                          <path fillRule="evenodd" d="M9.69 18.933l.003.001C9.89 19.02 10 19 10 19s.11.02.308-.066l.002-.001.006-.003.018-.008a5.741 5.741 0 00.281-.14c.186-.096.446-.24.757-.433.62-.384 1.445-.966 2.274-1.765C14.827 15.482 17 12.93 17 10a7 7 0 10-14 0c0 2.93 2.173 5.482 3.355 6.585.829.799 1.654 1.381 2.274 1.765.31.192.57.337.757.433a5.74 5.74 0 00.281.14l.018.008.006.003zM10 12a2 2 0 100-4 2 2 0 000 4z" clipRule="evenodd" />
                        </svg>
                        Use my location
                      </>
                    )}
                  </button>
                  <AnimatePresence mode="wait">
                    {geoError ? (
                      <motion.p key="geo-err" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="text-[11px] text-red-400">
                        {geoError}
                      </motion.p>
                    ) : (
                      <motion.p key="geo-hint" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="text-[11px] text-ink-muted">
                        Or find coordinates on <span className="text-ink-dim">maps.google.com</span> by right-clicking your masjid
                      </motion.p>
                    )}
                  </AnimatePresence>
                </div>

                {/* ── Prayer settings ──────────────────────────────────── */}
                <SectionDivider label="Prayer settings" />

                <div className="mb-6 grid grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="rm-calc" className="mb-1.5 block text-step--1 font-medium text-ink-dim">
                      Calculation method
                    </label>
                    <div className="relative">
                      <select
                        id="rm-calc"
                        value={calcMethod}
                        onChange={(e) => setCalcMethod(e.target.value)}
                        className={selectCls("calc_method")}
                      >
                        {CALC_METHODS.map((m) => (
                          <option key={m.value} value={m.value}>{m.label}</option>
                        ))}
                      </select>
                      <SelectChevron />
                    </div>
                  </div>

                  <div>
                    <label htmlFor="rm-tz" className="mb-1.5 block text-step--1 font-medium text-ink-dim">
                      Timezone <span className="text-red-400/70" aria-hidden="true">*</span>
                    </label>
                    <div className="relative">
                      <select
                        id="rm-tz"
                        value={timezone}
                        onChange={(e) => { setTimezone(e.target.value); clearFieldError("timezone"); }}
                        className={selectCls("timezone")}
                        aria-invalid={errors.timezone ? "true" : "false"}
                        aria-describedby={errors.timezone ? "rm-tz-err" : undefined}
                      >
                        {browserTzNotInList && (
                          <optgroup label="Auto-detected">
                            <option value={BROWSER_TZ}>{BROWSER_TZ}</option>
                          </optgroup>
                        )}
                        {TZ_GROUPS.map((grp) => (
                          <optgroup key={grp.group} label={grp.group}>
                            {grp.zones.map((z) => (
                              <option key={z.value} value={z.value}>{z.label}</option>
                            ))}
                          </optgroup>
                        ))}
                      </select>
                      <SelectChevron />
                    </div>
                    <AnimatePresence>
                      {errors.timezone && <span id="rm-tz-err"><FieldError message={errors.timezone} /></span>}
                    </AnimatePresence>
                  </div>
                </div>

                {/* ── Contact (optional) ───────────────────────────────── */}
                <SectionDivider label="Contact (optional)" />

                <div className="mb-5">
                  <label htmlFor="rm-phone" className="mb-1.5 block text-step--1 font-medium text-ink-dim">
                    Phone{" "}
                    <span className="font-normal text-ink-muted">(optional)</span>
                  </label>
                  <input
                    id="rm-phone"
                    type="tel"
                    autoComplete="tel"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    placeholder="+1 (614) 555-0100"
                    className={inputBase + normalBorder}
                  />
                </div>

                <div className="mb-7">
                  <label htmlFor="rm-website" className="mb-1.5 block text-step--1 font-medium text-ink-dim">
                    Website{" "}
                    <span className="font-normal text-ink-muted">(optional)</span>
                  </label>
                  <input
                    id="rm-website"
                    type="url"
                    autoComplete="url"
                    value={website}
                    onChange={(e) => setWebsite(e.target.value)}
                    placeholder="https://masjid-alhuda.org"
                    className={inputBase + normalBorder}
                  />
                </div>

                {/* Form-level error banner */}
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

                {/* Submit */}
                <button
                  type="submit"
                  disabled={loading}
                  className="btn-primary w-full justify-center py-3 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? (
                    <><Spinner />Registering…</>
                  ) : (
                    "Register masjid →"
                  )}
                </button>
              </form>
            </div>
          </div>

          {/* Back link */}
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
