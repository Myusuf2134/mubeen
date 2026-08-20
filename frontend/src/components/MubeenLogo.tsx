import mubeenIcon from "@/assets/mubeen-icon.png";

/**
 * Mubeen Logo — Real brand mark (teal dome + infinity symbol + gold diamond)
 * Rendered from src/assets/mubeen-icon.png (transparent background)
 * Used on login, display, and other brand-forward pages
 */
export function MubeenLogo({ size = 64 }: { size?: number }) {
  return (
    <img
      src={mubeenIcon}
      alt="Mubeen"
      width={size}
      height={size}
      style={{ display: "block" }}
    />
  );
}
