import { useRef, useEffect, useState } from "react";
import { motion } from "framer-motion";

function MosqueScene() {
  return (
    <svg viewBox="0 0 800 450" className="w-full h-full" preserveAspectRatio="xMidYMax slice" aria-hidden="true">
      <defs>
        <linearGradient id="hero-sky" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#153D35" stopOpacity="0.08" />
          <stop offset="100%" stopColor="#285C50" stopOpacity="0.14" />
        </linearGradient>
      </defs>
      <rect width="800" height="450" fill="url(#hero-sky)" />
      {/* main arch */}
      <path
        d="M250 450V300C250 220 320 180 400 180C480 180 550 220 550 300V450"
        fill="none"
        stroke="#153D35"
        strokeOpacity="0.35"
        strokeWidth="2"
      />
      {/* dome */}
      <path
        d="M370 180C370 140 385 110 400 100C415 110 430 140 430 180Z"
        fill="none"
        stroke="#153D35"
        strokeOpacity="0.35"
        strokeWidth="2"
      />
      <line x1="400" y1="100" x2="400" y2="75" stroke="#C6A85A" strokeOpacity="0.6" strokeWidth="2" />
      <circle cx="400" cy="70" r="4" fill="#C6A85A" fillOpacity="0.6" />
      {/* side minarets */}
      <rect x="150" y="240" width="10" height="210" fill="none" stroke="#153D35" strokeOpacity="0.25" strokeWidth="1.6" />
      <path d="M145 240l10-24 10 24Z" fill="none" stroke="#153D35" strokeOpacity="0.25" strokeWidth="1.6" />
      <rect x="640" y="240" width="10" height="210" fill="none" stroke="#153D35" strokeOpacity="0.25" strokeWidth="1.6" />
      <path d="M635 240l10-24 10 24Z" fill="none" stroke="#153D35" strokeOpacity="0.25" strokeWidth="1.6" />
      {/* small arches row */}
      {[300, 400, 500].map((cx) => (
        <path
          key={cx}
          d={`M${cx - 26} 450V400C${cx - 26} 380 ${cx - 14} 370 ${cx} 370C${cx + 14} 370 ${cx + 26} 380 ${cx + 26} 400V450`}
          fill="none"
          stroke="#C6A85A"
          strokeOpacity="0.4"
          strokeWidth="1.4"
        />
      ))}
    </svg>
  );
}

export function Hero() {
  const containerRef = useRef<HTMLDivElement>(null);
  const [scrollProgress, setScrollProgress] = useState(0);

  useEffect(() => {
    const handleScroll = () => {
      if (!containerRef.current) return;
      const rect = containerRef.current.getBoundingClientRect();
      const progress = Math.max(0, Math.min(1, 1 - rect.top / window.innerHeight));
      setScrollProgress(progress);
    };

    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const imageScale = 1 + scrollProgress * 0.5;

  return (
    <section ref={containerRef} className="relative min-h-screen pt-24 pb-32 px-5 overflow-hidden bg-white">
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 rounded-full bg-gradient-radial from-[#153D35]/5 to-transparent blur-3xl" />
        <div className="absolute -bottom-40 -left-40 w-80 h-80 rounded-full bg-gradient-radial from-[#C6A85A]/3 to-transparent blur-3xl" />
      </div>

      <div className="relative max-w-6xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: "easeOut" }}
          className="text-center mb-12"
        >
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="inline-flex items-center gap-2 mb-6 px-4 py-2 rounded-full bg-[#153D35]/5 border border-[#153D35]/10"
          >
            <span className="w-2 h-2 rounded-full bg-[#153D35] animate-pulse" />
            <span className="text-sm font-medium text-[#153D35]">Introducing Mubeen</span>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.15 }}
            className="text-5xl md:text-7xl font-bold leading-tight mb-6 text-[#173A33]"
          >
            The Khutbah
            <br />
            <span className="bg-gradient-to-r from-[#153D35] to-[#285C50] bg-clip-text text-transparent">
              Should Reach Everyone
            </span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.25 }}
            className="text-lg md:text-xl text-[#6E7D78] max-w-2xl mx-auto mb-8"
          >
            Mubeen helps masjids make khutbahs accessible through live Arabic transcription, real-time translation, intelligent Islamic references, and connected digital experiences.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.3 }}
            className="flex flex-col md:flex-row gap-4 justify-center mb-12"
          >
            <motion.button
              whileHover={{ scale: 1.04, boxShadow: "0 20px 40px rgba(21, 61, 53, 0.2)" }}
              whileTap={{ scale: 0.96 }}
              className="px-8 py-3 bg-gradient-to-r from-[#153D35] to-[#285C50] text-white font-semibold rounded-full"
            >
              Explore Mubeen
            </motion.button>
            <motion.button
              whileHover={{ scale: 1.04 }}
              whileTap={{ scale: 0.96 }}
              className="px-8 py-3 border-2 border-[#153D35] text-[#153D35] font-semibold rounded-full hover:bg-[#153D35]/5 transition-colors"
            >
              Request a Demo
            </motion.button>
          </motion.div>

          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.8, delay: 0.4 }}
            className="text-sm text-[#6E7D78]"
          >
            Built for masjids. <br className="hidden sm:block" /> Designed for the communities they serve.
          </motion.p>
        </motion.div>

        <motion.div
          style={{
            scale: imageScale,
            opacity: Math.max(0.6, 1 - scrollProgress * 0.4),
          }}
          className="mt-16 relative"
        >
          <div className="aspect-video rounded-3xl bg-gradient-to-br from-[#153D35]/[0.03] to-[#285C50]/[0.02] border border-[#153D35]/10 overflow-hidden">
            <MosqueScene />
          </div>
        </motion.div>
      </div>
    </section>
  );
}
