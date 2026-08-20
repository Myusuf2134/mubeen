import { motion } from "framer-motion";

function MicIcon({ color }: { color: string }) {
  return (
    <svg width="34" height="34" viewBox="0 0 34 34" fill="none">
      <rect x="13" y="6" width="8" height="14" rx="4" stroke={color} strokeWidth="1.4" />
      <path d="M9 16a8 8 0 0016 0M17 24v4M12 28h10" stroke={color} strokeWidth="1.4" strokeLinecap="round" />
    </svg>
  );
}

function TranslateIcon({ color }: { color: string }) {
  return (
    <svg width="34" height="34" viewBox="0 0 34 34" fill="none">
      <path d="M6 11h9M10.5 8v3M8.5 11c1 3.5 3 6 5.5 7M12.5 11c-1 2.5-2.5 4.5-4.5 6" stroke={color} strokeWidth="1.4" strokeLinecap="round" />
      <path d="M18 22h9M23 19v3M20.5 22c1 3.5 3 6 5.5 7M25 22c-1 2.5-2.5 4.5-4.5 6" stroke={color} strokeWidth="1.4" strokeLinecap="round" />
    </svg>
  );
}

function MapIcon({ color }: { color: string }) {
  return (
    <svg width="30" height="30" viewBox="0 0 30 30" fill="none">
      <path d="M15 27s9-9.5 9-16a9 9 0 10-18 0c0 6.5 9 16 9 16Z" stroke={color} strokeWidth="1.4" strokeLinejoin="round" />
      <circle cx="15" cy="11" r="3" stroke={color} strokeWidth="1.4" />
    </svg>
  );
}

function ClockIcon({ color }: { color: string }) {
  return (
    <svg width="30" height="30" viewBox="0 0 30 30" fill="none">
      <circle cx="15" cy="15" r="11" stroke={color} strokeWidth="1.4" />
      <path d="M15 9v6l4 3" stroke={color} strokeWidth="1.4" strokeLinecap="round" />
    </svg>
  );
}

function BookIcon({ color }: { color: string }) {
  return (
    <svg width="30" height="30" viewBox="0 0 30 30" fill="none">
      <path d="M8 8c2.2-1.4 5-1.4 7 0v14c-2-1.4-4.8-1.4-7 0zM22 8c-2.2-1.4-5-1.4-7 0v14c2-1.4 4.8-1.4 7 0z" stroke={color} strokeWidth="1.4" strokeLinejoin="round" />
    </svg>
  );
}

function ScreenIcon({ color }: { color: string }) {
  return (
    <svg width="30" height="30" viewBox="0 0 30 30" fill="none">
      <rect x="4" y="6" width="22" height="14" rx="1.6" stroke={color} strokeWidth="1.4" />
      <path d="M12 24h6" stroke={color} strokeWidth="1.4" strokeLinecap="round" />
    </svg>
  );
}

function MobileIcon({ color }: { color: string }) {
  return (
    <svg width="26" height="30" viewBox="0 0 26 30" fill="none">
      <rect x="4" y="3" width="18" height="24" rx="2.4" stroke={color} strokeWidth="1.4" />
      <path d="M11 23h4" stroke={color} strokeWidth="1.4" strokeLinecap="round" />
    </svg>
  );
}

function GearIcon({ color }: { color: string }) {
  return (
    <svg width="30" height="30" viewBox="0 0 30 30" fill="none">
      <circle cx="15" cy="15" r="4.2" stroke={color} strokeWidth="1.4" />
      <path
        d="M15 4v3M15 23v3M4 15h3M23 15h3M7 7l2 2M21 21l2 2M23 7l-2 2M9 21l-2 2"
        stroke={color}
        strokeWidth="1.4"
        strokeLinecap="round"
      />
    </svg>
  );
}

const features = [
  {
    title: "Live Khutbah",
    description: "Real-time Arabic transcription and English translation",
    Icon: MicIcon,
    large: true,
    color: "from-[#153D35] to-[#0f2620]",
  },
  {
    title: "Arabic → English",
    description: "Translation appears moments behind the spoken word",
    Icon: TranslateIcon,
    large: true,
    color: "from-[#285C50] to-[#1a3a33]",
  },
  {
    title: "Masjid Directory",
    description: "Find masjids near you with detailed profiles",
    Icon: MapIcon,
    color: "from-[#C6A85A]/20 to-[#C6A85A]/5",
  },
  {
    title: "Prayer Times",
    description: "Accurate prayer times for every salah",
    Icon: ClockIcon,
    color: "from-[#153D35]/10 to-[#285C50]/5",
  },
  {
    title: "Qur'an & Hadith Detection",
    description: "Intelligent reference surfacing",
    Icon: BookIcon,
    color: "from-[#153D35]/10 to-[#285C50]/5",
  },
  {
    title: "TV Displays",
    description: "A calm, legible big-screen experience for congregants",
    Icon: ScreenIcon,
    color: "from-[#285C50]/10 to-[#153D35]/5",
  },
  {
    title: "Mobile Experience",
    description: "Follow the khutbah on your phone",
    Icon: MobileIcon,
    color: "from-[#153D35]/10 to-[#285C50]/5",
  },
  {
    title: "Operator Console",
    description: "Masjid admins manage everything in one place",
    Icon: GearIcon,
    color: "from-[#153D35]/10 to-[#285C50]/5",
  },
];

export function FeatureEcosystem() {
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
        delayChildren: 0.2,
      },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.5 } },
  };

  return (
    <section id="features" className="py-24 px-5 bg-white">
      <div className="max-w-6xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          viewport={{ once: true, margin: "-200px" }}
          className="text-center mb-16"
        >
          <h2 className="text-5xl md:text-6xl font-bold text-[#173A33] mb-4">
            More than live translation
            <br />
            <span className="text-[#153D35]">One connected platform</span>
          </h2>
          <p className="text-lg text-[#6E7D78] max-w-2xl mx-auto">
            A complete digital ecosystem for the modern masjid
          </p>
        </motion.div>

        <motion.div
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-200px" }}
          className="grid grid-cols-1 md:grid-cols-3 gap-6"
        >
          {features.map((feature, index) => (
            <motion.div
              key={index}
              variants={itemVariants}
              whileHover={{ y: -4 }}
              className={`
                rounded-2xl p-8 border border-black/5 backdrop-blur-sm
                ${
                  feature.large
                    ? "md:col-span-2 md:row-span-2 bg-gradient-to-br " + feature.color + " text-white"
                    : "bg-gradient-to-br " + feature.color
                }
                hover:border-[#153D35]/20 transition-all cursor-pointer group
              `}
            >
              <div className="mb-4 transform group-hover:scale-110 transition-transform inline-block">
                <feature.Icon color={feature.large ? "#FFFDF8" : "#153D35"} />
              </div>
              <h3 className={`text-xl font-bold mb-2 ${feature.large ? "text-white" : "text-[#173A33]"}`}>
                {feature.title}
              </h3>
              <p className={`${feature.large ? "text-white/80" : "text-[#6E7D78]"}`}>
                {feature.description}
              </p>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
