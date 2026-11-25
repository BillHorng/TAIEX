# Architecture

```text
GitHub schedule -> calendar gate -> TWSE adapter -> Pydantic validation
                                               |-> CSV / JSON artifact -> Google Drive (optional)
                                               |-> Sheets append (optional)
                                               `-> public/latest.json -> Vite build -> GitHub Pages
```

The browser consumes only versioned static JSON. Credentials stay in GitHub's OIDC exchange and never enter the bundle. A run is `SKIPPED` on a known closure, `FAILED` if collection fails, and `PARTIAL_SUCCESS` when local output succeeds but a Google destination fails.

