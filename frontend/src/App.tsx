import { MotionConfig } from "framer-motion";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { HomePage } from "@/pages/HomePage";
import { MasjidPage } from "@/pages/MasjidPage";

export default function App() {
  return (
    // reducedMotion="user" reads prefers-reduced-motion from the OS and
    // disables all Framer Motion animations for users who have it set.
    <MotionConfig reducedMotion="user">
      <BrowserRouter>
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:absolute focus:left-2 focus:top-2 focus:z-50 focus:rounded-pill focus:bg-raised focus:px-3 focus:py-2 focus:text-step--1 focus:text-mint focus:shadow-glass"
        >
          Skip to main content
        </a>
        <main id="main-content" className="min-h-screen">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/masjid/:id" element={<MasjidPage />} />
          </Routes>
        </main>
      </BrowserRouter>
    </MotionConfig>
  );
}
