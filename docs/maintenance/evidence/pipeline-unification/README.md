# Pipeline integration evidence

Owning report: [integration verification](../../pipeline-unification.md). Source decision: [ADR0002](../../../adr/0002-single-inference-command.md).

- [Before drivers/config](before/): copied before modification from revision `ceb9751c28dc749f5928bb37555cdb6913607535`.
- [Before tests](before-tests.log): 139 passing baseline tests.
- [After tests](after-tests.log): 146 passing tests including CLI, custom-path evaluation/comparison and engine cleanup on recovery failure.
- [CLI regression checks](test_cli.py) and [pipeline recovery checks](test_experiment_engine.py): tested file contents.
- [Environment sync](environment-sync.log): locked offline reinstall of only the local package.
- [Installed help](help.txt) and [module help](module-help.txt): one CLI surface.
- [Preparation console](preparation.log): installed command exited0; 200 full inputs prepared.
- [Initial smoke summary](smoke-summary.json): inference succeeded, but this invocation exposed command-return and worker-shutdown issues. It is not final process-exit verification.
- [Initial smoke record](../../checks/20260914_160139_pipeline-unification-smoke.md): exact source snapshot, manifests, traces and request/cache/scheduler evidence.
- [Preparation record](../../checks/20260914_160432_pipeline-unification-preparation.md): source snapshot after exit-code repair and before explicit GPU cleanup.

Task work remains at [tmp/pipeline-unification](../../../../tmp/pipeline-unification/); essential verification evidence is also retained here and in the linked routine check runs. Original experiment evidence was not changed.

- [Final smoke summary](final-smoke-summary.json), [console](final-smoke.log), and [owning check](../../checks/20260914_160718_pipeline-unification-final-smoke.md): final source match, exit0, explicit worker cleanup and request/cache observations.
- [Initial smoke console](smoke.log): retained shutdown defect evidence.
