import { useState, useEffect } from "react";
import { motion } from "framer-motion";

export function Navbar() {
  const [isScrolled, setIsScrolled] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <motion.nav
      className="fixed top-0 left-0 right-0 z-50 px-5 py-4"
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <div
        className={`max-w-7xl mx-auto px-5 py-4 rounded-2xl transition-all duration-300 ${
          isScrolled
            ? "bg-white/80 dark:bg-[#1a2633]/80 backdrop-blur-xl border border-black/5 dark:border-white/5 shadow-sm"
            : "bg-transparent"
        }`}
      >
        <div className="flex items-center justify-between">
          {/* Logo */}
          <motion.div
            className="flex items-center gap-2 cursor-pointer"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-[#153D35] to-[#285C50] flex items-center justify-center text-white font-bold text-sm">
              M
            </div>
            <span className="font-bold text-lg text-[#173A33]">Mubeen</span>
          </motion.div>

          {/* Desktop Menu */}
          <div className="hidden md:flex items-center gap-8">
            <motion.a href="#product" className="text-sm text-[#6E7D78] hover:text-[#173A33] transition-colors">
              Product
            </motion.a>
            <motion.a href="#features" className="text-sm text-[#6E7D78] hover:text-[#173A33] transition-colors">
              Features
            </motion.a>
            <motion.a href="#masjids" className="text-sm text-[#6E7D78] hover:text-[#173A33] transition-colors">
              For Masjids
            </motion.a>
            <motion.a href="#vision" className="text-sm text-[#6E7D78] hover:text-[#173A33] transition-colors">
              About
            </motion.a>
          </div>

          {/* CTA Buttons */}
          <div className="hidden md:flex items-center gap-3">
            <motion.button
              whileHover={{ scale: 1.04 }}
              whileTap={{ scale: 0.96 }}
              className="px-4 py-2 text-sm font-medium text-[#173A33] hover:text-[#153D35] transition-colors"
            >
              Sign In
            </motion.button>
            <motion.button
              whileHover={{ scale: 1.04 }}
              whileTap={{ scale: 0.96 }}
              className="px-5 py-2 text-sm font-medium bg-gradient-to-r from-[#153D35] to-[#285C50] text-white rounded-full shadow-lg hover:shadow-xl transition-shadow"
            >
              Request Demo
            </motion.button>
          </div>

          {/* Mobile Menu Button */}
          <motion.button
            className="md:hidden p-2 rounded-lg hover:bg-black/5"
            onClick={() => setMenuOpen(!menuOpen)}
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={menuOpen ? "M6 18L18 6M6 6l12 12" : "M4 6h16M4 12h16M4 18h16"} />
            </svg>
          </motion.button>
        </div>

        {/* Mobile Menu */}
        {menuOpen && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="md:hidden mt-4 pt-4 border-t border-black/5 space-y-3"
          >
            <a href="#product" className="block text-sm text-[#6E7D78] hover:text-[#173A33]">Product</a>
            <a href="#features" className="block text-sm text-[#6E7D78] hover:text-[#173A33]">Features</a>
            <a href="#masjids" className="block text-sm text-[#6E7D78] hover:text-[#173A33]">For Masjids</a>
            <a href="#vision" className="block text-sm text-[#6E7D78] hover:text-[#173A33]">About</a>
            <div className="flex gap-2 pt-2">
              <button className="flex-1 px-4 py-2 text-sm font-medium text-[#173A33] border border-[#153D35] rounded-full">
                Sign In
              </button>
              <button className="flex-1 px-4 py-2 text-sm font-medium bg-gradient-to-r from-[#153D35] to-[#285C50] text-white rounded-full">
                Request Demo
              </button>
            </div>
          </motion.div>
        )}
      </div>
    </motion.nav>
  );
}
