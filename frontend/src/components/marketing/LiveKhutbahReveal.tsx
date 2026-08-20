import { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";

function BookIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
      <path d="M5.5 5c1.4-0.9 3.2-0.9 4.5 0v10c-1.3-0.9-3.1-0.9-4.5 0zM14.5 5c-1.4-0.9-3.2-0.9-4.5 0v10c1.3-0.9 3.1-0.9 4.5 0z" stroke="#153D35" strokeWidth="1.3" strokeLinejoin="round" />
    </svg>
  );
}

export function LiveKhutbahReveal() {
  const [displayedArabic, setDisplayedArabic] = useState("");
  const [displayedEnglish, setDisplayedEnglish] = useState("");
  const [showReference, setShowReference] = useState(false);
  const [isAnimating, setIsAnimating] = useState(false);
  const [runId, setRunId] = useState(0);

  const arabicText = "الحمد لله رب العالمين";
  const englishText = "All praise belongs to Allah, Lord of all worlds.";

  const startAnimation = useCallback(() => {
    setDisplayedArabic("");
    setDisplayedEnglish("");
    setShowReference(false);
    setIsAnimating(true);

    let arabicIndex = 0;
    const arabicInterval = setInterval(() => {
      if (arabicIndex <= arabicText.length) {
        setDisplayedArabic(arabicText.substring(0, arabicIndex));
        arabicIndex++;
      } else {
        clearInterval(arabicInterval);
        let englishIndex = 0;
        const englishInterval = setInterval(() => {
          if (englishIndex <= englishText.length) {
            setDisplayedEnglish(englishText.substring(0, englishIndex));
            englishIndex++;
          } else {
            clearInterval(englishInterval);
            setTimeout(() => setShowReference(true), 500);
          }
        }, 20);
      }
    }, 30);

    setTimeout(() => setIsAnimating(false), 5000);
  }, []);

  useEffect(() => {
    startAnimation();
    const interval = setInterval(startAnimation, 8000);
    return () => clearInterval(interval);
  }, [startAnimation, runId]);

  return (
    <section id="product" className="py-24 px-5 bg-white">
      <div className="max-w-5xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          viewport={{ once: true, margin: "-200px" }}
          className="text-center mb-16"
        >
          <h2 className="text-5xl md:text-6xl font-bold text-[#173A33] mb-4">
            Understand the khutbah
            <br />
            <span className="text-[#153D35]">while it's happening.</span>
          </h2>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 40, scale: 0.95 }}
          whileInView={{ opacity: 1, y: 0, scale: 1 }}
          transition={{ duration: 0.7 }}
          viewport={{ once: true, margin: "-200px" }}
          className="relative"
        >
          <div className="rounded-3xl bg-gradient-to-br from-[#153D35]/5 to-[#285C50]/5 border border-[#153D35]/10 overflow-hidden backdrop-blur-sm shadow-2xl">
            <div className="bg-gradient-to-b from-white to-[#FFFDF8] border-b border-black/5 px-6 py-4 flex items-center gap-3">
              <div className="flex gap-2">
                <div className="w-3 h-3 rounded-full bg-red-400" />
                <div className="w-3 h-3 rounded-full bg-yellow-400" />
                <div className="w-3 h-3 rounded-full bg-green-400" />
              </div>
              <div className="flex-1 mx-4">
                <div className="bg-black/5 rounded-full px-4 py-2 text-xs text-[#6E7D78]">
                  mubeen.app/live
                </div>
              </div>
            </div>

            <div className="p-8 md:p-12 bg-gradient-to-br from-[#FFFDF8] to-white">
              <div className="mb-8 flex items-center gap-3">
                <motion.div
                  animate={{ scale: [1, 1.2, 1] }}
                  transition={{ duration: 2, repeat: Infinity }}
                  className="w-3 h-3 rounded-full bg-red-500"
                />
                <span className="text-sm font-semibold text-[#153D35]">LIVE — Friday Khutbah</span>
              </div>

              <div className="mb-8">
                <div className="text-3xl md:text-4xl font-semibold text-[#153D35] text-right leading-relaxed mb-3 font-amiri">
                  {displayedArabic}
                  {isAnimating && <span className="animate-pulse">|</span>}
                </div>
              </div>

              {displayedEnglish && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="mb-8 p-6 bg-[#F7F3E9] rounded-xl border border-[#C6A85A]/20"
                >
                  <p className="text-lg text-[#6E7D78]">
                    {displayedEnglish}
                    {isAnimating && <span className="animate-pulse">|</span>}
                  </p>
                </motion.div>
              )}

              {showReference && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="p-6 bg-gradient-to-r from-[#153D35]/5 to-[#285C50]/5 rounded-xl border border-[#153D35]/10"
                >
                  <div className="flex items-center gap-2 mb-3">
                    <BookIcon />
                    <span className="text-lg font-semibold text-[#153D35]">QUR'AN REFERENCE</span>
                  </div>
                  <h4 className="font-bold text-[#173A33] mb-2">Al-Fatiha (The Opening)</h4>
                  <p className="text-sm text-[#6E7D78]">Surah 1 · Ayah 2</p>
                </motion.div>
              )}

              <div className="mt-8 flex items-center justify-between text-sm text-[#6E7D78]">
                <div className="flex items-center gap-4">
                  <span>Available on TV • Mobile • Web</span>
                </div>
                <button
                  onClick={() => setRunId((r) => r + 1)}
                  className="px-4 py-2 bg-[#153D35] text-white rounded-lg text-xs font-semibold hover:bg-[#0f2620] transition-colors"
                >
                  Restart Demo
                </button>
              </div>
            </div>
          </div>

          <div className="absolute inset-0 rounded-3xl bg-gradient-to-r from-[#153D35]/10 to-[#C6A85A]/5 blur-3xl pointer-events-none -z-10" />
        </motion.div>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.3 }}
          viewport={{ once: true, margin: "-200px" }}
          className="text-center mt-12 text-[#6E7D78] max-w-2xl mx-auto"
        >
          The imam delivers the khutbah as usual. Mubeen transcribes Arabic in real time, translates to English, and surfaces relevant Qur'an and Hadith references. The congregation follows on their phones, the masjid displays, or their browsers.
        </motion.p>
        <p className="text-center text-xs text-[#6E7D78]/70 mt-2">Simulated demo — not a live broadcast.</p>
      </div>
    </section>
  );
}
