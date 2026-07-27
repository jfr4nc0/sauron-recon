# Profile-distribution cron examples

These files are examples only. They are intentionally not installed into a live gateway by the repository.

- `search-new-listings.json`: run an idempotent search for a saved criteria set.
- `report-new-listings.json`: render and deliver only new/changed listings.
- `knowledge-health.json`: ask the profile to validate and update the knowledge index.

Before enabling them on a VPS, set the target profile, `workdir`, source policy, runtime data directory, and Telegram destination in that environment. Use a dry-run first.
