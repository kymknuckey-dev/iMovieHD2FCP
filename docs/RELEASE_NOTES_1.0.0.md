# iMovieHD2FCP 1.0.0

The first stable release of the iMovie HD to Final Cut Pro migration tool.

## Included

- Archive analysis and inventory
- Resumable batch conversion
- Modern QuickTime media output
- FCPXML timeline reconstruction
- Music, still images, rendered titles and transitions
- Timestamp preservation with recorded provenance
- Clean project-qualified Browser names
- Verification and PASS/WARN/FAIL reports
- Text and HTML archive reports
- Event-plan CSV generation
- Safe intact per-project Final Cut imports
- Persistent command logs

## Supported workflow

```bash
imoviehd2fcp doctor
imoviehd2fcp analyse SOURCE OUTPUT
imoviehd2fcp convert SOURCE OUTPUT
imoviehd2fcp verify SOURCE OUTPUT
imoviehd2fcp report OUTPUT
imoviehd2fcp plan-events OUTPUT --plan EVENT_PLAN.csv
imoviehd2fcp build-imports --plan EVENT_PLAN.csv --output FINAL_CUT_IMPORTS
```

## Known limitations

- Titles and transitions are rendered media rather than native editable Final Cut effects.
- Final Cut Libraries are not written directly.
- Some original projects contain inconsistent source metadata; selection decisions are recorded in the manifest.
