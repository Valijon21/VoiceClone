import {
  ApprovedModel,
  AudioAsset,
  CheckoutResponse,
  GenerationJob,
  QuotaInfo,
  SubscriptionInfo,
  User,
  VoiceProfile,
} from "../types";
import { logger } from "../utils/logger";

const BASE_URL = "";

function getCsrfToken(): string | null {
  const match = document.cookie.match(/csrftoken=([^;]+)/);
  return match ? decodeURIComponent(match[1]) : null;
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers || {});
  if (!(options.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const csrf = getCsrfToken();
  if (csrf && !headers.has("X-CSRFToken")) {
    headers.set("X-CSRFToken", csrf);
  }

  if (!headers.has("X-Request-ID")) {
    headers.set("X-Request-ID", `fe_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`);
  }

  const res = await fetch(`${BASE_URL}${endpoint}`, {
    ...options,
    headers,
    credentials: "include",
  });

  if (!res.ok) {
    let errorData = { message: `Request failed with status ${res.status}` };
    try {
      errorData = await res.json();
    } catch {
      // fallback
    }
    const reqId = headers.get("X-Request-ID") || "-";
    logger.warn(`API_CALL_FAILED [${reqId}] ${options.method || "GET"} ${endpoint} status=${res.status}`, { errorData });
    throw errorData;
  }

  return res.json() as Promise<T>;
}

export const api = {
  // Accounts
  async register(username: string, email: string, password: string): Promise<User> {
    return request<User>("/api/v1/accounts/register/", {
      method: "POST",
      body: JSON.stringify({ username, email, password }),
    });
  },

  async login(username: string, password: string): Promise<User> {
    return request<User>("/api/v1/accounts/login/", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    });
  },

  async logout(): Promise<void> {
    await request<{ status: string }>("/api/v1/accounts/logout/", {
      method: "POST",
    });
  },

  async getMe(): Promise<User> {
    return request<User>("/api/v1/accounts/me/");
  },

  async getQuota(): Promise<QuotaInfo> {
    return request<QuotaInfo>("/api/v1/accounts/quota/");
  },

  async getSubscription(): Promise<SubscriptionInfo> {
    return request<SubscriptionInfo>("/api/v1/accounts/subscription/");
  },

  async initiateCheckout(payload: {
    plan: string;
    billing_cycle?: "MONTHLY" | "YEARLY";
    provider?: "PAYME" | "CLICK";
    return_url?: string;
  }): Promise<CheckoutResponse> {
    return request<CheckoutResponse>("/api/v1/accounts/payments/checkout/", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async cancelSubscription(payload?: { immediate?: boolean; reason?: string }): Promise<any> {
    return request("/api/v1/accounts/subscription/cancel/", {
      method: "POST",
      body: JSON.stringify(payload || {}),
    });
  },

  // Voices & Consent
  async getVoices(): Promise<VoiceProfile[]> {
    const data = await request<{ results?: VoiceProfile[] } | VoiceProfile[]>("/api/v1/voices/");
    return Array.isArray(data) ? data : data.results || [];
  },

  async createVoice(name: string, language: string = "uz"): Promise<VoiceProfile> {
    return request<VoiceProfile>("/api/v1/voices/", {
      method: "POST",
      body: JSON.stringify({ name, language }),
    });
  },

  async provideConsent(voiceId: string, consentText: string): Promise<void> {
    await request(`/api/v1/voices/${voiceId}/consent/`, {
      method: "POST",
      body: JSON.stringify({ consent_text: consentText }),
    });
  },

  async deleteVoice(voiceId: string): Promise<void> {
    await request(`/api/v1/voices/${voiceId}/`, {
      method: "DELETE",
    });
  },

  // Audio Assets
  async uploadAudio(file: File, assetType: string = "REFERENCE_VOICE"): Promise<AudioAsset> {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("asset_type", assetType);
    return request<AudioAsset>("/api/v1/audio/", {
      method: "POST",
      body: formData,
    });
  },

  async deleteAudio(assetId: string): Promise<void> {
    await request(`/api/v1/audio/${assetId}/`, {
      method: "DELETE",
    });
  },

  // Generations
  async getApprovedModels(): Promise<ApprovedModel[]> {
    const data = await request<{ approved_models: ApprovedModel[] }>("/api/v1/generations/models/");
    return data.approved_models;
  },

  async getJobs(): Promise<GenerationJob[]> {
    const data = await request<{ results?: GenerationJob[] } | GenerationJob[]>("/api/v1/generations/jobs/");
    return Array.isArray(data) ? data : data.results || [];
  },

  async createJob(payload: {
    text: string;
    language: string;
    modelId: string;
    voiceProfileId?: string;
    idempotencyKey?: string;
  }): Promise<GenerationJob> {
    return request<GenerationJob>("/api/v1/generations/jobs/", {
      method: "POST",
      body: JSON.stringify({
        input_text: payload.text,
        language: payload.language,
        model_id: payload.modelId,
        voice_profile: payload.voiceProfileId || null,
        idempotency_key: payload.idempotencyKey || null,
      }),
    });
  },

  async getJobById(jobId: string): Promise<GenerationJob> {
    return request<GenerationJob>(`/api/v1/generations/jobs/${jobId}/`);
  },
};
