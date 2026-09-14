# Project documentation

Purpose: review procurement notices against the supplied24 items, preserve source evidence, and improve the competition submission. Official requirements and development observations have separate owners below.

Project timezone: **Asia/Seoul (UTC+09:00)**. New run IDs use actual orchestration start time to seconds: `YYYYMMDD_HHMMSS_summary`. Unknown historical starts use the explicitly approved `legacy_<old-name>` exception; migration time is separate.

`src/` contains maintained reusable code; `experiments/` contains hypothesis code and retained execution evidence. `tmp/<task-id>/` is retained until explicit deletion instructions. `outputs/` contains retained final user deliverables and is Git-excluded. Root `README.md`, `AGENT.md`, and `user/` are user-owned.

- [Project structure](project-structure.md): directory responsibilities and ownership.
- [Operations](operations.md): current commands, new sweeps, result-triggered follow-ups, and CPU replay.
- [Environment](environment.md): existing dependency/model/GPU setup and its verification scope.
- [Glossary](CONTEXT.md): domain and experiment terms only.
- [Competition](competition/README.md): official constraints, task, evaluation, submission, and source register.
- [Architecture](architecture/README.md): maintained modules, interfaces, dependencies, and verification.
- [Experiments](experiments/README.md): problem areas, sweeps, current judgments, and historical decisions.
- [Architectural decisions](adr/README.md): consequential adopted tradeoffs and status.
- [Maintenance](maintenance/README.md): structure migration, routine checks, and retained verification evidence.
