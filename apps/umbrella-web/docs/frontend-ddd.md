# Frontend Domain Architecture

## Why

`umbrella-web` already has several bounded contexts: `auth`, `admins`, `agents`, `groups`.
When the app is split only by technical layer, each feature change leaks across unrelated folders:

- `src/api/*`
- `src/pages/*`
- `src/components/*`
- `src/utils/*`

That is manageable while screens are small, but expensive once domains become stateful and UI-heavy:

- one feature spans many folders
- domain rules drift into route pages
- pages become huge because every dialog, section and action lives in one file
- refactoring one bounded context requires touching global-looking folders

The target is a stricter and more honest compromise:

- domain-first structure
- no duplicate legacy entrypoints
- no artificial deep layering like `model/services/adapters/factories`
- but UI inside a domain is still split by meaning so route files stay small

## Target Shape

```text
src/
  app/
    access/
      capabilities.js
      rbac.js
    api/
      http.js
    layouts/
    navigation/
      blocks/
      composables/
      sections/
      navigation.config.js
    pages/
      general/
    plugins/
  domains/
    auth/
      api.js
      store.js
      ui/
        pages/
          LoginPage.vue
          SettingsPage.vue
    admins/
      api.js
      store.js
      admins.utils.js
      useAdminsPage.js
      ui/
        pages/
          AdminsPage.vue
        sections/
        components/
    agents/
      api.js
      store.js
      agents.utils.js
      useAgentsPage.js
      ui/
        pages/
          AgentsPage.vue
        sections/
        blocks/
    groups/
      api.js
      store.js
      groups.utils.js
      useGroupsPage.js
      ui/
        pages/
          GroupsPage.vue
        sections/
        components/
  shared/
    ui/
    lib/
```

For this repository the non-domain kernel is now explicit:

- `src/app`: router, layouts, navigation, access rules, app-level pages and bootstrapping
- `src/shared`: reusable UI primitives and cross-domain library helpers

What matters is that migrated domains no longer depend on legacy root buckets like `src/components`, `src/pages`, `src/config`, `src/plugins`, `src/layouts`, `src/composables`, or `src/utils`.

## Domain Rules

Each domain should stay compact:

- `api.js`: transport and DTO-facing requests for this domain only
- `store.js`: Pinia store for this domain
- `*.utils.js`: labels, mappers and small domain helpers
- `use<Name>Page.js`: page orchestration when the route has enough behavior to justify extraction
- `ui/pages/*Page.vue`: route composition root
- `ui/sections/*`: major screen areas
- `ui/blocks/*`: repeatable visual blocks inside sections
- `ui/components/*`: dialogs and focused domain-specific UI pieces

The page file should stay thin:

- assemble sections and dialogs
- connect composables/store state to template
- avoid owning all rendering details and mutations inline

Each domain must not:

- import another domain's internal files directly unless that domain is an explicit dependency surface
- recreate shared UI primitives locally
- split into technical layers just for architecture aesthetics
- keep both old and new entrypoints alive

Allowed shared dependencies:

- `@/app/api/http`
- `@/shared/ui/*`
- `@/shared/lib/*`
- `@/app/access/*`
- `@/app/navigation/*` when the dependency is truly app-level
- `@/domains/auth/store`

## Migration Strategy

Do not rewrite the whole app at once.

Use this order:

1. Move one bounded context completely under `src/domains/<name>`.
2. Keep non-UI files flat unless complexity proves otherwise.
3. Split UI into `pages`, `sections`, `blocks`, `components` only where readability benefits.
4. Update imports to domain paths.
5. Point routes directly to `src/domains/<name>/ui/pages/*Page.vue` or `src/app/pages/*` for truly application-level screens.
6. Delete old files from legacy roots such as `src/pages`, `src/api`, `src/stores`.
7. Repeat domain by domain.

## Pilot Domain

`admins` is the first pilot because it is isolated and CRUD-heavy without the more dynamic UX of `agents`.

Pilot outcome:

- `src/domains/admins/api.js`
- `src/domains/admins/admins.utils.js`
- `src/domains/admins/store.js`
- `src/domains/admins/ui/pages/AdminsPage.vue`
- `src/domains/admins/ui/components/*`

Legacy admin entrypoints are removed after migration.

## Why Agents Need UI Splitting

`agents` is exactly the case where a flat single-page file stops helping:

- live filters
- grouped cards
- sticky summary behavior
- multiple dialogs
- optimistic action loaders
- contextual actions and token flows

For that kind of screen, keeping a thin page plus `useAgentsPage.js`, `ui/sections/*`, and `ui/blocks/*` is simpler than a single giant SFC and still much simpler than a heavy enterprise layering scheme.

## Definition Of Done For A Migrated Domain

A domain is considered migrated when:

- route points directly to `src/domains/<name>/ui/pages/*Page.vue`
- store lives in `src/domains/<name>/store.js`
- API client lives in `src/domains/<name>/api.js`
- page-specific helpers live next to the domain in `src/domains/<name>/*.utils.js`
- large route logic is extracted when the page would otherwise become oversized
- UI is split only as much as needed to keep the route readable
- there are no duplicate domain files left under legacy roots such as `src/pages`, `src/api`, `src/stores`
- there are no dependencies on removed legacy roots such as `src/components`, `src/config`, `src/plugins`, `src/layouts`, `src/composables`, `src/utils`
