# iMovieHD2FCP 1.1.0 Alpha 3

`iMovieHD2FCP` migrates legacy iMovie HD projects into modern Final Cut Pro.

Version 1.0.0 is the first stable release and includes:

- unified command-line interface;
- resume-safe batch conversion;
- post-conversion verification;
- persistent command logs;
- text and HTML archive reports;
- Event planning;
- safe intact per-project Final Cut imports;
- installer and environment diagnostics;
- product documentation and tests.

## Install or upgrade

Merge the RC3 files into the existing project folder, then run:

```bash
cd ~/Development/iMovieHD2FCP
source .venv/bin/activate
python3 install_product.py
imoviehd2fcp doctor
```

## Main commands

```bash
imoviehd2fcp doctor
imoviehd2fcp analyse SOURCE OUTPUT
imoviehd2fcp convert SOURCE OUTPUT
imoviehd2fcp verify SOURCE OUTPUT
imoviehd2fcp report OUTPUT
imoviehd2fcp plan-events OUTPUT --plan EVENT_PLAN.csv
imoviehd2fcp build-imports --plan EVENT_PLAN.csv --output FINAL_CUT_IMPORTS
```

## Generated output

A successful conversion now includes:

```text
Conversion Destination/
├── batch-conversion-state.json
├── batch-conversion-summary.json
├── batch-conversion-summary.csv
├── batch-conversion-report.txt
├── Logs/
└── Reports/
    ├── Archive Verification Report.txt
    └── Archive Verification Report.html
```

See `docs/GETTING_STARTED.md` and `docs/USER_GUIDE.md`.


## Release notes

See `docs/RELEASE_NOTES_1.0.0.md`.


## Graphical application (Version 1.1 Alpha 2)

Install the optional GUI:

```bash
source .venv/bin/activate
python3 install_gui.py
```

Launch it with:

```bash
imoviehd2fcp-app
```

The graphical application calls the same proven conversion engine as the CLI.
See `docs/VERSION_1.1_ALPHA1.md`.


### Alpha 2 interface polish

Alpha 2 adds toolbar actions, status cards, colour-coded logs, improved dialogs, remembered window state and Finder drag-and-drop. See `docs/VERSION_1.1_ALPHA2.md`.


## Alpha 3 Workflow Assistant

Alpha 3 guides users from archive selection through Final Cut import generation. See `docs/VERSION_1.1_ALPHA3.md`.


## Version 1.1 Delta 2

Delta 2 adds the Event Planning Assistant, contextual analysis results, archive-summary selection and the Migration Complete experience. See `docs/VERSION_1.1_DELTA2.md`.


## Version 1.1 Delta 3

Delta 3 writes fresh conversions beneath `projects/`, keeping each project's media, reports, metadata and FCPXML together. See `docs/VERSION_1.1_DELTA3.md`.


## Version 1.1 Delta 4

Delta 4 keeps one final FCPXML per project beside its converted media, removes duplicate import XML copies, and removes Preview Conversion from the guided GUI. See `docs/VERSION_1.1_DELTA4.md`.


## Version 1.1 Beta 1

Beta 1 removes the `-v1` suffix from new project FCPXML filenames and polishes the final user-facing workflow. See `docs/VERSION_1.1_BETA1.md`.
