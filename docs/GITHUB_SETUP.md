# GitHub setup

1. Push the project to `main`.
2. Settings → Pages → Source: **GitHub Actions**.
3. Create a protected `production` environment for Google publishing.
4. Add the WIF secrets and repository variables listed in `GOOGLE_API_SETUP.md`.
5. Run `CI`, then manually run `Track market` once with `force=true` to verify permissions.

The market workflow records nominal batches at 09:00, 11:00, 13:00, and 15:00 Asia/Taipei, while cron dispatch is deliberately set seven minutes later (01:07, 03:07, 05:07, 07:07 UTC). This avoids GitHub's high-load period at the start of each hour. A recovery check at 08:17 UTC (16:17 Asia/Taipei) collects the 15:00 batch only when today's successful 15:00 snapshot is missing. Each collection refreshes the published TWSE calendar, then updates `latest.json` plus `history.json`. Data freshness is calculated from the actual market-data timestamp.

