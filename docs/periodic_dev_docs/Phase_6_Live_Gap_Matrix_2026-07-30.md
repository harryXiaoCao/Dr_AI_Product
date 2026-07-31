# Phase 6 Live Gap Matrix — 2026-07-30

| Surface | Local implemented state | Exact live blocker | Next evidence |
|---|---|---|---|
| In-product inbox | Complete for patient, doctor, payer | None for local synthetic use | Controlled-staging migration/authenticated smoke |
| APNs | Contract/readiness and fail-closed attempt boundary | App ID entitlement, provisioning/signing identity, APNs key, secure token resolution, physical target | Separate synthetic signed-target exercise |
| Alibaba Cloud EMAS | Selected China Android boundary; disabled readiness | Alibaba project/app, signed package, OEM credentials/approvals, consent, secure endpoint resolution, physical target | OEM-by-OEM synthetic exercise |
| Web Push | Standards-based boundary; disabled readiness | Push service worker, VAPID, subscription lifecycle, supported browser/network evidence | HTTPS synthetic subscription/rotation test |
| On-device scheduling | Not activated | Ownership/cancellation semantics and native permission paths not implemented | Decide whether server or native scheduler owns each event |
| Controlled staging | Phase 5 remains current verified deployment | SSH authentication unavailable; Phase 6 was not deployed | Backup, restore rehearsal, migration `0053`, immutable images, authenticated smoke |
| Backup restore | Backup/checksum evidence exists | No disposable restore rehearsal record | Restore latest custom dump to isolated DB and run bounded smoke |

These gaps do not weaken the canonical in-product lifecycle. They prevent any
claim of external provider acceptance, operating-system display, user-visible
delivery, or Phase 6 controlled-staging activation.
