# Project Timeline (Nov 26 – Nov 30, 2025)

## November 30, 2025
- `9329b96` – Added AOS animations to community detail views and removed duplicate “Create Post” controls to polish UX at the end of the sprint.

## November 29, 2025
- `9962807` – Ensured Stripe dependency is shipped with the app to support hosted payment flows.
- `239320a` – Hardened checkout with richer error handling and logging for faster debugging.
- `acea604` – Expanded webhook logging plus new troubleshooting guide to aid ops teams.
- `b75cda9` – Added `STRIPE_WEBHOOK_SECRET` env support to keep Railway deployments secure.
- `69e5e21` – Redesigned enrollment and booking flow with explicit states and completion handling.
- `9888837` – Large UI polish sweep: footer fixes, pagination for communities, mobile layout cleanup, standalone policy pages, verified links, and button contrast improvements.

## November 28, 2025
- `8566065` – Removed legacy soft-delete system from models, views, and migrations to simplify data handling.
- `662387f` – Introduced footer component and refreshed enrolled classes display for end users.

## November 27, 2025
- `8f23a0b` – Streamlined messaging UI by removing banners and hiding destructive controls on mobile.
- `8c9ac2f` – Deleted obsolete scripts, migration data, and backups to reduce repo clutter.
- `abc0030` – Merged a broad set of front-end features: community redesigns, message notifications, favorites, and custom admin tools.
- `60732b4` – High-level redesign checkpoint.
- `062369f` – Comprehensive accessibility update (ARIA roles, skip links, screen-reader support, improved forms/modals).
- `dec733a` – Rounded out task backlog: class editing workflows, captcha modal, profile card redesign, and navigation tweaks.
- `2e76b9e` – Fixed messages tab scrolling behavior across screen sizes.
- `5355881` – Added admin-controlled class editing pipeline for safer content changes.
- `6f5c238` – Displayed thumbnails when classes lack video assets.
- `12d529a` – Introduced speech-enabled captcha popup for a better accessibility experience.

## November 26, 2025
- `e17b19b` – Stabilized password reset emails via improved SendGrid backend configuration.
- `85d67a8` – Resolved reCAPTCHA regressions and made validation conditional on configuration.
- `7b0406b` – Added smart migration handler tailored for Railway deployments.
- `7618f88` – Documented migration script usage for developers.
- `12b10dd` – Added SQLite-to-PostgreSQL migration script to ease environment moves.
- `36cd786` – Updated CSRF trusted origins to include Railway domain.
- `b4cca59` – Added startup script ensuring migrations run before boot.
- `77c4bd6` – Ensured `ALLOWED_HOSTS` always includes Railway domain when needed.
- `161c000` – Added `psycopg2-binary` dependency for PostgreSQL connectivity.
- `ba0f1c4` – Fixed persistence and class creation issues affecting the database.
- `a52d45a` – Refined booking modal aesthetics, spacing, and interactions for consistency.

---

**Next Steps:** Continue expanding the timeline as new commits land or extend it backward using `git log --date=short`. This file can also be imported into spreadsheets if you need Gantt-style planning.
