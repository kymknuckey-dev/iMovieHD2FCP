from __future__ import annotations

import html
import json
import re
import shlex
import sys
from dataclasses import dataclass, field
from pathlib import Path

try:
    from PySide6.QtCore import QProcess, QSettings, Qt, QUrl
    from PySide6.QtGui import QAction, QDesktopServices, QTextCursor
    from PySide6.QtWidgets import (
        QApplication,
        QButtonGroup,
        QFileDialog,
        QFrame,
        QGridLayout,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QMainWindow,
        QMessageBox,
        QPushButton,
        QProgressBar,
        QRadioButton,
        QScrollArea,
        QStackedWidget,
        QStatusBar,
        QStyle,
        QTextEdit,
        QToolBar,
        QVBoxLayout,
        QWidget,
    )
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "The graphical application requires PySide6.\n"
        "Run: python3 install_gui.py"
    ) from exc

from . import __version__


@dataclass
class AnalysisSummary:
    projects: int = 0
    media: int = 0
    titles: int = 0
    transitions: int = 0
    issues: int = 0
    reports: list[Path] = field(default_factory=list)
    archive_report: Path | None = None


class PathPicker(QWidget):
    def __init__(self, label: str, placeholder: str) -> None:
        super().__init__()
        self.label = QLabel(label)
        self.label.setObjectName("fieldLabel")
        self.edit = QLineEdit()
        self.edit.setPlaceholderText(placeholder)
        self.edit.setClearButtonEnabled(True)
        self.button = QPushButton("Choose…")
        self.button.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_DirOpenIcon)
        )
        self.button.clicked.connect(self.choose)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(self.edit, 1)
        row.addWidget(self.button)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        layout.addWidget(self.label)
        layout.addLayout(row)

    def choose(self) -> None:
        start = self.text() or str(Path.home())
        selected = QFileDialog.getExistingDirectory(self, self.label.text(), start)
        if selected:
            self.edit.setText(selected)

    def text(self) -> str:
        return self.edit.text().strip()

    def setText(self, value: str) -> None:
        self.edit.setText(value)


class JourneyItem(QFrame):
    def __init__(self, number: int, title: str) -> None:
        super().__init__()
        self.setObjectName("journeyItem")
        self.number = number

        self.badge = QLabel(str(number))
        self.badge.setObjectName("journeyBadge")
        self.badge.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.text = QLabel(title)
        self.text.setObjectName("journeyText")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.addWidget(self.badge)
        layout.addWidget(self.text, 1)

    def set_state(self, state: str) -> None:
        self.setProperty("state", state)
        self.badge.setText("✓" if state == "done" else str(self.number))
        self.style().unpolish(self)
        self.style().polish(self)


class ContextTile(QFrame):
    def __init__(self, title: str, explanation: str) -> None:
        super().__init__()
        self.setObjectName("contextTile")

        self.title = QLabel(title)
        self.title.setObjectName("tileTitle")
        self.value = QLabel("0")
        self.value.setObjectName("tileValue")
        self.explanation = QLabel(explanation)
        self.explanation.setObjectName("tileExplanation")
        self.explanation.setWordWrap(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(4)
        layout.addWidget(self.title)
        layout.addWidget(self.value)
        layout.addWidget(self.explanation)

    def set_value(self, value: int | str) -> None:
        self.value.setText(str(value))


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.settings = QSettings("iMovieHD2FCP", "iMovieHD2FCP")
        self.process: QProcess | None = None
        self.callback = None
        self.plan_path: Path | None = None
        self.import_path: Path | None = None
        self.last_output: Path | None = None
        self.analysis_summary = AnalysisSummary()
        self.previous_content_index = 0

        self.setWindowTitle(f"iMovieHD2FCP {__version__}")
        self.resize(1120, 800)

        self._build_actions()
        self._build_toolbar()
        self._build_ui()
        self._apply_style()
        self._restore()
        self._refresh_stage()

    # ---------- UI ----------

    def _build_actions(self) -> None:
        self.action_activity = QAction("Activity", self)
        self.action_activity.setCheckable(True)
        self.action_activity.triggered.connect(self.toggle_activity)

        self.action_doctor = QAction("Check Installation", self)
        self.action_doctor.triggered.connect(self.run_doctor)

        self.action_open = QAction("Open Output", self)
        self.action_open.triggered.connect(self.open_output)

    def _build_toolbar(self) -> None:
        bar = QToolBar("Main")
        bar.setMovable(False)
        bar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        bar.addAction(self.action_doctor)
        bar.addSeparator()
        bar.addAction(self.action_activity)
        bar.addSeparator()
        bar.addAction(self.action_open)
        self.addToolBar(bar)

    def _build_ui(self) -> None:
        central = QWidget()
        root = QHBoxLayout(central)
        root.setContentsMargins(20, 18, 20, 16)
        root.setSpacing(18)

        journey_panel = QFrame()
        journey_panel.setObjectName("journeyPanel")
        journey_layout = QVBoxLayout(journey_panel)
        journey_layout.setContentsMargins(12, 14, 12, 14)
        journey_layout.setSpacing(8)

        journey_title = QLabel("Migration Journey")
        journey_title.setObjectName("journeyTitle")
        journey_layout.addWidget(journey_title)

        self.journey = [
            JourneyItem(1, "Choose Archive"),
            JourneyItem(2, "Analyse"),
            JourneyItem(3, "Convert"),
            JourneyItem(4, "Organise"),
            JourneyItem(5, "Final Cut Imports"),
            JourneyItem(6, "Finished"),
        ]
        for item in self.journey:
            journey_layout.addWidget(item)
        journey_layout.addStretch(1)
        root.addWidget(journey_panel, 0)

        main = QVBoxLayout()
        main.setSpacing(12)

        title = QLabel("iMovieHD2FCP")
        title.setObjectName("appTitle")
        subtitle = QLabel(
            "A guided migration assistant for preserving iMovie HD projects in Final Cut Pro."
        )
        subtitle.setObjectName("appSubtitle")
        main.addWidget(title)
        main.addWidget(subtitle)

        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_home_page())      # 0
        self.stack.addWidget(self._build_analysis_page())  # 1
        self.stack.addWidget(self._build_organise_page())  # 2
        self.stack.addWidget(self._build_finish_page())    # 3
        self.stack.addWidget(self._build_activity_page())  # 4
        main.addWidget(self.stack, 1)
        root.addLayout(main, 1)

        self.setCentralWidget(central)

        status = QStatusBar()
        self.setStatusBar(status)
        self.status_label = QLabel("Ready")
        self.progress = QProgressBar()
        self.progress.setMinimumWidth(260)
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setFormat("Ready")
        status.addWidget(self.status_label, 1)
        status.addPermanentWidget(self.progress)

    def _build_home_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 8, 0, 0)
        layout.setSpacing(12)

        intro = QFrame()
        intro.setObjectName("introPanel")
        intro_layout = QVBoxLayout(intro)
        intro_layout.setContentsMargins(18, 16, 18, 16)

        intro_title = QLabel("Preserve your iMovie HD archive")
        intro_title.setObjectName("sectionTitle")
        intro_text = QLabel(
            "This assistant will guide you through analysing, converting, "
            "organising and preparing your projects for Final Cut Pro."
        )
        intro_text.setObjectName("bodyText")
        intro_text.setWordWrap(True)
        intro_layout.addWidget(intro_title)
        intro_layout.addWidget(intro_text)
        layout.addWidget(intro)

        self.source = PathPicker(
            "Original archive",
            "Choose the folder containing your original iMovie HD projects",
        )
        self.output = PathPicker(
            "Output folder",
            "Choose a separate folder for converted media and reports",
        )
        self.source.edit.textChanged.connect(self._refresh_stage)
        self.output.edit.textChanged.connect(self._refresh_stage)
        layout.addWidget(self.source)
        layout.addWidget(self.output)

        info = QFrame()
        info.setObjectName("infoPanel")
        info_row = QHBoxLayout(info)
        info_row.setContentsMargins(14, 12, 14, 12)

        icon = QLabel("i")
        icon.setObjectName("infoIcon")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)

        message = QLabel(
            "<b>Your original archive is never modified.</b><br>"
            "All converted media, reports and Final Cut files are written "
            "to the output folder."
        )
        message.setObjectName("bodyText")
        message.setWordWrap(True)

        info_row.addWidget(icon)
        info_row.addWidget(message, 1)
        layout.addWidget(info)

        self.home_status = QFrame()
        self.home_status.setObjectName("statusPanel")
        hs = QVBoxLayout(self.home_status)
        hs.setContentsMargins(16, 14, 16, 14)

        self.home_title = QLabel("Waiting to begin")
        self.home_title.setObjectName("sectionTitle")
        self.home_text = QLabel("Choose both folders to begin.")
        self.home_text.setObjectName("bodyText")
        self.home_text.setWordWrap(True)
        hs.addWidget(self.home_title)
        hs.addWidget(self.home_text)
        layout.addWidget(self.home_status)

        controls = QHBoxLayout()

        self.cancel_button = QPushButton("Stop Current Operation")
        self.cancel_button.clicked.connect(self.cancel_process)
        self.cancel_button.setVisible(False)

        self.primary_button = QPushButton("Analyse Archive")
        self.primary_button.setObjectName("primaryButton")
        self.primary_button.clicked.connect(self.run_primary)

        controls.addWidget(self.cancel_button)
        controls.addStretch(1)
        controls.addWidget(self.primary_button)
        layout.addLayout(controls)
        layout.addStretch(1)

        return page

    def _build_analysis_page(self) -> QWidget:
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(0, 8, 0, 0)
        outer.setSpacing(12)

        self.analysis_heading = QLabel("Analysis Complete")
        self.analysis_heading.setObjectName("pageHeading")
        self.analysis_intro = QLabel(
            "Here is what iMovieHD2FCP found in your archive."
        )
        self.analysis_intro.setObjectName("bodyText")
        outer.addWidget(self.analysis_heading)
        outer.addWidget(self.analysis_intro)

        overview_label = QLabel("Archive overview")
        overview_label.setObjectName("sectionTitle")
        overview_help = QLabel(
            "These figures come from the archive reports and project timelines."
        )
        overview_help.setObjectName("bodyText")
        overview_help.setWordWrap(True)
        outer.addWidget(overview_label)
        outer.addWidget(overview_help)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        holder = QWidget()
        grid = QGridLayout(holder)
        grid.setSpacing(10)

        self.tiles = {
            "projects": ContextTile(
                "Projects found",
                "Original iMovie HD projects detected in the archive.",
            ),
            "media": ContextTile(
                "Media referenced",
                "Unique video, audio and image files referenced by project timelines.",
            ),
            "titles": ContextTile(
                "Titles detected",
                "Title references recorded in the analysed timelines.",
            ),
            "transitions": ContextTile(
                "Transitions detected",
                "Transition and dissolve references recorded in the timelines.",
            ),
            "issues": ContextTile(
                "Issues found",
                "Warnings, missing media or unresolved references detected.",
            ),
        }

        for i, tile in enumerate(self.tiles.values()):
            grid.addWidget(tile, i // 2, i % 2)
        scroll.setWidget(holder)
        outer.addWidget(scroll, 1)

        self.health_panel = QFrame()
        self.health_panel.setObjectName("statusPanel")
        hp = QVBoxLayout(self.health_panel)
        hp.setContentsMargins(16, 14, 16, 14)

        self.health_title = QLabel("Archive status")
        self.health_title.setObjectName("sectionTitle")
        self.health_text = QLabel("No issues detected.")
        self.health_text.setObjectName("bodyText")
        self.health_text.setWordWrap(True)
        hp.addWidget(self.health_title)
        hp.addWidget(self.health_text)
        outer.addWidget(self.health_panel)

        report_row = QHBoxLayout()
        self.open_summary_button = QPushButton("Open Archive Summary")
        self.open_summary_button.clicked.connect(self.open_archive_summary)

        open_folder = QPushButton("Open Output Folder")
        open_folder.clicked.connect(self.open_output)

        report_row.addWidget(self.open_summary_button)
        report_row.addWidget(open_folder)
        report_row.addStretch(1)
        outer.addLayout(report_row)

        next_panel = QFrame()
        next_panel.setObjectName("nextPanel")
        np = QVBoxLayout(next_panel)
        np.setContentsMargins(18, 16, 18, 16)

        next_title = QLabel("Recommended next step")
        next_title.setObjectName("sectionTitle")
        self.next_text = QLabel(
            "Convert the archive to create modern media and per-project FCPXML files."
        )
        self.next_text.setObjectName("bodyText")
        self.next_text.setWordWrap(True)
        np.addWidget(next_title)
        np.addWidget(self.next_text)
        outer.addWidget(next_panel)

        controls = QHBoxLayout()
        back = QPushButton("Back")
        back.clicked.connect(lambda: self.stack.setCurrentIndex(0))

        self.convert_button = QPushButton("Convert Archive")
        self.convert_button.setObjectName("primaryButton")
        self.convert_button.clicked.connect(self.run_convert)

        controls.addWidget(back)
        controls.addStretch(1)
        controls.addWidget(self.convert_button)
        outer.addLayout(controls)

        return page

    def _build_organise_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 8, 0, 0)
        layout.setSpacing(12)

        heading = QLabel("Organise your Final Cut Events")
        heading.setObjectName("pageHeading")
        intro = QLabel(
            "Final Cut Pro places projects inside Events. Choose how you would "
            "like the converted projects grouped."
        )
        intro.setObjectName("bodyText")
        intro.setWordWrap(True)
        layout.addWidget(heading)
        layout.addWidget(intro)

        explanation = QFrame()
        explanation.setObjectName("infoPanel")
        ex = QVBoxLayout(explanation)
        ex.setContentsMargins(16, 14, 16, 14)

        ex_title = QLabel("Recommended for most archives")
        ex_title.setObjectName("sectionTitle")
        ex_text = QLabel(
            "<b>One Event per parent folder</b> keeps related projects together "
            "using the organisation already present in your archive."
        )
        ex_text.setObjectName("bodyText")
        ex_text.setWordWrap(True)
        ex.addWidget(ex_title)
        ex.addWidget(ex_text)
        layout.addWidget(explanation)

        self.grouping_group = QButtonGroup(self)

        self.radio_parent = QRadioButton("One Event per parent folder")
        self.radio_parent.setChecked(True)
        self.radio_project = QRadioButton("One Event per project")
        self.radio_top = QRadioButton("One Event for the whole archive")

        self.grouping_group.addButton(self.radio_parent)
        self.grouping_group.addButton(self.radio_project)
        self.grouping_group.addButton(self.radio_top)

        layout.addWidget(self.radio_parent)
        layout.addWidget(self.radio_project)
        layout.addWidget(self.radio_top)

        optional = QFrame()
        optional.setObjectName("statusPanel")
        op = QVBoxLayout(optional)
        op.setContentsMargins(16, 14, 16, 14)

        op_title = QLabel("Reviewing the Event Plan is optional")
        op_title.setObjectName("sectionTitle")
        op_text = QLabel(
            "The Event Plan is a CSV file listing each project and its proposed "
            "Final Cut Event. Most users can accept the suggested organisation "
            "without editing it."
        )
        op_text.setObjectName("bodyText")
        op_text.setWordWrap(True)

        self.plan_path_label = QLabel("Event Plan has not been created yet.")
        self.plan_path_label.setObjectName("pathText")
        self.plan_path_label.setWordWrap(True)

        op.addWidget(op_title)
        op.addWidget(op_text)
        op.addWidget(self.plan_path_label)
        layout.addWidget(optional)

        plan_row = QHBoxLayout()

        self.create_plan_button = QPushButton("Create Event Plan")
        self.create_plan_button.clicked.connect(self.run_plan)

        self.open_plan_button = QPushButton("Open Event Plan")
        self.open_plan_button.clicked.connect(self.open_event_plan)

        self.open_plan_folder_button = QPushButton("Open Event Plan Folder")
        self.open_plan_folder_button.clicked.connect(self.open_event_plan_folder)

        plan_row.addWidget(self.create_plan_button)
        plan_row.addWidget(self.open_plan_button)
        plan_row.addWidget(self.open_plan_folder_button)
        plan_row.addStretch(1)
        layout.addLayout(plan_row)

        next_panel = QFrame()
        next_panel.setObjectName("nextPanel")
        next_layout = QVBoxLayout(next_panel)
        next_layout.setContentsMargins(18, 16, 18, 16)

        next_title = QLabel("Next step")
        next_title.setObjectName("sectionTitle")
        next_text = QLabel(
            "When the Event Plan is ready, prepare each project file with its Final Cut Event name."
        )
        next_text.setObjectName("bodyText")
        next_text.setWordWrap(True)

        self.build_imports_button = QPushButton("Prepare Final Cut Project Files")
        self.build_imports_button.setObjectName("primaryButton")
        self.build_imports_button.clicked.connect(self.run_imports)

        next_layout.addWidget(next_title)
        next_layout.addWidget(next_text)
        next_layout.addWidget(
            self.build_imports_button, 0, Qt.AlignmentFlag.AlignRight
        )
        layout.addWidget(next_panel)
        layout.addStretch(1)

        return page

    def _build_finish_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 8, 0, 0)
        layout.setSpacing(12)

        heading = QLabel("Your projects are ready for Final Cut Pro")
        heading.setObjectName("pageHeading")
        intro = QLabel(
            "Each Final Cut project file is stored beside its converted project media."
        )
        intro.setObjectName("bodyText")
        layout.addWidget(heading)
        layout.addWidget(intro)

        summary = QFrame()
        summary.setObjectName("statusPanel")
        sl = QVBoxLayout(summary)
        sl.setContentsMargins(18, 16, 18, 16)

        summary_title = QLabel("Completed")
        summary_title.setObjectName("sectionTitle")

        summary_text = QLabel(
            "✓ Archive analysed<br>"
            "✓ Media converted<br>"
            "✓ Event Plan created<br>"
            "✓ Final Cut project files created"
        )
        summary_text.setObjectName("bodyText")
        summary_text.setWordWrap(True)

        sl.addWidget(summary_title)
        sl.addWidget(summary_text)
        layout.addWidget(summary)

        instructions = QFrame()
        instructions.setObjectName("nextPanel")
        il = QVBoxLayout(instructions)
        il.setContentsMargins(18, 16, 18, 16)

        instructions_title = QLabel("Import into Final Cut Pro")
        instructions_title.setObjectName("sectionTitle")

        instructions_text = QLabel(
            "Open Final Cut Pro, then choose <b>File → Import → XML…</b>. "
            "Select the XML inside the relevant converted project folder."
        )
        instructions_text.setObjectName("bodyText")
        instructions_text.setWordWrap(True)

        il.addWidget(instructions_title)
        il.addWidget(instructions_text)
        layout.addWidget(instructions)

        buttons = QHBoxLayout()

        open_final_cut = QPushButton("Open Converted Projects")
        open_final_cut.clicked.connect(self.open_projects_folder)

        open_report = QPushButton("Open Archive Summary")
        open_report.clicked.connect(self.open_archive_summary)

        buttons.addWidget(open_report)
        buttons.addWidget(open_final_cut)
        buttons.addStretch(1)
        layout.addLayout(buttons)
        layout.addStretch(1)

        return page

    def _build_activity_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 8, 0, 0)

        heading = QLabel("Activity")
        heading.setObjectName("pageHeading")

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)

        back = QPushButton("Back")
        back.clicked.connect(self.hide_activity)

        layout.addWidget(heading)
        layout.addWidget(self.log, 1)
        layout.addWidget(back, 0, Qt.AlignmentFlag.AlignRight)

        return page

    def _apply_style(self) -> None:
        self.setStyleSheet("""
        QLabel#appTitle {
            color: palette(text);
            font-size: 28px;
            font-weight: 700;
        }

        QLabel#appSubtitle,
        QLabel#bodyText,
        QLabel#pathText {
            color: palette(text);
            font-size: 13px;
        }

        QLabel#pathText {
            font-family: monospace;
        }

        QLabel#pageHeading {
            color: palette(text);
            font-size: 24px;
            font-weight: 700;
        }

        QLabel#sectionTitle {
            color: palette(text);
            font-size: 17px;
            font-weight: 700;
        }

        QLabel#fieldLabel {
            color: palette(text);
            font-size: 13px;
            font-weight: 650;
        }

        QFrame#journeyPanel,
        QFrame#introPanel,
        QFrame#statusPanel,
        QFrame#nextPanel,
        QFrame#contextTile {
            background: palette(base);
            border: 1px solid palette(midlight);
            border-radius: 11px;
        }

        QFrame#infoPanel {
            background: palette(alternate-base);
            border: 1px solid palette(highlight);
            border-radius: 10px;
        }

        QLabel#infoIcon {
            background: palette(highlight);
            color: palette(highlighted-text);
            border-radius: 10px;
            min-width: 20px;
            max-width: 20px;
            min-height: 20px;
            max-height: 20px;
            font-weight: 700;
        }

        QLabel#journeyTitle {
            color: palette(text);
            font-size: 16px;
            font-weight: 700;
        }

        QFrame#journeyItem {
            border-radius: 8px;
        }

        QFrame#journeyItem[state="current"] {
            background: palette(highlight);
        }

        QFrame#journeyItem[state="done"] {
            background: palette(alternate-base);
        }

        QFrame#journeyItem[state="current"] QLabel {
            color: palette(highlighted-text);
        }

        QLabel#journeyBadge {
            background: palette(midlight);
            color: palette(text);
            border-radius: 13px;
            min-width: 26px;
            max-width: 26px;
            min-height: 26px;
            max-height: 26px;
            font-weight: 700;
        }

        QLabel#tileTitle {
            color: palette(text);
            font-size: 13px;
            font-weight: 700;
        }

        QLabel#tileValue {
            color: palette(text);
            font-size: 26px;
            font-weight: 700;
        }

        QLabel#tileExplanation {
            color: palette(text);
            font-size: 11px;
        }

        QPushButton#primaryButton {
            min-width: 190px;
            min-height: 36px;
            font-size: 14px;
            font-weight: 700;
        }

        QLineEdit {
            min-height: 30px;
        }

        QPushButton {
            min-height: 28px;
            padding: 3px 10px;
        }
        """)

    # ---------- persistence ----------

    def _restore(self) -> None:
        self.source.setText(self.settings.value("source", "", str))
        self.output.setText(self.settings.value("output", "", str))

        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)

    def closeEvent(self, event) -> None:  # type: ignore[override]
        if self.process is not None:
            answer = QMessageBox.question(
                self,
                "Operation is running",
                "Stop the operation and close the app?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
            self.process.kill()

        self.settings.setValue("source", self.source.text())
        self.settings.setValue("output", self.output.text())
        self.settings.setValue("geometry", self.saveGeometry())
        event.accept()

    # ---------- workflow ----------

    def _refresh_stage(self) -> None:
        if not hasattr(self, "source"):
            return

        source = self.source.text()
        output = self.output.text()
        ready = bool(source and output)
        idle = self.process is None

        self.primary_button.setEnabled(ready and idle)

        if not ready:
            self.home_title.setText("Waiting to begin")
            self.home_text.setText("Choose both folders to begin.")
            self.primary_button.setText("Analyse Archive")
            self._set_journey(0)
            return

        out = Path(output)
        build_reports = out / "Final Cut Build Reports"
        status_file = build_reports / "final-cut-import-status.json"
        plan = out / "Event Plan.csv"
        fcpxml = list(out.rglob("*.fcpxml")) if out.exists() else []
        analysis_files = list(out.rglob("*-analysis.txt")) if out.exists() else []

        if status_file.exists():
            self.home_title.setText("Migration complete")
            self.home_text.setText(
                "Final Cut import files are ready. Review the completion page."
            )
            self.primary_button.setText("View Completion")
            self._set_journey(5)
        elif plan.exists():
            self.plan_path = plan
            self.home_title.setText("Event Plan ready")
            self.home_text.setText(
                "The archive has been organised. Build the Final Cut imports next."
            )
            self.primary_button.setText("Review Event Plan")
            self._set_journey(4)
        elif fcpxml:
            self.home_title.setText("Conversion complete")
            self.home_text.setText(
                f"{len(fcpxml)} project FCPXML file(s) are ready beneath the "
                "projects folder. Organise them into Final Cut Events next."
            )
            self.primary_button.setText("Organise Final Cut Events")
            self._set_journey(3)
        elif analysis_files:
            self.home_title.setText("Analysis available")
            self.home_text.setText(
                "Analysis results are available. Review the archive summary before "
                "converting."
            )
            self.primary_button.setText("View Analysis Results")
            self._set_journey(2)
        else:
            self.home_title.setText("Ready to analyse")
            self.home_text.setText(
                "The assistant will inspect the archive and present a summary before "
                "any conversion begins."
            )
            self.primary_button.setText("Analyse Archive")
            self._set_journey(1)

    def _set_journey(self, current: int) -> None:
        for index, item in enumerate(self.journey):
            if index < current:
                item.set_state("done")
            elif index == current:
                item.set_state("current")
            else:
                item.set_state("waiting")

    def run_primary(self) -> None:
        text = self.primary_button.text()

        if text == "Analyse Archive":
            self.run_analyse()
        elif text == "View Analysis Results":
            self.show_analysis_results()
        elif text in {"Organise Final Cut Events", "Review Event Plan"}:
            self.show_organise_page()
        elif text == "View Completion":
            self.stack.setCurrentIndex(3)
        else:
            self.open_output()

    def run_analyse(self) -> None:
        self._run(
            ["analyse", self.source.text(), self.output.text()],
            "Analysing archive",
            self._after_analyse,
        )

    def _after_analyse(self) -> None:
        self.show_analysis_results()

    def show_analysis_results(self) -> None:
        self.analysis_summary = self._parse_analysis(Path(self.output.text()))

        self.tiles["projects"].set_value(self.analysis_summary.projects)
        self.tiles["media"].set_value(self.analysis_summary.media)
        self.tiles["titles"].set_value(self.analysis_summary.titles)
        self.tiles["transitions"].set_value(self.analysis_summary.transitions)
        self.tiles["issues"].set_value(self.analysis_summary.issues)

        if self.analysis_summary.issues:
            self.health_title.setText("Archive health: Attention required")
            self.health_text.setText(
                f"{self.analysis_summary.issues} warning, missing-media or "
                "unresolved-reference occurrence(s) were found. Open the Archive "
                "Summary before converting."
            )
        else:
            self.health_title.setText("Archive health: Ready")
            self.health_text.setText(
                "No warnings, missing-media or unresolved-reference occurrences "
                "were detected in the available archive reports."
            )

        self.analysis_heading.setText("Analysis Complete")
        self.analysis_intro.setText(
            "Here is what iMovieHD2FCP found in your archive."
        )
        self.next_text.setText(
            "Convert the archive to create modern media and per-project FCPXML files."
        )
        self.stack.setCurrentIndex(1)
        self.action_activity.setChecked(False)
        self._set_journey(2)

    def run_convert(self) -> None:
        self._run(
            ["convert", self.source.text(), self.output.text()],
            "Converting archive",
            self._after_convert,
        )

    def _after_convert(self) -> None:
        out = Path(self.output.text())
        count = len(list(out.rglob("*.fcpxml"))) if out.exists() else 0

        if count == 0:
            QMessageBox.warning(
                self,
                "No project XML files found",
                "Conversion completed, but no per-project FCPXML files were found. "
                "Open Activity to review the detailed output.",
            )
            return

        self.show_organise_page()
        self._refresh_stage()

    def show_organise_page(self) -> None:
        out = Path(self.output.text())
        self.plan_path = out / "Event Plan.csv"

        if self.plan_path.exists():
            self.plan_path_label.setText(str(self.plan_path))
            self.create_plan_button.setText("Rebuild Event Plan")
            self.build_imports_button.setEnabled(True)
        else:
            self.plan_path_label.setText(
                "Event Plan has not been created yet."
            )
            self.create_plan_button.setText("Create Event Plan")
            self.build_imports_button.setEnabled(False)

        self.open_plan_button.setEnabled(self.plan_path.exists())
        self.open_plan_folder_button.setEnabled(self.plan_path.exists())

        self.stack.setCurrentIndex(2)
        self.action_activity.setChecked(False)
        self._set_journey(3 if not self.plan_path.exists() else 4)

    def _selected_event_mode(self) -> str:
        if self.radio_project.isChecked():
            return "project"
        if self.radio_top.isChecked():
            return "top"
        return "parent"

    def run_plan(self) -> None:
        out = Path(self.output.text())
        fcpxml = list(out.rglob("*.fcpxml")) if out.exists() else []

        if not fcpxml:
            QMessageBox.information(
                self,
                "Convert first",
                "An Event Plan requires per-project FCPXML files. "
                "Analyse and Preview do not create them.",
            )
            return

        self.plan_path = out / "Event Plan.csv"
        mode = self._selected_event_mode()

        self._run(
            [
                "plan-events",
                str(out),
                "--plan",
                str(self.plan_path),
                "--event-mode",
                mode,
                "--event-level",
                "1",
            ],
            "Creating Event Plan",
            self._after_plan,
        )

    def _after_plan(self) -> None:
        self.show_organise_page()
        self._refresh_stage()

    def run_imports(self) -> None:
        out = Path(self.output.text())
        plan = self.plan_path or (out / "Event Plan.csv")

        if not plan.exists():
            QMessageBox.information(
                self,
                "Create the Event Plan first",
                "Build Final Cut Imports becomes available after the Event Plan "
                "has been created.",
            )
            return

        build_reports = out / "Final Cut Build Reports"
        self.import_path = out / "projects"

        self._run(
            [
                "build-imports",
                "--plan",
                str(plan),
                "--output",
                str(build_reports),
            ],
            "Preparing Final Cut project files",
            self._after_imports,
        )

    def _after_imports(self) -> None:
        self.stack.setCurrentIndex(3)
        self.action_activity.setChecked(False)
        self._set_journey(5)
        self._refresh_stage()

    # ---------- analysis parsing ----------

    def _parse_analysis(self, output: Path) -> AnalysisSummary:
        reports = (
            list(output.rglob("*-analysis.txt"))
            + list(output.rglob("*-report.txt"))
            + list(output.rglob("*.html"))
        )
        timeline_json = list(output.rglob("*-timeline.json"))

        summary = AnalysisSummary()
        summary.reports = reports
        summary.projects = len(timeline_json)

        media_names: set[str] = set()
        title_count = 0
        transition_count = 0
        issue_count = 0

        for path in timeline_json:
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue

            blob = json.dumps(data)

            title_count += len(re.findall(r"\btitle\b", blob, re.I))
            transition_count += len(
                re.findall(r"\btransition\b|\bdissolve\b", blob, re.I)
            )

            for match in re.findall(
                r'[^"\\]+\.(?:mov|mp4|dv|avi|m4v|wav|aif|aiff|mp3|jpg|jpeg|png)',
                blob,
                re.I,
            ):
                media_names.add(match)

        for path in reports:
            if path.suffix.lower() == ".html":
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue

            issue_count += len(
                re.findall(
                    r"\b(?:missing|warning|unresolved|not found)\b",
                    text,
                    re.I,
                )
            )

        summary.media = len(media_names)
        summary.titles = title_count
        summary.transitions = transition_count
        summary.issues = issue_count
        summary.archive_report = self._find_archive_summary(output)
        return summary

    def _find_archive_summary(self, output: Path) -> Path | None:
        candidates = list(output.rglob("*"))

        def score(path: Path) -> int:
            if not path.is_file():
                return -1

            name = path.name.lower()
            suffix = path.suffix.lower()
            value = 0

            if suffix == ".html":
                value += 50
            elif suffix in {".txt", ".md"}:
                value += 20
            else:
                return -1

            if "archive" in name:
                value += 40
            if "summary" in name:
                value += 40
            if "batch" in name:
                value += 25
            if "report" in name:
                value += 15
            if "analysis" in name:
                value += 5

            if "-analysis" in name or "-report" in name:
                value -= 20

            return value

        ranked = sorted(
            ((score(path), path) for path in candidates),
            key=lambda item: item[0],
            reverse=True,
        )

        for value, path in ranked:
            if value > 0:
                return path

        return None

    # ---------- open helpers ----------

    def open_archive_summary(self) -> None:
        report = self.analysis_summary.archive_report

        if report is None:
            report = self._find_archive_summary(Path(self.output.text()))

        if report and report.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(report)))
            return

        QMessageBox.information(
            self,
            "Archive Summary not found",
            "No archive-wide summary file was found. Open the Output Folder to "
            "review the available project reports.",
        )

    def open_event_plan(self) -> None:
        if self.plan_path and self.plan_path.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.plan_path)))
        else:
            QMessageBox.information(
                self,
                "Event Plan unavailable",
                "Create the Event Plan first.",
            )

    def open_event_plan_folder(self) -> None:
        if self.plan_path and self.plan_path.exists():
            QDesktopServices.openUrl(
                QUrl.fromLocalFile(str(self.plan_path.parent))
            )
        else:
            QMessageBox.information(
                self,
                "Event Plan unavailable",
                "Create the Event Plan first.",
            )

    def open_projects_folder(self) -> None:
        target = Path(self.output.text()) / "projects"

        if target.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(target)))
        else:
            QMessageBox.information(
                self,
                "Converted projects unavailable",
                "The projects folder has not been created yet.",
            )

    def open_output(self) -> None:
        target = Path(self.output.text())

        if target.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(target)))
        else:
            QMessageBox.information(
                self,
                "Output unavailable",
                "The output folder does not exist yet.",
            )

    # ---------- process ----------

    def _run(self, args: list[str], description: str, callback) -> None:
        if self.process is not None:
            return

        self.last_output = Path(self.output.text()) if self.output.text() else None
        self.callback = callback

        command = "imoviehd2fcp " + " ".join(
            shlex.quote(item) for item in args
        )
        self._append_log(f"\n$ {command}\n", "#4f7cff")

        self.process = QProcess(self)
        self.process.setProgram(sys.executable)
        self.process.setArguments(["-m", "imoviehd2fcp", *args])
        self.process.setProcessChannelMode(
            QProcess.ProcessChannelMode.MergedChannels
        )
        self.process.readyReadStandardOutput.connect(self._read_output)
        self.process.finished.connect(self._finished)

        self.status_label.setText(description)
        self.progress.setRange(0, 0)
        self.progress.setFormat(description)
        self.cancel_button.setVisible(True)
        self._set_controls(False)
        self.process.start()

    def _read_output(self) -> None:
        if not self.process:
            return

        text = bytes(self.process.readAllStandardOutput()).decode(
            errors="replace"
        )
        colour = (
            "#d64545"
            if re.search(r"error|failed|traceback", text, re.I)
            else None
        )
        self._append_log(text, colour)

    def _finished(self, code: int, _status) -> None:
        self._read_output()

        callback = self.callback
        self.process = None
        self.callback = None
        self.cancel_button.setVisible(False)

        self.progress.setRange(0, 100)
        self.progress.setValue(100 if code == 0 else 0)
        self.progress.setFormat("Complete" if code == 0 else "Failed")
        self.status_label.setText("Completed" if code == 0 else f"Error {code}")

        self._set_controls(True)

        if code == 0 and callback:
            callback()
        elif code != 0:
            self.previous_content_index = self.stack.currentIndex()
            self.stack.setCurrentIndex(4)
            self.action_activity.setChecked(True)
            QMessageBox.critical(
                self,
                "Operation failed",
                "The operation did not complete. Review Activity for details.",
            )

    def _set_controls(self, enabled: bool) -> None:
        for button in (
            self.primary_button,
            self.convert_button,
            self.create_plan_button,
            self.open_plan_button,
            self.open_plan_folder_button,
            self.build_imports_button,
        ):
            button.setEnabled(enabled)

    def cancel_process(self) -> None:
        if self.process is None:
            return

        answer = QMessageBox.question(
            self,
            "Stop operation",
            "Stop the current operation? Completed conversion work can normally "
            "be resumed later.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if answer == QMessageBox.StandardButton.Yes:
            self.status_label.setText("Stopping…")
            self.process.terminate()

    def _append_log(self, text: str, colour: str | None = None) -> None:
        escaped = html.escape(text).replace("\n", "<br>")
        style = f"color:{colour};" if colour else ""

        cursor = self.log.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertHtml(
            f"<span style='{style}white-space:pre;font-family:monospace'>"
            f"{escaped}</span>"
        )
        self.log.setTextCursor(cursor)
        self.log.ensureCursorVisible()

    def run_doctor(self) -> None:
        self._run(["doctor"], "Checking installation", lambda: None)

    def toggle_activity(self, checked: bool) -> None:
        if checked:
            self.previous_content_index = self.stack.currentIndex()
            self.stack.setCurrentIndex(4)
        else:
            self.stack.setCurrentIndex(self.previous_content_index)

    def hide_activity(self) -> None:
        self.action_activity.setChecked(False)
        self.stack.setCurrentIndex(self.previous_content_index)


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("iMovieHD2FCP")
    app.setOrganizationName("iMovieHD2FCP")
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
