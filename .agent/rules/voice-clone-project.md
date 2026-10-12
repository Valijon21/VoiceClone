# Voice Clone Project Rules

- Read `AGENTS.md`, `docs/SYSTEM_DESIGN.md`, and `tasks/ROADMAP.md` before implementation.
- One phase at a time; never mark a task complete without evidence.
- Do not claim language support until benchmarked on Uzbek, Russian, and English samples.
- Do not enable any model in production before reviewing its code, weights, upstream, and dataset licenses.
- Keep model-specific code behind `VoiceModelAdapter`.
- Keep inference isolated from Django and protect internal inference endpoints.
- Never store raw audio in public static directories.
- Every generated asset must have an owner, retention policy, and deletion path.
- Do not build non-consensual impersonation features.
- Finish every task with tests and a concise report.
