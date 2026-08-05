# Version 1.1 Alpha 2 — Phase 1 Polish

Alpha 2 polishes the first graphical application without changing the proven
Version 1 conversion engine.

## Interface improvements

- Native-style toolbar with Check, Start, Cancel and Open Output actions
- Larger status and progress display
- Summary cards for Projects, Media, Titles, Transitions and Warnings
- Colour-coded Activity Log
- Improved error, cancellation and completion dialogs
- Persistent window size, position and last-used paths
- Drag-and-drop support for Finder paths
- Keyboard shortcuts
- Command copying for troubleshooting or CLI use
- Improved validation of source paths, limits and Event Plans
- Refined macOS light and dark appearance

## Progress behaviour

The current conversion engine does not yet emit structured progress events.
Alpha 2 therefore displays an animated activity indicator while a command runs.
The Activity Log remains the authoritative record of processing.

Alpha 3 is planned to add structured project and media progress.
