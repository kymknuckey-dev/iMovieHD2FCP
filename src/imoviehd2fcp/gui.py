from __future__ import annotations

import os
import shlex
import subprocess
import sys
from pathlib import Path

try:
    from PySide6.QtCore import QProcess, QSettings, Qt, QUrl
    from PySide6.QtGui import QAction, QDesktopServices, QFont, QTextCursor
    from PySide6.QtWidgets import (
        QApplication,
        QCheckBox,
        QComboBox,
        QFileDialog,
        QFormLayout,
        QGridLayout,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QMainWindow,
        QMessageBox,
        QPlainTextEdit,
        QProgressBar,
        QPushButton,
        QTabWidget,
        QVBoxLayout,
        QWidget,
    )
except ImportError as exc:  # pragma: no cover - exercised on user machines
    raise SystemExit(
        "The graphical application requires PySide6.\n"
        "Install it inside the active virtual environment with:\n\n"
        "  python3 -m pip install '.[gui]'\n"
    ) from exc

from . import __version__


class PathRow(QWidget):
    def __init__(
        self,
        *,
        choose_directory: bool = True,
        save_file: bool = False,
        file_filter: str = "All Files (*)",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.choose_directory = choose_directory
        self.save_file = save_file
        self.file_filter = file_filter

        self.edit = QLineEdit()
        self.edit.setClearButtonEnabled(True)
        self.button = QPushButton("Choose…")
        self.button.clicked.connect(self.choose)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.edit, 1)
        layout.addWidget(self.button)

    def choose(self) -> None:
        current = self.edit.text().strip() or str(Path.home())
        if self.choose_directory:
            selected = QFileDialog.getExistingDirectory(self, "Choose Folder", current)
        elif self.save_file:
            selected, _ = QFileDialog.getSaveFileName(
                self, "Choose File", current, self.file_filter
            )
        else:
            selected, _ = QFileDialog.getOpenFileName(
                self, "Choose File", current, self.file_filter
            )
        if selected:
            self.edit.setText(selected)

    def text(self) -> str:
        return self.edit.text().strip()

    def setText(self, value: str) -> None:
        self.edit.setText(value)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.settings = QSettings("iMovieHD2FCP", "iMovieHD2FCP")
        self.process: QProcess | None = None
        self.last_output: Path | None = None

        self.setWindowTitle(f"iMovieHD2FCP {__version__}")
        self.resize(940, 720)
        self._build_menu()
        self._build_ui()
        self._restore_settings()
        self._set_idle_state()

    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu("&File")
        quit_action = QAction("Quit", self)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        help_menu = self.menuBar().addMenu("&Help")
        docs_action = QAction("Open Documentation", self)
        docs_action.triggered.connect(self.open_documentation)
        help_menu.addAction(docs_action)

        about_action = QAction("About iMovieHD2FCP", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def _build_ui(self) -> None:
        central = QWidget()
        outer = QVBoxLayout(central)
        outer.setContentsMargins(24, 20, 24, 20)
        outer.setSpacing(16)

        title = QLabel("iMovieHD2FCP")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title.setFont(title_font)
        subtitle = QLabel(
            "Migrate legacy iMovie HD projects into modern Final Cut Pro."
        )
        subtitle.setStyleSheet("color: palette(mid);")

        outer.addWidget(title)
        outer.addWidget(subtitle)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_migration_tab(), "Migration")
        self.tabs.addTab(self._build_event_tab(), "Final Cut Imports")
        self.tabs.addTab(self._build_log_tab(), "Activity Log")
        outer.addWidget(self.tabs, 1)

        status_row = QHBoxLayout()
        self.status_label = QLabel("Ready")
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setMaximumWidth(260)
        self.progress.setRange(0, 1)
        self.progress.setValue(0)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.cancel_process)
        self.open_output_button = QPushButton("Open Output")
        self.open_output_button.clicked.connect(self.open_output)

        status_row.addWidget(self.status_label, 1)
        status_row.addWidget(self.progress)
        status_row.addWidget(self.open_output_button)
        status_row.addWidget(self.cancel_button)
        outer.addLayout(status_row)

        self.setCentralWidget(central)

    def _build_migration_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(14)

        paths_box = QGroupBox("Archive")
        paths_form = QFormLayout(paths_box)
        self.source_row = PathRow()
        self.output_row = PathRow()
        paths_form.addRow("Source archive:", self.source_row)
        paths_form.addRow("Conversion output:", self.output_row)
        layout.addWidget(paths_box)

        action_box = QGroupBox("Operation")
        action_layout = QGridLayout(action_box)

        self.operation = QComboBox()
        self.operation.addItem("Analyse archive", "analyse")
        self.operation.addItem("Convert archive", "convert")
        self.operation.addItem("Verify conversion", "verify")
        self.operation.addItem("Build reports", "report")
        self.operation.currentIndexChanged.connect(self._operation_changed)

        self.force_check = QCheckBox("Force reconversion of completed projects")
        self.dry_run_check = QCheckBox("Dry run — show work without converting")
        self.allow_missing_check = QCheckBox("Continue when source media is missing")
        self.stop_on_error_check = QCheckBox("Stop after the first project error")

        self.match_edit = QLineEdit()
        self.match_edit.setPlaceholderText("Optional project name or path text")
        self.limit_edit = QLineEdit()
        self.limit_edit.setPlaceholderText("Optional number")

        action_layout.addWidget(QLabel("Action:"), 0, 0)
        action_layout.addWidget(self.operation, 0, 1, 1, 3)
        action_layout.addWidget(QLabel("Only matching:"), 1, 0)
        action_layout.addWidget(self.match_edit, 1, 1)
        action_layout.addWidget(QLabel("Project limit:"), 1, 2)
        action_layout.addWidget(self.limit_edit, 1, 3)
        action_layout.addWidget(self.force_check, 2, 0, 1, 2)
        action_layout.addWidget(self.dry_run_check, 2, 2, 1, 2)
        action_layout.addWidget(self.allow_missing_check, 3, 0, 1, 2)
        action_layout.addWidget(self.stop_on_error_check, 3, 2, 1, 2)
        layout.addWidget(action_box)

        buttons = QHBoxLayout()
        self.doctor_button = QPushButton("Check Installation")
        self.doctor_button.clicked.connect(self.run_doctor)
        self.run_button = QPushButton("Start")
        self.run_button.setDefault(True)
        self.run_button.clicked.connect(self.run_migration)
        buttons.addWidget(self.doctor_button)
        buttons.addStretch(1)
        buttons.addWidget(self.run_button)
        layout.addLayout(buttons)
        layout.addStretch(1)
        return page

    def _build_event_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(14)

        plan_box = QGroupBox("Create Event Plan")
        plan_form = QFormLayout(plan_box)
        self.converted_root_row = PathRow()
        self.plan_row = PathRow(
            choose_directory=False,
            save_file=True,
            file_filter="CSV Files (*.csv);;All Files (*)",
        )
        self.event_mode = QComboBox()
        self.event_mode.addItems(["parent", "project", "top", "level"])
        self.event_level = QLineEdit("1")
        plan_form.addRow("Converted archive:", self.converted_root_row)
        plan_form.addRow("Event Plan CSV:", self.plan_row)
        plan_form.addRow("Grouping mode:", self.event_mode)
        plan_form.addRow("Folder level:", self.event_level)

        self.plan_button = QPushButton("Create Event Plan")
        self.plan_button.clicked.connect(self.run_plan_events)
        plan_form.addRow("", self.plan_button)
        layout.addWidget(plan_box)

        build_box = QGroupBox("Build Final Cut Imports")
        build_form = QFormLayout(build_box)
        self.import_plan_row = PathRow(
            choose_directory=False,
            save_file=False,
            file_filter="CSV Files (*.csv);;All Files (*)",
        )
        self.import_output_row = PathRow()
        build_form.addRow("Event Plan CSV:", self.import_plan_row)
        build_form.addRow("Import output:", self.import_output_row)

        self.build_button = QPushButton("Build Final Cut Imports")
        self.build_button.clicked.connect(self.run_build_imports)
        build_form.addRow("", self.build_button)
        layout.addWidget(build_box)
        layout.addStretch(1)
        return page

    def _build_log_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setLineWrapMode(QPlainTextEdit.NoWrap)
        layout.addWidget(self.log)

        row = QHBoxLayout()
        clear = QPushButton("Clear Log")
        clear.clicked.connect(self.log.clear)
        copy = QPushButton("Copy All")
        copy.clicked.connect(lambda: QApplication.clipboard().setText(self.log.toPlainText()))
        row.addWidget(clear)
        row.addWidget(copy)
        row.addStretch(1)
        layout.addLayout(row)
        return page

    def _restore_settings(self) -> None:
        self.source_row.setText(self.settings.value("source", "", str))
        self.output_row.setText(self.settings.value("output", "", str))
        self.converted_root_row.setText(
            self.settings.value("converted_root", "", str)
        )
        self.plan_row.setText(self.settings.value("plan", "", str))
        self.import_plan_row.setText(self.settings.value("plan", "", str))
        self.import_output_row.setText(
            self.settings.value("import_output", "", str)
        )

    def _save_settings(self) -> None:
        self.settings.setValue("source", self.source_row.text())
        self.settings.setValue("output", self.output_row.text())
        self.settings.setValue("converted_root", self.converted_root_row.text())
        plan = self.plan_row.text() or self.import_plan_row.text()
        self.settings.setValue("plan", plan)
        self.settings.setValue("import_output", self.import_output_row.text())

    def closeEvent(self, event) -> None:  # type: ignore[override]
        self._save_settings()
        if self.process and self.process.state() != QProcess.NotRunning:
            answer = QMessageBox.question(
                self,
                "Conversion is running",
                "Stop the current operation and quit?",
            )
            if answer != QMessageBox.Yes:
                event.ignore()
                return
            self.process.kill()
        event.accept()

    def _operation_changed(self) -> None:
        command = self.operation.currentData()
        converting = command == "convert"
        filterable = command in {"convert", "verify"}
        self.force_check.setEnabled(converting)
        self.dry_run_check.setEnabled(converting)
        self.allow_missing_check.setEnabled(converting)
        self.stop_on_error_check.setEnabled(converting)
        self.match_edit.setEnabled(filterable)
        self.limit_edit.setEnabled(filterable)

    def _set_idle_state(self) -> None:
        self.cancel_button.setEnabled(False)
        self.open_output_button.setEnabled(bool(self.last_output))
        self.run_button.setEnabled(True)
        self.doctor_button.setEnabled(True)
        self.plan_button.setEnabled(True)
        self.build_button.setEnabled(True)
        self.progress.setRange(0, 1)
        self.progress.setValue(0)

    def _set_running_state(self, description: str) -> None:
        self.status_label.setText(description)
        self.cancel_button.setEnabled(True)
        self.open_output_button.setEnabled(False)
        self.run_button.setEnabled(False)
        self.doctor_button.setEnabled(False)
        self.plan_button.setEnabled(False)
        self.build_button.setEnabled(False)
        self.progress.setRange(0, 0)
        self.tabs.setCurrentIndex(2)

    def append_log(self, text: str) -> None:
        if text:
            self.log.moveCursor(QTextCursor.MoveOperation.End)
            self.log.insertPlainText(text)
            self.log.ensureCursorVisible()

    def run_cli(self, arguments: list[str], description: str, output: Path | None = None) -> None:
        if self.process and self.process.state() != QProcess.NotRunning:
            QMessageBox.warning(self, "Operation in progress", "Please wait or cancel it.")
            return

        self.last_output = output
        command_text = "imoviehd2fcp " + " ".join(shlex.quote(item) for item in arguments)
        self.append_log(f"\n$ {command_text}\n")
        self._set_running_state(description)

        self.process = QProcess(self)
        self.process.setProgram(sys.executable)
        self.process.setArguments(["-m", "imoviehd2fcp", *arguments])
        self.process.setProcessChannelMode(QProcess.MergedChannels)
        self.process.readyReadStandardOutput.connect(self._read_process_output)
        self.process.finished.connect(self._process_finished)
        self.process.errorOccurred.connect(self._process_error)
        self.process.start()

    def _read_process_output(self) -> None:
        if not self.process:
            return
        data = bytes(self.process.readAllStandardOutput()).decode(
            errors="replace"
        )
        self.append_log(data)

    def _process_finished(self, exit_code: int, _status) -> None:
        self._read_process_output()
        success = exit_code == 0
        self.status_label.setText(
            "Completed successfully" if success else f"Stopped with error {exit_code}"
        )
        self._set_idle_state()
        if success:
            self.open_output_button.setEnabled(bool(self.last_output))
        else:
            self.tabs.setCurrentIndex(2)

    def _process_error(self, error) -> None:
        self.append_log(f"\nUnable to run command: {error}\n")
        self.status_label.setText("Unable to start operation")
        self._set_idle_state()

    def cancel_process(self) -> None:
        if not self.process or self.process.state() == QProcess.NotRunning:
            return
        self.status_label.setText("Cancelling…")
        self.process.terminate()
        if not self.process.waitForFinished(3000):
            self.process.kill()

    def run_doctor(self) -> None:
        self.run_cli(["doctor"], "Checking installation")

    def run_migration(self) -> None:
        command = str(self.operation.currentData())
        source = self.source_row.text()
        output = self.output_row.text()

        if command == "report":
            if not output:
                self._missing("Choose the conversion output folder.")
                return
            self.run_cli(["report", output], "Building reports", Path(output))
            return

        if not source or not output:
            self._missing("Choose both the source archive and conversion output.")
            return

        args = [command, source, output]
        if command == "analyse":
            pass
        elif command == "convert":
            if self.force_check.isChecked():
                args.append("--force")
            if self.dry_run_check.isChecked():
                args.append("--dry-run")
            if self.allow_missing_check.isChecked():
                args.append("--allow-missing")
            if self.stop_on_error_check.isChecked():
                args.append("--stop-on-error")
        if command in {"convert", "verify"}:
            if self.match_edit.text().strip():
                args.extend(["--match", self.match_edit.text().strip()])
            if self.limit_edit.text().strip():
                if not self.limit_edit.text().strip().isdigit():
                    self._missing("Project limit must be a whole number.")
                    return
                args.extend(["--limit", self.limit_edit.text().strip()])

        self.run_cli(args, f"Running {command}", Path(output))

    def run_plan_events(self) -> None:
        converted = self.converted_root_row.text()
        plan = self.plan_row.text()
        if not converted or not plan:
            self._missing("Choose a converted archive and Event Plan CSV.")
            return
        args = [
            "plan-events",
            converted,
            "--plan",
            plan,
            "--event-mode",
            self.event_mode.currentText(),
        ]
        level = self.event_level.text().strip()
        if level:
            if not level.isdigit():
                self._missing("Folder level must be a whole number.")
                return
            args.extend(["--event-level", level])
        self.import_plan_row.setText(plan)
        self.run_cli(args, "Creating Event Plan", Path(plan).parent)

    def run_build_imports(self) -> None:
        plan = self.import_plan_row.text()
        output = self.import_output_row.text()
        if not plan or not output:
            self._missing("Choose an Event Plan CSV and import output folder.")
            return
        self.run_cli(
            ["build-imports", "--plan", plan, "--output", output],
            "Building Final Cut imports",
            Path(output),
        )

    def _missing(self, message: str) -> None:
        QMessageBox.information(self, "More information required", message)

    def open_output(self) -> None:
        if self.last_output and self.last_output.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.last_output)))
        elif self.last_output:
            QMessageBox.information(
                self, "Output unavailable", f"Folder does not exist yet:\n{self.last_output}"
            )

    def open_documentation(self) -> None:
        project_root = Path(__file__).resolve().parents[2]
        docs = project_root / "docs" / "GETTING_STARTED.md"
        if docs.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(docs)))
        else:
            QMessageBox.information(
                self,
                "Documentation",
                "See the docs folder in the iMovieHD2FCP project.",
            )

    def show_about(self) -> None:
        QMessageBox.about(
            self,
            "About iMovieHD2FCP",
            f"<h3>iMovieHD2FCP {__version__}</h3>"
            "<p>Graphical migration assistant for preserving legacy "
            "iMovie HD projects in Final Cut Pro.</p>"
            "<p>Version 1.1 Alpha 1 uses the proven Version 1 conversion engine.</p>",
        )


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("iMovieHD2FCP")
    app.setOrganizationName("iMovieHD2FCP")
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
