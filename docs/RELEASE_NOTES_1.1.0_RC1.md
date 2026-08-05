# iMovieHD2FCP 1.1.0 Release Candidate 1

Release Candidate 1 is the first feature-frozen build of Version 1.1.

## What is included

- Guided macOS migration workflow
- Archive analysis and archive health summary
- Media conversion using the proven Version 1 engine
- Project outputs stored beneath `projects/`
- One cleanly named FCPXML file per project
- Editable Event Plan
- Event names applied to each project's existing FCPXML
- No duplicate Final Cut XML output tree
- Resume detection from existing outputs
- Completion screen with direct access to converted projects
- CLI retained for advanced and scripted use

## Final output structure

```text
Output/
├── projects/
│   └── <archive folder>/
│       └── <project>/
│           ├── Converted Media/
│           ├── <project>.fcpxml
│           ├── <project>-analysis.txt
│           ├── <project>-report.txt
│           └── <project>-timeline.json
├── Event Plan.csv
├── Final Cut Build Reports/
├── Logs/
└── _Batch Logs/
```

## Release-candidate policy

No new features are planned between RC1 and Version 1.1 final.

Changes after RC1 should be limited to:

- bug fixes
- compatibility fixes
- documentation corrections
- small accessibility and presentation improvements

## Recommended RC1 test

Use a fresh output folder and complete the full workflow:

1. Analyse Archive
2. Review Analysis Results
3. Convert Archive
4. Create or edit the Event Plan
5. Prepare Final Cut Project Files
6. Import each project FCPXML into Final Cut Pro
7. Confirm that projects appear in the intended Events
