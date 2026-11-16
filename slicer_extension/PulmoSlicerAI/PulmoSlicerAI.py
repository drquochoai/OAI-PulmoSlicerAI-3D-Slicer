"""Thin 3D Slicer entry point for the pulmonary reconstruction workflow."""

from __future__ import annotations

import ctk
import os
import queue as thread_queue
import qt
import slicer
import sys
import threading
from slicer.ScriptedLoadableModule import ScriptedLoadableModule, ScriptedLoadableModuleWidget

# Prefer the library shipped beside this entry point during an extension upgrade.
_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
if _MODULE_DIR in sys.path:
    sys.path.remove(_MODULE_DIR)
sys.path.insert(0, _MODULE_DIR)
# Source-tree runs keep the engine at the repository root; packaged installs
# place it beside this module.  Support both without changing global Slicer.
_SOURCE_ROOT = os.path.abspath(os.path.join(_MODULE_DIR, "..", ".."))
if os.path.isdir(os.path.join(_SOURCE_ROOT, "pulmoslicer_engine")):
    if _SOURCE_ROOT in sys.path:
        sys.path.remove(_SOURCE_ROOT)
    sys.path.insert(1, _SOURCE_ROOT)

from PulmoSlicerAILib.workflow import PulmonarySegmentationWorkflow
from PulmoSlicerAILib.progress_panel import ProgressPanel
from PulmoSlicerAILib.html_export import InteractiveHtmlExporter
from PulmoSlicerAILib.html_export_panel import HtmlExportPanel


class PulmoSlicerAI(ScriptedLoadableModule):
    def __init__(self, parent) -> None:
        super().__init__(parent)
        self.parent.title = "PulmoSlicer AI for segmentectomy"
        self.parent.categories = ["Chest by bsquochoainew"]
        self.parent.dependencies = ["TotalSegmentator"]
        self.parent.contributors = ["PulmoSlicer AI research team"]
        self.parent.helpText = (
            "Dựng hình giải phẫu phổi phục vụ nghiên cứu. "
            "Mọi kết quả cần được bác sĩ kiểm tra."
        )
        self.parent.acknowledgementText = "Built on 3D Slicer and TotalSegmentator."


class PulmoSlicerAIWidget(ScriptedLoadableModuleWidget):
    OUTPUT_ROLE_ATTRIBUTE = "PulmoSlicerAI.OutputRole"

    def setup(self) -> None:
        super().setup()
        self.workflow = PulmonarySegmentationWorkflow()
        self.htmlExporter = InteractiveHtmlExporter()

        notice = qt.QLabel(
            "<b>Nguyên mẫu nghiên cứu.</b> Kết quả không tự động được xem là "
            "xác nhận lâm sàng hoặc quyết định phẫu thuật."
        )
        notice.wordWrap = True
        self.layout.addWidget(notice)

        self.statusLabel = qt.QLabel(self.workflow.environment_status())
        self.statusLabel.wordWrap = True
        self.layout.addWidget(self.statusLabel)

        self.branchGateLabel = qt.QLabel(
            "<b>PTL nhánh phân thùy:</b> sẵn sàng cài runtime nghiên cứu cho "
            "airway/artery/vein; PTL không tự tạo khối nhu mô phân thùy và "
            "kết quả A/B/V phải được bác sĩ kiểm tra."
        )
        self.branchGateLabel.wordWrap = True
        self.branchGateLabel.maximumWidth = 520
        self.layout.addWidget(self.branchGateLabel)

        section = ctk.ctkCollapsibleButton()
        section.text = "1. Chọn CT và dựng hình cơ bản"
        self.layout.addWidget(section)
        form = qt.QFormLayout(section)

        self.inputSelector = self._node_selector(["vtkMRMLScalarVolumeNode"], False)
        self.inputSelector.noneEnabled = False
        self.vesselSelector = self._node_selector(["vtkMRMLSegmentationNode"], True)
        self.lobeSelector = self._node_selector(["vtkMRMLSegmentationNode"], True)
        self.ptlSelector = self._node_selector(["vtkMRMLSegmentationNode"], True)
        self.contextSelector = self._node_selector(["vtkMRMLSegmentationNode"], True)
        for selector in (
            self.vesselSelector,
            self.lobeSelector,
            self.ptlSelector,
            self.contextSelector,
        ):
            selector.noneDisplay = "Tự động tạo khi chạy"
        self.inputLabel = self._addFormRow(
            form,
            "CT ngực:",
            self.inputSelector,
            "CT đầu vào. Extension tự chọn volume CT đầu tiên; hãy kiểm tra lại đúng series trước khi chạy.",
        )
        self.vesselLabel = self._addFormRow(
            form,
            "A/V/B nguồn:",
            self.vesselSelector,
            "Mask nguồn TotalSegmentator gồm phế quản, động mạch và tĩnh mạch. "
            "Khi chọn PTL, node này được tạo tự động và ẩn khỏi phần lựa chọn để tránh chạy trùng.",
        )
        self.lobeLabel = self._addFormRow(
            form,
            "Năm thùy:",
            self.lobeSelector,
            "Output năm thùy phổi. Nếu chưa có, extension tự tạo khi bấm Một click hoặc Tạo năm thùy.",
        )
        self.ptlLabel = self._addFormRow(
            form,
            "PTL theo phân thùy:",
            self.ptlSelector,
            "Output các voxel của cây A/B/V đã được PTL gắn nhãn theo vùng; không phải khối nhu mô phân thùy.",
        )
        self.contextLabel = self._addFormRow(
            form,
            "Bối cảnh ngực:",
            self.contextSelector,
            "Output tùy chọn gồm động mạch chủ/nhánh quai hoặc sườn, ức và T1-T12. Không gồm xương đòn, xương vai hay sụn sườn.",
        )
        self._selectExistingOutputs()

        vesselMode = qt.QLabel("Chi tiết cố định — lung_vessels không có Fast")
        vesselMode.wordWrap = True
        self._addFormRow(
            form,
            "A/V/B quality:",
            vesselMode,
            "Task lung_vessels của TotalSegmentator 2.14 chỉ có full resolution; không có Fast hợp lệ.",
        )

        self.lobeQualityCombo = qt.QComboBox()
        self.lobeQualityCombo.addItem("Chi tiết — normal", "normal")
        self.lobeQualityCombo.addItem("Nhanh — fast", "fast")
        self._addFormRow(
            form,
            "Năm thùy quality:",
            self.lobeQualityCombo,
            "Chọn trước khi chạy. Nhanh giảm độ phân giải; Chi tiết giữ full resolution. Không hỏi lại giữa chừng.",
        )

        self.backendCombo = qt.QComboBox()
        self.backendCombo.addItem("Tự động tốt nhất — CUDA/ROCm rồi CPU", "auto")
        self.backendCombo.addItem("Ưu tiên NVIDIA CUDA — tự fallback", "cuda")
        self.backendCombo.addItem(
            "Ưu tiên AMD ROCm — tự fallback", "amd_rocm"
        )
        self.backendCombo.addItem("CPU — bắt buộc", "cpu")
        self.backendCombo.connect("currentIndexChanged(int)", self._updateBackendStatus)
        self._addFormRow(
            form,
            "Thiết bị:",
            self.backendCombo,
            "Chọn trước khi chạy. Nếu GPU ưu tiên không khả dụng, extension tự fallback về backend tốt nhất còn lại rồi CPU.",
        )

        self.backendStatusLabel = qt.QLabel()
        self.backendStatusLabel.wordWrap = True
        self._addFormRow(
            form,
            "Backend thực tế:",
            self.backendStatusLabel,
            "Backend đã được PyTorch xác nhận, không suy đoán chỉ từ shared VRAM.",
        )
        self._updateBackendStatus()

        self.slicePolicyCombo = qt.QComboBox()
        self.slicePolicyCombo.addItem(
            "Stride 1 — dùng toàn bộ lát cắt (bắt buộc cho cây nhỏ)", 1
        )
        self.slicePolicyCombo.enabled = False
        self._addFormRow(
            form,
            "Lát cắt đầu vào:",
            self.slicePolicyCombo,
            "TotalSegmentator là mô hình 3D. Không được bỏ lát 2/4/6 vì sẽ đổi spacing và có thể làm đứt nhánh ngoại vi.",
        )

        self.resourcePolicyCombo = qt.QComboBox()
        self.resourcePolicyCombo.addItem("Tự động an toàn — khuyến nghị", "auto")
        self.resourcePolicyCombo.addItem("Mục tiêu CPU khoảng 85% — best effort", "cpu85")
        self.resourcePolicyCombo.addItem("Trần RAM 85% — không cố lấp RAM", "ram85")
        self.resourcePolicyCombo.addItem("CPU 85% + trần RAM 85%", "both85")
        self.resourcePolicyCombo.addItem("Thủ công — dành cho benchmark", "manual")
        self.resourcePolicyCombo.connect(
            "currentIndexChanged(int)", self._updatePerformanceUI
        )
        self._addFormRow(
            form,
            "Chính sách tài nguyên:",
            self.resourcePolicyCombo,
            "Mục tiêu CPU là best effort, không phải cam kết. RAM 85% là trần an toàn; dùng nhiều RAM hơn không đồng nghĩa nhanh hơn.",
        )

        logical_cpus = max(1, os.cpu_count() or 1)
        self.threadCombo = qt.QComboBox()
        for count in sorted({max(1, logical_cpus // 2), 18, 20, logical_cpus}):
            if count <= logical_cpus:
                self.threadCombo.addItem(f"{count} CPU thread", count)
        self.threadCombo.currentIndex = self.threadCombo.count - 1
        self.threadCombo.connect("currentIndexChanged(int)", self._updatePerformanceUI)
        self._addFormRow(
            form,
            "CPU threads:",
            self.threadCombo,
            "Giới hạn thread được truyền vào tiến trình riêng. 24 logical thread không bảo đảm Task Manager đạt 100% vì máy có 12 lõi vật lý/SMT.",
        )

        self.resampleWorkersCombo = qt.QComboBox()
        for count in (1, 2, 4, 6):
            self.resampleWorkersCombo.addItem(f"{count} worker", count)
        self.resampleWorkersCombo.connect(
            "currentIndexChanged(int)", self._updatePerformanceUI
        )
        self._addFormRow(
            form,
            "Resampling workers:",
            self.resampleWorkersCombo,
            "Worker song song của bước resampling TotalSegmentator. Mặc định upstream là 1; nhiều hơn có thể chậm hơn do băng thông RAM.",
        )

        self.savingWorkersCombo = qt.QComboBox()
        for count in (1, 2, 4, 6):
            self.savingWorkersCombo.addItem(f"{count} worker", count)
        self.savingWorkersCombo.currentIndex = 3
        self.savingWorkersCombo.connect(
            "currentIndexChanged(int)", self._updatePerformanceUI
        )
        self._addFormRow(
            form,
            "Saving workers:",
            self.savingWorkersCombo,
            "Worker ghi mask của TotalSegmentator. Mặc định upstream là 6; giảm xuống nếu RAM gần trần.",
        )
        self.performancePlanLabel = qt.QLabel()
        self.performancePlanLabel.wordWrap = True
        self.performancePlanLabel.maximumWidth = 520
        form.addRow("Kế hoạch hiệu năng:", self.performancePlanLabel)
        self._updatePerformanceUI()

        self.surfaceCombo = qt.QComboBox()
        self.surfaceCombo.addItem("Nhanh — không smoothing", "preview")
        self.surfaceCombo.addItem("Cân bằng — smoothing nhẹ, mesh gọn", "balanced")
        self.surfaceCombo.addItem("Chi tiết — smoothing mặc định", "detailed")
        self._addFormRow(
            form,
            "Bề mặt 3D:",
            self.surfaceCombo,
            "Nhanh cho preview; Cân bằng/Chi tiết dựng lại mesh mượt từ mask gốc mà không đổi segmentation.",
        )

        self.treeModeCombo = qt.QComboBox()
        self.treeModeCombo.addItem("None — chỉ tạo năm thùy", "none")
        self.treeModeCombo.addItem("A/V/B nguồn gộp — không chạy PTL", "source")
        self.treeModeCombo.addItem("PTL B — chỉ nhãn phế quản", "airway")
        self.treeModeCombo.addItem("PTL A — chỉ nhãn động mạch", "artery")
        self.treeModeCombo.addItem("PTL V — chỉ nhãn tĩnh mạch", "vein")
        self.treeModeCombo.addItem("PTL A+B+V — đầy đủ ba cây", "all")
        self.treeModeCombo.currentIndex = 5
        self.treeModeCombo.connect("currentIndexChanged(int)", self._updateModeUI)
        self._addFormRow(
            form,
            "Cây phân thùy:",
            self.treeModeCombo,
            "Quyết định chính xác bước nào được chạy. PTL tự chạy TotalSegmentator A/V/B làm nguồn; None bỏ qua toàn bộ A/V/B và PTL.",
        )
        self.modeExplanationLabel = qt.QLabel()
        self.modeExplanationLabel.wordWrap = True
        self.modeExplanationLabel.maximumWidth = 520
        form.addRow("Luồng sẽ chạy:", self.modeExplanationLabel)

        self.contextModeCombo = qt.QComboBox()
        self.contextModeCombo.addItem("None — không tạo thêm", "none")
        self.contextModeCombo.addItem("Động mạch chủ", "aorta")
        self.contextModeCombo.addItem("Động mạch chủ + các nhánh quai", "aorta_branches")
        self.contextModeCombo.addItem("Thành ngực — sườn, ức, T1-T12", "chest_wall")
        self.contextModeCombo.addItem("Động mạch chủ + nhánh quai + thành ngực", "all")
        self.contextModeCombo.connect("currentIndexChanged(int)", self._updateModeUI)
        self._addFormRow(
            form,
            "Cấu trúc bổ sung:",
            self.contextModeCombo,
            "Tùy chọn chạy trong Một click. Aorta hiện là mask liên tục; không tự tuyên bố đã tách chính xác đoạn lên/quai/xuống khi chưa có landmark review.",
        )

        self.runAllButton = qt.QPushButton("MỘT CLICK: Tạo và hiển thị mô hình 3D phổi")
        self.runAllButton.toolTip = (
            "Luồng khuyến nghị. Tự tạo đúng các output còn thiếu theo Cây phân thùy, "
            "tổ chức Data tree và hiển thị 3D. Không hiện câu hỏi Fast/Full-resolution giữa chừng."
        )
        self.runAllButton.connect("clicked()", self._runAll)
        form.addRow(self.runAllButton)

        advancedSection = ctk.ctkCollapsibleButton()
        advancedSection.text = "Tác vụ riêng lẻ / công cụ nâng cao"
        advancedSection.collapsed = True
        self.layout.addWidget(advancedSection)
        advancedForm = qt.QFormLayout(advancedSection)
        advancedHelp = qt.QLabel(
            "Các nút dưới đây là bước riêng lẻ để kiểm tra/sửa lại kết quả. "
            "Không cần bấm chúng trước nút Một click."
        )
        advancedHelp.wordWrap = True
        advancedForm.addRow(advancedHelp)

        self.vesselButton = qt.QPushButton("Tạo riêng nguồn phế quản, động mạch và tĩnh mạch")
        self.vesselButton.toolTip = (
            "Chỉ chạy TotalSegmentator lung_vessels và tạo ba mask nguồn gộp. "
            "Không chạy PTL, không tạo năm thùy."
        )
        self.vesselButton.connect("clicked()", self._runVessels)
        advancedForm.addRow(self.vesselButton)

        self.lobeButton = qt.QPushButton("Tạo riêng năm thùy phổi")
        self.lobeButton.toolTip = (
            "Chỉ chạy subset năm thùy của TotalSegmentator. Không tạo A/V/B và không chạy PTL."
        )
        self.lobeButton.connect("clicked()", self._runLobes)
        advancedForm.addRow(self.lobeButton)

        self.showButton = qt.QPushButton("Tạo lại / làm mượt mô hình 3D theo mức đã chọn")
        self.showButton.toolTip = (
            "Không chạy AI. Chỉ xóa closed-surface cũ và dựng lại từ mask hiện có theo mức Bề mặt 3D."
        )
        self.showButton.connect("clicked()", self._showResults)
        advancedForm.addRow(self.showButton)

        self.openTotalSegmentatorButton = qt.QPushButton("Mở giao diện TotalSegmentator")
        self.openTotalSegmentatorButton.toolTip = (
            "Mở module gốc để chạy task ngoài workflow PulmoSlicer. Không cần dùng cho luồng Một click."
        )
        self.openTotalSegmentatorButton.connect("clicked()", self._openTotalSegmentator)
        advancedForm.addRow(self.openTotalSegmentatorButton)

        self.ptlSetupButton = qt.QPushButton("Cài/kiểm tra PTL runtime chính thức")
        self.ptlSetupButton.toolTip = (
            "Tải source đã pin, torch-geometric và ba checkpoint tác giả; "
            "weights chỉ lưu cục bộ, không đóng gói lại. Một click cũng tự thực hiện nếu cần."
        )
        self.ptlSetupButton.connect("clicked()", self._setupPTL)
        advancedForm.addRow(self.ptlSetupButton)

        self.ptlButton = qt.QPushButton("PTL: Tách và đặt nhãn A/B/V theo phân thùy")
        self.ptlButton.toolTip = (
            "Tự tạo mask nguồn TotalSegmentator nếu còn thiếu, sau đó chỉ chạy checkpoint PTL đã chọn. "
            "Không tạo nhu mô phân thùy."
        )
        self.ptlButton.connect("clicked()", self._runPTL)
        advancedForm.addRow(self.ptlButton)

        self.contextButton = qt.QPushButton("Tạo riêng động mạch chủ / thành ngực đã chọn")
        self.contextButton.toolTip = (
            "Chạy một subset TotalSegmentator theo mục Cấu trúc bổ sung. "
            "Không tạo xương đòn, xương vai hoặc sụn sườn."
        )
        self.contextButton.connect("clicked()", self._runContext)
        advancedForm.addRow(self.contextButton)

        visibilitySection = ctk.ctkCollapsibleButton()
        visibilitySection.text = "2. Ẩn/hiện nhanh theo bên và thùy"
        self.layout.addWidget(visibilitySection)
        visibilityLayout = qt.QVBoxLayout(visibilitySection)
        self.anatomyTree = qt.QTreeWidget()
        self.anatomyTree.setHeaderLabel("Right / Left → Lobe → B / A / V / Lung")
        self.anatomyTree.maximumHeight = 300
        self.anatomyTree.maximumWidth = 520
        self.anatomyTree.connect(
            "itemChanged(QTreeWidgetItem*,int)", self._onAnatomyVisibilityChanged
        )
        visibilityLayout.addWidget(self.anatomyTree)
        refreshTreeButton = qt.QPushButton("Làm mới cây phân nhóm")
        refreshTreeButton.connect("clicked()", self._refreshAnatomyTree)
        visibilityLayout.addWidget(refreshTreeButton)
        self._refreshAnatomyTree()
        self._htmlExportState = None
        self._htmlExportTimer = qt.QTimer()
        self._htmlExportTimer.setInterval(100)
        self._htmlExportTimer.connect("timeout()", self._pollHtmlExport)
        self.htmlExportPanel = HtmlExportPanel(
            self.layout, self._exportInteractiveHtml, self._cancelHtmlExport
        )
        self._runButtons = [
            self.runAllButton,
            self.vesselButton,
            self.lobeButton,
            self.showButton,
            self.openTotalSegmentatorButton,
            self.ptlSetupButton,
            self.ptlButton,
            self.contextButton,
            self.htmlExportPanel.exportButton,
        ]
        self._runControls = [
            self.inputSelector,
            self.vesselSelector,
            self.lobeSelector,
            self.ptlSelector,
            self.contextSelector,
            self.lobeQualityCombo,
            self.backendCombo,
            self.resourcePolicyCombo,
            self.threadCombo,
            self.resampleWorkersCombo,
            self.savingWorkersCombo,
            self.surfaceCombo,
            self.treeModeCombo,
            self.contextModeCombo,
        ]
        self._updateModeUI()

        self.progressPanel = ProgressPanel(self.layout)
        openLogsButton = qt.QPushButton("Mở thư mục log hiệu năng")
        openLogsButton.connect("clicked()", self._openLogs)
        self.layout.addWidget(openLogsButton)
        self.layout.addStretch(1)

    @staticmethod
    def _node_selector(node_types, allow_add):
        selector = slicer.qMRMLNodeComboBox()
        selector.nodeTypes = node_types
        selector.noneEnabled = True
        selector.addEnabled = allow_add
        selector.removeEnabled = allow_add
        selector.renameEnabled = allow_add
        selector.setMRMLScene(slicer.mrmlScene)
        return selector

    @staticmethod
    def _addFormRow(form, label_text, widget, tooltip):
        label = qt.QLabel(label_text)
        label.toolTip = tooltip
        widget.toolTip = tooltip
        form.addRow(label, widget)
        return label

    def _selectExistingOutputs(self) -> None:
        for selector, name in (
            (self.vesselSelector, "PulmoSlicer A-V-B"),
            (self.lobeSelector, "PulmoSlicer Lobes"),
            (self.ptlSelector, "PulmoSlicer PTL A-B-V segmental"),
            (self.contextSelector, "PulmoSlicer Thoracic Context"),
        ):
            node = slicer.mrmlScene.GetFirstNodeByName(name)
            if node and node.IsA("vtkMRMLSegmentationNode"):
                selector.setCurrentNode(node)

    def _lobeQuality(self) -> str:
        return self.lobeQualityCombo.currentData

    def _performanceSettings(self):
        logical = max(1, os.cpu_count() or 1)
        policy = str(self.resourcePolicyCombo.currentData)
        if policy == "auto":
            return {"threads": logical, "resample": 1, "saving": min(6, logical)}
        if policy == "cpu85":
            return {
                "threads": max(1, round(logical * 0.85)),
                "resample": 1,
                "saving": min(6, logical),
            }
        if policy == "ram85":
            return {"threads": logical, "resample": 1, "saving": 2}
        if policy == "both85":
            return {
                "threads": max(1, round(logical * 0.85)),
                "resample": 1,
                "saving": 2,
            }
        return {
            "threads": int(self.threadCombo.currentData),
            "resample": int(self.resampleWorkersCombo.currentData),
            "saving": int(self.savingWorkersCombo.currentData),
        }

    def _updatePerformanceUI(self, *_args) -> None:
        manual = str(self.resourcePolicyCombo.currentData) == "manual"
        self.threadCombo.enabled = manual
        self.resampleWorkersCombo.enabled = manual
        self.savingWorkersCombo.enabled = manual
        settings = self._performanceSettings()
        self.performancePlanLabel.text = (
            f"Dùng đủ mọi lát (stride 1); CPU target {settings['threads']} thread; "
            f"resampling {settings['resample']} worker; saving {settings['saving']} worker. "
            "Không chạy nhiều lát như các ảnh 2D độc lập."
        )

    def _threadCount(self):
        return self._performanceSettings()["threads"]

    def _resampleWorkers(self):
        return self._performanceSettings()["resample"]

    def _savingWorkers(self):
        return self._performanceSettings()["saving"]

    def _backendPreference(self) -> str:
        return str(self.backendCombo.currentData)

    def _backendDecision(self):
        preference = self._backendPreference()
        try:
            return self.workflow.resolve_backend(preference)
        except Exception:
            # A preferred GPU is a pre-run hint, never a reason to strand an
            # unattended job. CPU remains the final verified fallback.
            if preference in ("cuda", "amd_rocm"):
                return self.workflow.resolve_backend("auto")
            raise

    def _updateBackendStatus(self, *_args) -> None:
        try:
            decision = self._backendDecision()
            self.backendStatusLabel.text = decision.message
        except Exception as exc:
            self.backendStatusLabel.text = str(exc)

    def _surfaceProfile(self) -> str:
        return str(self.surfaceCombo.currentData)

    def _treeMode(self) -> str:
        return str(self.treeModeCombo.currentData)

    def _contextMode(self) -> str:
        return str(self.contextModeCombo.currentData)

    def _ptlRoles(self):
        mode = self._treeMode()
        if mode == "all":
            return ("airway", "artery", "vein")
        if mode in ("airway", "artery", "vein"):
            return (mode,)
        return ()

    @staticmethod
    def _roleLetters(roles):
        letters = {"airway": "B", "artery": "A", "vein": "V"}
        return "/".join(letters[role] for role in roles)

    def _updateModeUI(self, *_args) -> None:
        mode = self._treeMode()
        descriptions = {
            "none": (
                "Chỉ chạy TotalSegmentator cho 5 thùy → dựng 3D. "
                "Không tạo A/V/B và không chạy PTL. Kết quả A/V/B cũ, nếu có, chỉ bị ẩn chứ không bị xóa."
            ),
            "source": (
                "Chạy TotalSegmentator A/V/B nguồn + 5 thùy → dựng 3D. Không chạy PTL."
            ),
            "airway": (
                "Tự chạy TotalSegmentator A/V/B làm nguồn ẩn → PTL phế quản B → 5 thùy → dựng 3D."
            ),
            "artery": (
                "Tự chạy TotalSegmentator A/V/B làm nguồn ẩn → PTL động mạch A → 5 thùy → dựng 3D."
            ),
            "vein": (
                "Tự chạy TotalSegmentator A/V/B làm nguồn ẩn → PTL tĩnh mạch V → 5 thùy → dựng 3D."
            ),
            "all": (
                "Tự chạy một lần TotalSegmentator A/V/B làm nguồn ẩn → PTL B/A/V → 5 thùy → dựng 3D."
            ),
        }
        self.modeExplanationLabel.text = descriptions[mode]
        if self._contextMode() != "none":
            self.modeExplanationLabel.text += (
                " Sau đó tạo cấu trúc bối cảnh ngực đã chọn bằng subset riêng và tái sử dụng nếu output còn hợp lệ."
            )
        source_is_user_output = mode == "source"
        ptl_selected = bool(self._ptlRoles())
        context_selected = self._contextMode() != "none"
        self.vesselLabel.visible = source_is_user_output
        self.vesselSelector.visible = source_is_user_output
        self.ptlLabel.visible = ptl_selected
        self.ptlSelector.visible = ptl_selected
        self.vesselButton.visible = source_is_user_output
        self.ptlButton.visible = ptl_selected
        self.ptlSetupButton.visible = ptl_selected
        self.contextLabel.visible = context_selected
        self.contextSelector.visible = context_selected
        self.contextButton.visible = context_selected
        if mode != "source":
            node = self.vesselSelector.currentNode()
            if node and node.GetDisplayNode():
                node.GetDisplayNode().SetVisibility3D(False)
        if not ptl_selected:
            node = self.ptlSelector.currentNode()
            if node and node.GetDisplayNode():
                node.GetDisplayNode().SetVisibility3D(False)
        if not context_selected:
            node = self.contextSelector.currentNode()
            if node and node.GetDisplayNode():
                node.GetDisplayNode().SetVisibility3D(False)

    def _onProgress(self, message: str) -> None:
        self.progressPanel.on_message(message)
        slicer.app.processEvents()

    @staticmethod
    def _treeGroup(parent, label):
        for index in range(parent.childCount()):
            child = parent.child(index)
            if child.text(0) == label:
                return child
        item = qt.QTreeWidgetItem(parent, [label])
        item.setFlags(item.flags() | qt.Qt.ItemIsUserCheckable | qt.Qt.ItemIsTristate)
        item.setCheckState(0, qt.Qt.Checked)
        return item

    def _addVisibilityLeaf(self, parent, label, node, segment_id):
        item = qt.QTreeWidgetItem(parent, [label])
        item.setFlags(item.flags() | qt.Qt.ItemIsUserCheckable)
        item.setData(0, qt.Qt.UserRole, node.GetID() + "\t" + segment_id)
        display = node.GetDisplayNode()
        visible = True if display is None else bool(display.GetSegmentVisibility(segment_id))
        item.setCheckState(0, qt.Qt.Checked if visible else qt.Qt.Unchecked)

    def _refreshAnatomyTree(self) -> None:
        from pulmoslicer_engine.adapters.labeling.ptl_labels import ptl_region_metadata

        self.anatomyTree.blockSignals(True)
        try:
            self.anatomyTree.clear()
            roots = {
                side: qt.QTreeWidgetItem(self.anatomyTree, [side])
                for side in ("Right", "Left")
            }
            if self._ptlRoles():
                roots["Central"] = qt.QTreeWidgetItem(self.anatomyTree, ["Central"])
            if self._treeMode() == "source":
                roots["Nguồn tổng hợp"] = qt.QTreeWidgetItem(
                    self.anatomyTree, ["Nguồn tổng hợp"]
                )
            for root in roots.values():
                root.setFlags(
                    root.flags() | qt.Qt.ItemIsUserCheckable | qt.Qt.ItemIsTristate
                )
                root.setCheckState(0, qt.Qt.Checked)

            lobe_node = self.lobeSelector.currentNode()
            lobe_map = {
                "lung_upper_lobe_right": ("Right", "Upper"),
                "lung_middle_lobe_right": ("Right", "Middle"),
                "lung_lower_lobe_right": ("Right", "Lower"),
                "lung_upper_lobe_left": ("Left", "Upper"),
                "lung_lower_lobe_left": ("Left", "Lower"),
            }
            if lobe_node:
                ids = self.workflow._segment_ids(lobe_node)
                for segment_id, (side, lobe) in lobe_map.items():
                    if segment_id in ids:
                        parent = self._treeGroup(roots[side], lobe)
                        self._addVisibilityLeaf(parent, "Lung — whole lobe", lobe_node, segment_id)

            ptl_node = self.ptlSelector.currentNode() if self._ptlRoles() else None
            if ptl_node:
                segmentation = ptl_node.GetSegmentation()
                for index in range(segmentation.GetNumberOfSegments()):
                    segment_id = segmentation.GetNthSegmentID(index)
                    parts = segment_id.split("_")
                    if len(parts) != 4 or parts[0] != "PTL":
                        continue
                    class_id = int(parts[3])
                    metadata = ptl_region_metadata(class_id)
                    side, lobe = metadata["side"], metadata["lobe"]
                    parent = self._treeGroup(roots[side], lobe)
                    system_labels = {
                        "B": "B — Phế quản",
                        "A": "A — Động mạch",
                        "V": "V — Tĩnh mạch",
                    }
                    system = self._treeGroup(parent, system_labels[parts[1]])
                    region = self._treeGroup(system, metadata["region"])
                    name = segmentation.GetSegment(segment_id).GetName()
                    self._addVisibilityLeaf(region, name, ptl_node, segment_id)

            source_node = (
                self.vesselSelector.currentNode()
                if self._treeMode() == "source"
                else None
            )
            if source_node:
                segmentation = source_node.GetSegmentation()
                for segment_id in self.workflow.VESSEL_SEGMENTS:
                    if segmentation.GetSegment(segment_id):
                        name = segmentation.GetSegment(segment_id).GetName()
                        self._addVisibilityLeaf(
                            roots["Nguồn tổng hợp"], name, source_node, segment_id
                        )
            context_node = self.contextSelector.currentNode()
            if context_node:
                from PulmoSlicerAILib.html_export.anatomy import describe_segment

                context_roots = {}
                segmentation = context_node.GetSegmentation()
                for index in range(segmentation.GetNumberOfSegments()):
                    segment_id = segmentation.GetNthSegmentID(index)
                    descriptor = describe_segment("context", segment_id)
                    if descriptor is None or not descriptor.path:
                        continue
                    root_name = descriptor.path[0]
                    if root_name not in context_roots:
                        root_item = qt.QTreeWidgetItem(self.anatomyTree, [root_name])
                        root_item.setFlags(
                            root_item.flags()
                            | qt.Qt.ItemIsUserCheckable
                            | qt.Qt.ItemIsTristate
                        )
                        root_item.setCheckState(0, qt.Qt.Checked)
                        context_roots[root_name] = root_item
                    parent = context_roots[root_name]
                    for group_name in descriptor.path[1:]:
                        parent = self._treeGroup(parent, group_name)
                    self._addVisibilityLeaf(
                        parent, descriptor.display_name, context_node, segment_id
                    )
            self.anatomyTree.expandToDepth(2)
        finally:
            self.anatomyTree.blockSignals(False)

    def _onAnatomyVisibilityChanged(self, item, _column) -> None:
        locator = item.data(0, qt.Qt.UserRole)
        if not locator:
            return
        node_id, segment_id = str(locator).split("\t", 1)
        node = slicer.mrmlScene.GetNodeByID(node_id)
        if node is None:
            return
        node.CreateDefaultDisplayNodes()
        node.GetDisplayNode().SetSegmentVisibility(
            segment_id, item.checkState(0) == qt.Qt.Checked
        )

    def _requireInput(self):
        volume = self.inputSelector.currentNode()
        if volume is None:
            raise ValueError("Hãy chọn một volume CT trước khi chạy.")
        return volume

    def _output(self, selector, name, role):
        node = selector.currentNode()
        node_id = node.GetID() if node else None
        sharing_selectors = [
            other
            for other in (
                self.vesselSelector,
                self.lobeSelector,
                self.ptlSelector,
                self.contextSelector,
            )
            if (
                other is not selector
                and other.currentNode() is not None
                and other.currentNode().GetID() == node_id
            )
        ]
        matches_role = self._nodeMatchesRole(node, role)
        if sharing_selectors:
            if matches_role:
                for other in sharing_selectors:
                    other.setCurrentNode(None)
            else:
                node = None
        if node is not None:
            assigned_role = node.GetAttribute(self.OUTPUT_ROLE_ATTRIBUTE)
            if assigned_role and assigned_role != role and not matches_role:
                node = None
        if node is None:
            node = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentationNode", name)
            selector.setCurrentNode(node)
        node.SetAttribute(self.OUTPUT_ROLE_ATTRIBUTE, role)
        return node

    @classmethod
    def _nodeMatchesRole(cls, node, role) -> bool:
        if node is None:
            return False
        if role == "source":
            return cls._hasSegments(node, PulmonarySegmentationWorkflow.VESSEL_SEGMENTS)
        if role == "lobes":
            return cls._hasSegments(node, PulmonarySegmentationWorkflow.LOBE_SEGMENTS)
        if role == "ptl":
            return any(
                segment_id.startswith("PTL_")
                for segment_id in PulmonarySegmentationWorkflow._segment_ids(node)
            )
        if role == "context":
            known = set(PulmonarySegmentationWorkflow.AORTA_SEGMENTS)
            known.update(PulmonarySegmentationWorkflow.ARCH_BRANCH_SEGMENTS)
            known.update(PulmonarySegmentationWorkflow.CHEST_WALL_SEGMENTS)
            return bool(known & PulmonarySegmentationWorkflow._segment_ids(node))
        return False

    @staticmethod
    def _hasSegments(node, expected) -> bool:
        if node is None:
            return False
        try:
            PulmonarySegmentationWorkflow.verify_segments(node, expected)
            return True
        except RuntimeError:
            return False

    @staticmethod
    def _hasPtlRoles(node, roles) -> bool:
        if node is None:
            return False
        role_prefix = {"airway": "PTL_B_", "artery": "PTL_A_", "vein": "PTL_V_"}
        segment_ids = PulmonarySegmentationWorkflow._segment_ids(node)
        return all(
            any(segment_id.startswith(role_prefix[role]) for segment_id in segment_ids)
            for role in roles
        )

    def _organizeOutputs(self) -> None:
        self.workflow.organize_subject_hierarchy(
            self.lobeSelector.currentNode(),
            self.ptlSelector.currentNode(),
            self.vesselSelector.currentNode(),
            self.contextSelector.currentNode(),
        )

    def _execute(self, label, task, operation) -> None:
        try:
            decision = self._backendDecision()
        except Exception as exc:
            slicer.util.errorDisplay(str(exc))
            return
        for button in self._runButtons:
            button.enabled = False
        for control in self._runControls:
            control.enabled = False
        self.progressPanel.begin(
            task,
            {
                "backend_preference": self._backendPreference(),
                "backend_resolved": decision.backend,
                "backend_message": decision.message,
                "requested_threads": self._threadCount(),
                "slice_stride": 1,
                "resource_policy": str(self.resourcePolicyCombo.currentData),
                "resample_workers": self._resampleWorkers(),
                "saving_workers": self._savingWorkers(),
                "lobe_quality": self._lobeQuality(),
                "patient_data_recorded": False,
            },
        )
        self.progressPanel.note("Hiệu năng: " + self.performancePlanLabel.text)
        try:
            self.statusLabel.text = f"Đang chạy: {label}..."
            self.backendStatusLabel.text = decision.message
            slicer.app.processEvents()
            names = operation(self._onProgress)
            if len(names) <= 5:
                message = "Hoàn tất: " + ", ".join(names)
            else:
                message = f"Hoàn tất: đã tạo {len(names)} segment."
            self.statusLabel.text = message
            self.progressPanel.finish(True, message)
        except Exception as exc:
            self.statusLabel.text = "Thất bại — chưa tạo kết quả hợp lệ."
            safe_detail = " ".join(str(exc).split())[:400]
            self.progressPanel.finish(False, "Tác vụ thất bại: " + safe_detail)
            slicer.util.errorDisplay(str(exc))
        finally:
            for button in self._runButtons:
                button.enabled = True
            for control in self._runControls:
                control.enabled = True
            self._updateModeUI()
            self._updatePerformanceUI()

    def _runVessels(self) -> None:
        self._execute(
            "phân đoạn phế quản và mạch phổi",
            "lung_vessels",
            lambda callback: self._runVesselsOperation(callback),
        )

    def _runVesselsOperation(self, callback, show=True):
        decision = self._backendDecision()
        self.progressPanel.set_subtask("TotalSegmentator — A/V/B nguồn")
        self.progressPanel.note("Thiết bị: " + decision.message)
        output = self._output(self.vesselSelector, "PulmoSlicer A-V-B", "source")
        names = self.workflow.run_vessels(
                self._requireInput(),
                output,
                "normal",
                decision.force_cpu,
                callback,
                self._threadCount(),
                self._resampleWorkers(),
                self._savingWorkers(),
        )
        if show:
            self.progressPanel.set_subtask("Dựng 3D — A/V/B nguồn")
            self.workflow.show_3d(
                [output], self._surfaceProfile(), progress_callback=callback
            )
        self._organizeOutputs()
        self._refreshAnatomyTree()
        return names

    def _runLobes(self) -> None:
        self._execute(
            "phân đoạn năm thùy phổi",
            "five_lobes",
            lambda callback: self._runLobesOperation(callback),
        )

    def _runLobesOperation(self, callback, show=True):
        decision = self._backendDecision()
        self.progressPanel.set_subtask("TotalSegmentator — năm thùy phổi")
        self.progressPanel.note("Thiết bị: " + decision.message)
        output = self._output(self.lobeSelector, "PulmoSlicer Lobes", "lobes")
        names = self.workflow.run_lobes(
                self._requireInput(),
                output,
                self._lobeQuality(),
                decision.force_cpu,
                callback,
                self._threadCount(),
                self._resampleWorkers(),
                self._savingWorkers(),
        )
        if show:
            self.progressPanel.set_subtask("Dựng 3D — năm thùy phổi")
            self.workflow.show_3d(
                [output], self._surfaceProfile(), progress_callback=callback
            )
        self._organizeOutputs()
        self._refreshAnatomyTree()
        return names

    def _runContext(self) -> None:
        if self._contextMode() == "none":
            slicer.util.infoDisplay("Hãy chọn một mục Cấu trúc bổ sung trước khi chạy.")
            return
        self._execute(
            "động mạch chủ và bối cảnh thành ngực",
            "thoracic_context",
            lambda callback: self._runContextOperation(callback),
        )

    def _runContextOperation(self, callback, show=True):
        mode = self._contextMode()
        if mode == "none":
            return ()
        decision = self._backendDecision()
        self.progressPanel.set_subtask("TotalSegmentator — bối cảnh ngực")
        self.progressPanel.note("Thiết bị: " + decision.message)
        output = self._output(
            self.contextSelector, "PulmoSlicer Thoracic Context", "context"
        )
        names = self.workflow.run_thoracic_context(
            self._requireInput(),
            output,
            mode,
            self._lobeQuality(),
            decision.force_cpu,
            callback,
            self._threadCount(),
            self._resampleWorkers(),
            self._savingWorkers(),
        )
        if show:
            self.progressPanel.set_subtask("Dựng 3D — bối cảnh ngực")
            self.workflow.show_3d(
                [output], self._surfaceProfile(), progress_callback=callback
            )
        self._organizeOutputs()
        self._refreshAnatomyTree()
        return names

    def _setupPTL(self) -> None:
        self._execute(
            "cài đặt và xác minh PTL runtime",
            "ptl_setup",
            lambda callback: (self.workflow.setup_ptl(callback),),
        )

    def _runPTL(self) -> None:
        self._execute(
            "gán nhãn PTL airway/artery/vein",
            "ptl_avb_labels",
            lambda callback: self._runPTLStandaloneOperation(callback),
        )

    def _runPTLStandaloneOperation(self, callback):
        source = self.vesselSelector.currentNode()
        source_ready = False
        if source:
            try:
                self.workflow.verify_segments(source, self.workflow.VESSEL_SEGMENTS)
                source_ready = True
            except RuntimeError:
                source_ready = False
        if not source_ready:
            self.progressPanel.note(
                "Tự động tạo A/V/B nguồn trước PTL; không cần chạy nút TotalSegmentator riêng."
            )
            self._runVesselsOperation(callback, show=False)
        return self._runPTLOperation(callback)

    def _runPTLOperation(self, callback, show=True):
        roles = self._ptlRoles()
        if not roles:
            raise ValueError("Hãy chọn PTL B, PTL A, PTL V hoặc PTL A+B+V.")
        vessel_output = self.vesselSelector.currentNode()
        if vessel_output is None:
            raise ValueError("Hãy tạo A/V/B bằng TotalSegmentator trước khi chạy PTL.")
        output = self._output(
            self.ptlSelector, "PulmoSlicer PTL A-B-V segmental", "ptl"
        )
        self.progressPanel.set_subtask("PTL — " + self._roleLetters(roles))
        names = self.workflow.run_ptl_labels(
            self._requireInput(), vessel_output, output, callback, roles=roles
        )
        if show:
            self.progressPanel.set_subtask("Dựng 3D — PTL " + self._roleLetters(roles))
            self.workflow.show_3d(
                [output], self._surfaceProfile(), progress_callback=callback
            )
        self.branchGateLabel.text = (
            "<b>PTL đã chạy cho " + self._roleLetters(roles) + ".</b> "
            "Đã tạo các nhãn cây theo 10 vùng phải và 8 vùng trái gộp của checkpoint PTL; "
            "đây không phải khối nhu mô phân thùy và phải được bác sĩ kiểm tra từng nhánh."
        )
        self._organizeOutputs()
        self._refreshAnatomyTree()
        return names

    def _runAll(self) -> None:
        self._execute("toàn bộ mô hình 3D cơ bản", "one_click_base_3d", self._runAllOperation)

    def _runAllOperation(self, callback):
        mode = self._treeMode()
        context_mode = self._contextMode()
        roles = self._ptlRoles()
        if mode != "none":
            self._output(self.vesselSelector, "PulmoSlicer A-V-B", "source")
        self._output(self.lobeSelector, "PulmoSlicer Lobes", "lobes")
        if roles:
            self._output(
                self.ptlSelector, "PulmoSlicer PTL A-B-V segmental", "ptl"
            )
        if context_mode != "none":
            self._output(
                self.contextSelector, "PulmoSlicer Thoracic Context", "context"
            )

        run_source = mode != "none" and not self._hasSegments(
            self.vesselSelector.currentNode(), self.workflow.VESSEL_SEGMENTS
        )
        run_lobes = not self._hasSegments(
            self.lobeSelector.currentNode(), self.workflow.LOBE_SEGMENTS
        )
        run_ptl = bool(roles) and not self._hasPtlRoles(
            self.ptlSelector.currentNode(), roles
        )
        context_expected = (
            self.workflow.context_segments(context_mode)
            if context_mode != "none"
            else ()
        )
        run_context = bool(context_expected) and not self._hasSegments(
            self.contextSelector.currentNode(), context_expected
        )
        total_steps = int(run_source) + int(run_lobes) + int(run_ptl) + int(run_context)
        step = 0
        vessel_names = self.workflow.VESSEL_SEGMENTS if mode != "none" else ()
        if run_source:
            step += 1
            self.progressPanel.note(
                f"Bước {step}/{total_steps}: tạo mask nguồn phế quản và mạch phổi"
            )
            vessel_names = self._runVesselsOperation(callback, show=False)
        elif mode != "none":
            self.progressPanel.note("Tái sử dụng A/V/B nguồn hợp lệ; không chạy lại model.")
        lobe_names = self.workflow.LOBE_SEGMENTS
        if run_lobes:
            step += 1
            self.progressPanel.note(f"Bước {step}/{total_steps}: năm thùy phổi")
            lobe_names = self._runLobesOperation(callback, show=False)
        else:
            self.progressPanel.note("Tái sử dụng năm thùy hợp lệ; không chạy lại model.")
        ptl_names = ()
        if run_ptl:
            step += 1
            self.progressPanel.note(
                f"Bước {step}/{total_steps}: PTL " + self._roleLetters(roles)
            )
            ptl_names = self._runPTLOperation(callback, show=False)
        elif roles:
            self.progressPanel.note(
                "Tái sử dụng PTL " + self._roleLetters(roles) + " hợp lệ."
            )
            segmentation = self.ptlSelector.currentNode().GetSegmentation()
            ptl_names = tuple(
                segmentation.GetSegment(segmentation.GetNthSegmentID(index)).GetName()
                for index in range(segmentation.GetNumberOfSegments())
            )
        context_names = ()
        if run_context:
            step += 1
            self.progressPanel.note(
                f"Bước {step}/{total_steps}: động mạch chủ / bối cảnh thành ngực"
            )
            context_names = self._runContextOperation(callback, show=False)
        elif context_expected:
            self.progressPanel.note(
                "Tái sử dụng bối cảnh ngực hợp lệ; không chạy lại model."
            )
            context_names = context_expected
        nodes = [self.lobeSelector.currentNode()]
        if mode == "source":
            nodes.append(self.vesselSelector.currentNode())
        if roles:
            nodes.append(self.ptlSelector.currentNode())
        if context_expected:
            nodes.append(self.contextSelector.currentNode())
        nodes = [node for node in nodes if node]
        self.progressPanel.note("Bước cuối: dựng bề mặt 3D tối ưu")
        self.progressPanel.set_subtask("Dựng bề mặt 3D cuối")
        self.workflow.show_3d(
            nodes, self._surfaceProfile(), progress_callback=callback
        )
        self._organizeOutputs()
        self._refreshAnatomyTree()
        if mode == "none":
            self.branchGateLabel.text = (
                "<b>Đã chỉ tạo năm thùy.</b> A/V/B và PTL bị bỏ qua theo lựa chọn None."
            )
        return vessel_names + lobe_names + ptl_names + context_names

    def _showResults(self) -> None:
        mode = self._treeMode()
        nodes = [self.lobeSelector.currentNode()]
        if mode == "source":
            nodes.append(self.vesselSelector.currentNode())
        if self._ptlRoles():
            nodes.append(self.ptlSelector.currentNode())
        if self._contextMode() != "none":
            nodes.append(self.contextSelector.currentNode())
        try:
            self.progressPanel.set_subtask("Dựng lại bề mặt 3D")
            self.statusLabel.text = self.workflow.show_3d(
                [node for node in nodes if node], self._surfaceProfile()
            )
            self._organizeOutputs()
            self._refreshAnatomyTree()
        except Exception as exc:
            slicer.util.errorDisplay(str(exc))

    def _htmlExportNodes(self):
        nodes = []
        if self.lobeSelector.currentNode():
            nodes.append(self.lobeSelector.currentNode())
        if self._ptlRoles() and self.ptlSelector.currentNode():
            nodes.append(self.ptlSelector.currentNode())
        elif self._treeMode() == "source" and self.vesselSelector.currentNode():
            nodes.append(self.vesselSelector.currentNode())
        if self.contextSelector.currentNode():
            nodes.append(self.contextSelector.currentNode())
        extra_roles = {"tumor", "aorta", "chest_wall", "territories"}
        for node in slicer.util.getNodesByClass("vtkMRMLSegmentationNode"):
            if node.GetAttribute(self.OUTPUT_ROLE_ATTRIBUTE) in extra_roles and node not in nodes:
                nodes.append(node)
        return nodes

    def _exportInteractiveHtml(self, options, open_after) -> None:
        if self._htmlExportState is not None:
            slicer.util.infoDisplay("Một tác vụ xuất HTML đang chạy.")
            return
        for button in self._runButtons:
            button.enabled = False
        for control in self._runControls:
            control.enabled = False
        self.htmlExportPanel.set_running(True)
        self.progressPanel.begin(
            "interactive_html_export",
            {
                "profile": options.profile,
                "color_template": options.color_template_id,
                "select_all_valid": True,
                "anonymized": True,
                "patient_data_recorded": False,
            },
        )
        self.progressPanel.set_subtask("Xuất HTML 3D tương tác")
        self.statusLabel.text = "Đang sao chép bề mặt nguồn để xử lý nền..."
        slicer.app.processEvents()
        try:
            export_nodes = self._htmlExportNodes()
            self.htmlExporter.apply_slicer_colors(
                export_nodes, options.color_template_id
            )
            captured = self.htmlExporter.capture(
                export_nodes, progress_callback=self._onProgress
            )
        except Exception as exc:
            safe_detail = " ".join(str(exc).split())[:400]
            self.statusLabel.text = "Xuất HTML thất bại; scene nguồn không bị thay đổi."
            self.progressPanel.finish(False, "Xuất HTML thất bại: " + safe_detail)
            slicer.util.errorDisplay(str(exc))
            self._setHtmlExportUiRunning(False)
            return

        messages = thread_queue.Queue()
        cancel_event = threading.Event()

        def run_export():
            try:
                result = self.htmlExporter.export_captured(
                    captured,
                    options,
                    progress_callback=lambda message: messages.put(
                        ("progress", message)
                    ),
                    cancellation_check=cancel_event.is_set,
                )
                messages.put(("result", result))
            except Exception as exc:
                messages.put(("error", " ".join(str(exc).split())[:400]))

        worker = threading.Thread(
            target=run_export,
            name="PulmoSlicerHtmlExport",
            daemon=True,
        )
        self._htmlExportState = {
            "queue": messages,
            "cancel": cancel_event,
            "thread": worker,
            "open_after": open_after,
        }
        self.statusLabel.text = "Đang tối ưu mesh trong worker nền; Slicer vẫn sử dụng được."
        worker.start()
        self._htmlExportTimer.start()

    def _setHtmlExportUiRunning(self, running: bool) -> None:
        self.htmlExportPanel.set_running(running)
        for button in self._runButtons:
            button.enabled = not running
        for control in self._runControls:
            control.enabled = not running
        if not running:
            self._updateModeUI()
            self._updatePerformanceUI()

    def _cancelHtmlExport(self) -> None:
        if self._htmlExportState is None:
            return
        self._htmlExportState["cancel"].set()
        self.htmlExportPanel.cancelButton.enabled = False
        self.statusLabel.text = "Đang yêu cầu hủy tại checkpoint an toàn gần nhất..."
        self.progressPanel.note(
            "Đã yêu cầu hủy; filter VTK hiện tại sẽ hoàn tất rồi tác vụ mới dừng."
        )

    def _pollHtmlExport(self) -> None:
        state = self._htmlExportState
        if state is None:
            self._htmlExportTimer.stop()
            return
        while True:
            try:
                event, payload = state["queue"].get_nowait()
            except thread_queue.Empty:
                break
            if event == "progress":
                self._onProgress(payload)
                continue
            self._htmlExportTimer.stop()
            self._htmlExportState = None
            self._setHtmlExportUiRunning(False)
            if event == "result":
                result = payload
                size_mb = result.byte_count / (1024 * 1024)
                message = (
                    f"Đã xuất {result.node_count} cấu trúc, "
                    f"{result.triangle_count:,} triangle, {size_mb:.1f} MB. "
                    f"SHA-256: {result.file_sha256[:12]}…"
                )
                if result.warnings:
                    message += (
                        f" Có {len(result.warnings)} cảnh báo trong manifest/log."
                    )
                self.statusLabel.text = message
                self.progressPanel.finish(True, message)
                if state["open_after"]:
                    qt.QDesktopServices.openUrl(
                        qt.QUrl.fromLocalFile(str(result.output_path))
                    )
            else:
                cancelled = "người dùng hủy" in payload
                message = (
                    "Đã hủy xuất HTML; scene nguồn không bị thay đổi."
                    if cancelled
                    else "Xuất HTML thất bại: " + payload
                )
                self.statusLabel.text = message
                self.progressPanel.finish(False, message)
                if not cancelled:
                    slicer.util.errorDisplay(payload)
            break

    def cleanup(self) -> None:
        if self._htmlExportState is not None:
            self._htmlExportState["cancel"].set()
        if hasattr(self, "_htmlExportTimer"):
            self._htmlExportTimer.stop()

    def _openLogs(self) -> None:
        path = self.progressPanel.log_path
        if path is None:
            slicer.util.infoDisplay("Chưa có log. Hãy chạy một tác vụ trước.")
            return
        qt.QDesktopServices.openUrl(qt.QUrl.fromLocalFile(str(path.parent)))

    @staticmethod
    def _openTotalSegmentator() -> None:
        if slicer.app.moduleManager().module("TotalSegmentator") is None:
            slicer.util.errorDisplay("TotalSegmentator chưa được cài hoặc chưa được bật.")
            return
        slicer.util.selectModule("TotalSegmentator")
