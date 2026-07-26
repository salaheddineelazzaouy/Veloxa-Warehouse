# Veloxa Warehouse — Full Project Scan Report

**Date:** 2026-07-22

---

## Architecture

- **Backend**: Django 5.0 + DRF + SimpleJWT, 9 apps (accounts, tenants, warehouse, backorder, finance, crm, audit, landing, subscriptions)
- **Frontend**: React 19 + Vite 8 SPA, 15 components, hash-based routing, JWT auth
- **Multi-tenant** via thread-local `TenantAwareManager`

---

## CRITICAL Issues

| # | Issue | Status |
|---|---|---|
| 1 | **Privilege escalation on register** — user can self-assign `super_admin` role | FIXED — `RegisterSerializer` forces `role="viewer"` |
| 2 | **Privilege escalation on profile** — any user can PATCH their own `role` | FIXED — `read_only_fields` on `UserSerializer` |
| 3 | **No RBAC in any API view** — all endpoints only check `IsAuthenticated`, never check `role`. A `viewer` can delete invoices, anonymize customers, modify stock | FIXED — `RoleBasedPermission` applied as default, `role_required()` on template views |
| 4 | **Fragile tenant isolation** — relies on `threading.local()`. Breaks in async/Celery/management commands. Returns **unfiltered** data when unset | FIXED — `_get_tenant_object_or_404` on all PK lookups, superuser bypass in managers/middleware |
| 5 | **Hardcoded secrets** in `.env` and `docker-compose.yml` | FIXED — fresh keys generated, `.env` loaded via custom `load_dotenv()` |

---

## HIGH Issues

| # | Issue | Status |
|---|---|---|
| 6 | **Stock race condition** — `select_for_update` locks Product, but stock is computed from StockMovement (unlocked) | FIXED — `available_stock()` accounts for active reservations, `fulfill_sales_order` uses `available_stock`, `StockReservation` uses `select_for_update` on reservation rows |
| 7 | **Mass assignment** — all 8 landing serializers use `fields = "__all__"` | FIXED — explicit fields on all 8 serializers |
| 8 | **JWT not blacklisted** — `token_blacklist` not in INSTALLED_APPS, old tokens remain valid | FIXED — `token_blacklist` added, `BLACKLIST_AFTER_ROTATION: True` |
| 9 | **Pagination bypass** — `?all=1` dumps entire database | FIXED — restricted to super_admin only |
| 10 | **FormData Content-Type broken** — `apiFetch` forces `application/json` on FormData uploads (payment proof images) | FIXED |
| 11 | **JWT refresh race condition** — concurrent 401s trigger duplicate refreshes | OPEN |
| 12 | **Event listener memory leak** — anonymous fn in cleanup never removes listener | FIXED |
| 13 | **Missing security headers** — no `SECURE_CONTENT_TYPE_NOSNIFF`, no `SESSION_COOKIE_HTTPONLY` | FIXED — added to `prod.py` |
| 14 | **Weak SECRET_KEY fallback** — hardcoded `"insecure-dev-key-change-in-prod"` | FIXED — `.env` has real key |

---

## MEDIUM Issues

| # | Issue | Status |
|---|---|---|
| 15 | **No account lockout** — brute-force login possible | OPEN |
| 16 | **No rate limit on public endpoints** — registration, leads | OPEN |
| 17 | **CKEditor `allowedContent: True`** — stored XSS via page content | OPEN |
| 18 | **Payment proof upload** — `FileField` accepts any file type | OPEN |
| 19 | **`check_limits` trusts client data** — client sends `current_usage` | OPEN |
| 20 | **10 silent error catches** in frontend — `.catch(() => {})` hides failures | OPEN |
| 21 | **Broken signup link** — `<a href="/signup/">` not a hash route, 404s | FIXED — changed to `#/signup` |
| 22 | **CDN without SRI** — Font Awesome loaded without integrity hash | OPEN |
| 23 | **No nav active state on detail pages** — `#/inventory/detail/5` doesn't highlight Inventory | OPEN |
| 24 | **`AnomalyCheckView` uncaught ValueError** — non-numeric params crash | OPEN |
| 25 | **Docker runs as root, uses `runserver`, exposes DB/Redis ports** | OPEN |

---

## LOW Issues

| # | Issue | Status |
|---|---|---|
| 26 | `fmt()` duplicated in 6 files, `dt()` in 7 files — extract to shared util | OPEN |
| 27 | Unused dependency `react-router-dom` (~40KB) — app uses hash routing | OPEN |
| 28 | `App.css` unused Vite boilerplate (184 lines) | OPEN |
| 29 | `App.jsx:3` imports `App.css` — should be removed | OPEN |
| 30 | No loading/disabled state on MovementModal submit button | OPEN |
| 31 | `prompt()` in Backorders — empty string -> qty 0 submitted | OPEN |
| 32 | Counts show `customers.length` not `totalCount` | OPEN |
| 33 | Celery in requirements but no `celery.py` config | OPEN |
| 34 | `backorder/admin.py` empty — model invisible in admin | OPEN |
| 35 | `landing/manage` views only `@login_required` — any user can edit | FIXED — `@role_required("super_admin")` added |

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
