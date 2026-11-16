"""Compact Slicer UI for the offline interactive HTML exporter."""

from __future__ import annotations

from pathlib import Path

import ctk
import qt
import slicer

from .html_export.color_templates import template_names
from .html_export.contracts import ExportOptions


class HtmlExportPanel:
    def __init__(self, parent_layout, run_callback, cancel_callback=None) -> None:
        self._run_callback = run_callback
        self._cancel_callback = cancel_callback
        section = ctk.ctkCollapsibleButton()
        section.text = "3. Xuất HTML 3D tương tác — một file, ngoại tuyến"
        section.collapsed = False
        parent_layout.addWidget(section)
        form = qt.QFormLayout(section)

        explanation = qt.QLabel(
            "Mặc định xuất toàn bộ cấu trúc PulmoSlicer hợp lệ đang có. "
            "Không chạy lại AI, không chứa lát CT và không xuất nguồn A/V/B ẩn khi đã có PTL chi tiết."
        )
        explanation.wordWrap = True
        explanation.maximumWidth = 520
        form.addRow(explanation)

        self.titleEdit = qt.QLineEdit("PulmoSlicer Case")
        self.titleEdit.toolTip = "Chỉ nhập mã ca đã ẩn danh; không nhập tên, MRN hoặc ngày sinh."
        form.addRow("Tên ca ẩn danh:", self.titleEdit)

        self.qualityCombo = qt.QComboBox()
        self.qualityCombo.addItem("Tiêu chuẩn — cân bằng chất lượng/tốc độ", "standard")
        self.qualityCombo.addItem("Chia sẻ nhanh — file nhẹ", "quick")
        self.qualityCombo.addItem("Chi tiết — giữ nhiều polygon", "detail")
        self.qualityCombo.toolTip = "Mạch nhỏ luôn đi qua QA; nếu tối ưu làm mất nhánh, exporter tự fallback mesh ít xử lý hơn."
        form.addRow("Chất lượng HTML:", self.qualityCombo)

        self.colorCombo = qt.QComboBox()
        for template_id, name in template_names():
            self.colorCombo.addItem(name, template_id)
        self.colorCombo.toolTip = "Template phiên bản hóa dùng cùng stable anatomical ID; người xem vẫn có thể đổi màu trong HTML."
        form.addRow("Template màu:", self.colorCombo)

        self.allStructures = qt.QCheckBox("Chọn toàn bộ cấu trúc hợp lệ")
        self.allStructures.checked = True
        self.allStructures.enabled = False
        self.allStructures.toolTip = "Mặc định bắt buộc của bản này. Cấu trúc rỗng, không nhận diện hoặc ngoài allowlist sẽ bị bỏ qua có log."
        form.addRow(self.allStructures)

        self.openAfter = qt.QCheckBox("Mở HTML sau khi xuất")
        self.openAfter.checked = True
        form.addRow(self.openAfter)

        self.exportButton = qt.QPushButton("Xuất một file HTML 3D all-in-one")
        self.exportButton.toolTip = (
            "Tạo bản sao mesh dẫn xuất, làm mượt theo loại giải phẫu, kiểm tra QA, "
            "nén từng cấu trúc, quét PHI và ghi file atomically."
        )
        self.exportButton.connect("clicked()", self._choose_and_run)
        form.addRow(self.exportButton)

        self.cancelButton = qt.QPushButton("Hủy xuất HTML")
        self.cancelButton.enabled = False
        self.cancelButton.toolTip = (
            "Yêu cầu dừng tại checkpoint an toàn gần nhất. Filter VTK đang chạy sẽ hoàn tất trước khi dừng."
        )
        if cancel_callback is not None:
            self.cancelButton.connect("clicked()", cancel_callback)
        form.addRow(self.cancelButton)

    def set_running(self, running: bool) -> None:
        self.exportButton.enabled = not running
        self.cancelButton.enabled = running
        self.qualityCombo.enabled = not running
        self.colorCombo.enabled = not running
        self.titleEdit.enabled = not running

    def _choose_and_run(self) -> None:
        default_path = str(Path.home() / "PulmoSlicer-3D.html")
        selected = qt.QFileDialog.getSaveFileName(
            slicer.util.mainWindow(),
            "Xuất HTML 3D tương tác",
            default_path,
            "HTML (*.html)",
        )
        if isinstance(selected, tuple):
            selected = selected[0]
        if not selected:
            return
        path = Path(str(selected))
        if path.suffix.lower() != ".html":
            path = path.with_suffix(".html")
        options = ExportOptions(
            output_path=path,
            profile=str(self.qualityCombo.currentData),
            color_template_id=str(self.colorCombo.currentData),
            case_title=str(self.titleEdit.text),
        )
        self._run_callback(options, bool(self.openAfter.checked))
