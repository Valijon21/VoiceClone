export interface User {
  id: string;
  username: string;
  email: string;
  is_verified: boolean;
  plan?: string;
  is_unlimited?: boolean;
  audio_seconds_quota?: number;
  audio_seconds_used?: number;
  remaining_seconds?: number;
  created_at: string;
}

export interface QuotaInfo {
  plan: string;
  is_unlimited: boolean;
  audio_seconds_quota: number;
  audio_seconds_used: number;
  remaining_seconds: number;
  usage_percent: number;
}

export interface SubscriptionInfo {
  id: string;
  plan: string;
  status: "TRIAL" | "ACTIVE" | "PAST_DUE" | "CANCELED" | "EXPIRED";
  billing_cycle: "MONTHLY" | "YEARLY";
  price_amount: number;
  currency: string;
  current_period_start: string;
  current_period_end: string;
  cancel_at_period_end: boolean;
  grace_period_until?: string | null;
}

export interface CheckoutResponse {
  status: string;
  provider: string;
  plan: string;
  amount_uzs: number;
  checkout_url: string;
}

export interface ConsentRecord {
  id: string;
  consent_text: string;
  status: "PENDING" | "VERIFIED" | "REVOKED";
  consented_at: string;
  is_valid: boolean;
}

export interface VoiceProfile {
  id: string;
  name: string;
  language: "uz" | "en" | "ru";
  is_active: boolean;
  has_consent: boolean;
  consent?: ConsentRecord;
  created_at: string;
}

export interface AudioAsset {
  id: string;
  original_filename: string;
  download_url: string;
  duration_sec: number;
  sample_rate: number;
  channels: number;
  size_bytes: number;
  asset_type: "REFERENCE_VOICE" | "GENERATED_OUTPUT" | "CONSENT_RECORDING";
  created_at: string;
}

export interface GeneratedAudio {
  id: string;
  asset: AudioAsset;
  duration_sec: number;
  quality_rating?: number;
  created_at: string;
}

export interface GenerationJob {
  id: string;
  voice_profile?: string;
  model_id: string;
  language: "uz" | "en" | "ru";
  input_text: string;
  status: "PENDING" | "RUNNING" | "SUCCEEDED" | "FAILED" | "CANCELLED";
  progress_percent: number;
  error_message: string;
  idempotency_key?: string;
  result_audio?: GeneratedAudio;
  created_at: string;
  started_at?: string;
  completed_at?: string;
}

export interface ApprovedModel {
  model_id: string;
  name: string;
  license: string;
  license_status: string;
  commercial_ready: boolean;
  supported_languages: string[];
}
