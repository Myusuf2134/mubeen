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
    <div className="overflow-hidden rounded-lg border border-gray-200">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-gray-50 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">
            <th className="px-4 py-3">Prayer</th>
            <th className="px-4 py-3">Adhan</th>
            {hasIqamah && <th className="px-4 py-3">Iqamah</th>}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {PRAYER_ORDER.map((prayer) => {
            const iq = iqamahByPrayer[prayer];
            return (
              <tr key={prayer} className="bg-white hover:bg-gray-50">
                <td className="px-4 py-3 font-medium text-gray-900">
                  {PRAYER_LABELS[prayer]}
                </td>
                <td className="px-4 py-3 tabular-nums text-gray-700">
                  {formatAdhan(adhanTimes[prayer])}
                </td>
                {hasIqamah && (
                  <td className="px-4 py-3 tabular-nums text-gray-600">
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
