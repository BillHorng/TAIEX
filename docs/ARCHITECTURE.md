# Architecture

```text
GitHub schedule -> calendar refresh -> calendar gate -> TWSE MIS adapter -> Pydantic validation
                                               |-> CSV / JSON artifact -> Google Drive (optional)
                                               |-> Sheets append (optional)
                                               `-> public/latest/history/run-status JSON -> Vite build -> GitHub Pages
```

The MIS adapter falls back to TWSE closing OpenAPI when the real-time service is unavailable. The browser consumes versioned `latest.json` and `history.json`; `run-status.json` separately audits every run. `FAILED` and `SKIPPED` runs update only run status, preserving the last valid market snapshot. Credentials stay in GitHub's OIDC exchange and never enter the bundle. A run is `SKIPPED` on a known closure, `FAILED` if collection fails, and `PARTIAL_SUCCESS` when local output succeeds but a Google destination fails.

