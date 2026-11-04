# TraceRail — project plan

Living plan for **tracerail** ([mertcp/tracerail](https://github.com/mertcp/tracerail)). Updated 4 Nov 2026.

**Status:** Local demo at http://127.0.0.1:8000/ — side-view train, measurements, delay-risk formula, maintenance draft with accept/edit. Deploy only after Mert asks. Next step: warn, then remove agent-only notes (see below).

Open this file from the left file tree. In a new chat, say: read `PROJECT.md` and continue from the next unchecked step.

## Product positioning (LinkedIn / recruiter)

**Headline:** Operational fleet intelligence for condition-based maintenance — ranked by delay minutes at risk.

**One-liner:** Ingest measurements, score health and delay risk, rank the fleet, draft depot work—maintainer accepts or edits before the failure hits the timetable.

**Showcase copy:** [LINKEDIN.md](LINKEDIN.md). README uses the same professional tone.

## What we are building

TraceRail is a **business-facing demo SaaS** for railway condition-based maintenance on a synthetic **Nordic Metro** fleet. It ranks assets by **delay minutes at risk**, surfaces both signals per system, and drafts maintenance a human can accept or edit—moving failures from the line into the depot.

**Operational fleet twin:** asset record + health + visible delay-risk math. Not 3D, CAD, or physics simulation.

**Audience:** CV and cloud / SaaS solutions pre-sales. **Data:** synthetic only—no OEM or employer vehicle data.

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
- Inputs are two measurements per system. Doors: motor current and lock time. Brakes: cylinder pressure and pad distance. HVAC: supply-to-return temperature gap and compressor current. Traction: inverter temperature and phase current. TraceRail scores health and delay risk from those numbers. The model reads the same measurements and decides the maintenance for the upcoming days.
- Delay risk: failure probability times typical delay minutes. The formula stays visible in the UI.
- Stack: FastAPI, a simple UI, SQLite or Postgres, one LLM call that returns JSON, TF-IDF for similar assets.
- Host: Fly, Railway, or Render so it stays up. Azure is the production story in the README, not the weekend setup.
- Auth: one Demo entry. No SSO, tenants, or billing.
- Data: synthetic only. No OEM drawings, logs, suppliers, or vehicle data from work.

## In the demo, a recruiter can

Open the live URL, see Train 07, click the door on the side view, read the maintenance line (inspect the door operator tonight — about 13 delay minutes avoided), accept or edit it, see the two charts, then open the API docs and see how a TCMS or depot system would post events.

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
- [x] API: fleet list, asset detail, ingest event, recommend (`app/api.py`)
- [x] Scoring: health and delay-risk rank, formula visible in the UI (`app/fleet.html`)
- [x] AI draft: the model reads the two measurements and decides the upcoming maintenance (`app/recommend.py`). Without `OPENAI_API_KEY` the page drafts from the same numbers.
- [x] UI: fleet, asset with similar items and if-we-wait, two charts (`app/fleet.html`)
- [x] README, architecture, curl, and the 8-minute script. Cloud deploy was removed. Deploy again only when Mert asks.
- [ ] Before calling it finished: warn Mert, then remove agent-only notes (see below)

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
4. Click the door on the side view. Accept or edit the draft.
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

## How the code should read

Mert will walk a recruiter through this repo. The code should read like a system engineer wrote a short demo, not like a generated framework.

- Keep files small and the path straight. A function should be readable aloud.
- Use fleet words: train, car, door operator, delay minutes.
- Comment the delay-risk formula and any decision that the name does not show. Do not comment every function.
- Skip extra layers, base classes, banners, and placeholder scaffolds.
- After each step, Mert should be able to explain the changed file in a few sentences.

## Before the project is finished

Warn Mert first. Do not delete these notes until he agrees.

Then remove everything that exists for the agent rather than for a recruiter:

- This section, "How the code should read," and "How we work in Cursor."
- `.cursor/rules/tracerail.mdc` and any other agent instructions, except the cost-approval rule.
- Comments, commands, and files whose only job is to steer the agent or to hide that an agent wrote the code.

Keep the product, the README, the demo script, and the delay-risk explanation. The plain coding style stays. The notes about that style do not.

## Cost approval

Finish the code on this Mac. Do not deploy to the cloud until Mert says the demo is ready for recruiters.

Any action that can cost money must stop first. State the amount, then ask exactly: "This will cost you this amount. Do you approve this action?" Do not continue until he says yes. This includes Fly.io, Azure, OpenAI, and any other paid service. Keep this rule when agent-only notes are removed.

## How we work in Cursor

- This folder is the project. Open it before coding.
- This file is the memory. Update it when a decision changes.
- `.cursor/rules/tracerail.mdc` keeps a new chat inside this scope.
- Stay in one chat until the URL is live.
- Resume line: read `PROJECT.md` and continue from the next unchecked step.
