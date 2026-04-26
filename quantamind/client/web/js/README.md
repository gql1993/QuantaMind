# Frontend Script Layout

- `core/`: shared runtime and shell helpers such as `BASE`, navigation, toast, and modal support.
- `pages/`: page-level scripts with concrete UI behavior, including `overview`, `chat`, `admin`, `pipeline`, `skills`, `settings`, `discovery`, `library`, and `datahub`.
- root `js/`: directory index and shared documentation.

Rule of thumb:

- Put cross-page helpers in `core/`.
- Put page-owned behavior in `pages/`.
- Avoid adding new inline scripts back into `index.html`.
- Prefer updating `pages/` files first.
