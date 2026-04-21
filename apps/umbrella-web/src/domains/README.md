# Domains

This directory contains bounded contexts for the frontend.

Rules:

- put domain-specific API, store, helpers and UI here
- keep route entries in `ui/pages`
- split larger screens into `ui/sections` and `ui/blocks`
- keep pages thin: composition root plus wiring, not the whole screen implementation
- keep global primitives in shared layers such as `@/shared/ui`, `@/shared/lib`, `@/app/access`
- do not keep duplicate compatibility wrappers once a domain is migrated
- import directly from `@/domains/<domain>/...`
- avoid `index.js` barrels unless they actually reduce repetition
