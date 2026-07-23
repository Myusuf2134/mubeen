import type { AdhanTimes, IqamahTime, PrayerName } from "@/types/api";
import { PRAYER_LABELS, PRAYER_ORDER } from "@/types/api";

interface Props {
  adhanTimes: AdhanTimes;
  iqamahTimes: IqamahTime[];
}

function formatAdhan(isoStr: string): string {
  return new Date(isoStr).toLocaleTimeString("en-US", {
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  });
}

function formatIqamah(iqamah: IqamahTime): string {
  if (iqamah.fixed_time) {
    const [h, m] = iqamah.fixed_time.split(":");
    const d = new Date();
    d.setHours(Number(h), Number(m), 0, 0);
    return d.toLocaleTimeString("en-US", {
      hour: "numeric",
      minute: "2-digit",
      hour12: true,
    });
  }
  if (iqamah.minutes_after_adhan != null) {
    return `+${String(iqamah.minutes_after_adhan)} min`;
  }
  return "—";
}

export function PrayerTimesTable({ adhanTimes, iqamahTimes }: Props) {
  const iqamahByPrayer = Object.fromEntries(
    iqamahTimes.map((it) => [it.prayer, it]),
  ) as Partial<Record<PrayerName, IqamahTime>>;

  const hasIqamah = iqamahTimes.length > 0;

  return (
    <div className="overflow-hidden rounded-card border border-white/8">
      <table className="w-full">
        <thead>
          <tr
            className="border-b border-white/8"
            style={{ background: "rgba(255,255,255,0.04)" }}
          >
            <th className="px-4 py-3 text-left text-step--1 font-semibold uppercase tracking-caps text-ink-muted">
              Prayer
            </th>
            <th className="px-4 py-3 text-left text-step--1 font-semibold uppercase tracking-caps text-ink-muted">
              Adhan
            </th>
            {hasIqamah && (
              <th className="px-4 py-3 text-left text-step--1 font-semibold uppercase tracking-caps text-ink-muted">
                Iqamah
              </th>
            )}
          </tr>
        </thead>
        <tbody>
          {PRAYER_ORDER.map((prayer, i) => {
            const iq = iqamahByPrayer[prayer];
            return (
              <tr
                key={prayer}
                className="border-b border-white/5 last:border-0 transition-colors duration-150 hover:bg-white/4"
                style={i % 2 === 1 ? { background: "rgba(255,255,255,0.02)" } : undefined}
              >
                <td className="px-4 py-3.5 font-sora font-semibold text-step--1 text-ink">
                  {PRAYER_LABELS[prayer]}
                </td>
                <td className="px-4 py-3.5 tabular-nums text-step--1 text-mint">
                  {formatAdhan(adhanTimes[prayer])}
                </td>
                {hasIqamah && (
                  <td className="px-4 py-3.5 tabular-nums text-step--1 text-ink-dim">
                    {iq ? formatIqamah(iq) : "—"}
                  </td>
                )}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
