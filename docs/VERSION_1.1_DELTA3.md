# Version 1.1 Delta 3 — Project Output Structure

Delta 3 changes where new conversions are written.

## New project layout

```text
Output/
├── projects/
│   ├── Disney Final/
│   │   ├── Disney/
│   │   │   ├── Converted Media/
│   │   │   ├── Disney-v1.fcpxml
│   │   │   ├── Disney-analysis.txt
│   │   │   ├── Disney-report.txt
│   │   │   └── Disney-timeline.json
│   │   ├── Parade/
│   │   └── Small World/
│   └── ...
├── Event Plan.csv
├── Final Cut Imports/
├── Logs/
└── _Batch Logs/
```

Fresh conversions now keep each project's converted media, FCPXML, reports and
timeline metadata together beneath `projects/`.

## Compatibility

- Existing root-level Version 1 and Delta 2 outputs remain readable.
- `--force` rebuilds into the new `projects/` layout.
- Event Plan generation hides the technical `projects/` container.
- Generated files beneath `Final Cut Imports/` are excluded from source discovery.

Delta 3 does not move completed conversion files. Use a fresh output folder to
test the new structure.
