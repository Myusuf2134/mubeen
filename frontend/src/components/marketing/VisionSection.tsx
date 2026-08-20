import { motion } from "framer-motion";

export function VisionSection() {
  return (
    <section id="vision" className="py-32 px-5 bg-gradient-to-b from-[#0f1419] to-[#153D35] relative overflow-hidden">
      {/* Aurora-like background effect */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <motion.div
          animate={{ opacity: [0.3, 0.6, 0.3] }}
          transition={{ duration: 8, repeat: Infinity }}
          className="absolute top-0 left-1/4 w-96 h-96 bg-gradient-radial from-[#153D35]/30 to-transparent blur-3xl rounded-full"
        />
        <motion.div
          animate={{ opacity: [0.2, 0.5, 0.2] }}
          transition={{ duration: 10, repeat: Infinity, delay: 2 }}
          className="absolute bottom-0 right-1/4 w-96 h-96 bg-gradient-radial from-[#C6A85A]/20 to-transparent blur-3xl rounded-full"
        />
      </div>

      <div className="relative max-w-4xl mx-auto text-center">
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7 }}
          viewport={{ once: true, margin: "-200px" }}
        >
          {/* Main vision */}
          <h2 className="text-6xl md:text-7xl font-bold text-white mb-8 leading-tight">
            One masjid.
            <br />
            Every screen.
            <br />
            Every language.
            <br />
            <span className="text-[#C6A85A]">One Mubeen.</span>
          </h2>

          {/* Supporting text */}
          <motion.p
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            transition={{ duration: 0.7, delay: 0.2 }}
            viewport={{ once: true }}
            className="text-xl text-white/80 max-w-2xl mx-auto mb-12"
          >
            A connected digital experience that brings masjids into the modern era—making every khutbah accessible, every community member connected, and every congregation served.
          </motion.p>

          {/* CTA */}
          <motion.button
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            viewport={{ once: true }}
            whileHover={{ scale: 1.04, boxShadow: "0 20px 40px rgba(198, 168, 90, 0.3)" }}
            whileTap={{ scale: 0.96 }}
            className="px-8 py-4 bg-[#C6A85A] text-[#0f1419] font-semibold rounded-full"
          >
            Learn More About Our Vision
          </motion.button>
        </motion.div>
      </div>
    </section>
  );
}
