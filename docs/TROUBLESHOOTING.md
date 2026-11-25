# Troubleshooting

- **`SKIPPED`**: inspect `calendar_status`; this is expected on weekends and listed holidays.
- **`UNAVAILABLE` symbol**: TWSE returned no matching row or closing field. Check the uploaded run artifact before changing symbol configuration.
- **`PARTIAL_SUCCESS`**: local data was created but a Google destination failed. Verify folder sharing, WIF attribute conditions, APIs, and variables.
- **Pages assets return 404**: confirm the repository is named `TAIEX`; this project uses the GitHub Pages base path `/TAIEX/`.
- **Schedule is late**: GitHub cron is best effort. Use `workflow_dispatch` for a manual recovery run; duplicate IDs are deterministic per date/time/symbol.

