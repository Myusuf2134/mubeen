import { motion } from "framer-motion";

function MicIcon() {
  return (
    <svg width="40" height="40" viewBox="0 0 40 40" fill="none">
      <rect x="16" y="8" width="8" height="14" rx="4" stroke="#153D35" strokeWidth="1.4" />
      <path d="M11 19a9 9 0 0018 0M20 28v5M14 33h12" stroke="#153D35" strokeWidth="1.4" strokeLinecap="round" />
    </svg>
  );
}

function ListenIcon() {
  return (
    <svg width="40" height="40" viewBox="0 0 40 40" fill="none">
      <path d="M7 20h3l2.5-8 4 16 3-12 2.5 6 4-10 3 8h3" stroke="#153D35" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function TranslateIcon() {
  return (
    <svg width="40" height="40" viewBox="0 0 40 40" fill="none">
      <path d="M8 13h10M13 10v3M11 13c1 4 3.5 7 6 8M15 13c-1 3-2.5 5.5-4.5 7" stroke="#153D35" strokeWidth="1.4" strokeLinecap="round" />
      <path d="M20 25h10M25 22v3M23 25c1 4 3.5 7 6 8M27 25c-1 3-2.5 5.5-4.5 7" stroke="#153D35" strokeWidth="1.4" strokeLinecap="round" />
    </svg>
  );
}

function BookIcon() {
  return (
    <svg width="40" height="40" viewBox="0 0 40 40" fill="none">
      <path d="M10 10c3-2 7-2 10 0v19c-3-2-7-2-10 0zM30 10c-3-2-7-2-10 0v19c3-2 7-2 10 0z" stroke="#153D35" strokeWidth="1.4" strokeLinejoin="round" />
    </svg>
  );
}

function ScreensIcon() {
  return (
    <svg width="40" height="40" viewBox="0 0 40 40" fill="none">
      <rect x="7" y="9" width="16" height="11" rx="1.5" stroke="#153D35" strokeWidth="1.4" />
      <path d="M13 20v3M17 20v3M10 23h13" stroke="#153D35" strokeWidth="1.4" strokeLinecap="round" />
      <rect x="26" y="16" width="8" height="13" rx="1.5" stroke="#153D35" strokeWidth="1.4" />
    </svg>
  );
}

const steps = [
  {
    number: "01",
    title: "The imam speaks",
    description: "The imam delivers the khutbah naturally in Arabic.",
    Icon: MicIcon,
  },
  {
    number: "02",
    title: "Mubeen listens",
    description: "Arabic speech is transcribed in real-time with high accuracy.",
    Icon: ListenIcon,
  },
  {
    number: "03",
    title: "Mubeen translates",
    description: "English captions appear almost immediately with natural phrasing.",
    Icon: TranslateIcon,
  },
  {
    number: "04",
    title: "Context is added",
    description: "Relevant Qur'an and Hadith references are detected and surfaced.",
    Icon: BookIcon,
  },
  {
    number: "05",
    title: "Everyone can follow",
    description: "The experience appears on TVs, phones, and web displays simultaneously.",
    Icon: ScreensIcon,
  },
];

export function HowItWorks() {
  return (
    <section className="py-24 px-5 bg-[#F7F3E9]">
      <div className="max-w-5xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          viewport={{ once: true, margin: "-200px" }}
          className="text-center mb-20"
        >
          <h2 className="text-5xl md:text-6xl font-bold text-[#173A33] mb-4">
            How Mubeen
            <br />
            <span className="text-[#153D35]">works</span>
          </h2>
        </motion.div>

        <div className="space-y-12">
          {steps.map((step, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, x: -40 }}
              whileInView={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              viewport={{ once: true, margin: "-200px" }}
              className="flex gap-8 items-start"
            >
              <div className={`hidden md:block flex-1 ${index % 2 === 1 ? "order-2" : ""}`}>
                <motion.div
                  animate={{ y: [0, -10, 0] }}
                  transition={{ duration: 3, repeat: Infinity, delay: index * 0.2 }}
                  className="aspect-video rounded-2xl bg-gradient-to-br from-[#153D35]/10 to-[#285C50]/5 border border-[#153D35]/10 flex items-center justify-center"
                >
                  <step.Icon />
                </motion.div>
              </div>

              <div className="flex-1">
                <div className="text-sm font-semibold text-[#153D35] mb-2">{step.number}</div>
                <h3 className="text-2xl font-bold text-[#173A33] mb-3">{step.title}</h3>
                <p className="text-[#6E7D78] leading-relaxed">{step.description}</p>
              </div>

              <div className="md:hidden flex-shrink-0">
                <div className="w-16 h-16 rounded-lg bg-gradient-to-br from-[#153D35]/10 to-[#285C50]/5 border border-[#153D35]/10 flex items-center justify-center">
                  <step.Icon />
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
