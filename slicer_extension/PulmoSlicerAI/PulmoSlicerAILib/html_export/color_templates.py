"""Deterministic, versioned presentation colors shared by Slicer and HTML."""

from __future__ import annotations


TEMPLATES = {
    "pulmoslicer-surgical-contrast-v1": {
        "name": "PulmoSlicer Surgical Contrast",
        "colors": {
            "airway": (0.95, 0.78, 0.34, 1.0),
            "artery": (0.93, 0.25, 0.23, 1.0),
            "vein": (0.20, 0.62, 0.92, 1.0),
            "aorta": (0.82, 0.12, 0.16, 1.0),
            "tumor": (0.95, 0.12, 0.62, 1.0),
            "lobe_right_upper": (0.96, 0.66, 0.50, 0.38),
            "lobe_right_middle": (0.98, 0.82, 0.47, 0.38),
            "lobe_right_lower": (0.86, 0.58, 0.77, 0.38),
            "lobe_left_upper": (0.51, 0.79, 0.88, 0.38),
            "lobe_left_lower": (0.46, 0.74, 0.62, 0.38),
            "lung": (0.72, 0.82, 0.88, 0.32),
            "bone": (0.85, 0.79, 0.68, 0.82),
            "other": (0.70, 0.72, 0.76, 0.85),
        },
    },
    "high-contrast-v1": {
        "name": "High Contrast",
        "colors": {
            "airway": (1.0, 0.82, 0.0, 1.0),
            "artery": (1.0, 0.08, 0.08, 1.0),
            "vein": (0.0, 0.62, 1.0, 1.0),
            "aorta": (0.78, 0.0, 0.12, 1.0),
            "tumor": (1.0, 0.0, 0.72, 1.0),
            "lung": (0.72, 0.82, 0.92, 0.28),
            "bone": (0.98, 0.94, 0.76, 0.9),
            "other": (0.85, 0.85, 0.85, 0.9),
        },
    },
    "color-vision-friendly-v1": {
        "name": "Color-vision Friendly",
        "colors": {
            "airway": (0.94, 0.89, 0.26, 1.0),
            "artery": (0.84, 0.37, 0.0, 1.0),
            "vein": (0.0, 0.45, 0.70, 1.0),
            "aorta": (0.80, 0.22, 0.28, 1.0),
            "tumor": (0.80, 0.47, 0.65, 1.0),
            "lung": (0.35, 0.70, 0.90, 0.28),
            "bone": (0.82, 0.78, 0.66, 0.86),
            "other": (0.65, 0.65, 0.65, 0.9),
        },
    },
    "monochrome-anatomy-v1": {
        "name": "Monochrome Anatomy",
        "colors": {
            "airway": (0.82, 0.82, 0.82, 1.0),
            "artery": (0.68, 0.68, 0.68, 1.0),
            "vein": (0.54, 0.54, 0.54, 1.0),
            "aorta": (0.62, 0.62, 0.62, 1.0),
            "tumor": (1.0, 0.8, 0.0, 1.0),
            "lung": (0.72, 0.72, 0.72, 0.25),
            "bone": (0.88, 0.88, 0.88, 0.85),
            "other": (0.64, 0.64, 0.64, 0.9),
        },
    },
}


def template_names() -> tuple[tuple[str, str], ...]:
    return tuple((key, value["name"]) for key, value in TEMPLATES.items())


def color_for(template_id: str, anatomy_class: str) -> tuple[float, float, float, float]:
    try:
        colors = TEMPLATES[template_id]["colors"]
    except KeyError as exc:
        raise ValueError(f"Unknown color template: {template_id}") from exc
    family = "lung" if anatomy_class.startswith("lobe_") else anatomy_class.split("_")[0]
    return colors.get(anatomy_class, colors.get(family, colors["other"]))
