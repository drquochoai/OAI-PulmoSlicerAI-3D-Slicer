"""Allowlisted anatomical identity and hierarchy mapping."""

from __future__ import annotations

from dataclasses import dataclass
import re


_SAFE_ID = re.compile(r"[^a-z0-9_.-]+")


@dataclass(frozen=True)
class AnatomyDescriptor:
    stable_id: str
    display_name: str
    path: tuple[str, ...]
    anatomy_class: str


_LOBES = {
    "lung_upper_lobe_right": ("Right upper lobe", ("Lungs", "Right", "Upper", "Lung"), "lobe_right_upper"),
    "lung_middle_lobe_right": ("Right middle lobe", ("Lungs", "Right", "Middle", "Lung"), "lobe_right_middle"),
    "lung_lower_lobe_right": ("Right lower lobe", ("Lungs", "Right", "Lower", "Lung"), "lobe_right_lower"),
    "lung_upper_lobe_left": ("Left upper lobe", ("Lungs", "Left", "Upper", "Lung"), "lobe_left_upper"),
    "lung_lower_lobe_left": ("Left lower lobe", ("Lungs", "Left", "Lower", "Lung"), "lobe_left_lower"),
}
_SOURCE = {
    "lung_airways": ("Airways — source mask", "airway"),
    "lung_arteries": ("Pulmonary arteries — source mask", "artery"),
    "lung_veins": ("Pulmonary veins — source mask", "vein"),
}
_AORTA = {
    "aorta": "Aorta",
    "aorta_ascending": "Ascending aorta",
    "aortic_arch": "Aortic arch",
    "aorta_descending": "Descending thoracic aorta",
    "brachiocephalic_trunk": "Brachiocephalic trunk",
    "common_carotid_artery_right": "Right common carotid artery",
    "common_carotid_artery_left": "Left common carotid artery",
    "subclavian_artery_right": "Right subclavian artery",
    "subclavian_artery_left": "Left subclavian artery",
}


def _stable(value: str) -> str:
    return _SAFE_ID.sub("-", value.lower()).strip("-")[:96]


def _ptl_descriptor(segment_id: str):
    parts = segment_id.split("_")
    if len(parts) != 4 or parts[0] != "PTL" or parts[1] not in ("B", "A", "V"):
        return None
    try:
        class_id = int(parts[3])
        from pulmoslicer_engine.adapters.labeling.ptl_labels import ptl_region_metadata

        metadata = ptl_region_metadata(class_id)
    except (ValueError, KeyError):
        return None
    system_names = {"B": "Bronchi", "A": "Pulmonary arteries", "V": "Pulmonary veins"}
    anatomy_classes = {"B": "airway", "A": "artery", "V": "vein"}
    label = f"{parts[1]}{metadata['region'][1:]} {metadata['side']}"
    path = (
        "Lungs",
        metadata["side"],
        metadata["lobe"],
        system_names[parts[1]],
        metadata["region"],
    )
    return AnatomyDescriptor(_stable(segment_id), label, path, anatomy_classes[parts[1]])


def describe_segment(output_role: str, segment_id: str) -> AnatomyDescriptor | None:
    """Return only known anatomy; arbitrary MRML names never enter shared HTML."""

    if segment_id in _LOBES:
        name, path, anatomy_class = _LOBES[segment_id]
        return AnatomyDescriptor(_stable(segment_id), name, path, anatomy_class)
    ptl = _ptl_descriptor(segment_id)
    if ptl:
        return ptl
    if output_role == "source" and segment_id in _SOURCE:
        name, anatomy_class = _SOURCE[segment_id]
        return AnatomyDescriptor(_stable(segment_id), name, ("Source A/B/V",), anatomy_class)
    if segment_id in _AORTA:
        return AnatomyDescriptor(_stable(segment_id), _AORTA[segment_id], ("Aorta",), "aorta")
    lower = segment_id.lower()
    if output_role == "tumor" and any(token in lower for token in ("tumor", "lesion", "nodule")):
        return AnatomyDescriptor(_stable("tumor-" + segment_id), "Tumor", ("Tumor",), "tumor")
    rib = re.fullmatch(r"rib_(left|right)_(\d{1,2})", lower)
    if rib and 1 <= int(rib.group(2)) <= 12:
        side = rib.group(1).title()
        number = int(rib.group(2))
        return AnatomyDescriptor(_stable(segment_id), f"{side} rib {number}", ("Chest wall", f"{side} ribs"), "bone")
    vertebra = re.fullmatch(r"vertebrae?_t(\d{1,2})", lower)
    if vertebra and 1 <= int(vertebra.group(1)) <= 12:
        number = int(vertebra.group(1))
        return AnatomyDescriptor(_stable(segment_id), f"T{number}", ("Chest wall", "Thoracic spine"), "bone")
    if lower == "sternum":
        return AnatomyDescriptor("sternum", "Sternum", ("Chest wall",), "bone")
    # Deliberately excluded: clavicles, scapulae and costal cartilage.
    return None
