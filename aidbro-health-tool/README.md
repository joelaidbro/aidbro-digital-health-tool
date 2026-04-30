# Aidbro Digital Health Tool

Aidbro Digital Health Tool is a full-stack audit platform for evaluating a business's digital presence, generating a free AI-assisted health score, converting users into paid detailed audits, and managing delivery through an internal admin workspace.

The project currently includes:

- A public audit tool for free digital health checks
- Custom Aidbro branding with site logo, footer, and floating WhatsApp action
- Internal About, Privacy Policy, Terms, Return Policy, and Contact pages hosted on the same domain
- Google Places and PageSpeed based website/profile analysis
- SEO crawl, social detection, competitor snapshot, and AI insights
- Required mobile capture with country-code aware validation
- User authentication and saved search history
- Paid detailed audits with Razorpay
- A client portal for paid report tracking and downloads
- A separate admin panel for operations, review, and report delivery

## 1. High-Level Architecture

```text
Frontend (React + Vite)
  |- Public free audit app
  |- Internal legal / policy / company info pages
  |- Auth / register / login pages
  |- Upgrade / payment page
  |- Client portal
  |- Separate admin app

Backend (FastAPI + SQLAlchemy Async)
  |- Audit engine
  |- Auth + Google OAuth
  |- Payment + portal APIs
  |- Admin APIs
  |- Scoring, SEO, PDF, competitor, and AI services

Database (PostgreSQL)
  |- Searches
  |- Leads
  |- Users
  |- Payment orders
  |- Audit jobs
  |- Detailed audits
  |- Admin users
```

## 2. Main Product Flow

1. A visitor searches for a business.
2. The backend gathers Google, website, SEO, social, and competitor data.
3. A weighted score is calculated across multiple pillars.
4. The user sees a free result and can download a free PDF.
5. Logged-in users can save searches in history.
6. A user can pay for a detailed audit for a specific saved search.
7. The admin team reviews the paid audit, adds manual inputs, and approves the report.
8. The client accesses the report from the portal.

## 3. Core Features

- Free digital health audit
- Google Business profile analysis
- Website performance and SEO scoring
- Social media presence detection and manual correction
- Competitor snapshot and keyword gap discovery
- AI-generated summary and recommendations
- Search history per logged-in user
- Paid audit purchase per selected search
- Admin operations console
- PDF export for free and paid flows
- Same-domain company/legal pages with direct routes
- Shared footer and floating WhatsApp CTA
- Anonymous search limiting by IP
- Search result stability cache for repeat checks
- Confidence-based Google profile matching
- Search-specific paid audit status and report access in the portal
- Full audit snapshot viewing inside admin detail screens

## 4. Tech Stack

### Frontend

- React 18
- React DOM
- Vite
- Axios

### Backend

- FastAPI
- Uvicorn
- SQLAlchemy Async
- asyncpg
- psycopg2-binary
- Alembic
- python-jose
- passlib
- Razorpay Python SDK
- httpx
- requests
- BeautifulSoup4
- lxml
- Groq SDK
- ReportLab
- Pillow
- python-dotenv
- Pydantic

## 5. Repository Structure

```text
aidbro-health-tool/
  backend/
    database/
    routes/
    services/
    utils/
    main.py
    requirements.txt
    env.example
  frontend/
    admin/
    about-us/
    auth/
    contact-us/
    login/
    portal/
    privacy-policy/
    public/
    register/
    return-policy/
    src/
    terms-and-conditions/
    upgrade/
    aidbroai-logo.png
    admin.html
    index.html
    package.json
    vite.config.js
  test/
    pagespeedtest.py
    test_seo_crawler.py
```

## 6. Folder-by-Folder Explanation

### `backend/`

The FastAPI server, business logic, database models, and audit services live here.

#### Important backend root files

| File | Purpose |
|---|---|
| [backend/main.py](D:\Joel\Job\AidBro\Business%20Digital%20Health\aidbro-health-tool\backend\main.py) | FastAPI entry point, CORS setup, startup lifecycle, and route registration |
| [backend/requirements.txt](D:\Joel\Job\AidBro\Business%20Digital%20Health\aidbro-health-tool\backend\requirements.txt) | Python dependency list |
| [backend/env.example](D:\Joel\Job\AidBro\Business%20Digital%20Health\aidbro-health-tool\backend\env.example) | Backend environment variable template |
| `backend/.env` | Local or server runtime secrets. Do not commit this file |

#### `backend/database/`

| File | Purpose |
|---|---|
| [backend/database/connection.py](D:\Joel\Job\AidBro\Business%20Digital%20Health\aidbro-health-tool\backend\database\connection.py) | Async engine/session setup, DB connectivity, table creation |
| [backend/database/models.py](D:\Joel\Job\AidBro\Business%20Digital%20Health\aidbro-health-tool\backend\database\models.py) | SQLAlchemy models for searches, users, payments, audits, and admin users |
| [backend/database/crud.py](D:\Joel\Job\AidBro\Business%20Digital%20Health\aidbro-health-tool\backend\database\crud.py) | Reusable DB operations used by the route layer |

#### `backend/routes/`

| File | Purpose |
|---|---|
| [backend/routes/audit.py](D:\Joel\Job\AidBro\Business%20Digital%20Health\aidbro-health-tool\backend\routes\audit.py) | Main audit execution, free PDF generation, anonymous limits, 24-hour score cache |
| [backend/routes/auth.py](D:\Joel\Job\AidBro\Business%20Digital%20Health\aidbro-health-tool\backend\routes\auth.py) | Email/password auth, Google OAuth, admin login |
| [backend/routes/payment.py](D:\Joel\Job\AidBro\Business%20Digital%20Health\aidbro-health-tool\backend\routes\payment.py) | Razorpay order creation, payment verification, webhook handling, payment status |
| [backend/routes/portal.py](D:\Joel\Job\AidBro\Business%20Digital%20Health\aidbro-health-tool\backend\routes\portal.py) | Client portal APIs for history, audit status, reports, and PDFs |
| [backend/routes/admin.py](D:\Joel\Job\AidBro\Business%20Digital%20Health\aidbro-health-tool\backend\routes\admin.py) | Admin dashboard, users, anonymous searches, legacy leads, audit queue, analytics |
| [backend/routes/leads.py](D:\Joel\Job\AidBro\Business%20Digital%20Health\aidbro-health-tool\backend\routes\leads.py) | Lead management endpoints kept for legacy/free-tool CRM flows |

#### `backend/services/`

| File | Purpose |
|---|---|
| [backend/services/google_places.py](D:\Joel\Job\AidBro\Business%20Digital%20Health\aidbro-health-tool\backend\services\google_places.py) | Google Places business lookup with confidence-based profile matching |
| [backend/services/pagespeed.py](D:\Joel\Job\AidBro\Business%20Digital%20Health\aidbro-health-tool\backend\services\pagespeed.py) | PageSpeed Insights analysis and website URL normalization |
| [backend/services/social_check.py](D:\Joel\Job\AidBro\Business%20Digital%20Health\aidbro-health-tool\backend\services\social_check.py) | Social media profile detection and manual social-link merge logic |
| [backend/services/seo_crawler.py](D:\Joel\Job\AidBro\Business%20Digital%20Health\aidbro-health-tool\backend\services\seo_crawler.py) | On-page SEO crawl and check extraction |
| [backend/services/seo_recommendations.py](D:\Joel\Job\AidBro\Business%20Digital%20Health\aidbro-health-tool\backend\services\seo_recommendations.py) | Human-readable SEO recommendations from crawl data |
| [backend/services/scorer.py](D:\Joel\Job\AidBro\Business%20Digital%20Health\aidbro-health-tool\backend\services\scorer.py) | Core digital health scoring engine |
| [backend/services/competitor_analyzer.py](D:\Joel\Job\AidBro\Business%20Digital%20Health\aidbro-health-tool\backend\services\competitor_analyzer.py) | Competitor extraction and comparison summary |
| [backend/services/keyword_extractor.py](D:\Joel\Job\AidBro\Business%20Digital%20Health\aidbro-health-tool\backend\services\keyword_extractor.py) | Keyword extraction and competitive gap discovery |
| [backend/services/ai_writer.py](D:\Joel\Job\AidBro\Business%20Digital%20Health\aidbro-health-tool\backend\services\ai_writer.py) | AI-generated executive summary and CTA text |
| [backend/services/contact_finder.py](D:\Joel\Job\AidBro\Business%20Digital%20Health\aidbro-health-tool\backend\services\contact_finder.py) | Website email discovery helper |
| [backend/services/pdf_generator.py](D:\Joel\Job\AidBro\Business%20Digital%20Health\aidbro-health-tool\backend\services\pdf_generator.py) | PDF report creation for audit exports |

#### `backend/utils/`

| File | Purpose |
|---|---|
| [backend/utils/auth_utils.py](D:\Joel\Job\AidBro\Business%20Digital%20Health\aidbro-health-tool\backend\utils\auth_utils.py) | JWT creation, password hashing, password verification |
| [backend/utils/admin_setup.py](D:\Joel\Job\AidBro\Business%20Digital%20Health\aidbro-health-tool\backend\utils\admin_setup.py) | Script to create the first admin user |

### `frontend/`

The React frontend contains both the public client app and the admin app.

#### Important frontend root files

| File | Purpose |
|---|---|
| [frontend/package.json](D:\Joel\Job\AidBro\Business%20Digital%20Health\aidbro-health-tool\frontend\package.json) | Frontend scripts and dependencies |
| [frontend/vite.config.js](D:\Joel\Job\AidBro\Business%20Digital%20Health\aidbro-health-tool\frontend\vite.config.js) | Vite multi-page setup, dev proxy, and build config |
| [frontend/index.html](D:\Joel\Job\AidBro\Business%20Digital%20Health\aidbro-health-tool\frontend\index.html) | Main public app entry HTML |
| [frontend/admin.html](D:\Joel\Job\AidBro\Business%20Digital%20Health\aidbro-health-tool\frontend\admin.html) | Admin app entry HTML |
| [frontend/.env.example](D:\Joel\Job\AidBro\Business%20Digital%20Health\aidbro-health-tool\frontend\.env.example) | Frontend environment template |
| [frontend/aidbroai-logo.png](D:\Joel\Job\AidBro\Business%20Digital%20Health\aidbro-health-tool\frontend\aidbroai-logo.png) | Main logo asset used across the public frontend |

#### `frontend/src/`

##### App and config

| File | Purpose |
|---|---|
| [frontend/src/main.jsx](D:\Joel\Job\AidBro\Business%20Digital%20Health\aidbro-health-tool\frontend\src\main.jsx) | Main React bootstrapping entry |
| [frontend/src/App.jsx](D:\Joel\Job\AidBro\Business%20Digital%20Health\aidbro-health-tool\frontend\src\App.jsx) | Route-level app switching between free audit, auth, portal, and upgrade flows |
| [frontend/src/config/api.js](D:\Joel\Job\AidBro\Business%20Digital%20Health\aidbro-health-tool\frontend\src\config\api.js) | API base configuration for local and deployed environments |
| [frontend/src/content/siteContent.js](D:\Joel\Job\AidBro\Business%20Digital%20Health\aidbro-health-tool\frontend\src\content\siteContent.js) | Central source for policy/company-page content, contact details, and footer links |
| [frontend/src/context/AuthContext.jsx](D:\Joel\Job\AidBro\Business%20Digital%20Health\aidbro-health-tool\frontend\src\context\AuthContext.jsx) | Auth state, token storage, and authenticated fetch helper |

##### Pages

| File | Purpose |
|---|---|
| [frontend/src/pages/AuthPage.jsx](D:\Joel\Job\AidBro\Business%20Digital%20Health\aidbro-health-tool\frontend\src\pages\AuthPage.jsx) | Login and registration UI |
| [frontend/src/pages/AuthCallbackPage.jsx](D:\Joel\Job\AidBro\Business%20Digital%20Health\aidbro-health-tool\frontend\src\pages\AuthCallbackPage.jsx) | Google OAuth callback handler |
| [frontend/src/pages/InfoPage.jsx](D:\Joel\Job\AidBro\Business%20Digital%20Health\aidbro-health-tool\frontend\src\pages\InfoPage.jsx) | Shared renderer for About, Privacy, Terms, Return Policy, and Contact pages |
| [frontend/src/pages/PaymentPage.jsx](D:\Joel\Job\AidBro\Business%20Digital%20Health\aidbro-health-tool\frontend\src\pages\PaymentPage.jsx) | Detailed audit purchase flow |
| [frontend/src/pages/ClientPortal.jsx](D:\Joel\Job\AidBro\Business%20Digital%20Health\aidbro-health-tool\frontend\src\pages\ClientPortal.jsx) | Saved searches, paid audit status, reports, and download actions |

##### Components

| File | Purpose |
|---|---|
| [frontend/src/components/SearchForm.jsx](D:\Joel\Job\AidBro\Business%20Digital%20Health\aidbro-health-tool\frontend\src\components\SearchForm.jsx) | Public input form for business audits |
| [frontend/src/components/ResultsDashboard.jsx](D:\Joel\Job\AidBro\Business%20Digital%20Health\aidbro-health-tool\frontend\src\components\ResultsDashboard.jsx) | Main results view, premium gating, live warnings, social improvement, and PDF action |
| [frontend/src/components/SiteLogo.jsx](D:\Joel\Job\AidBro\Business%20Digital%20Health\aidbro-health-tool\frontend\src\components\SiteLogo.jsx) | Shared logo renderer used across public pages |
| [frontend/src/components/SiteFooter.jsx](D:\Joel\Job\AidBro\Business%20Digital%20Health\aidbro-health-tool\frontend\src\components\SiteFooter.jsx) | Shared footer with internal policy links and contact details |
| [frontend/src/components/FloatingWhatsApp.jsx](D:\Joel\Job\AidBro\Business%20Digital%20Health\aidbro-health-tool\frontend\src\components\FloatingWhatsApp.jsx) | Persistent floating WhatsApp button for public pages |
| [frontend/src/components/SeoReport.jsx](D:\Joel\Job\AidBro\Business%20Digital%20Health\aidbro-health-tool\frontend\src\components\SeoReport.jsx) | SEO crawler report UI |
| [frontend/src/components/CompetitorTable.jsx](D:\Joel\Job\AidBro\Business%20Digital%20Health\aidbro-health-tool\frontend\src\components\CompetitorTable.jsx) | Paid competitor and keyword gap presentation |
| [frontend/src/components/SocialImprove.jsx](D:\Joel\Job\AidBro\Business%20Digital%20Health\aidbro-health-tool\frontend\src\components\SocialImprove.jsx) | Manual social link correction and re-audit |
| [frontend/src/components/ContactCapture.jsx](D:\Joel\Job\AidBro\Business%20Digital%20Health\aidbro-health-tool\frontend\src\components\ContactCapture.jsx) | Lead/contact capture after audit |
| [frontend/src/components/ScoreRing.jsx](D:\Joel\Job\AidBro\Business%20Digital%20Health\aidbro-health-tool\frontend\src\components\ScoreRing.jsx) | Circular score display |
| [frontend/src/components/PillarChart.jsx](D:\Joel\Job\AidBro\Business%20Digital%20Health\aidbro-health-tool\frontend\src\components\PillarChart.jsx) | Pillar comparison summary chart |
| [frontend/src/components/useAuditPrice.js](D:\Joel\Job\AidBro\Business%20Digital%20Health\aidbro-health-tool\frontend\src\components\useAuditPrice.js) | Price fetch helper from backend payment status |
| [frontend/src/components/LoadingScreen.jsx](D:\Joel\Job\AidBro\Business%20Digital%20Health\aidbro-health-tool\frontend\src\components\LoadingScreen.jsx) | Audit loading state |

##### Styles

| File | Purpose |
|---|---|
| [frontend/src/index.css](D:\Joel\Job\AidBro\Business%20Digital%20Health\aidbro-health-tool\frontend\src\index.css) | Main visual system and most client UI styles |
| [frontend/src/App.css](D:\Joel\Job\AidBro\Business%20Digital%20Health\aidbro-health-tool\frontend\src\App.css) | App shell styles |
| [frontend/src/additions.css](D:\Joel\Job\AidBro\Business%20Digital%20Health\aidbro-health-tool\frontend\src\additions.css) | Supplemental styling from earlier iterations |
| [frontend/src/additions_v2.css](D:\Joel\Job\AidBro\Business%20Digital%20Health\aidbro-health-tool\frontend\src\additions_v2.css) | Additional UI refinements, especially around results/social flows |
| [frontend/src/stage4.css](D:\Joel\Job\AidBro\Business%20Digital%20Health\aidbro-health-tool\frontend\src\stage4.css) | Portal / payment / Stage 4 related styling |

#### `frontend/admin/`

The internal admin frontend runs separately from the public app.

| File | Purpose |
|---|---|
| [frontend/admin/main.jsx](D:\Joel\Job\AidBro\Business%20Digital%20Health\aidbro-health-tool\frontend\admin\main.jsx) | Admin React entry |
| [frontend/admin/AdminApp.jsx](D:\Joel\Job\AidBro\Business%20Digital%20Health\aidbro-health-tool\frontend\admin\AdminApp.jsx) | Admin shell, auth state, sidebar, page switching |
| [frontend/admin/admin.css](D:\Joel\Job\AidBro\Business%20Digital%20Health\aidbro-health-tool\frontend\admin\admin.css) | Admin styles |

##### Admin pages

| File | Purpose |
|---|---|
| [frontend/admin/pages/AdminLogin.jsx](D:\Joel\Job\AidBro\Business%20Digital%20Health\aidbro-health-tool\frontend\admin\pages\AdminLogin.jsx) | Admin login form |
| [frontend/admin/pages/Analytics.jsx](D:\Joel\Job\AidBro\Business%20Digital%20Health\aidbro-health-tool\frontend\admin\pages\Analytics.jsx) | Admin dashboard metrics and alerts |
| [frontend/admin/pages/AnonymousSearches.jsx](D:\Joel\Job\AidBro\Business%20Digital%20Health\aidbro-health-tool\frontend\admin\pages\AnonymousSearches.jsx) | Anonymous-search monitoring |
| [frontend/admin/pages/AnonymousSearchDetail.jsx](D:\Joel\Job\AidBro\Business%20Digital%20Health\aidbro-health-tool\frontend\admin\pages\AnonymousSearchDetail.jsx) | Detail view for anonymous searches |
| [frontend/admin/pages/UsersTable.jsx](D:\Joel\Job\AidBro\Business%20Digital%20Health\aidbro-health-tool\frontend\admin\pages\UsersTable.jsx) | Registered-user listing |
| [frontend/admin/pages/UserDetail.jsx](D:\Joel\Job\AidBro\Business%20Digital%20Health\aidbro-health-tool\frontend\admin\pages\UserDetail.jsx) | Registered-user detail and activity view |
| [frontend/admin/pages/LeadsTable.jsx](D:\Joel\Job\AidBro\Business%20Digital%20Health\aidbro-health-tool\frontend\admin\pages\LeadsTable.jsx) | Legacy leads CRM list |
| [frontend/admin/pages/LeadDetail.jsx](D:\Joel\Job\AidBro\Business%20Digital%20Health\aidbro-health-tool\frontend\admin\pages\LeadDetail.jsx) | Legacy lead detail view |
| [frontend/admin/pages/AuditQueue.jsx](D:\Joel\Job\AidBro\Business%20Digital%20Health\aidbro-health-tool\frontend\admin\pages\AuditQueue.jsx) | Paid audit queue |
| [frontend/admin/pages/AuditEditor.jsx](D:\Joel\Job\AidBro\Business%20Digital%20Health\aidbro-health-tool\frontend\admin\pages\AuditEditor.jsx) | Detailed audit workbench for analysts/managers |
| [frontend/admin/pages/TeamManagement.jsx](D:\Joel\Job\AidBro\Business%20Digital%20Health\aidbro-health-tool\frontend\admin\pages\TeamManagement.jsx) | Admin account management |
| [frontend/admin/components/SearchAuditSnapshot.jsx](D:\Joel\Job\AidBro\Business%20Digital%20Health\aidbro-health-tool\frontend\admin\components\SearchAuditSnapshot.jsx) | Shared full-result renderer used in admin detail views |

#### `frontend/auth/`, `frontend/login/`, `frontend/register/`, `frontend/portal/`, `frontend/upgrade/`

These folders contain HTML entry points so direct URLs like `/auth`, `/register`, `/portal`, and `/upgrade` work correctly in Vite's multi-page setup.

#### `frontend/about-us/`, `frontend/privacy-policy/`, `frontend/terms-and-conditions/`, `frontend/return-policy/`, `frontend/contact-us/`

These folders contain HTML entry points for the internal website pages so those routes work directly in development, build output, and production hosting without redirecting to another website.

### `test/`

This folder contains standalone backend validation scripts.

| File | Purpose |
|---|---|
| [test/pagespeedtest.py](D:\Joel\Job\AidBro\Business%20Digital%20Health\aidbro-health-tool\test\pagespeedtest.py) | Quick PageSpeed testing script |
| [test/test_seo_crawler.py](D:\Joel\Job\AidBro\Business%20Digital%20Health\aidbro-health-tool\test\test_seo_crawler.py) | SEO crawler validation script |

## 7. Database Model Summary

The current schema is built in SQLAlchemy and includes both newer search-centric structures and some legacy lead/payment structures.

Main entity groups:

- `Lead`: free-tool capture / legacy CRM layer
- `User`: authenticated client account
- `Search`: saved free audit search
- `PaymentOrder`: Razorpay order state
- `AuditJob`: purchased detailed audit for a specific search
- `DetailedAudit`: admin-edited detailed audit workspace
- `AuditClient`: legacy paid-client container still used by parts of the Stage 4 flow
- `AdminUser`: admin login accounts
- `UserActivityLog`: activity tracking

## 8. API Groups

All backend routes are mounted under `/api`.

### Audit

- `/api/audit`
- `/api/audit/pdf`

### Authentication

- `/api/auth/register`
- `/api/auth/login`
- `/api/auth/google/login`
- `/api/auth/google/callback`
- `/api/auth/me`
- `/api/auth/admin/login`

### Payment

- `/api/payment/create-order`
- `/api/payment/verify`
- `/api/payment/status`
- `/api/payment/webhook`

### Portal

- `/api/portal/status`
- `/api/portal/report`
- `/api/portal/report/pdf`
- `/api/portal/searches`
- `/api/portal/searches/{search_id}`

### Admin

- dashboard and analytics endpoints
- anonymous search monitoring
- registered user views
- legacy leads CRM
- paid audit queue and editing
- admin team management

## 9. Important Business Rules Already Implemented

### Search limiting

- Anonymous users can run 2 audits per IP in a rolling 7-day window
- Logged-in users are currently unlimited

### Contact capture

- A mobile number is required on the public audit form
- The form supports country-code selection and validates the local number length by country
- The submitted number is stored with the audit/search record and used as the primary manual phone contact

### Search history

- Logged-in users get saved search history
- Anonymous users do not get history access

### Paid audit ownership

- Detailed audit purchases are linked to a specific search, not just to the overall account
- Portal status, report view, and report PDF actions are resolved per selected paid search

### Public website shell

- The public app now uses a shared logo component instead of text-only brand text
- Parent-site/company-site redirects in the main navigation were removed
- About, Privacy Policy, Terms and Conditions, Return Policy, and Contact Us now live on the same Aidbro domain
- A shared footer and floating WhatsApp action are available across the public-facing pages

### Scoring model

- Website quality now carries 50% of the total digital health score
- The remaining score is distributed across Google Business profile, social presence, reputation, and competitor position
- The old Google "business description" scoring check was removed because Google Places `editorialSummary` is not a reliable proxy for the owner-entered GBP description

### Score consistency

- Identical searches may reuse the most recent audit snapshot for up to 24 hours
- This reduces visible score drift caused by live third-party data volatility

### Google profile safety

- The Google Places layer now uses confidence-based matching
- Low-confidence Google profile matches are excluded from scoring to avoid showing the wrong company
- Medium-confidence matches are still usable, but the UI shows a verification warning

### Social presence detection source

The current social checker is a lightweight presence detector, not an official platform API integration.

It combines:

- manually entered social links from the user
- website HTML scraping for known platform URLs such as Instagram, Facebook, LinkedIn, YouTube, and X
- WhatsApp presence inference from detected business phone numbers

It does not currently fetch follower counts, post frequency, engagement metrics, or platform-authenticated account analytics

## 10. Environment Variables

Use [backend/env.example](D:\Joel\Job\AidBro\Business%20Digital%20Health\aidbro-health-tool\backend\env.example) and [frontend/.env.example](D:\Joel\Job\AidBro\Business%20Digital%20Health\aidbro-health-tool\frontend\.env.example) as references.

### Backend variables

- `GOOGLE_API_KEY`
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GROQ_API_KEY`
- `DATABASE_URL`
- `RAZORPAY_KEY_ID`
- `RAZORPAY_KEY_SECRET`
- `RAZORPAY_WEBHOOK_SECRET`
- `AUDIT_PRICE_INR`
- `PORTAL_ACCESS_DAYS`
- `JWT_SECRET`
- `ADMIN_JWT_SECRET`
- `JWT_EXPIRES_DAYS`
- `PASSWORD_HASH_ITERATIONS`
- `ENVIRONMENT`
- `FRONTEND_URL`
- `BACKEND_URL`
- `ADMIN_URL`
- `CORS_ALLOWED_ORIGINS`

### Frontend variables

- `VITE_API_BASE_URL`
- `VITE_BACKEND_DEV_PROXY_TARGET`

## 11. Local Development Setup

### Backend

```powershell
cd D:\Joel\Job\AidBro\Business Digital Health\aidbro-health-tool\backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Backend default URL:

```text
http://localhost:8000
```

Docs:

```text
http://localhost:8000/docs
```

### Frontend

```powershell
cd D:\Joel\Job\AidBro\Business Digital Health\aidbro-health-tool\frontend
npm install
npm run dev
```

Public app:

```text
http://localhost:5173
```

### Admin frontend

```powershell
cd D:\Joel\Job\AidBro\Business Digital Health\aidbro-health-tool\frontend
npm run dev:admin
```

Admin app:

```text
http://localhost:5174/admin.html
```

## 12. Production Deployment Notes

Current deployment model is designed for:

- Hostinger VPS
- CyberPanel / OpenLiteSpeed
- PostgreSQL on the VPS
- FastAPI backend behind reverse proxy
- Static frontend build served from `public_html`

Recommended production shape:

- Frontend served from `https://ai.aidbro.com`
- Backend served internally on `127.0.0.1:8000`
- `/api`, `/docs`, and `/openapi.json` proxied by OpenLiteSpeed

## 13. Files and Folders That Should Not Be Committed

- `backend/.env`
- `backend/venv/`
- `backend/.venv/`
- `backend/__pycache__/`
- `frontend/node_modules/`
- `frontend/dist/`
- `**/__pycache__/`
- `*.pyc`
- `.pytest_cache/`
- `.coverage`
- `htmlcov/`
- editor-specific folders such as `.vscode/` and `.idea/`

## 14. Known Technical Notes

- The database currently uses SQLAlchemy models plus startup `create_tables()`. Alembic is installed but not fully set up yet for structured schema migration history.
- Some legacy `Lead` / `AuditClient` paths still exist alongside newer `Search` / `AuditJob` flows.
- The project has gone through several iterations, so some CSS and older components still include legacy styling layers.
- The frontend is multi-page Vite, not a React Router SPA.

## 15. Recommended Next Improvements

- Introduce full Alembic migrations before major schema evolution
- Reduce remaining dependence on legacy paid-client structures
- Add automated email or WhatsApp notifications after audit approval
- Add more explicit Google match labeling at the pillar level
- Add monitoring and error logging for external API failures
- Add proper automated tests for payment, portal, and admin flows

## 16. Ownership Note

This README is intended as a working technical guide for development, deployment, debugging, and team handover. Keep it updated whenever:

- a route group is added
- payment or portal flow changes
- data model changes
- deployment structure changes
- new environment variables are introduced
