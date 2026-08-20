import { motion } from "framer-motion";

export function Problem() {
  const problems = [
    "Language barriers prevent millions from understanding the khutbah.",
    "Masjid technology lives in disconnected silos.",
    "Community information is scattered across multiple platforms.",
    "Limited accessibility for non-Arabic speakers and elderly members.",
  ];

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: { staggerChildren: 0.15, delayChildren: 0.2 },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0 },
  };

  return (
    <section className="py-24 px-5 bg-[#F7F3E9]">
      <div className="max-w-4xl mx-auto">
        {/* Heading */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          viewport={{ once: true, margin: "-200px" }}
          className="text-center mb-16"
        >
          <h2 className="text-5xl md:text-6xl font-bold text-[#173A33] mb-6">
            Millions hear
            <br />
            <span className="text-[#153D35]">the khutbah.</span>
            <br />
            <span className="text-[#6E7D78]">Not everyone understands it.</span>
          </h2>
        </motion.div>

        {/* Problems */}
        <motion.div
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-200px" }}
          className="space-y-6 mb-16"
        >
          {problems.map((problem, i) => (
            <motion.div
              key={i}
              variants={itemVariants}
              className="p-8 bg-white rounded-2xl border border-black/5 hover:border-[#153D35]/20 transition-colors"
            >
              <p className="text-lg text-[#6E7D78] leading-relaxed">{problem}</p>
            </motion.div>
          ))}
        </motion.div>

        {/* Solution intro */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.4 }}
          viewport={{ once: true, margin: "-200px" }}
          className="text-center"
        >
          <h3 className="text-4xl md:text-5xl font-bold text-[#173A33] mb-4">
            Mubeen
            <br />
            <span className="text-[#153D35]">changes that.</span>
          </h3>
        </motion.div>
      </div>
    </section>
  );
}
