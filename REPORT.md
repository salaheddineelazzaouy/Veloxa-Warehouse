# Veloxa Warehouse — Full Project Scan Report

**Date:** 2026-07-22

---

## Architecture

- **Backend**: Django 5.0 + DRF + SimpleJWT, 9 apps (accounts, tenants, warehouse, backorder, finance, crm, audit, landing, subscriptions)
- **Frontend**: React 19 + Vite 8 SPA, 15 components, hash-based routing, JWT auth
- **Multi-tenant** via thread-local `TenantAwareManager`

---

## CRITICAL Issues

| # | Issue | Location |
|---|---|---|
| 1 | **Privilege escalation on register** — user can self-assign `super_admin` role | `accounts/serializers.py:11` |
| 2 | **Privilege escalation on profile** — any user can PATCH their own `role` | `accounts/views.py:57` + `accounts/serializers.py:53` |
| 3 | **No RBAC in any API view** — all endpoints only check `IsAuthenticated`, never check `role`. A `viewer` can delete invoices, anonymize customers, modify stock | All API views across 9 apps |
| 4 | **Fragile tenant isolation** — relies on `threading.local()`. Breaks in async/Celery/management commands. Returns **unfiltered** data when unset | `tenants/utils.py`, `tenants/managers.py:9` |
| 5 | **Hardcoded secrets** in `.env` and `docker-compose.yml` | `.env:1-10`, `docker-compose.yml:38-46` |

---

## HIGH Issues

| # | Issue | Location |
|---|---|---|
| 6 | **Stock race condition** — `select_for_update` locks Product, but stock is computed from StockMovement (unlocked) | `warehouse/services/outbound.py:34` |
| 7 | **Mass assignment** — all 8 landing serializers use `fields = "__all__"` | `landing/api/serializers.py` (all) |
| 8 | **JWT not blacklisted** — `token_blacklist` not in INSTALLED_APPS, old tokens remain valid | `config/settings/base.py:126` |
| 9 | **Pagination bypass** — `?all=1` dumps entire database | `lib/pagination.py:10` |
| 10 | **FormData Content-Type broken** — `apiFetch` forces `application/json` on FormData uploads (payment proof images) | `api/client.js:22` |
| 11 | **JWT refresh race condition** — concurrent 401s trigger duplicate refreshes | `api/client.js:25-41` |
| 12 | **Event listener memory leak** — anonymous fn in cleanup never removes listener | `MovementModal.jsx:11-12` |
| 13 | **Missing security headers** — no `SECURE_CONTENT_TYPE_NOSNIFF`, no `SESSION_COOKIE_HTTPONLY` | `config/settings/base.py`, `prod.py` |
| 14 | **Weak SECRET_KEY fallback** — hardcoded `"insecure-dev-key-change-in-prod"` | `base.py:7` |

---

## MEDIUM Issues

| # | Issue | Location |
|---|---|---|
| 15 | **No account lockout** — brute-force login possible | `accounts/views.py`, `config/views.py:30` |
| 16 | **No rate limit on public endpoints** — registration, leads | Multiple |
| 17 | **CKEditor `allowedContent: True`** — stored XSS via page content | `base.py:141` |
| 18 | **Payment proof upload** — `FileField` accepts any file type | `subscriptions/models.py:114` |
| 19 | **`check_limits` trusts client data** — client sends `current_usage` | `subscriptions/views.py:81` |
| 20 | **10 silent error catches** in frontend — `.catch(() => {})` hides failures | Dashboard, Customers, Finance, etc. |
| 21 | **Broken signup link** — `<a href="/signup/">` not a hash route, 404s | `LoginPage.jsx:37` |
| 22 | **CDN without SRI** — Font Awesome loaded without integrity hash | `index.html:7` |
| 23 | **No nav active state on detail pages** — `#/inventory/detail/5` doesn't highlight Inventory | `Layout.jsx:32` |
| 24 | **`AnomalyCheckView` uncaught ValueError** — non-numeric params crash | `audit/api/views.py:29` |
| 25 | **Docker runs as root, uses `runserver`, exposes DB/Redis ports** | `Dockerfile`, `docker-compose.yml` |

---

## LOW Issues

| # | Issue | Location |
|---|---|---|
| 26 | `fmt()` duplicated in 6 files, `dt()` in 7 files — extract to shared util | Multiple components |
| 27 | Unused dependency `react-router-dom` (~40KB) — app uses hash routing | `package.json` |
| 28 | `App.css` unused Vite boilerplate (184 lines) | `src/App.css` |
| 29 | `App.jsx:3` imports `App.css` — should be removed | `App.jsx:3` |
| 30 | No loading/disabled state on MovementModal submit button | `MovementModal.jsx:70` |
| 31 | `prompt()` in Backorders — empty string -> qty 0 submitted | `Backorders.jsx:32` |
| 32 | Counts show `customers.length` not `totalCount` | `Customers.jsx:105` |
| 33 | Celery in requirements but no `celery.py` config | requirements vs code |
| 34 | `backorder/admin.py` empty — model invisible in admin | `backorder/admin.py` |
| 35 | `landing/manage` views only `@login_required` — any user can edit | `config/views.py:505-753` |

---

## Recommended Fix Priority

### Immediate

1. **Add `read_only_fields` to `UserSerializer`** — set `read_only_fields = ("id", "username", "role", "is_active", "date_joined")`. Remove `role` from `RegisterSerializer` fields or hardcode it to `"viewer"`.
2. **Create a `RoleBasedPermission` class** — reference the already-defined groups in `apps/accounts/permissions.py` and apply to every API view.
3. **Fix FormData upload** — in `api/client.js`, delete `Content-Type` header when body is a `FormData` instance so the browser sets `multipart/form-data` automatically.
4. **Fix MovementModal memory leak** — store handler reference in a variable and reuse in cleanup.
5. **Rotate all secrets** — remove hardcoded credentials from `docker-compose.yml`.

### This Sprint

6. Add `token_blacklist` to INSTALLED_APPS and `BLACKLIST_AFTER_ROTATION: True` to SIMPLE_JWT.
7. Replace all `fields = "__all__"` in landing serializers with explicit field lists.
8. Add explicit `obj.tenant == request.user.tenant` checks in views fetching objects by PK.
9. Add missing security headers to `prod.py`.
10. Remove the `?all=1` pagination bypass or restrict to admin users only.

### Next Sprint

11. Implement JWT blacklisting on logout.
12. Add throttling to public endpoints (registration, leads).
13. Implement account lockout after failed login attempts.
14. Add file type validation on payment proof upload.
15. Compute subscription limits server-side instead of trusting client input.
16. Fix all silent `.catch(() => {})` in the frontend to show error feedback.
17. Fix the broken signup link in `LoginPage.jsx`.
