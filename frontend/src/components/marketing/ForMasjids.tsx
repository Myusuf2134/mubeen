import { motion } from "framer-motion";

const benefits = [
  "Make khutbahs accessible to all congregants",
  "Create one digital home for your community",
  "Improve internal communication",
  "Modernize your displays and technology",
  "Reduce tool fragmentation and complexity",
  "Serve multilingual and international communities",
  "Give members a seamless digital experience",
];

export function ForMasjids() {
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: { staggerChildren: 0.1, delayChildren: 0.2 },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, x: -20 },
    visible: { opacity: 1, x: 0 },
  };

  return (
    <section id="masjids" className="py-24 px-5 bg-white">
      <div className="max-w-5xl mx-auto">
        {/* Heading */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          viewport={{ once: true, margin: "-200px" }}
          className="text-center mb-16"
        >
          <h2 className="text-5xl md:text-6xl font-bold text-[#173A33] mb-4">
            Bring Mubeen
            <br />
            <span className="text-[#153D35]">to your masjid</span>
          </h2>
          <p className="text-lg text-[#6E7D78] max-w-2xl mx-auto">
            Transform your masjid into a modern, connected community with Mubeen's complete platform.
          </p>
        </motion.div>

        {/* Benefits Grid */}
        <motion.div
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-200px" }}
          className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-12"
        >
          {benefits.map((benefit, index) => (
            <motion.div
              key={index}
              variants={itemVariants}
              className="flex items-start gap-4 p-6 rounded-xl hover:bg-[#F7F3E9] transition-colors"
            >
              <div className="flex-shrink-0">
                <div className="flex items-center justify-center h-6 w-6 rounded-full bg-gradient-to-r from-[#153D35] to-[#285C50]">
                  <svg className="h-4 w-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
              </div>
              <p className="text-[#173A33] font-medium">{benefit}</p>
            </motion.div>
          ))}
        </motion.div>

        {/* CTA Section */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.4 }}
          viewport={{ once: true, margin: "-200px" }}
          className="text-center"
        >
          <div className="inline-block p-12 rounded-3xl bg-gradient-to-br from-[#153D35]/5 to-[#285C50]/5 border border-[#153D35]/10">
            <h3 className="text-3xl font-bold text-[#173A33] mb-6">Ready to get started?</h3>
            <p className="text-[#6E7D78] mb-8 max-w-md mx-auto">
              Request a personalized demo and see how Mubeen can transform your masjid's digital experience.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <motion.button
                whileHover={{ scale: 1.04 }}
                whileTap={{ scale: 0.96 }}
                className="px-8 py-3 bg-gradient-to-r from-[#153D35] to-[#285C50] text-white font-semibold rounded-full"
              >
                Request a Demo
              </motion.button>
              <motion.button
                whileHover={{ scale: 1.04 }}
                whileTap={{ scale: 0.96 }}
                className="px-8 py-3 border-2 border-[#153D35] text-[#153D35] font-semibold rounded-full hover:bg-[#153D35]/5 transition-colors"
              >
                Explore the Platform
              </motion.button>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
