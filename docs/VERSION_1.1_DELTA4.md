# Version 1.1 Delta 4 — Final Per-Project XML

Delta 4 removes duplicate import XML files.

## Final structure

Each converted project retains one importable FCPXML beside its own media:

```text
Output/
├── projects/
│   └── Disney Final/
│       └── Small World/
│           ├── Converted Media/
│           ├── Small World-v1.fcpxml
│           ├── Small World-analysis.txt
│           ├── Small World-report.txt
│           └── Small World-timeline.json
├── Event Plan.csv
├── Final Cut Build Reports/
│   ├── event-import-set-report.txt
│   ├── event-import-set.csv
│   ├── event-import-set.json
│   └── final-cut-import-status.json
├── Logs/
└── _Batch Logs/
```

The Finalise step updates the Event name inside each project's existing XML
atomically. It does not make a duplicate XML tree.

## Workflow changes

- Preview Conversion has been removed from the GUI.
- Analyse is followed directly by Convert Archive.
- The CLI still retains `convert --dry-run` for advanced troubleshooting.
- Build Final Cut Imports is now labelled **Finalise Project XML Files**.
- The completion page opens the converted projects folder.
