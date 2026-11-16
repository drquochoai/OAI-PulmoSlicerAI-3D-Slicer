"""PTL class-to-anatomy display mapping for the 18 pulmonary regions."""

from __future__ import annotations


RIGHT_SEGMENTS = tuple((index, f"S{index}") for index in range(1, 11))
LEFT_SEGMENTS = (
    (11, "S1+2"),
    (12, "S3"),
    (13, "S4"),
    (14, "S5"),
    (15, "S6"),
    (16, "S7+8"),
    (17, "S9"),
    (18, "S10"),
)

ROLE_PREFIX = {"airway": "B", "artery": "A", "vein": "V"}


def ptl_region_metadata(class_id: int) -> dict[str, str]:
    """Return laterality, lobe, and pulmonary-region metadata."""

    if class_id in range(1, 4):
        return {"side": "Right", "lobe": "Upper", "region": f"S{class_id}"}
    if class_id in range(4, 6):
        return {"side": "Right", "lobe": "Middle", "region": f"S{class_id}"}
    if class_id in range(6, 11):
        return {"side": "Right", "lobe": "Lower", "region": f"S{class_id}"}
    left = {
        11: ("Upper", "S1+2"),
        12: ("Upper", "S3"),
        13: ("Upper", "S4"),
        14: ("Upper", "S5"),
        15: ("Lower", "S6"),
        16: ("Lower", "S7+8"),
        17: ("Lower", "S9"),
        18: ("Lower", "S10"),
    }
    if class_id in left:
        lobe, region = left[class_id]
        return {"side": "Left", "lobe": lobe, "region": region}
    if class_id == 19:
        return {"side": "Central", "lobe": "Central", "region": "S0"}
    raise ValueError(f"invalid PTL class: {class_id}")


def ptl_class_labels(role: str) -> dict[int, str]:
    """Return stable human-readable labels; class 19 is central/out-of-lung."""

    try:
        prefix = ROLE_PREFIX[role]
    except KeyError as exc:
        raise ValueError(f"unsupported PTL role: {role}") from exc
    labels = {
        class_id: f"{prefix}{segment[1:]} Right"
        for class_id, segment in RIGHT_SEGMENTS
    }
    labels.update(
        {
            class_id: f"{prefix}{segment[1:]} Left"
            for class_id, segment in LEFT_SEGMENTS
        }
    )
    labels[19] = f"{prefix}0 Central/out-of-lung"
    return labels


def ptl_segment_id(role: str, class_id: int) -> str:
    prefix = ROLE_PREFIX.get(role)
    if prefix is None or class_id not in range(1, 20):
        raise ValueError("invalid PTL role or class")
    side = "R" if class_id <= 10 else "L" if class_id <= 18 else "C"
    return f"PTL_{prefix}_{side}_{class_id:02d}"
