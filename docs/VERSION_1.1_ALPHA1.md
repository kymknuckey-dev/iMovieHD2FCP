# Version 1.1 Alpha 1 — Graphical Application

Version 1.1 Alpha 1 adds the first native desktop interface while retaining the
proven Version 1 conversion engine.

## Included in Alpha 1

- Source and output folder choosers
- Analyse, convert, verify and report operations
- Conversion options including force, dry run, match and limit
- Live combined command output
- Cancel support
- Persistent last-used paths
- Event Plan generation
- Final Cut import generation
- Open-output button
- Installation diagnostics
- macOS light and dark appearance through Qt

## Install

```bash
cd ~/Development/iMovieHD2FCP
source .venv/bin/activate
python3 install_gui.py
```

Launch with:

```bash
imoviehd2fcp-app
```

You can also double-click:

```text
Launch iMovieHD2FCP.command
```

## Alpha status

This is a functional GUI foundation, not the finished Version 1.1 application.

The progress indicator is indeterminate because the Version 1 engine does not
yet emit structured progress events. The Activity Log remains the authoritative
view of current work.

## Next planned milestone

Alpha 2 will add:

- structured per-project and per-media progress
- archive-analysis dashboard
- project selection before conversion
- richer completion summaries
- clearer warning and failure presentation
