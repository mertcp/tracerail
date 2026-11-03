# TraceRail

Condition-based maintenance for a synthetic metro fleet. The job of the app is to keep delay minutes off the line by maintaining a component before it fails in service.

The trains do not report that they are healthy. They send measurements. TraceRail scores health and delay risk. A maintainer accepts or edits the maintenance line.

Live page: https://tracerail-mertcp.fly.dev/

All data is synthetic. Nordic Metro, trains NM-01 to NM-12. No operator, supplier, or vehicle data from a real project.

## What a recruiter can click

Open the live page. Train NM-07, car 2, door operator is first. Motor current and lock time have drifted. The page shows the delay-risk formula, the minutes at risk if the door stays in service, and other doors with the same pattern. Recommend maintenance, then accept or edit the line. `/docs` is the API a depot or TCMS system would call.

## Measurements

| System | Signals |
|---|---|
| Doors | Motor current (A), lock time (s) |
| Brakes | Cylinder pressure (bar), pad distance (mm) |
| HVAC | Supply-to-return temperature gap (°C), compressor current (A) |
| Traction | Inverter temperature (°C), phase current (A) |

Delay risk is `failure probability × typical delay minutes`. The limits used to turn a reading into a probability are demo limits, not a manufacturer's specification.

## Architecture

```
measurements → FastAPI → health and delay risk → fleet page
                      ↘ one model call writes the maintenance line
```

SQLite holds the fleet and is seeded on an empty start. The page is one HTML file. The model call is optional: set `OPENAI_API_KEY` and the recommend button asks the model. Without that key, the same numbers produce the sentence.

A production version of this would sit on Azure, with the depot system posting readings to the API. This demo is a single container so a stranger can open it.

## Run it

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.api:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000/

```bash
curl -s http://127.0.0.1:8000/fleet | head -c 400
curl -s -X POST http://127.0.0.1:8000/assets/1/readings \
  -H 'content-type: application/json' \
  -d '{"metric":"motor_current_a","value":4.2}'
curl -s -X POST http://127.0.0.1:8000/assets/1/recommend
```

## Eight-minute walkthrough

1. A door that fails in service holds the train. Maintenance is still booked by the calendar.
2. The fleet list is ranked by delay minutes. This is the product, not a notebook.
3. Open NM-07, car 2. Motor current and lock time have risen. The formula is on the page.
4. If that door waits until the next exam, the delay minutes get worse.
5. Recommend maintenance. Accept the line, or edit it. The engineer stays in control.
6. Two other doors are already drifting the same way.
7. Doors account for more delay minutes than brakes, HVAC, or traction.
8. `/docs` is where a TCMS or depot system posts the next reading.

## Demo script, said aloud

"Nordic Metro was finding door faults at the platform. TraceRail takes motor current and lock time from the door controller, scores the chance of a delay, and drafts the work for tonight. The maintainer accepts it. The same pattern is already on two other trains."
