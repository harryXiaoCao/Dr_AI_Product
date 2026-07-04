# Dr. AI v1.0 Web/API Staging Architecture

Recorded: 2026-07-04

Status: guidance only. Tencent staging execution is intentionally excluded from
this polish pass.

## Preferred first-beta shape

Use same-origin HTTPS hosting for the first beta:

- Caddy serves the Flutter web build.
- Caddy reverse-proxies `/api/*` to the FastAPI service.
- FastAPI keeps `DR_AI_CORS_ALLOWED_ORIGINS=[]`.
- The browser sees one public HTTPS origin, which simplifies preflight behavior
  and avoids broad CORS exposure.

This matches the Week 1 security posture: bearer access tokens are short-lived,
refresh tokens stay in Flutter secure storage, and no credentialed browser
cookies are needed.

## Separate web/API origin fallback

If Tencent hosting constraints require a separate Flutter web origin, configure
FastAPI with exact CORS origins only:

```bash
DR_AI_CORS_ALLOWED_ORIGINS='["https://dr-ai-web.example.test"]'
```

Do not use `*` in staging or production. The API rejects wildcard CORS in those
environments. Keep `allow_credentials` disabled unless a later approved design
moves authentication to browser cookies.

## Smoke path

Use Flutter-native integration testing for real browser confidence:

```bash
flutter test integration_test/auth_smoke_test.dart -d chrome \
  --dart-define=DR_AI_API_BASE_URL=https://YOUR-STAGING-ORIGIN \
  --dart-define=DR_AI_SMOKE_EMAIL=doctor.demo@example.com \
  --dart-define=DR_AI_SMOKE_PASSWORD="$DR_AI_SEED_DOCTOR_PASSWORD" \
  --dart-define=DR_AI_SMOKE_DASHBOARD_TEXT="Quick Access"
```

Do not add DOM-driven login tests for Flutter web. The rendered canvas does not
provide stable HTML input/text targets, so DOM automation is a false confidence
path for this app.
