import { motion } from "framer-motion";

export function MubeenNetwork() {
  return (
    <section className="py-24 px-5 bg-[#F7F3E9]">
      <div className="max-w-6xl mx-auto">
        {/* Heading */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          viewport={{ once: true, margin: "-200px" }}
          className="text-center mb-16"
        >
          <h2 className="text-5xl md:text-6xl font-bold text-[#173A33] mb-4">
            Mubeen connects
            <br />
            <span className="text-[#153D35]">the entire masjid</span>
          </h2>
        </motion.div>

        {/* Network Diagram */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          whileInView={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.7 }}
          viewport={{ once: true, margin: "-200px" }}
          className="relative"
        >
          <div className="aspect-video rounded-3xl bg-gradient-to-br from-white to-[#FFFDF8] border border-[#153D35]/10 p-12 flex items-center justify-center overflow-hidden">
            {/* Simplified network visualization */}
            <svg className="w-full h-full" viewBox="0 0 800 400" preserveAspectRatio="xMidYMid meet">
              {/* Center circle - Mubeen */}
              <circle cx="400" cy="200" r="40" fill="url(#mubeenGradient)" stroke="#153D35" strokeWidth="2" />
              <text x="400" y="210" textAnchor="middle" className="text-xs font-bold fill-white">
                MUBEEN
              </text>

              {/* Connected elements */}
              <g>
                {/* Imam */}
                <line x1="400" y1="200" x2="150" y2="100" stroke="#153D35" strokeWidth="2" strokeDasharray="5,5" />
                <circle cx="150" cy="100" r="35" fill="#153D35" opacity="0.1" stroke="#153D35" strokeWidth="2" />
                <text x="150" y="108" textAnchor="middle" className="text-sm fill-[#173A33] font-bold">
                  Imam
                </text>

                {/* TV Display */}
                <line x1="400" y1="200" x2="650" y2="80" stroke="#153D35" strokeWidth="2" strokeDasharray="5,5" />
                <circle cx="650" cy="80" r="35" fill="#285C50" opacity="0.1" stroke="#285C50" strokeWidth="2" />
                <text x="650" y="88" textAnchor="middle" className="text-sm fill-[#173A33] font-bold">
                  TV Display
                </text>

                {/* Phones */}
                <line x1="400" y1="200" x2="150" y2="320" stroke="#153D35" strokeWidth="2" strokeDasharray="5,5" />
                <circle cx="150" cy="320" r="35" fill="#153D35" opacity="0.1" stroke="#153D35" strokeWidth="2" />
                <text x="150" y="328" textAnchor="middle" className="text-sm fill-[#173A33] font-bold">
                  Phones
                </text>

                {/* Web */}
                <line x1="400" y1="200" x2="650" y2="320" stroke="#153D35" strokeWidth="2" strokeDasharray="5,5" />
                <circle cx="650" cy="320" r="35" fill="#285C50" opacity="0.1" stroke="#285C50" strokeWidth="2" />
                <text x="650" y="328" textAnchor="middle" className="text-sm fill-[#173A33] font-bold">
                  Web
                </text>

                {/* Admin Console */}
                <line x1="400" y1="200" x2="400" y2="50" stroke="#153D35" strokeWidth="2" strokeDasharray="5,5" />
                <circle cx="400" cy="50" r="35" fill="#C6A85A" opacity="0.2" stroke="#C6A85A" strokeWidth="2" />
                <text x="400" y="58" textAnchor="middle" className="text-sm fill-[#173A33] font-bold">
                  Console
                </text>
              </g>

              <defs>
                <linearGradient id="mubeenGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#153D35" />
                  <stop offset="100%" stopColor="#285C50" />
                </linearGradient>
              </defs>
            </svg>

            {/* Overlay text */}
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
              <p className="text-center text-[#6E7D78] font-medium">
                One platform connects the Imam, congregation, displays, and administration
              </p>
            </div>
          </div>
        </motion.div>

        {/* Description */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.3 }}
          viewport={{ once: true, margin: "-200px" }}
          className="mt-12 grid grid-cols-1 md:grid-cols-2 gap-8"
        >
          <div>
            <h3 className="text-2xl font-bold text-[#173A33] mb-3">For the congregation</h3>
            <p className="text-[#6E7D78]">
              Follow the khutbah on their phones or the big screens, with real-time captions in Arabic and English. No app needed.
            </p>
          </div>
          <div>
            <h3 className="text-2xl font-bold text-[#173A33] mb-3">For the masjid</h3>
            <p className="text-[#6E7D78]">
              One digital home for prayer times, announcements, community information, and everything else. Replace multiple disconnected tools.
            </p>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
