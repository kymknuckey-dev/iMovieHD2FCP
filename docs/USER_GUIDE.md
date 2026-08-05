# User Guide

## Supported production workflow

1. Run `doctor`.
2. Analyse the archive when inventory is needed.
3. Convert into an empty destination.
4. Verify the completed conversion.
5. Review the text or HTML archive report.
6. Create and edit the Event-plan CSV.
7. Build safe per-project Event imports.
8. Import the numbered FCPXML files into Final Cut.

## Status meanings

- **PASS** — conversion and verification completed without reported concerns.
- **WARN** — usable output exists, but warnings or unresolved references require review.
- **FAIL** — conversion failed or output did not pass required verification.

## Logs and reports

Each product command creates a timestamped log. Conversion and verification
also create archive reports from `batch-conversion-summary.json`.

The HTML report is intended for convenient browsing. JSON and CSV remain the
authoritative machine-readable records.

## Final Cut import policy

Version 1 uses one intact XML document per original iMovie project. These files
are grouped into folders matching the intended Final Cut Event. This avoids the
internal-reference problems encountered when complete project documents were
merged into one large XML.
