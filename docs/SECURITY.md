# Security & Hardening Policy — VoiceClone AI

> **Status:** APPROVED & ACTIVE  
> **Audience:** DevOps, Backend Engineers, QA, Security Officers  
> **Related Standards:** OWASP Top 10 (2025), GDPR Audio Rights, SOC2 Compliance

---

## 1. Secrets Management & Environment Hygiene

1. **Zero Secret Leaks in Git:**
   - `.env`, `.env.local`, API keys, private certificates, and database credentials are strictly barred from version control via `.gitignore`.
   - CI pipeline runs automated pattern scanners (`trufflehog`/`git-secrets`) checking against potential API tokens or credentials.
2. **Production Secret Injection:**
   - Secrets must be passed via Docker environment variables or external Key Management Systems (AWS Secrets Manager, Vault) with strict file permissions (`chmod 600`).
   - `DEBUG=False` is strictly enforced in production environments; debug endpoints and traceback formatting are disabled.

---

## 2. Network Isolation & Service Boundaries

1. **FastAPI Inference Microservice Isolation:**
   - Port `8001` (Inference Service) is kept internal within the Docker bridge network (`infra/docker-compose.yml`).
   - The FastAPI GPU service does not accept direct public web traffic. All requests must route through Django DRF (`8000`) where authentication, ownership verification, and the Consent Gate are enforced.
2. **CORS & CSRF Policies:**
   - CORS is restricted to validated frontend origins (`CORS_ALLOWED_ORIGINS`).
   - `CSRF_COOKIE_SECURE=True` and `SESSION_COOKIE_SECURE=True` are required in HTTPS production setups.
   - `X-Frame-Options: DENY` is active to eliminate clickjacking vectors.

---

## 3. Rate Limiting & Throttling (VC-071)

To mitigate brute force, Denial of Service (DoS), and resource starvation on GPU workers:

| Scope | Rate Limit | Target Endpoints | Behavior on Exceeded |
|---|---|---|---|
| **Anonymous (`anon`)** | 120 req / min | Public endpoints (`/api/v1/health/`, schema) | `429 Too Many Requests` |
| **User Session (`user`)** | 300 req / min | General authenticated API requests | `429 Too Many Requests` |
| **Audio Upload (`audio_upload`)** | 30 req / min | `POST /api/v1/audio/` | `429 Too Many Requests` |
| **Speech Generation (`generation`)** | 60 req / min | `POST /api/v1/generations/jobs/` | `429 Too Many Requests` |
| **Abuse Complaints (`reports`)** | 20 req / min | `POST /api/v1/audit/reports/` | `429 Too Many Requests` |

---

## 4. Input Sanitization & Malformed File Defense (VC-072)

1. **Audio Validation:**
   - Maximum upload size per file: **25 MB** (`MAX_FILE_SIZE_BYTES`).
   - Minimum container size: **44 bytes**.
   - Enforced extensions & MIME types: `WAV`, `MP3`, `OGG`, `M4A`.
   - Binary header verification: WAV files must start with the valid `RIFF` and `WAVE` 4-byte chunk signatures. Malformed files are rejected immediately with `400 BAD REQUEST` and do not reach the audio decoder.
2. **Text Normalization Limits:**
   - Synthesis input text length: bounded between 1 and 1000 characters. Blank or whitespace-only inputs are rejected at serialization.

---

## 5. Storage Quotas & Asset Isolation (VC-071, VC-077)

- **Per-User Quota:** Maximum 100 MB of stored audio assets per user account.
- **Tenant Isolation:** Users are only permitted to query, play, or delete audio assets they personally own (`owner=request.user`).
- **Private Media Streaming:** Media files are never served from unprotected public static paths.
