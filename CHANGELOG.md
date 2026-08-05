# Changelog

## 1.1.0rc1

- Declared Version 1.1 feature complete and entered release-candidate testing.
- Preserved the guided Analyse → Convert → Organise → Prepare → Import workflow.
- Preserved one cleanly named FCPXML per project.
- Preserved Event Plan editing and in-place Event assignment.
- Added RC1 release notes and a formal test checklist.
- Limited further work to bug fixes, compatibility and documentation.

## 1.1.0b1

- Released Version 1.1 Beta 1 for final workflow testing.
- Removed the internal -v1 suffix from new FCPXML filenames.
- Simplified Final Cut terminology in the GUI.
- Refined the completion page and final preparation action.
- Retained compatibility with existing older FCPXML filenames.

## 1.1.0.dev4

- Removed Preview Conversion from the guided GUI.
- Retained convert --dry-run in the CLI.
- Finalised each project's existing FCPXML in place.
- Removed duplicate Final Cut Imports XML copies.
- Added Final Cut Build Reports and a completion status marker.
- Updated the completion screen to open Converted Projects.

## 1.1.0.dev3

- New conversions are written beneath output/projects/.
- Converted media, FCPXML, reports and timeline metadata stay together.
- Existing root-level conversion outputs remain readable.
- Event grouping hides the technical projects/ container.
- Final Cut Imports are excluded from Event Plan source discovery.
- Added Open Converted Projects to the completion page.

## 1.1.0.dev2

- Added Delta 2 User Experience improvements.
- Added archive-wide summary selection.
- Added contextual descriptions to analysis statistics.
- Fixed text contrast in light and dark macOS appearances.
- Added the Event Planning Assistant.
- Added plain-language Event grouping choices.
- Added Event Plan open and folder actions.
- Added a dedicated Migration Complete page.
- Preserved Version 1 output compatibility.

## 1.1.0a3.post1

- Replaced the dry-run checkbox with an explicit Preview Conversion button.
- Added clear post-preview guidance to run a full conversion.
- Added a visible Stop Current Operation control.
- Added close/cancel confirmation while processing.
- Kept the guided workflow visible during operations.

## 1.1.0a3

- Rebuilt the GUI as a guided Workflow Assistant.
- Added clear step-by-step next actions.
- Added prerequisite checking for Event Plan generation.
- Added explicit dry-run explanations.
- Replaced ambiguous summary cards with contextual status panels.
- Improved preservation-message contrast and readability.
- Hid detailed logs behind an optional Activity view.

## 1.1.0a2

- Added the Phase 1 graphical interface polish.
- Added toolbar actions, status cards and improved progress display.
- Added colour-coded logs and stronger dialogs.
- Added Finder drag-and-drop support.
- Added persistent window geometry and paths.
- Added input validation and command copying.
- Retained the Version 1 conversion engine unchanged.

## 1.1.0a1

- Added the first graphical desktop application.
- Added folder selection, migration operations, live logs and cancellation.
- Added graphical Event Plan and Final Cut import workflows.
- Added persistent GUI preferences and output opening.
- Kept the Version 1 conversion engine unchanged.

## 1.0.0

- First stable release.
- Finalised the unified CLI and production migration workflow.
- Added analysis, resumable conversion, verification, reporting, Event planning and safe import generation.
- Added timestamp provenance, clean duplicate Browser names, persistent logs and HTML/text reports.
- Added installer safeguards, documentation, regression tests and GitHub Actions.
- Declared intact one-project-per-FCPXML as the production import strategy.

## 1.0.0rc3
- Reporting, logging, documentation and operational polish.

## 1.0.0rc2
- Timestamp provenance and duplicate-name cleanup.

## 1.0.0rc1
- Unified installed command and product wrapper.
