# Repository instructions

## Scope
These instructions apply to the entire `taiwan-stock-dashboard` project.

## Architecture
- `backend/` owns collection, validation, calendar decisions, and publishing.
- `frontend/` is a static React application. It reads only generated JSON under `frontend/public/data/`.
- Cloud integrations are optional adapters. Core collection must work without credentials.
- `config/` is the source of truth for tracked symbols and scheduled Taiwan times.

## Engineering rules
- Use Asia/Taipei for all market decisions and store timestamps as ISO 8601 with offsets.
- Preserve the schema in `backend/models.py`; add fields compatibly.
- Never commit credentials, downloaded service-account JSON, tokens, or personal Drive IDs.
- External requests require timeouts, bounded retries, and useful errors.
- A Google publishing failure may produce `PARTIAL_SUCCESS`; it must not erase valid local output.
- Tests must not call live services. Use fixtures or injected transports.
- Keep generated history out of Git; commit only `frontend/public/data/latest.json` as the Pages snapshot.

## Verification
- Backend: `python -m pytest`
- Frontend: `npm ci && npm run check && npm run build`
- Run both before changing workflows or data contracts.

## Git
- Keep commits focused and use imperative messages.
- Do not rewrite shared history or commit secrets/generated credential files.

