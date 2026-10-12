# Incident Response & Disaster Recovery Runbook — VoiceClone AI

> **Status:** APPROVED & TESTED  
> **Audience:** Site Reliability Engineers, DevOps, Platform Leads  
> **Scope:** Outages, Security Incidents, GPU Failures, and Data Recovery (VC-079)

---

## 1. Incident Severity Matrix

| Severity | Description | Target Response | Target Resolution |
|---|---|---|---|
| **P1 — Critical** | Consent bypass, voice identity theft / unauthorized generation, security breach | < 15 minutes | < 2 hours |
| **P2 — Major** | GPU inference service crash, Celery queue backlog spike (> 100 jobs), database unavailability | < 30 minutes | < 4 hours |
| **P3 — Moderate** | Single adapter timeout, audio upload latency degradation, non-blocking bug | < 2 hours | < 24 hours |

---

## 2. Emergency Response Procedures

### 2.1 Emergency Revocation of an Unauthorized Voice Profile (P1)
If an abuse report (`AbuseReport`) confirms that an uploaded voice lacks verified consent or is being used for impersonation:

1. **Immediate Revocation via Django Shell:**
   ```bash
   python manage.py shell
   ```
   ```python
   from apps.voices.models import VoiceProfile
   from apps.audit.models import AuditEvent

   profile = VoiceProfile.objects.get(id="<TARGET_VOICE_UUID>")
   profile.is_active = False
   profile.save()

   if hasattr(profile, "consent_record"):
       profile.consent_record.status = "REVOKED"
       profile.consent_record.save()

   AuditEvent.objects.create(
       actor=None, # System/Admin
       action="USER_BLOCKED",
       target_model="VoiceProfile",
       target_id=str(profile.id),
       metadata={"reason": "Emergency revocation: lack of legal consent"}
   )
   ```
2. **Purge Audio Assets:**
   Delete all generated files associated with that profile from disk.

---

### 2.2 GPU Out Of Memory (OOM) Recovery (P2)
When inference memory is exhausted or CUDA driver returns error `700 (CUDA error: an illegal memory access was encountered)`:

1. **Check GPU VRAM allocation:**
   ```powershell
   nvidia-smi
   ```
2. **Restart Inference Microservice Container:**
   ```bash
   docker compose -f infra/docker-compose.yml restart inference
   ```
3. **Flush Concurrency Lock:**
   The `BoundedInferenceLock` in `concurrency.py` automatically releases locks in `finally:` blocks. If an unhandled OS signal killed the process, restarting the container reinitializes semaphore state cleanly.

---

## 3. Database Backup & Restore Drill (VC-079)

### 3.1 Automated Daily Backup
```bash
pg_dump -h localhost -U postgres -d voiceclone_db -F c -b -v -f "/var/backups/voiceclone_$(date +%Y%m%d_%H%M%S).dump"
```

### 3.2 Recovery Drill Procedure
1. Stop backend and worker containers:
   ```bash
   docker compose stop backend worker
   ```
2. Restore database from snapshot:
   ```bash
   pg_restore -h localhost -U postgres -d voiceclone_db -c -v "/var/backups/voiceclone_target.dump"
   ```
3. Run Django migrations check:
   ```bash
   python manage.py migrate --check
   ```
4. Restart services and execute health probe:
   ```bash
   curl -I http://localhost:8000/api/v1/health/
   ```
