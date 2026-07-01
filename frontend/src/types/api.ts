export interface MasjidSummary {
  id: string;
  name: string;
  city: string;
  state: string;
  country: string;
  lat: number;
  lon: number;
  distance_km?: number;
}

export type PrayerName = "fajr" | "dhuhr" | "asr" | "maghrib" | "isha";

export const PRAYER_LABELS: Record<PrayerName, string> = {
  fajr: "Fajr",
  dhuhr: "Dhuhr",
  asr: "Asr",
  maghrib: "Maghrib",
  isha: "Isha",
};

export const PRAYER_ORDER: PrayerName[] = [
  "fajr",
  "dhuhr",
  "asr",
  "maghrib",
  "isha",
];

export interface AdhanTimes {
  fajr: string;
  dhuhr: string;
  asr: string;
  maghrib: string;
  isha: string;
}

export interface IqamahTime {
  id: string;
  prayer: PrayerName;
  minutes_after_adhan?: number;
  fixed_time?: string;
}

export interface JumuahTime {
  id: string;
  label?: string;
  language: string;
  time: string;
  sort_order: number;
}

export interface MasjidDetail {
  id: string;
  name: string;
  address_line: string;
  city: string;
  state: string;
  country: string;
  lat: number;
  lon: number;
  phone?: string;
  website?: string;
  calculation_method: string;
  adhan_times: AdhanTimes;
  iqamah_times: IqamahTime[];
  jumuah_times: JumuahTime[];
  has_live_session: boolean;
  latest_session_id?: string;
}
