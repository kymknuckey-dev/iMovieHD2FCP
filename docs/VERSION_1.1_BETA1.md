# Version 1.1 Beta 1

Beta 1 begins final release testing of the guided Migration Assistant.

## Changes from Delta 4

- New project XML files use the clean project name:
  - `Small World.fcpxml`
  - `Disney.fcpxml`
  - `Parade.fcpxml`
- The internal `-v1` filename suffix has been removed.
- Existing older outputs containing `-v1.fcpxml` remain usable.
- The completion page now says **Your projects are ready for Final Cut Pro**.
- User-facing wording has been simplified:
  - **Prepare Final Cut Project Files**
  - **Final Cut project files**
- Preview Conversion remains removed from the guided interface.
- CLI dry-run support remains available for advanced use.

## Final project layout

```text
Output/
└── projects/
    └── <archive folder>/
        └── <project>/
            ├── Converted Media/
            ├── <project>.fcpxml
            ├── <project>-analysis.txt
            ├── <project>-report.txt
            └── <project>-timeline.json
```

Beta 1 should be tested with a fresh output folder so the new clean FCPXML
filenames are generated.
