# UI specification

A pragmatic, dashboard-style SPA. No marketing flourishes — this is an internal
tool whose users want speed and clarity, not animation.

## Design tokens

| Token        | Light                     | Dark                       |
| ------------ | ------------------------- | -------------------------- |
| `--bg`       | `#F8FAFC` (slate-50)      | `#020617` (slate-950)      |
| `--surface`  | `#FFFFFF`                 | `#0F172A` (slate-900)      |
| `--surface-2`| `#F1F5F9` (slate-100)     | `#1E293B` (slate-800)      |
| `--border`   | `#E2E8F0` (slate-200)     | `#1E293B` (slate-800)      |
| `--text`     | `#0F172A` (slate-900)     | `#F1F5F9` (slate-100)      |
| `--muted`    | `#475569` (slate-600)     | `#94A3B8` (slate-400)      |

Brand palette: teal scale `brand-50…950` (primary `brand-600 #0D9488`).
Action accent: orange `accent-500 #F97316` — reserved for the **Generate**
button, the single highest-cost action.

Font: **Plus Jakarta Sans** (300/400/500/600/700) from Google Fonts.

## Components

Everything is built on a tiny set of primitives in `web/src/components/ui.tsx`:

- `Button` — `primary | accent | outline | ghost | danger`, with `loading` prop.
- `Input`, `Textarea`, `Select` — share `input-base` utility class.
- `Field` — label + control + hint/error wrapper.
- `Card`, `EmptyState`, `Spinner`, `PageHeader`.

Layouts:

- **`Sidebar`** — collapses below `md`; admin items render only when
  `me.is_superuser`.
- **`Topbar`** — sticky, backdrop-blurred; theme toggle + email + sign out.
- **`ProtectedLayout`** — gate that redirects unauthenticated users to
  `/login?from=…`. An `adminOnly` variant guards `/admin/*`.

## Theming

`localStorage["joblab.theme"] = "light" | "dark"`. Applied before render in
`main.tsx` to prevent a flash. The toggle button in the topbar persists each
flip.

Respects `prefers-reduced-motion`: all transitions collapse to ~0 ms.

## Page-by-page

### `/login`

Single column, centred card. Email + password. Error message renders under the
password field. Theme toggle in the top-right corner (unauthenticated users can
still set their preference).

### `/` (Dashboard)

- Six wiki tiles linking into `/wiki/{entity}` with live counts.
- "Recent applications" list, last 5, click to detail.
- Empty state if no applications.

### `/wiki/:entity`

Two-column on `lg+`: list on the left, **right-rail form** for create/edit.
Tabs at the top to switch entity. Inline edit (click pencil → form populates).
Delete is a single button + native confirm.

Above the tabs: an **Import CV (PDF)** button. Disabled (with a link to
Settings) while no default provider is set. On success, shows a per-entity
breakdown: new / flagged-duplicate / skipped. Rows in the list whose
`possible_duplicate_of_id` is non-null carry an amber "Possible duplicate"
badge inline with the title.

### `/applications`

List of all applications with status chip. Inline "New application" form
expands above the list. Status uses tonally-distinct chips
(slate/blue/amber/emerald/red).

### `/applications/:id`

Three sections:

1. **Role details** — editable role/company/status/JD card; explicit Save
   button (no auto-save) so unintended JD edits don't silently propagate.
2. **Generate document** — type, provider, word_limit, extra_instructions,
   behaviour_name (only when type=behaviour, required to enable submit).
   The Generate button uses the **accent** colour to mark it as the costly
   action.
3. **Generated artifacts** — each `Artifact` rendered via `ArtifactViewer` with
   chips for type, behaviour name, provider, words used vs limit, attempts,
   plus a Copy button. If `warning_flag=true`, an amber banner explains the
   model couldn't meet the limit.

A side card on `lg+` holds **Feedback & notes**.

### `/settings`

Two stacked sections:

1. **Default AI provider** — dropdown listing only providers the user has a
   working key for (own + visible globals). Auto-selects the first available
   provider when none is set. Used by CV import + generation.
2. **My keys** — own keys + visible globals (own = trash icon; global = shield
   icon; premium-only globals additionally show a crown). Right-rail form has
   `Provider`, `Label`, `API key`, then `Test` (probes the key with a 1-token
   call) and `Add key` side-by-side. Result of `Test` shown inline (green tick
   on ok, red panel with the provider's message on failure).

### `/admin/users`

Table: email, role chip (toggleable), **premium** checkbox, active checkbox,
reset-password, delete. Inline "New user" form above the table.

### `/admin/llm-keys`

List of global keys with `Premium` checkbox per row and a crown icon when set.
Right-rail "New global key" form mirrors `/settings`: `Provider`, `Label`,
`API key`, `Premium users only` toggle, then `Test` + `Add key` side-by-side.

### Site-wide "no provider" banner

Amber strip mounted in the protected layout, above the main content. Renders
on every authenticated route except `/settings` while
`me.default_provider === null`, linking back to Settings.

## Accessibility

- All buttons that aren't text-labelled get `aria-label` (icons-only buttons).
- Focus rings: `focus:ring-2 focus:ring-brand-500/30` on inputs;
  `focus:ring-brand-500/40` on buttons.
- Colour is never the only indicator (chips include text labels).
- Form inputs always paired with `<label>` via `Field`.
- `prefers-reduced-motion` honoured globally.
- Light-mode body text is `--text` `#0F172A` on `--bg` `#F8FAFC` → contrast
  ratio ≈ 16.5:1. Dark-mode is `--text` `#F1F5F9` on `--bg` `#020617` ≈ 16.6:1.

## Icons

Lucide React only — no emojis. Standard size `h-4 w-4`. Sourced from
`lucide-react` so the bundle stays tree-shakable.
