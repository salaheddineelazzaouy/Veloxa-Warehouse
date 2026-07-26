# Veloxa Warehouse — Enterprise Roadmap

Prioritized by what actually blocks enterprise deals (RFP hard-requirements first), then by dependency order (some features need others underneath them). Security items from the earlier review are folded in at the top since they block everything else.

---

## Phase 0 — Security & Trust Foundation (blocks all enterprise sales)
*No enterprise buyer signs a contract without these. Do this before adding any new feature.*

1. Fix privilege escalation on register/profile (`role` field writable)
2. Implement real RBAC — wire `apps/accounts/permissions.py` into every API view via a permission class
3. Resolve the CRM encryption regression (migration 0005 silently dropped field encryption while marketing still claims it)
4. Fix tenant isolation reliance on `threading.local()` — audit every management command / async path for cross-tenant leakage
5. Rotate & externalize secrets (env → secrets manager)
6. JWT blacklisting on logout, pagination bypass removed/restricted
7. Sentry wired up, health/readiness endpoints, structured logging with correlation IDs

**Exit criteria:** a third-party pentest or SOC 2 readiness review wouldn't flag a critical.

---

## Phase 1 — Core Domain Gaps (RFP hard-blockers)
*These are the features that get a WMS eliminated in the first round of enterprise evaluation, regardless of how polished everything else is.*

| # | Feature | Why it's P1 |
|---|---|---|
| 1.1 | **Warehouse entity** (not just flat `Location` codes) | Multi-warehouse is assumed table-stakes; almost every mid-size buyer has >1 site |
| 1.2 | **Purchase Order lifecycle** as a real model (line items, approval, partial receipt, variance) | Currently just a free-text `po_ref` string — no enterprise procurement team will accept this |
| 1.3 | **Sales Order lifecycle** distinct from Invoice (draft → confirmed → picking → shipped → invoiced) | Same gap on the outbound side |
| 1.4 | **Lot/batch & serial number tracking** | Hard compliance requirement for pharma, food, electronics-with-warranty verticals |
| 1.5 | **Stock reservations/allocations** | DONE — `StockReservation` model, `reserve_stock`/`confirm_reservation`/`release_reservation` services, `available_stock` endpoint, `expire_stale_reservations` job |
| 1.6 | **Bin/zone/aisle location hierarchy** | Flat location codes don't support pick-path logic buyers expect |
| 1.7 | **Approval / maker-checker workflow** for adjustments, large POs | Internal controls requirement in most enterprise finance/audit policies |

**Exit criteria:** you can answer "yes" to the multi-warehouse, lot-tracking, and PO/SO lifecycle line items on a typical WMS RFP checklist.

---

## Phase 2 — Warehouse Floor Operations
*Needed once you're selling to companies with actual pick/pack/ship teams, not just back-office inventory tracking.*

1. Barcode/QR scanning (add barcode field to `Product`, scan-to-confirm flows)
2. Pick list generation + wave/batch picking + picker assignment
3. Directed put-away workflow on inbound
4. Packing station / LPN (license plate / carton-pallet) management
5. Returns / RMA model (currently nonexistent)
6. Stock status dimension: available / damaged / quarantined / in-transit
7. Cross-warehouse transfer orders with in-transit tracking
8. Cycle counting workflows (scheduled plans, blind counts, variance approval) — extends existing `reconcile()`

**Exit criteria:** a warehouse supervisor could run a full day's operations (receive → putaway → pick → pack → ship) without leaving the system.

---

## Phase 3 — Finance & Costing Maturity
*Needed to pass finance/controller sign-off at enterprise accounts.*

1. Selectable costing method (FIFO/LIFO/weighted-average) — currently average-cost only
2. Landed cost allocation (freight, duties → inventory value)
3. Multi-currency support
4. Tax engine (VAT/TVA calculation on invoice lines — ICE/IF/TP/RC fields exist but no actual tax logic)
5. Credit notes / return crediting model
6. AR aging & payment terms for customer invoices (currently `PaymentTransaction` only covers subscriptions)
7. Formal inventory valuation report with historical snapshots
8. Three-way matching (PO ↔ receipt ↔ supplier invoice)

**Exit criteria:** finance can close the books using system-generated valuation and AR reports without a spreadsheet workaround.

---

## Phase 4 — Supplier & Demand Side
*Rounds out procurement; needed for companies with formal vendor management.*

1. Supplier/vendor master data (symmetric to the existing `Customer`/CRM model)
2. RFQ / quote comparison workflow
3. Supplier performance metrics (on-time %, rejection rate)
4. Reorder point / min-max per product per location → auto-PO suggestions
5. Kitting / BOM (assemble/decompose kit SKUs)
6. Unit-of-measure conversion table

---

## Phase 5 — Reporting, Analytics & Compliance Ops
*Differentiates "functional" from "enterprise-polished." Also where audit/compliance teams start asking questions.*

1. ABC analysis, inventory turnover, dead-stock, OTIF/fill-rate reports
2. Scheduled report exports (PDF/Excel on a cadence)
3. Audit log retention/purge job (plan already advertises `audit_log_retention_days`; nothing enforces it)
4. GDPR/CNDP subject-access export flow (you have anonymization; add full data export)
5. Enforce `SubscriptionPlan.features` limits at actual write time (currently only partially checked)
6. Custom report builder for non-technical users

---

## Phase 6 — Integration & Platform Extensibility
*Last because it's valuable but rarely a deal-blocker — more of a scale/ecosystem play once core is solid.*

1. Public API versioning (`/api/v1/...`) + OpenAPI schema (`drf-spectacular`) — you already advertise "full OpenAPI docs," it doesn't exist yet
2. Webhooks for stock/order events
3. Bulk CSV import/export tooling (beyond dev-only Faker seed commands)
4. EDI/e-commerce integrations (Shopify, WooCommerce)
5. Shipping carrier integration (label gen, tracking, rate shopping)
6. Per-tenant API rate limiting tied to plan (not just global anon/user throttle)

---

## Suggested sequencing at a glance

```
Phase 0 (security)         →  weeks 1–4    — non-negotiable, do first
Phase 1 (domain gaps)      →  weeks 5–14   — biggest RFP risk reduction per engineering hour
Phase 2 (floor ops)        →  weeks 15–22
Phase 3 (finance)          →  weeks 20–28  — can overlap tail of Phase 2
Phase 4 (supplier/demand)  →  weeks 26–32  — can overlap
Phase 5 (reporting/comp.)  →  weeks 30–36  — can overlap
Phase 6 (integrations)     →  weeks 34+    — ongoing, prioritize per customer ask
```

Phases 3–5 have real overlap potential since they touch different parts of the codebase (finance app, reporting layer, subscriptions) and can run on parallel workstreams once Phase 1's domain models (PO/SO/Warehouse) exist as a foundation.
