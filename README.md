# TraceRail

**Operational fleet intelligence for condition-based maintenance — ranked by delay minutes at risk.**

Metro operators still lose timetable when a degrading door or brake fails in service, while maintenance is often calendar-driven. TraceRail ingests **measurements** (not “healthy” flags), scores health and delay risk, ranks the fleet, and drafts the depot action a maintainer can accept or edit—so failures move from the line into planned work.

Demo for solutions pre-sales: API-first, synthetic **UK Regional** fleet, runs locally. Companion project: [solar-warranty](https://github.com/mertcp/solar-warranty) (portfolio warranty & performance).

**Repository:** [github.com/mertcp/tracerail](https://github.com/mertcp/tracerail)

---

## What you can show in five minutes

Open http://127.0.0.1:8000/ after starting the server below. Use the **priority queue** (with UK depot location per train), open **MM-07** car 2 doors for the maintenance line, motor current, lock time, and delay-risk formula. **Back** returns to the prior view. API docs stay embedded on the page.

Name aloud: measurements in, ranked fleet out, human approves the work order narrative, optional LLM when `OPENAI_API_KEY` is set (rule-based draft otherwise).

---

## Run locally

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.api:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000/

---

## Signals (demo limits, not OEM specs)

| System | Measurements |
|--------|----------------|
| Doors | Motor current (A), lock time (s) |
| Brakes | Cylinder pressure (bar), pad distance (mm) |
| HVAC | Supply–return ΔT (°C), compressor current (A) |
| Traction | Inverter temperature (°C), phase current (A) |

**Delay risk** = failure probability × typical delay minutes (shown on the asset view).

---

## Architecture

```
telemetry → FastAPI + SQLite → health & delay risk → fleet UI
                          ↘ maintenance draft (LLM if OPENAI_API_KEY)
```

Production story in conversation: Azure-hosted API with depot ingest. This repo is a single container-friendly demo.

---

## LinkedIn showcase copy

See **[LINKEDIN.md](LINKEDIN.md)** for headline, short description, and highlight lines.

---

## API samples

```bash
curl -s http://127.0.0.1:8000/fleet | python3 -m json.tool | head -30
curl -s -X POST http://127.0.0.1:8000/assets/<ID>/readings \
  -H 'content-type: application/json' \
  -d '{"metric":"motor_current_a","value":4.2}'
curl -s -X POST http://127.0.0.1:8000/assets/<ID>/recommend
```

Replace `<ID>` with the MM-07 door asset from `/fleet`. Open `/docs` for events and recommendations.

---

## Eight-minute walkthrough

1. Platform delays come from in-service failures; maintenance is still often calendar-based.
2. Fleet view ranks by **delay minutes at risk**—the product metric, not a notebook chart.
3. MM-07 door: both measurements drifted; formula and “if we wait” are on screen.
4. Open the asset from the queue; review the draft for tonight.
5. Accept or edit—engineer stays in control.
6. Peer doors show the same pattern (fleet learning, not one-off).
7. Priority queue shows **location** so the team knows where to go.
8. `/docs`: integration point for the next telemetry POST.

**Said aloud:** *“UK Regional was holding trains at the platform on door faults. TraceRail reads motor current and lock time, quantifies delay risk, and drafts inspect-tonight work the maintainer can accept—before the failure hits the timetable.”*

---

## Disclaimer

All trains, limits, and events are **synthetic**. No operator, supplier, or vehicle data from any real project.
