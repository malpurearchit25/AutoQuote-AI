"""Illustrative INR amounts from the original project, not market quotations.

Confidence measures model certainty, not repair severity. It never changes prices.
Multiple boxes with the same label are grouped into one provisional repair item.
"""

VEHICLES = {
    "Hyundai": ["i20", "Creta", "Verna"],
    "Maruti": ["Swift", "Baleno", "Brezza"],
    "Honda": ["City", "Amaze"],
    "Toyota": ["Innova", "Fortuner", "Corolla"],
}

BASE_PRICES = {
    "scratch": 1500,
    "doorouter_dent": 3000,
    "front_bumper_dent": 4000,
    "rear_bumper_dent": 3500,
    "headlight_damage": 5000,
    "taillight_damage": 4500,
}

VEHICLE_PRICES = {
    ("Hyundai", "i20"): {
        "front_bumper_dent": 3500, "rear_bumper_dent": 3000,
        "doorouter_dent": 4000, "scratch": 1500,
        "headlight_damage": 6000, "front_windscreen_damage": 9000,
    },
    ("Maruti", "Swift"): {
        "front_bumper_dent": 3000, "doorouter_dent": 3500,
        "scratch": 1200, "front_windscreen_damage": 8000,
    },
}


def estimate(detections: list[dict], make: str, model: str) -> dict:
    items = {}
    overrides = VEHICLE_PRICES.get((make, model), {})
    for detection in detections:
        label = detection["class_name"]
        if label in items:
            items[label]["detection_count"] += 1
            continue
        cost = overrides.get(label, BASE_PRICES.get(label))
        items[label] = {
            "class_name": label,
            "label": label.replace("_", " ").capitalize(),
            "estimated_cost": cost,
            "price_basis": "vehicle-specific sample" if label in overrides else
                           "generic sample" if cost is not None else "inspection required",
            "detection_count": 1,
        }
    breakdown = list(items.values())
    return {
        "items": breakdown,
        "total_cost": sum(item["estimated_cost"] or 0 for item in breakdown),
        "unpriced_count": sum(item["estimated_cost"] is None for item in breakdown),
        "currency": "INR",
        "disclaimer": "Illustrative estimate only. Model labels can be incorrect; review every finding. "
                      "A workshop inspection is needed for a quotation. "
                      "Repeated labels are grouped once; separate damaged panels may cost more. "
                      "Hidden damage, taxes and additional labour are not assessed.",
    }
