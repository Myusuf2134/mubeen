import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Navbar } from "@/components/marketing/Navbar";
import { Hero } from "@/components/marketing/Hero";
import { Problem } from "@/components/marketing/Problem";
import { LiveKhutbahReveal } from "@/components/marketing/LiveKhutbahReveal";
import { HowItWorks } from "@/components/marketing/HowItWorks";
import { FeatureEcosystem } from "@/components/marketing/FeatureEcosystem";
import { MubeenNetwork } from "@/components/marketing/MubeenNetwork";
import { AudienceCards } from "@/components/marketing/AudienceCards";
import { ProductGallery } from "@/components/marketing/ProductGallery";
import { VisionSection } from "@/components/marketing/VisionSection";
import { ForMasjids } from "@/components/marketing/ForMasjids";
import { FinalCTA } from "@/components/marketing/FinalCTA";
import { Footer } from "@/components/marketing/Footer";

export function MarketingPage() {
  const [scrollProgress, setScrollProgress] = useState(0);

  useEffect(() => {
    const handleScroll = () => {
      const windowHeight = window.innerHeight;
      const documentHeight = document.documentElement.scrollHeight - windowHeight;
      const scrolled = window.scrollY;
      setScrollProgress(documentHeight > 0 ? scrolled / documentHeight : 0);
    };

    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <div className="min-h-screen bg-white dark:bg-[#0f1419]">
      {/* Progress indicator */}
      <motion.div
        className="fixed top-0 left-0 h-1 bg-gradient-to-r from-[#153D35] to-[#285C50] z-40"
        style={{ width: `${scrollProgress * 100}%` }}
      />

      <Navbar />

      <main>
        <Hero />
        <Problem />
        <LiveKhutbahReveal />
        <HowItWorks />
        <FeatureEcosystem />
        <MubeenNetwork />
        <AudienceCards />
        <ProductGallery />
        <VisionSection />
        <ForMasjids />
        <FinalCTA />
      </main>

      <Footer />
    </div>
  );
}
