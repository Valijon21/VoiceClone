import React, { useState } from "react";
import { api } from "../api/client";
import { ApprovedModel, GenerationJob, VoiceProfile } from "../types";

interface SynthesisFormProps {
  voices: VoiceProfile[];
  models: ApprovedModel[];
  onJobCreated: (job: GenerationJob) => void;
  onOpenConsentModal: () => void;
}

export const SynthesisForm: React.FC<SynthesisFormProps> = ({
  voices,
  models,
  onJobCreated,
  onOpenConsentModal,
}) => {
  const [inputText, setInputText] = useState(
    "Assalomu alaykum! VoiceClone AI sun'iy intellekt nutq sintezi platformasiga xush kelibsiz."
  );
  const [selectedLanguage, setSelectedLanguage] = useState<"uz" | "en" | "ru">("uz");
  const [selectedModelId, setSelectedModelId] = useState<string>("openvoice_v2");
  const [selectedVoiceId, setSelectedVoiceId] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Selected profile helper
  const selectedVoice = voices.find((v) => v.id === selectedVoiceId);

  // Presets
  const presets: Record<"uz" | "en" | "ru", string[]> = {
    uz: [
      "Assalomu alaykum! VoiceClone AI sun'iy intellekt nutq sintezi platformasiga xush kelibsiz.",
      "O‘zbekiston Respublikasi bo‘ylab axloqiy va xavfsiz sun'iy intellekt texnologiyalarini rivojlantiramiz.",
      "Bugun 2026-yilda barcha sinovlar muvaffaqiyatli yakunlandi va tizim foydalanishga tayyor.",
    ],
    en: [
      "Hello! Welcome to the ethical VoiceClone AI speech synthesis system.",
      "Antigravity engineering ensures robust performance and bounded inference concurrency.",
    ],
    ru: [
      "Здравствуйте! Экспериментальная модель генерации речи готова к тестированию.",
      "Система VoiceClone обеспечивает безопасность и обязательное согласие владельца голоса.",
    ],
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    if (!inputText.trim()) {
      setErrorMessage("Iltimos, sintezlash uchun matn kiriting.");
      return;
    }

    // Ethical check: If a voice profile is selected, verify consent
    if (selectedVoice && !selectedVoice.has_consent) {
      setErrorMessage("Tanlangan ovoz profili uchun tasdiqlangan qonuniy rozilik mavjud emas. Avval rozilik bering.");
      return;
    }

    setLoading(true);

    try {
      // Generate unique idempotency key
      const idempotencyKey = `job_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;

      const job = await api.createJob({
        text: inputText.trim(),
        language: selectedLanguage,
        modelId: selectedModelId,
        voiceProfileId: selectedVoiceId || undefined,
        idempotencyKey,
      });

      onJobCreated(job);
    } catch (err: any) {
      const msg =
        err?.detail ||
        err?.message ||
        "Nutq sintezlash jarayonini boshlashda xatolik yuz berdi.";
      setErrorMessage(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="glass-panel" style={{ padding: "1.75rem" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "1.25rem" }}>
        <h2 style={{ fontSize: "1.2rem", fontWeight: 700, display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <span>✨</span> Nutq sintezi & Ovoz klonlash
        </h2>
        <span className="badge badge-emerald">Asinxron Celery Navbat</span>
      </div>

      {errorMessage && (
        <div className="badge badge-rose" style={{ width: "100%", padding: "0.75rem", marginBottom: "1.25rem", display: "block" }}>
          ⚠️ {errorMessage}
        </div>
      )}

      <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
        
        {/* Row 1: Language and Model */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
          <div>
            <label style={{ display: "block", fontSize: "0.85rem", fontWeight: 600, marginBottom: "0.4rem" }}>
              Til (Language)
            </label>
            <select
              className="form-select"
              value={selectedLanguage}
              onChange={(e) => {
                const lang = e.target.value as "uz" | "en" | "ru";
                setSelectedLanguage(lang);
                if (presets[lang]?.[0]) {
                  setInputText(presets[lang][0]);
                }
              }}
            >
              <option value="uz">🇺🇿 O‘zbekcha (Lotin — MVP Asosiy)</option>
              <option value="en">🇬🇧 English (Supported)</option>
              <option value="ru">🇷🇺 Русский (Eksperimental)</option>
            </select>
          </div>

          <div>
            <label style={{ display: "block", fontSize: "0.85rem", fontWeight: 600, marginBottom: "0.4rem" }}>
              AI Model & Tayanch
            </label>
            <select
              className="form-select"
              value={selectedModelId}
              onChange={(e) => setSelectedModelId(e.target.value)}
            >
              {models.length > 0 ? (
                models.map((m) => (
                  <option key={m.model_id} value={m.model_id}>
                    {m.name} ({m.license})
                  </option>
                ))
              ) : (
                <option value="openvoice_v2">OpenVoice V2 + MeloTTS (MIT License)</option>
              )}
            </select>
          </div>
        </div>

        {/* Row 2: Voice Profile selector with Consent gate check */}
        <div>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "0.4rem" }}>
            <label style={{ fontSize: "0.85rem", fontWeight: 600 }}>
              Klonlanadigan Ovoz Profili
            </label>
            <button
              type="button"
              onClick={onOpenConsentModal}
              style={{
                background: "none",
                border: "none",
                color: "var(--accent-cyan)",
                fontSize: "0.8rem",
                fontWeight: 600,
                cursor: "pointer",
                display: "inline-flex",
                alignItems: "center",
                gap: "0.25rem",
              }}
            >
              + Yangi ovoz va rozilik qo‘shish
            </button>
          </div>

          <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
            <select
              className="form-select"
              value={selectedVoiceId}
              onChange={(e) => setSelectedVoiceId(e.target.value)}
              style={{ flex: 1 }}
            >
              <option value="">Standart Nativ Ovoz (Tayanch TTS)</option>
              {voices.map((v) => (
                <option key={v.id} value={v.id}>
                  {v.name} ({v.language.toUpperCase()}) — {v.has_consent ? "✅ Rozilik mavjud" : "❌ Roziliksiz"}
                </option>
              ))}
            </select>

            {selectedVoice && (
              <span className={selectedVoice.has_consent ? "badge badge-emerald" : "badge badge-rose"}>
                {selectedVoice.has_consent ? "Rozilik: OK" : "Rozilik: TALAB QILINADI"}
              </span>
            )}
          </div>
        </div>

        {/* Text Area Input */}
        <div>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "0.4rem" }}>
            <label style={{ fontSize: "0.85rem", fontWeight: 600 }}>
              Sintezlash uchun matn
            </label>
            <span style={{ fontSize: "0.78rem", color: "var(--text-dim)" }}>
              {inputText.length} / 500 belgi
            </span>
          </div>

          <textarea
            className="form-textarea"
            rows={4}
            value={inputText}
            maxLength={500}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="Nutqqa aylantiriladigan matnni kiriting..."
            required
          />

          {/* Quick Presets */}
          <div style={{ marginTop: "0.5rem", display: "flex", gap: "0.5rem", flexWrap: "wrap", alignItems: "center" }}>
            <span style={{ fontSize: "0.75rem", color: "var(--text-dim)" }}>Tayyor namunalar:</span>
            {presets[selectedLanguage]?.map((sample, idx) => (
              <button
                key={idx}
                type="button"
                className="btn-secondary"
                style={{ fontSize: "0.75rem", padding: "0.2rem 0.55rem" }}
                onClick={() => setInputText(sample)}
              >
                Namuna {idx + 1}
              </button>
            ))}
          </div>
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          className="btn-primary"
          disabled={loading || (!!selectedVoice && !selectedVoice.has_consent)}
          style={{ width: "100%", padding: "0.85rem", fontSize: "1rem" }}
        >
          {loading ? (
            "Generatsiya navbatga qo‘yilmoqda..."
          ) : (
            <>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <polygon points="5 3 19 12 5 21 5 3" />
              </svg>
              Nutqni sintezlash (Generate Speech)
            </>
          )}
        </button>

      </form>
    </div>
  );
};
