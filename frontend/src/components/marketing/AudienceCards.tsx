import { motion } from "framer-motion";
import { useState } from "react";

function ImamIcon() {
  return (
    <svg width="36" height="36" viewBox="0 0 36 36" fill="none">
      <circle cx="18" cy="12" r="5" stroke="#153D35" strokeWidth="1.4" />
      <path d="M7 30c0-7 5-11 11-11s11 4 11 11" stroke="#153D35" strokeWidth="1.4" strokeLinecap="round" />
    </svg>
  );
}

function LeadershipIcon() {
  return (
    <svg width="36" height="36" viewBox="0 0 36 36" fill="none">
      <path d="M6 15l12-8 12 8" stroke="#153D35" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M9 15v13h18V15M15 28v-8h6v8" stroke="#153D35" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function CongregationIcon() {
  return (
    <svg width="36" height="36" viewBox="0 0 36 36" fill="none">
      <circle cx="13" cy="13" r="4" stroke="#153D35" strokeWidth="1.4" />
      <circle cx="24" cy="13" r="4" stroke="#153D35" strokeWidth="1.4" />
      <path d="M5 29c0-5.5 3.6-9 8-9s8 3.5 8 9M17 29c0-5.5 3.1-9 7-9s7 3.5 7 9" stroke="#153D35" strokeWidth="1.4" strokeLinecap="round" />
    </svg>
  );
}

function GlobalIcon() {
  return (
    <svg width="36" height="36" viewBox="0 0 36 36" fill="none">
      <circle cx="18" cy="18" r="12" stroke="#153D35" strokeWidth="1.4" />
      <ellipse cx="18" cy="18" rx="5" ry="12" stroke="#153D35" strokeWidth="1.4" />
      <path d="M6 18h24" stroke="#153D35" strokeWidth="1.4" />
    </svg>
  );
}

const audiences = [
  {
    title: "For the Imam",
    description: "Deliver the khutbah as you always have. Mubeen amplifies your message to everyone.",
    Icon: ImamIcon,
  },
  {
    title: "For Masjid Leadership",
    description: "Give your community one connected digital platform. Reduce tool fragmentation.",
    Icon: LeadershipIcon,
  },
  {
    title: "For the Congregation",
    description: "Follow, understand, and stay connected to every khutbah.",
    Icon: CongregationIcon,
  },
  {
    title: "For Non-Arabic Speakers",
    description: "Understand the khutbah while it happens, not after.",
    Icon: GlobalIcon,
  },
];

export function AudienceCards() {
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);

  return (
    <section className="py-24 px-5 bg-white">
      <div className="max-w-6xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          viewport={{ once: true, margin: "-200px" }}
          className="text-center mb-16"
        >
          <h2 className="text-5xl md:text-6xl font-bold text-[#173A33] mb-4">
            For everyone
            <br />
            <span className="text-[#153D35]">in the masjid</span>
          </h2>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {audiences.map((audience, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              viewport={{ once: true, margin: "-200px" }}
              onMouseEnter={() => setHoveredIndex(index)}
              onMouseLeave={() => setHoveredIndex(null)}
              whileHover={{ y: -8 }}
              className="group relative"
            >
              <div className="p-10 rounded-2xl border border-[#153D35]/10 bg-gradient-to-br from-[#FFFDF8] to-white hover:border-[#153D35]/30 transition-all cursor-pointer">
                <motion.div
                  animate={{
                    scale: hoveredIndex === index ? 1.1 : 1,
                    rotate: hoveredIndex === index ? 5 : 0,
                  }}
                  className="mb-6 inline-block"
                >
                  <audience.Icon />
                </motion.div>

                <h3 className="text-2xl font-bold text-[#173A33] mb-3">{audience.title}</h3>
                <p className="text-[#6E7D78] leading-relaxed">{audience.description}</p>

                <div className="absolute top-0 right-0 w-20 h-20 bg-gradient-to-br from-[#153D35]/5 to-transparent rounded-full -mr-10 -mt-10 pointer-events-none" />
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
