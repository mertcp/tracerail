# TraceRail CBM

Living plan for this repo. Updated 3 Nov 2026. Status: synthetic fleet seeded by `app/seed.py`. Next step is the API.

Open this file from the left file tree. In a new chat, say: read `PROJECT.md` and continue from the next unchecked step.

## What we are building

TraceRail is a demo SaaS for railway condition-based maintenance. It watches a synthetic fleet, ranks assets by risk of causing delay, and drafts a maintenance action a human can accept or edit. The job of the product is to move failures from the line into the depot.

Interview line: an operational fleet twin. Each asset has a live health state and a delay-risk forecast. Maintenance is recommended before the failure hits the timetable. The model is the asset record plus the health and delay-risk calculation. It is not a 3D or physics twin.

Pitch: detect degrading doors, brakes, HVAC, and traction early; open the right work order before the train holds the line.

Audience: a CV demo for cloud / SaaS solutions pre-sales roles. Mert currently works as a system engineer at a railway vehicle manufacturer. Use no data from that job.

## Why this shape

| Signal on the CV | What the demo shows |
|---|---|
| Cloud / SaaS | Hosted fleet dashboard, health check, CI deploy |
| API | Telemetry and fault ingest, work-order create, OpenAPI |
| AI automation | Recommend action, window, delay minutes avoided |
| Data science | Health score, delay-risk rank, similar assets |
| Pre-sales | 8-minute script a recruiter can click through |

Done means a public GitHub repo and a live URL a stranger can use with no setup.

## Locked decisions

- Domain: railway condition-based maintenance. The customer metric is delay minutes.
- Workflow: ingest, score, rank, AI draft, human accept or edit.
- Screens: fleet, asset detail, ops charts.
- Twin depth: train, car, system, component tree; state badge (healthy, degrading, act tonight); one “if we wait” line with expected delay minutes until the next exam.
- World: Nordic Metro, 12 trains, doors / brakes / HVAC / traction, about 80 assets. Seed a few obvious degrading trends, including a door on Train 07.
- Delay risk: failure probability times typical delay minutes. The formula stays visible in the UI.
- Stack: FastAPI, a simple UI, SQLite or Postgres, one LLM call that returns JSON, TF-IDF for similar assets.
- Host: Fly, Railway, or Render so it stays up. Azure is the production story in the README, not the weekend setup.
- Auth: one Demo entry. No SSO, tenants, or billing.
- Data: synthetic only. No OEM drawings, logs, suppliers, or vehicle data from work.

## In the demo, a recruiter can

Open the live URL, see a degrading door on Train 07, run Recommend maintenance, accept “inspect the door operator tonight — about 12 delay minutes avoided,” see similar assets and two charts, then open the API docs and see how a TCMS or depot system would post events.

## Out of scope

- 3D, CAD, physics, or a simulation engine
- Real IoT broker, Kafka, Kubernetes
- Neural remaining-life model, vector database, fine-tuning
- SSO, multi-tenant billing, crew rostering
- Full CMMS, RAMS, or document control
- Real work data

## Build order

Freeze features at the end of day 2 if day 3 is short. A live ranked fleet with a stubbed recommendation beats a local app that never deploys.

- [x] Schema: train, car, system, component, readings, events, recommendations (`app/models.py`)
- [x] Seed 12 trains and about 80 assets, including a few obvious degrading trends (`app/seed.py`)
- [ ] API: fleet list, asset detail, ingest event, recommend
- [ ] Scoring: health and delay-risk rank, formula visible in the UI
- [ ] AI draft: action, window, delay minutes avoided, confidence; accept and edit
- [ ] UI: fleet, asset with similar items and if-we-wait, two charts
- [ ] Deploy, public GitHub, README with live URL, architecture, curl, and the 8-minute script

### Day split

| Block | Stop when |
|---|---|
| Day 1 morning | Schema, seed, GET fleet returns data |
| Day 1 afternoon | Ingest and recommend. One curl classify works |
| Day 2 morning | Fleet, asset, accept or edit, similar assets |
| Day 2 afternoon | Two charts, health endpoint, Docker, local demo script |
| Day 3 half day | Deploy and GitHub. A stranger can use it with no setup |

## 8-minute demo script

1. Failures in service become delay minutes. Maintenance is still calendar-based.
2. Fleet view. This is a product, not a notebook.
3. Train 07 door. Health trend and if-we-wait delay minutes.
4. Recommend maintenance. Accept or edit the draft.
5. Similar assets. This is a pattern, not a one-off.
6. Charts: hotspot by system.
7. OpenAPI. A TCMS or depot system posts events here. The engineer stays in control.

## Risks

| Risk | Mitigation |
|---|---|
| Work data in the repo | Synthetic world only. Say so in the README. |
| Scope explosion | One workflow. Freeze at the end of day 2. |
| LLM-only look | Keep the visible formula, rank, and similar-asset list. |
| Link dies | Cheap always-on host, health check, seed on boot. |
| Over-claiming a digital twin | Say operational fleet twin, and name the model. |
| Auth or Azure setup eats the weekend | Demo button. Mention Azure as the production target only. |

## How we work in Cursor

- This folder is the project. Open it before coding.
- This file is the memory. Update it when a decision changes.
- `.cursor/rules/tracerail.mdc` keeps a new chat inside this scope.
- Stay in one chat until the URL is live.
- Resume line: read `PROJECT.md` and continue from the next unchecked step.
