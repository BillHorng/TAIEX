# GitHub setup

1. Push the project to `main`.
2. Settings → Pages → Source: **GitHub Actions**.
3. Create a protected `production` environment for Google publishing.
4. Add the WIF secrets and repository variables listed in `GOOGLE_API_SETUP.md`.
5. Run `CI`, then manually run `Track market` once with `force=true` to verify permissions.

The market workflow runs at 09:00, 11:00, 13:00, and 15:00 Asia/Taipei (01:00, 03:00, 05:00, 07:00 UTC). Each run refreshes the published TWSE calendar, then collects MIS data and updates `latest.json` plus `history.json`. GitHub notes scheduled workflows may start late during platform load; data freshness is therefore calculated and displayed.

