# Phase 6 Notification Delivery Readiness

Date: 2026-07-30

Status: production-quality adapter contracts may be exercised locally; every
external provider remains disabled in controlled staging until its exact
prerequisites and target evidence pass.

This runbook governs APNs, Alibaba Cloud EMAS Mobile Push, and standards-based
Web Push. It does not authorize real-patient data, public production, live
payer integration, commercial rollout, or an external provider test. The
persisted in-product inbox is the authoritative notification surface when
external delivery is unavailable.

## Shared evidence contract

- Keep notification text, patient/resource identity, clinical or payer content,
  device endpoints, provider payloads, secrets, and tokens out of provider
  metadata, analytics, logs, deduplication keys, and evidence.
- Use opaque server-owned identifiers and privacy-safe previews. A provider
  payload must carry only the minimum routing data needed to reopen the
  authenticated application, where authorization is checked again.
- Preserve `accepted`, `sent`, `delivered_if_supported`, `failed`, `expired`,
  and `unknown` as different outcomes. A successful provider API response
  proves provider acceptance only. It does not prove that the operating system
  displayed the notification or that the user saw it.
- Do not invent a receipt when a provider lacks a receipt, a target is offline,
  permission is denied, a token is stale, or credentials are unavailable.
- Keep external delivery globally disabled unless the selected adapter is
  ready. A disabled or unavailable adapter must not prevent creation and
  readback of the authorized in-product inbox record.

## Credential and log policy

The checked-in `.env.example` contains variable names and disabled defaults
only. Populate secrets only in the host's mode-`0600` `.env` or an approved
secret manager:

- APNs: `DR_AI_NOTIFICATION_APNS_PRIVATE_KEY`;
- EMAS: `DR_AI_NOTIFICATION_EMAS_APP_SECRET`; and
- Web Push: `DR_AI_NOTIFICATION_WEB_PUSH_VAPID_PRIVATE_KEY`.

The corresponding identifiers and public keys are configuration, not
permission to expose patient or provider data. Never commit a populated
environment file, Apple `.p8` key, Android provider configuration, OEM
credential, VAPID private key, device token, or Web Push subscription.

Readiness and redaction checks must be presence-only:

1. compare a fixed allow-list of expected variable names against the active
   environment;
2. report only `set`, `empty`, or `absent`, never a value or value length;
3. scan recent API/Caddy logs for sensitive-pattern presence and return only a
   count or boolean;
4. do not print matching lines, headers, request bodies, provider payloads, or
   tokens; and
5. treat any suspected match as a failed gate requiring private investigation
   and credential rotation where applicable.

## Android selection: Alibaba Cloud EMAS Mobile Push

Alibaba Cloud EMAS Mobile Push is the selected Android aggregation boundary for
a new China-facing application. Alibaba's official documentation describes its
own channel plus Xiaomi, Huawei, Honor, vivo, OPPO, Meizu, and Google/FCM
manufacturer channels:

- [Manufacturer-channel overview](https://help.aliyun.com/zh/document_detail/434677.html)
- [Manufacturer-channel index](https://help.aliyun.com/zh/document_detail/434676.html)
- [Android SDK integration](https://help.aliyun.com/zh/document_detail/434660.html)
- [Current Android 4.x upgrade path](https://help.aliyun.com/zh/document_detail/3035053.html)
- [Android permission and provider troubleshooting](https://help.aliyun.com/zh/document_detail/2874047.html)
- [Current billing and service model](https://help.aliyun.com/en/document_detail/434638.html)

Tencent TPNS is not selected for a new application even though it technically
supports China OEM channels. Tencent's official notice states that new
application access and sales ended on 2024-03-31; existing purchased and
integrated applications may continue:

- [Tencent TPNS stop-sale notice](https://cloud.tencent.com/document/product/548/103030)

TPNS may be reconsidered only if the product owner proves a compatible,
grandfathered application and records its service status. Existing Tencent
compute or database use is not evidence of TPNS entitlement.

### EMAS prerequisites and current blockers

Before enabling EMAS, require all of the following:

- an Alibaba Cloud EMAS project and Android application bound to the exact
  release package;
- `DR_AI_NOTIFICATION_EMAS_APP_KEY` and the corresponding secret supplied
  outside the repository;
- `DR_AI_NOTIFICATION_EMAS_ANDROID_PACKAGE` matching the signed application;
- each intended OEM application, credential, channel/category, receipt
  configuration, and vendor approval;
- `DR_AI_NOTIFICATION_EMAS_OEM_APPROVALS_VERIFIED=true` only after those
  approvals are evidenced;
- privacy disclosure and consent before provider SDK initialization;
- Android 13-or-later `POST_NOTIFICATIONS` request and truthful denied/revoked
  handling;
- Android 8-or-later notification channels with user-controlled importance;
- release signing and a supported physical China Android target; and
- server acceptance, retry, stale-token, rotation, cancellation, and
  receipt-capability tests using synthetic endpoints only.

Current repository inspection found no EMAS configuration, provider SDK,
notification permission/channel implementation, release signing file, or
attached Android device. Therefore EMAS delivery remains disabled and no live
provider result is claimed.

Primary Android platform requirements:

- [Notification runtime permission](https://developer.android.com/develop/ui/compose/notifications/notification-permission)
- [Notification channels](https://developer.android.com/develop/ui/compose/notifications/channels)

## APNs prerequisites and current blockers

Before enabling APNs, require:

- Push Notifications enabled for the exact App ID and Xcode target;
- an `aps-environment` entitlement in the signed provisioning profile;
- a valid signing identity and profile for the configured bundle identifier;
- an APNs token-signing key stored outside the repository, plus its key ID and
  team ID;
- `DR_AI_NOTIFICATION_APNS_BUNDLE_ID` matching the signed application;
- device registration on every launch, secure server registration of rotated
  tokens, and multiple-device/sign-out revocation handling;
- user notification authorization with denied and revoked readback; and
- HTTP/2/TLS provider tests against the correct APNs environment on a supported
  signed target.

Current repository inspection found a mounted physical iPhone and simulators,
but no push entitlement, no valid local code-signing identity, no APNs
credential configuration, and no client registration/permission path. APNs
therefore remains disabled and no live provider result is claimed.

Apple primary sources:

- [Registering an app with APNs](https://developer.apple.com/documentation/usernotifications/registering-your-app-with-apns)
- [Setting up a remote notification server](https://developer.apple.com/documentation/usernotifications/setting-up-a-remote-notification-server)
- [Token-based APNs authentication](https://developer.apple.com/documentation/usernotifications/establishing-a-token-based-connection-to-apns)
- [Sending APNs requests and best-effort semantics](https://developer.apple.com/documentation/usernotifications/sending-notification-requests-to-apns)

## Web Push prerequisites and current blockers

Before enabling Web Push, require:

- HTTPS, a scoped service worker with `push`,
  `pushsubscriptionchange`, and notification-click handling;
- explicit user-gesture permission and truthful default/denied/revoked states;
- VAPID public/private keys and a valid subject, with the private key outside
  the repository;
- persisted, encrypted subscription endpoints with rotation, deactivation,
  sign-out, and account/session-revocation handling;
- feature detection and runtime readiness because the browser chooses the push
  service and network availability varies; and
- synthetic tests for foreground, background, launch, expired subscription,
  authorized deep link, and unavailable push-service behavior.

Current staging is HTTPS and the PWA manifest is standalone, but the generated
Flutter service worker is only an application-cache worker. The repository has
no push subscription flow, push/click handler, VAPID configuration, or
subscription endpoint. Web Push therefore remains disabled. Do not describe it
as China-wide support without successful runtime evidence on each supported
browser/network combination.

Primary sources:

- [W3C Push API](https://www.w3.org/TR/push-api/)
- [IETF VAPID RFC 8292](https://www.rfc-editor.org/info/rfc8292/)
- [Web Push for iOS and iPadOS Home Screen apps](https://webkit.org/blog/13878/web-push-for-web-apps-on-ios-and-ipados/)

## Backup-first controlled-staging procedure

An authorized provider exercise must extend, not replace, the existing Tencent
staging release sequence:

1. record source revision, migration head, immutable images, and the disabled
   notification configuration;
2. create host-only backups of `.env`, Compose/Caddy configuration, web bundle,
   release artifacts, and a PostgreSQL custom-format dump;
3. generate and verify checksums before changing the active release;
4. preserve the previous immutable API/retrieval digests as explicit rollback
   targets;
5. apply migrations, run two idempotent seeds, and verify public plus
   authenticated smoke before any provider exercise;
6. run presence-only credential and log scans;
7. enable only the separately authorized, fully ready adapter and use synthetic
   recipients/endpoints;
8. record local attempt state, provider acceptance or bounded failure, and
   target-visible evidence separately; and
9. disable the adapter and roll back to the exact predecessor if authorization,
   redaction, readiness, or delivery-state integrity fails.

The Phase 5 staging record proves that its backup and checksums were created and
verified before deployment. It does not record a restore into a disposable
database. Before the first external-provider activation, restore the latest
custom-format dump into a fresh isolated database, run migration/schema and
row-count sanity checks, execute the bounded smoke suite against that restored
target, and record the result. Until then, state “backup verified; restore
rehearsal not evidenced,” not “restore tested.”
