"""Depot work packs for priority-queue maintenance drafts (synthetic UK Regional)."""

from app.locations import TRAIN_LOCATIONS

# Demo work packs — not real OEM manuals.
WORK_PACKS = {
    "doors": {
        "duration": "2 hours 30 minutes",
        "crew": "2 door fitters (Grade 3 or above)",
        "documentation": "MM-WP-DO-07 — Door operator stroke, lock timing, and motor current verification",
    },
    "brakes": {
        "duration": "3 hours 15 minutes",
        "crew": "2 brake fitters plus 1 NVQ L4 tester for release test",
        "documentation": "MM-WP-BR-03 — Cylinder pressure, pad wear, and emergency application check",
    },
    "hvac": {
        "duration": "4 hours 00 minutes",
        "crew": "2 saloon HVAC technicians",
        "documentation": "MM-WP-HV-02 — Compressor current, supply/return delta-T, and filter inspection",
    },
    "traction": {
        "duration": "5 hours 00 minutes",
        "crew": "2 traction electricians plus 1 OEM witness slot (booked)",
        "documentation": "MM-WP-TR-09 — Inverter heatsink, phase current balance, and torque limit check",
    },
}


def depot_for_train(train_code: str) -> str:
    return TRAIN_LOCATIONS.get(train_code, "Nearest stabling road — confirm with depot control")


def sections(component) -> dict:
    """Structured draft fields for one asset."""
    system = component.system
    car = system.car
    train_code = car.train.code
    pack = WORK_PACKS[system.kind]
    depot = depot_for_train(train_code)
    if component.state == "degrading":
        duration = "1 hour 45 minutes (planned day shift slot)"
        window_note = "Schedule within 3 days"
    elif component.state == "act_tonight":
        duration = pack["duration"] + " (night possession)"
        window_note = "Tonight before first service"
    else:
        duration = pack["duration"]
        window_note = "Before next exam"

    summary = "Maintain {0} on {1} car {2} — {3}.".format(
        component.name.lower(),
        train_code,
        car.position,
        window_note,
    )
    return {
        "summary": summary,
        "depot": depot,
        "duration": duration,
        "crew": pack["crew"],
        "documentation": pack["documentation"],
    }


def action_text(component) -> str:
    """Plain-text maintenance draft stored on the recommendation."""
    s = sections(component)
    return (
        "{summary}\n\n"
        "Depot: {depot}\n"
        "Duration: {duration}\n"
        "Crew: {crew}\n"
        "Documentation: {documentation}"
    ).format(**s)
