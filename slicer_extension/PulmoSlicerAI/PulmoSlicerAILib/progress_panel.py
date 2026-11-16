"""Compact non-modal progress panel for long TotalSegmentator runs."""

from __future__ import annotations

import time

import qt

from .progress import ResearchRunLogger, SystemResourceSampler, parse_totalseg_progress


class ProgressPanel:
    def __init__(self, parent_layout) -> None:
        self.frame = qt.QFrame()
        self.frame.setStyleSheet(
            "QFrame { background-color: rgba(60, 60, 60, 90); border-radius: 6px; padding: 4px; }"
        )
        self.frame.maximumWidth = 520
        layout = qt.QVBoxLayout(self.frame)
        self.stageLabel = qt.QLabel("Sẵn sàng")
        self.stageLabel.wordWrap = True
        self.progressBar = qt.QProgressBar()
        self.progressBar.setRange(0, 100)
        self.progressBar.value = 0
        self.resourceLabel = qt.QLabel("Chưa có tác vụ")
        self.resourceLabel.wordWrap = True
        self.logView = qt.QPlainTextEdit()
        self.logView.readOnly = True
        self.logView.lineWrapMode = qt.QPlainTextEdit.WidgetWidth
        self.logView.horizontalScrollBarPolicy = qt.Qt.ScrollBarAlwaysOff
        self.logView.maximumBlockCount = 200
        self.logView.maximumHeight = 125
        self.logView.maximumWidth = 500
        layout.addWidget(self.stageLabel)
        layout.addWidget(self.progressBar)
        layout.addWidget(self.resourceLabel)
        layout.addWidget(self.logView)
        parent_layout.addWidget(self.frame)

        self._timer = qt.QTimer()
        self._timer.setInterval(1000)
        self._timer.connect("timeout()", self._tick)
        self._sampler = None
        self._logger = None
        self._started = None
        self._last_resource_log = 0
        self._task_label = "Tác vụ"
        self._subtask_label = "Tác vụ"
        self._visible_lines = []
        self._live_progress_index = None
        self._live_progress_key = None

    @property
    def log_path(self):
        return self._logger.path if self._logger else None

    def begin(self, task: str, metadata: dict, log_root=None) -> None:
        self._logger = ResearchRunLogger(task, metadata, root=log_root)
        self._sampler = SystemResourceSampler()
        self._started = time.monotonic()
        self._last_resource_log = 0
        task_labels = {
            "lung_vessels": "TotalSegmentator — A/V/B nguồn",
            "five_lobes": "TotalSegmentator — năm thùy phổi",
            "ptl_avb_labels": "PTL — cây phân thùy",
            "ptl_setup": "Cài đặt PTL",
            "one_click_base_3d": "Một click — mô hình phổi",
            "interactive_html_export": "Xuất HTML 3D all-in-one",
            "thoracic_context": "TotalSegmentator — bối cảnh ngực",
        }
        self._task_label = task_labels.get(task, task)
        self._subtask_label = self._task_label
        self._visible_lines = []
        self._live_progress_index = None
        self._live_progress_key = None
        self.logView.clear()
        self.progressBar.setRange(0, 0)
        self.stageLabel.text = "Đang chuẩn bị..."
        self._append_line(f"Bắt đầu: {self._task_label}")
        self._timer.start()

    def set_subtask(self, label: str) -> None:
        self._subtask_label = label
        self.stageLabel.text = label
        self._live_progress_index = None
        self._live_progress_key = None

    def _render_lines(self) -> None:
        self._visible_lines = self._visible_lines[-200:]
        self.logView.setPlainText("\n".join(self._visible_lines))
        scrollbar = self.logView.verticalScrollBar()
        scrollbar.value = scrollbar.maximum

    def _append_line(self, message: str) -> None:
        if self._visible_lines and self._visible_lines[-1] == message:
            return
        self._visible_lines.append(message)
        self._live_progress_index = None
        self._live_progress_key = None
        self._render_lines()

    def _replace_live_progress(self, key: str, message: str) -> None:
        if self._live_progress_key == key and self._live_progress_index is not None:
            self._visible_lines[self._live_progress_index] = message
        else:
            self._visible_lines.append(message)
            self._live_progress_index = len(self._visible_lines) - 1
            self._live_progress_key = key
        self._render_lines()

    def on_message(self, raw_message: str) -> None:
        update = parse_totalseg_progress(raw_message)
        if update is None:
            return
        self.stageLabel.text = f"{self._subtask_label} — {update.stage}"
        if update.percent is None:
            self.progressBar.setRange(0, 0)
        else:
            self.progressBar.setRange(0, 100)
            self.progressBar.value = update.percent
        visible_message = f"{self._subtask_label}: {update.message}"
        if update.percent is None:
            self._append_line(visible_message)
        else:
            self._replace_live_progress(
                f"{self._subtask_label}|{update.stage}", visible_message
            )
        self._logger.write(
            "progress", stage=update.stage, message=update.message, percent=update.percent
        )

    def note(self, message: str) -> None:
        self.stageLabel.text = message
        self._append_line(message)
        if self._logger:
            self._logger.write("stage", message=message)

    def finish(self, success: bool, message: str) -> None:
        self._timer.stop()
        self.progressBar.setRange(0, 100)
        self.progressBar.value = 100 if success else 0
        self.stageLabel.text = message
        self._append_line(message)
        if self._logger:
            self._logger.write("run_finished", success=success, message=message)
            self._append_line(f"Log: {self._logger.path}")
        self._tick()

    def _tick(self) -> None:
        if self._started is None or self._sampler is None:
            return
        elapsed = int(time.monotonic() - self._started)
        resources = self._sampler.sample()
        cpu = resources["cpu_percent"]
        ram = resources["memory_percent"]
        self.resourceLabel.text = (
            f"Đã chạy {elapsed // 60:02d}:{elapsed % 60:02d} | "
            f"CPU hệ thống {cpu if cpu is not None else '?'}% | RAM {ram if ram is not None else '?'}%"
        )
        if self._logger and elapsed - self._last_resource_log >= 5:
            self._logger.write("resources", **resources)
            self._last_resource_log = elapsed
