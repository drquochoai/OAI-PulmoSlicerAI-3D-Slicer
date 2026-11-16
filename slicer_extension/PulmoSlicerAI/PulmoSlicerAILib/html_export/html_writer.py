"""Atomic single-file HTML assembly and self-validation."""

from __future__ import annotations

import hashlib
import html
import json
import os
from pathlib import Path
import secrets

from .color_templates import TEMPLATES
from .contracts import CONTRACT_VERSION, VIEWER_VERSION, ExportOptions, MeshRecord
from .privacy import scan_html_for_phi, validate_case_title


DISCLAIMER = (
    "Research visualization; exported surface is not automatically validated "
    "for diagnosis or surgical decision."
)


def _asset(name: str) -> str:
    return (Path(__file__).parent / "assets" / name).read_text(encoding="utf-8")


def _script_json(value) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def _manifest(options: ExportOptions, meshes: tuple[MeshRecord, ...], warnings: tuple[str, ...]):
    return {
        "contractVersion": CONTRACT_VERSION,
        "viewerVersion": VIEWER_VERSION,
        "caseTitle": validate_case_title(options.case_title),
        "researchOnly": True,
        "anonymized": True,
        "units": "mm",
        "sourceCoordinateFrame": "Slicer world RAS",
        "webCoordinateFrame": "X=Right, Y=Superior, Z=Posterior",
        "sourceToWebMatrixRowMajor": [1, 0, 0, 0, 0, 0, 1, 0, 0, -1, 0, 0, 0, 0, 0, 1],
        "profile": options.profile,
        "colorTemplateId": options.color_template_id,
        "colorTemplates": TEMPLATES,
        "selectAllValid": options.select_all_valid,
        "showAllOnOpen": options.show_all_on_open,
        "disclaimer": DISCLAIMER,
        "warnings": list(warnings),
        "meshes": [mesh.manifest_entry() for mesh in meshes],
    }


def render_html(options: ExportOptions, meshes: tuple[MeshRecord, ...], warnings=()) -> str:
    options.validate()
    if not meshes:
        raise ValueError("Không có cấu trúc hợp lệ để xuất HTML")
    nonce = secrets.token_urlsafe(18)
    manifest = _manifest(options, meshes, tuple(warnings))
    payloads = "\n".join(
        f'<script nonce="{nonce}" id="mesh-{html.escape(mesh.stable_id)}" type="application/octet-stream">{mesh.payload_b64}</script>'
        for mesh in meshes
    )
    title = html.escape(manifest["caseTitle"])
    css = _asset("viewer.css")
    javascript = _asset("viewer_bundle.js")
    return f"""<!doctype html>
<html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'nonce-{nonce}'; style-src 'nonce-{nonce}'; img-src data: blob:; worker-src blob:; connect-src 'none';">
<title>{title} — PulmoSlicer 3D</title><style nonce="{nonce}">{css}</style></head>
<body><div id="app"><header><h1 id="case-title">{title}</h1>
<button id="fit-all">Fit all</button><button id="projection">Perspective</button><button id="theme">Sáng/tối</button><button id="screenshot" class="optional">PNG</button>
<button id="fullscreen" class="optional">Toàn màn hình</button><button id="help">Trợ giúp</button></header>
<aside><input id="search" type="search" placeholder="Tìm B1, A6, V3, thùy…" aria-label="Tìm cấu trúc">
<div class="toolbar"><button id="show-all">Hiện tất cả</button><button id="hide-all">Ẩn tất cả</button><button id="invert">Đảo</button><button id="isolate">Cô lập</button></div>
<div id="tree" aria-label="Cây giải phẫu"></div>
<section class="panel"><h2 id="selection-name">Chưa chọn cấu trúc</h2><div id="selection-meta">Nhấp vào mô hình hoặc tên trong cây.</div>
<label class="field">Độ mờ <input id="opacity" type="range" min="0" max="100" value="100"></label>
<label class="field">Màu <input id="node-color" type="color" value="#cccccc"></label>
<label class="field">Template <select id="color-template"></select></label><button id="reset-colors">Áp dụng lại template</button><br>
<label><input id="wireframe" type="checkbox"> Wireframe</label> <label><input id="flat-shading" type="checkbox"> Flat shading</label> <label><input id="autorotate" type="checkbox"> Tự xoay</label></section>
<section class="panel"><h2>Mặt cắt quan sát</h2>
<label class="field">X <input class="clip" data-clip="0" type="range" min="-500" max="10000" value="10000"></label>
<label class="field">Y <input class="clip" data-clip="1" type="range" min="-500" max="10000" value="10000"></label>
<label class="field">Z <input class="clip" data-clip="2" type="range" min="-500" max="10000" value="10000"></label>
<button id="clip-reset">Tắt clipping</button> <label><input id="measure" type="checkbox"> Đo 2 điểm</label><div id="measurement"></div></section></aside>
<main><canvas id="viewport"></canvas><div class="views"><button data-view="A">A</button><button data-view="P">P</button><button data-view="L">L</button><button data-view="R">R</button><button data-view="S">S</button><button data-view="I">I</button></div><div id="toast"></div></main>
<footer><span id="disclaimer"></span><span id="diagnostics">Đang chuẩn bị…</span></footer></div>
<dialog id="help-dialog"><h2>PulmoSlicer 3D</h2><p>Kéo chuột trái để xoay, chuột phải để pan, con lăn để zoom. Nhấp đúp tên cấu trúc để cô lập. Các phép đo dựa trên bề mặt đã xuất và chỉ dùng tham khảo/nghiên cứu.</p><p>Không có lát CT, chỉnh sửa segmentation hay AI trong file này.</p><button id="close-help">Đóng</button></dialog>
<script nonce="{nonce}" id="pulmoslicer-manifest" type="application/json">{_script_json(manifest)}</script>
{payloads}<script nonce="{nonce}">{javascript}</script></body></html>"""


def write_atomic_html(options: ExportOptions, meshes: tuple[MeshRecord, ...], warnings=()):
    document = render_html(options, meshes, warnings)
    findings = scan_html_for_phi(document)
    if findings:
        raise ValueError("PHI/path scan failed: " + ", ".join(findings))
    lowered = document.lower()
    if "<script src=" in lowered or "<link href=" in lowered:
        raise ValueError("Offline HTML unexpectedly references an external asset")
    destination = options.output_path.resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_suffix(destination.suffix + ".partial")
    partial.write_text(document, encoding="utf-8", newline="\n")
    if partial.stat().st_size < 1024 or "pulmoslicer-manifest" not in document:
        partial.unlink(missing_ok=True)
        raise ValueError("Generated HTML failed integrity validation")
    os.replace(partial, destination)
    content = destination.read_bytes()
    return hashlib.sha256(content).hexdigest(), len(content), {
        "offline": True,
        "singleFile": True,
        "phiScan": "PASS",
        "meshCount": len(meshes),
        "contractVersion": CONTRACT_VERSION,
    }
