import { BrowserRouter, Route, Routes } from "react-router-dom";
import { HomePage } from "@/pages/HomePage";
import { MasjidPage } from "@/pages/MasjidPage";

export default function App() {
  return (
    <BrowserRouter>
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:left-2 focus:top-2 focus:z-50 focus:rounded focus:bg-white focus:px-3 focus:py-2 focus:text-sm focus:shadow-lg"
      >
        Skip to main content
      </a>
      <main id="main-content" className="min-h-screen bg-gray-50">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/masjid/:id" element={<MasjidPage />} />
          {/* Phase 4: /masjid/:id/live — captions TV/phone view */}
        </Routes>
      </main>
    </BrowserRouter>
  );
}
