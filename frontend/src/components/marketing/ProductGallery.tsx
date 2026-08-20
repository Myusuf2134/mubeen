import { motion } from "framer-motion";
import { useState } from "react";

function OperatorConsolePreview() {
  return (
    <div className="w-full h-full bg-[#0C2620] p-6 flex flex-col justify-center gap-3">
      <div className="text-[#F7F3E9]/50 text-[10px] uppercase tracking-wider">Live Session</div>
      <div className="flex items-center gap-3">
        <div className="bg-[#C6A85A] text-[#153D35] text-xs font-semibold rounded-full px-4 py-1.5">Start</div>
        <div className="border border-[#F7F3E9]/20 text-[#F7F3E9]/40 text-xs rounded-full px-4 py-1.5">Stop</div>
      </div>
      <div className="text-[#F7F3E9]/40 text-[11px] mt-1">Status: Inactive</div>
    </div>
  );
}

function MasjidDetailPreview() {
  return (
    <div className="w-full h-full bg-[#FFFDF8] p-6 flex flex-col gap-2">
      <div className="h-14 rounded-lg bg-gradient-to-br from-[#C6A85A]/30 to-[#C6A85A]/10" />
      <div className="text-[#173A33] text-sm font-semibold mt-1">Daarul Ahbaab</div>
      <div className="text-[#6E7D78] text-[10px]">Columbus, OH</div>
      <div className="mt-2 flex gap-2">
        <div className="bg-[#153D35] text-white text-[10px] rounded-full px-3 py-1">Watch Live Khutbah</div>
      </div>
    </div>
  );
}

function DisplayPreview() {
  return (
    <div className="w-full h-full bg-[#0C2620] p-6 flex flex-col items-center justify-center gap-3 text-center">
      <div className="flex items-center gap-1.5 text-[#F7F3E9]/50 text-[9px] uppercase tracking-wider">
        <span className="w-1.5 h-1.5 rounded-full bg-red-400" /> Live
      </div>
      <div className="text-[#F7F3E9] text-sm" dir="rtl">الحمد لله رب العالمين</div>
      <div className="text-[#F7F3E9]/60 text-[11px]">All praise belongs to Allah, Lord of all worlds.</div>
    </div>
  );
}

function DirectoryPreview() {
  return (
    <div className="w-full h-full bg-[#FFFDF8] p-6 flex flex-col gap-2">
      <div className="h-6 rounded-full bg-[#153D35]/5 border border-[#153D35]/10 w-2/3" />
      {[1, 2, 3].map((i) => (
        <div key={i} className="flex items-center gap-2 border-b border-[#153D35]/5 py-1.5">
          <div className="w-6 h-6 rounded bg-[#C6A85A]/20 shrink-0" />
          <div className="h-2 rounded bg-[#153D35]/10 w-full" />
        </div>
      ))}
    </div>
  );
}

function MobilePreview() {
  return (
    <div className="w-full h-full bg-[#0C2620] flex items-center justify-center p-6">
      <div className="w-24 h-full max-h-40 rounded-xl border border-[#F7F3E9]/20 bg-[#0C2620] p-2 flex flex-col items-center justify-center gap-2">
        <div className="text-[#F7F3E9] text-[9px]" dir="rtl">بسم الله</div>
        <div className="text-[#F7F3E9]/50 text-[7px] text-center leading-tight">In the name of Allah</div>
      </div>
    </div>
  );
}

function LoginPreview() {
  return (
    <div className="w-full h-full bg-[#FFFDF8] p-6 flex flex-col gap-2.5 items-start">
      <div className="h-2.5 rounded bg-[#153D35]/10 w-1/3" />
      <div className="h-8 w-full rounded-lg border border-[#153D35]/15 bg-white" />
      <div className="h-2.5 rounded bg-[#153D35]/10 w-1/4" />
      <div className="h-8 w-full rounded-lg border border-[#153D35]/15 bg-white" />
      <div className="h-8 w-full rounded-full bg-[#153D35] mt-1" />
    </div>
  );
}

const screens = [
  {
    title: "Operator Console",
    description: "Manage everything from one intuitive dashboard",
    Preview: OperatorConsolePreview,
  },
  {
    title: "Masjid Detail Page",
    description: "Beautiful public profiles for every masjid",
    Preview: MasjidDetailPreview,
  },
  {
    title: "Live Khutbah Display",
    description: "Large-screen experience for the congregation",
    Preview: DisplayPreview,
  },
  {
    title: "Masjid Directory",
    description: "Discover masjids near you",
    Preview: DirectoryPreview,
  },
  {
    title: "Mobile Live Khutbah",
    description: "Follow on the go",
    Preview: MobilePreview,
  },
  {
    title: "Operator Login",
    description: "Secure authentication and access",
    Preview: LoginPreview,
  },
];

export function ProductGallery() {
  const [selectedIndex, setSelectedIndex] = useState(0);
  const SelectedPreview = screens[selectedIndex].Preview;

  return (
    <section className="py-24 px-5 bg-[#F7F3E9]">
      <div className="max-w-6xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          viewport={{ once: true, margin: "-200px" }}
          className="text-center mb-16"
        >
          <h2 className="text-5xl md:text-6xl font-bold text-[#173A33] mb-4">
            See Mubeen
            <br />
            <span className="text-[#153D35]">in action</span>
          </h2>
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.6 }}
            viewport={{ once: true, margin: "-200px" }}
            className="lg:col-span-2"
          >
            <div className="aspect-video rounded-3xl border border-[#153D35]/10 overflow-hidden">
              <motion.div
                key={selectedIndex}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="w-full h-full"
              >
                <SelectedPreview />
              </motion.div>
            </div>
            <h3 className="text-2xl font-bold text-[#173A33] mt-6">{screens[selectedIndex].title}</h3>
            <p className="text-[#6E7D78] mt-2">{screens[selectedIndex].description}</p>
          </motion.div>

          <div className="space-y-3 flex flex-col">
            {screens.map((screen, index) => (
              <motion.button
                key={index}
                initial={{ opacity: 0, x: 20 }}
                whileInView={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.4, delay: index * 0.05 }}
                viewport={{ once: true }}
                onClick={() => setSelectedIndex(index)}
                className={`p-4 rounded-xl text-left transition-all ${
                  selectedIndex === index
                    ? "bg-gradient-to-r from-[#153D35] to-[#285C50] text-white border-0"
                    : "bg-white border border-[#153D35]/10 text-[#173A33] hover:border-[#153D35]/30"
                }`}
              >
                <h4 className="font-semibold text-sm">{screen.title}</h4>
                <p className={`text-[11px] mt-0.5 ${selectedIndex === index ? "text-white/70" : "text-[#6E7D78]"}`}>
                  {screen.description}
                </p>
              </motion.button>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
