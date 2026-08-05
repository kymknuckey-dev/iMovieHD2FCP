# Version 1.1 Alpha 3 — Workflow Assistant

Alpha 3 redesigns the graphical application around a guided end-user workflow.

## User experience

The app now guides the user through:

1. Choose the original archive.
2. Choose a separate output folder.
3. Analyse the archive.
4. Convert the archive.
5. Create an Event Plan.
6. Build Final Cut imports.
7. Open the completed import folder.

The interface always explains the current state and the next recommended action.

## Important safeguards

- The preservation message is presented as a high-contrast information panel.
- Event Plan creation is blocked until per-project FCPXML files exist.
- Dry runs clearly explain that no media or FCPXML files are created.
- Existing output folders are inspected so work can resume at the correct stage.
- Detailed processing output is hidden behind the optional Activity view.

## Alpha status

The Workflow Assistant is functional, but the archive summary remains deliberately
simple until the analysis output is exposed as structured application data.
