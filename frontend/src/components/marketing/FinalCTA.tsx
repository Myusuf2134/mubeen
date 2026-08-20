import { motion } from "framer-motion";

export function FinalCTA() {
  return (
    <section className="py-24 px-5 bg-[#F7F3E9]">
      <div className="max-w-4xl mx-auto text-center">
        {/* Logo */}
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          whileInView={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.6 }}
          viewport={{ once: true, margin: "-200px" }}
          className="mb-8 flex justify-center"
        >
          <div className="h-16 w-16 rounded-xl bg-gradient-to-br from-[#153D35] to-[#285C50] flex items-center justify-center text-white font-bold text-3xl shadow-lg">
            M
          </div>
        </motion.div>

        {/* Headline */}
        <motion.h2
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
          viewport={{ once: true, margin: "-200px" }}
          className="text-5xl md:text-6xl font-bold text-[#173A33] mb-6"
        >
          This is Mubeen
        </motion.h2>

        {/* Subtitle */}
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          viewport={{ once: true, margin: "-200px" }}
          className="text-xl text-[#6E7D78] mb-12 max-w-2xl mx-auto leading-relaxed"
        >
          A new way for masjids to communicate, operate, and make every khutbah accessible to everyone.
        </motion.p>

        {/* CTAs */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.3 }}
          viewport={{ once: true, margin: "-200px" }}
          className="flex flex-col sm:flex-row gap-4 justify-center"
        >
          <motion.button
            whileHover={{ scale: 1.04, boxShadow: "0 20px 40px rgba(21, 61, 53, 0.2)" }}
            whileTap={{ scale: 0.96 }}
            className="px-8 py-4 bg-gradient-to-r from-[#153D35] to-[#285C50] text-white font-semibold rounded-full shadow-lg"
          >
            Request a Demo
          </motion.button>
          <motion.button
            whileHover={{ scale: 1.04 }}
            whileTap={{ scale: 0.96 }}
            className="px-8 py-4 border-2 border-[#153D35] text-[#153D35] font-semibold rounded-full hover:bg-[#153D35]/5 transition-colors"
          >
            Explore Mubeen
          </motion.button>
        </motion.div>
      </div>
    </section>
  );
}
