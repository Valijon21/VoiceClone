import React, { useEffect, useState } from "react";
import { api } from "./api/client";
import { ApprovedModel, AudioAsset, GenerationJob, User, VoiceProfile } from "./types";
import { Navbar } from "./components/Navbar";
import { AuthModal } from "./components/AuthModal";
import { ConsentModal } from "./components/ConsentModal";
import { VoiceRecorder } from "./components/VoiceRecorder";
import { SynthesisForm } from "./components/SynthesisForm";
import { JobProgressBar } from "./components/JobProgressBar";
import { AudioPlayer } from "./components/AudioPlayer";
import { VoiceProfilesList } from "./components/VoiceProfilesList";
import { GenerationHistory } from "./components/GenerationHistory";

export const App: React.FC = () => {
  const [user, setUser] = useState<User | null>(null);
  const [voices, setVoices] = useState<VoiceProfile[]>([]);
  const [models, setModels] = useState<ApprovedModel[]>([]);
  const [jobs, setJobs] = useState<GenerationJob[]>([]);
  const [activeJob, setActiveJob] = useState<GenerationJob | null>(null);
  const [activeAudio, setActiveAudio] = useState<{ url: string; title: string } | null>(null);

  const [isAuthOpen, setIsAuthOpen] = useState(false);
  const [isConsentOpen, setIsConsentOpen] = useState(false);

  // Load initial data
  useEffect(() => {
    // 1. Fetch current user if session exists
    api.getMe()
      .then((u) => setUser(u))
      .catch(() => setUser(null));

    // 2. Fetch approved models
    api.getApprovedModels()
      .then((m) => setModels(m))
      .catch(() => {
        // Fallback default
        setModels([
          {
            model_id: "openvoice_v2",
            name: "OpenVoice V2 + MeloTTS",
            license: "MIT",
            license_status: "APPROVED_COMMERCIAL",
            commercial_ready: true,
            supported_languages: ["uz", "en", "ru"],
          },
        ]);
      });

    // 3. Fetch voice profiles
    api.getVoices()
      .then((v) => setVoices(v))
      .catch(() => setVoices([]));

    // 4. Fetch jobs history
    api.getJobs()
      .then((j) => setJobs(j))
      .catch(() => setJobs([]));
  }, []);

  const handleLogout = async () => {
    try {
      await api.logout();
      setUser(null);
      setVoices([]);
      setJobs([]);
    } catch {
      setUser(null);
    }
  };

  const handleProfileCreated = (newProfile: VoiceProfile) => {
    setVoices((prev) => [newProfile, ...prev]);
  };

  const handleProfileDeleted = (id: string) => {
    setVoices((prev) => prev.filter((v) => v.id !== id));
  };

  const handleJobCreated = (newJob: GenerationJob) => {
    setActiveJob(newJob);
    setJobs((prev) => [newJob, ...prev]);
  };

  const handleJobFinished = (completedJob: GenerationJob) => {
    setActiveJob(completedJob);
    // Refresh history
    setJobs((prev) => [
      completedJob,
      ...prev.filter((j) => j.id !== completedJob.id),
    ]);

    if (completedJob.status === "SUCCEEDED" && completedJob.result_audio?.asset?.download_url) {
      setActiveAudio({
        url: completedJob.result_audio.asset.download_url,
        title: `Natija: "${completedJob.input_text.substring(0, 30)}..."`,
      });
    }
  };

  const handleAudioUploaded = (_asset: AudioAsset) => {
    // Refresh voices after reference upload
    api.getVoices().then((v) => setVoices(v)).catch(() => {});
  };

  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column", padding: "0 1rem" }}>
      {/* Top Navbar */}
      <Navbar
        user={user}
        onOpenAuth={() => setIsAuthOpen(true)}
        onLogout={handleLogout}
      />

      {/* Main Content Container */}
      <main style={{ maxWidth: "1280px", margin: "1rem auto 3rem", width: "100%", flex: 1 }}>
        
        {/* Banner Alert for Voice Safety */}
        <div
          className="glass-panel"
          style={{
            padding: "1rem 1.5rem",
            marginBottom: "1.5rem",
            borderLeft: "4px solid var(--accent-cyan)",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            flexWrap: "wrap",
            gap: "1rem",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "0.85rem" }}>
            <span style={{ fontSize: "1.3rem" }}>🛡️</span>
            <div>
              <div style={{ fontSize: "0.92rem", fontWeight: 700 }}>
                Axloqiy Ovoz Xavfsizligi va Consent Gate Faol
              </div>
              <div style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
                Har qanday ovoz klonlash uchun faqat tasdiqlangan qonuniy rozilik qabul qilinadi. Firibgarlik va noqonuniy taqlid man etiladi.
              </div>
            </div>
          </div>
          <button
            type="button"
            className="btn-secondary"
            style={{ fontSize: "0.8rem", padding: "0.35rem 0.8rem" }}
            onClick={() => setIsConsentOpen(true)}
          >
            Qoidalarni ko‘rish & Rozilik berish
          </button>
        </div>

        {/* 2-Column Responsive Dashboard */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(360px, 1fr))", gap: "1.5rem", alignItems: "start" }}>
          
          {/* Left Column: Studio Inputs */}
          <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
            <SynthesisForm
              voices={voices}
              models={models}
              onJobCreated={handleJobCreated}
              onOpenConsentModal={() => setIsConsentOpen(true)}
            />

            <VoiceRecorder onAudioUploaded={handleAudioUploaded} />
          </div>

          {/* Right Column: Execution, Player & Histories */}
          <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
            {/* Active Job Progress */}
            {activeJob && (
              <JobProgressBar
                initialJob={activeJob}
                onJobFinished={handleJobFinished}
                onRetry={() => setActiveJob(null)}
              />
            )}

            {/* Audio Player if an audio is active */}
            {activeAudio && (
              <AudioPlayer
                src={activeAudio.url}
                title={activeAudio.title}
              />
            )}

            {/* Voice Profiles List */}
            <VoiceProfilesList
              voices={voices}
              onProfileDeleted={handleProfileDeleted}
              onOpenCreateModal={() => setIsConsentOpen(true)}
            />

            {/* Generation History */}
            <GenerationHistory
              jobs={jobs}
              onSelectJobAudio={(url, title) => setActiveAudio({ url, title })}
            />
          </div>

        </div>
      </main>

      {/* Footer */}
      <footer
        style={{
          borderTop: "1px solid var(--border-subtle)",
          padding: "2rem 1rem",
          marginTop: "auto",
          textAlign: "center",
          fontSize: "0.82rem",
          color: "var(--text-dim)",
        }}
      >
        <p style={{ marginBottom: "0.5rem" }}>
          VoiceClone AI &bull; O‘zbek, ingliz va rus tillari uchun axloqiy ovoz platformasi
        </p>
        <p style={{ fontSize: "0.75rem" }}>
          Ovoz klonlash faqat rasmiy rozilik bilan amalga oshiriladi. Ma'lumotlarni saqlash muddati (Retention): 7 kun.
        </p>
      </footer>

      {/* Modals */}
      <AuthModal
        isOpen={isAuthOpen}
        onClose={() => setIsAuthOpen(false)}
        onSuccess={(u) => {
          setUser(u);
          api.getVoices().then((v) => setVoices(v)).catch(() => {});
          api.getJobs().then((j) => setJobs(j)).catch(() => {});
        }}
      />

      <ConsentModal
        isOpen={isConsentOpen}
        onClose={() => setIsConsentOpen(false)}
        onProfileCreated={handleProfileCreated}
      />
    </div>
  );
};

export default App;
