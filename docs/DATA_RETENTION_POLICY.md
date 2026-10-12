# Data Retention & Privacy Policy — VoiceClone AI

> **Status:** ACTIVE  
> **Compliance Target:** GDPR Article 17 (Right to Erasure), Uzbekistan Personal Data Law (ZRU-547)

---

## 1. Storage Lifecycle & Retention Rules (VC-077)

VoiceClone AI enforces a strict, privacy-first data lifecycle designed to prevent audio accumulation and protect user voice rights:

| Data Type | Storage Location | Retention Window | Lifecycle Action |
|---|---|---|---|
| **Synthesized Audio (`GENERATED_OUTPUT`)** | `var/media/audio/` + DB | **7 Days** | Automated deletion by Celery periodic worker (`cleanup_expired_audio_assets`) |
| **Voice Reference (`REFERENCE_VOICE`)** | `var/media/audio/` + DB | User Active Lifetime | Retained until explicit user deletion or account closure |
| **Consent Record (`ConsentRecord`)** | PostgreSQL DB | Permanent Audit Log | Preserved for compliance and proof of consent, even if profile is disabled |
| **Audit Log (`AuditEvent`, `AbuseReport`)** | PostgreSQL DB | 1 Year | Retained for compliance, dispute resolution, and security tracing |

---

## 2. Automated Cleanup Mechanism

The Celery cleanup task runs periodically:
```python
# Defined in backend/apps/generations/tasks.py
cleanup_expired_audio_assets()
```
- Filters all `AudioAsset` objects where `asset_type = GENERATED_OUTPUT` and `created_at < now() - 7 days`.
- Deletes physical audio files on disk (`file.delete(save=False)`).
- Deletes corresponding database metadata rows in `GeneratedAudio` and `AudioAsset`.

---

## 3. Right to Erasure (User Deletion Flow)

1. **Self-Service Deletion:**
   - Any user can immediately trigger `DELETE /api/v1/voices/<id>/` or `DELETE /api/v1/audio/<id>/`.
   - The deletion cascades: the voice profile, associated speaker embeddings, and reference audio assets are completely removed from the filesystem.
2. **Revocation of Consent:**
   - When consent is revoked (`status = REVOKED`), the backend immediately disables speech synthesis from that voice profile across all paths.
