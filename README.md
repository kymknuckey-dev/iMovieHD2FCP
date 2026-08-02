# iMovieHD2FCP v1.0.0 Release Candidate 3

`iMovieHD2FCP` migrates legacy iMovie HD projects into modern Final Cut Pro.

RC3 keeps the proven RC2 conversion engine frozen and completes the operational
product layer:

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

## RC3 output additions

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
