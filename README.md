# iMovieHD2FCP

> **Professional migration tools for preserving Apple iMovie HD projects in Final Cut Pro.**

iMovieHD2FCP is a comprehensive toolkit for analysing, converting and documenting legacy **iMovie HD** archives while preparing them for use in modern **Final Cut Pro**.

Rather than simply converting video files, iMovieHD2FCP provides a complete migration workflow that analyses an archive, verifies its contents, converts media, generates detailed reports, organises Final Cut Events and builds safe Final Cut Pro import files.

Version **1.0.0** is the first stable production release.

---

## Why iMovieHD2FCP?

Apple discontinued **iMovie HD** many years ago, leaving thousands of family history projects, travel documentaries and personal films locked inside an obsolete project format.

This project was created to preserve those archives for future generations by providing a reliable migration path into modern Final Cut Pro.

The guiding principles are simple:

- Preserve the original archive
- Never overwrite source media
- Produce reproducible outputs
- Generate reports for every stage
- Keep the migration process transparent and safe

---

# Features

### Archive Analysis

Analyse complete iMovie HD archives before conversion.

- Detect every project
- Inventory media
- Identify missing assets
- Summarise archive contents
- Generate detailed statistics

---

### Media Conversion

Convert legacy media into Final Cut Pro friendly formats.

- Resume-safe batch conversion
- FFmpeg-powered transcoding
- Preserves directory structure
- Safe re-run capability

---

### Verification

Automatically verify converted archives.

- Check converted outputs
- Detect missing files
- Validate conversion completeness
- Generate verification reports

---

### Archive Reports

Produce professional documentation for every archive.

- Plain text reports
- Rich HTML reports
- Archive summaries
- Conversion statistics
- Verification results

---

### Event Planning

Generate editable Event plans before import.

Features include:

- One Event per project
- Merge projects into Events
- Rename Events
- Reorganise archives before Final Cut import

---

### Final Cut Pro Import Builder

Create safe XML import packages.

- Per-project imports
- Event-based organisation
- Preserved media references
- Repeatable import workflow

---

### Environment Diagnostics

Built-in installation verification.

The Doctor command checks:

- Python installation
- Virtual environment
- FFmpeg
- FFprobe
- Required project files
- Product installation

---

# Version 1.0.0 Highlights

This first production release includes:

- Unified command-line interface
- Resume-safe batch conversion
- Archive verification
- Persistent command logs
- HTML and text reporting
- Event planning
- Final Cut Pro XML generation
- Product installer
- Environment diagnostics
- Documentation

---

# Installation

Clone the repository.

```bash
git clone https://github.com/kymknuckey-dev/iMovieHD2FCP.git
cd iMovieHD2FCP
```

Create and activate a virtual environment.

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies.

```bash
pip install -r requirements.txt
```

Install the product.

```bash
python3 install_product.py
```

Verify installation.

```bash
imoviehd2fcp doctor
```

Expected result:

```
READY
```

---

# Quick Start

## 1. Check your installation

```bash
imoviehd2fcp doctor
```

---

## 2. Analyse an archive

```bash
imoviehd2fcp analyse SOURCE OUTPUT
```

Review the generated report before converting.

---

## 3. Convert media

```bash
imoviehd2fcp convert SOURCE OUTPUT
```

The conversion is resume-safe and may be run multiple times.

---

## 4. Verify outputs

```bash
imoviehd2fcp verify SOURCE OUTPUT
```

---

## 5. Generate reports

```bash
imoviehd2fcp report OUTPUT
```

Creates both text and HTML reports.

---

## 6. Plan Final Cut Events

```bash
imoviehd2fcp plan-events OUTPUT --plan EVENT_PLAN.csv
```

Edit the CSV if required before importing.

---

## 7. Build Final Cut imports

```bash
imoviehd2fcp build-imports --plan EVENT_PLAN.csv --output FINAL_CUT_IMPORTS
```

Import the generated XML files into Final Cut Pro.

---

# Typical Workflow

```
iMovie HD Archive

        │

        ▼
Analyse Archive

        │

        ▼
Convert Media

        │

        ▼
Verify Conversion

        │

        ▼
Generate Reports

        │

        ▼
Plan Events

        │

        ▼
Build XML Imports

        │

        ▼
Import into Final Cut Pro
```

---

# Command Summary

| Command | Description |
|----------|-------------|
| `doctor` | Verify installation and environment |
| `analyse` | Analyse an archive without conversion |
| `convert` | Convert media and projects |
| `verify` | Verify conversion outputs |
| `report` | Generate archive reports |
| `plan-events` | Create an editable Event Plan CSV |
| `build-imports` | Generate Final Cut Pro XML imports |

---

# Output Structure

A successful conversion produces a structure similar to:

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

---

# Safety

**The original iMovie HD archive is never modified.**

All converted media, reports and Final Cut Pro imports are written to a separate destination folder.

This allows conversions to be repeated without risk to the original archive.

---

# Documentation

Additional documentation is available in the **docs** folder.

- Getting Started
- User Guide
- CLI Reference
- Installation Guide
- FAQ
- Troubleshooting
- Release Notes

---

# Current Limitations

iMovieHD2FCP focuses on preserving media and project organisation.

Some original iMovie HD editing features cannot currently be recreated exactly inside Final Cut Pro, including:

- Native iMovie HD titles
- Certain transitions
- Some timeline effects

These remain areas of ongoing research.

---

# Roadmap

## Version 1.0

- Stable command-line interface
- Archive analysis
- Media conversion
- Verification
- Reports
- Event planning
- Final Cut Pro XML generation

### Planned

- Improved title recreation
- Enhanced transition support
- Automatic Final Cut Library creation
- Metadata enhancements
- Native macOS graphical application

---

# Contributing

Bug reports, archive samples and feature suggestions are welcome.

If you encounter an archive that behaves unexpectedly, please open an Issue with as much detail as possible.

---

# Licence

This project is released under the MIT License.

See the LICENSE file for details.

---

# Acknowledgements

This project builds upon the work of:

- Apple iMovie HD
- Apple Final Cut Pro
- FFmpeg
- The Python open-source community

---

# Author

**Kym Knuckey**

Created to preserve decades of personal, family and historical iMovie HD archives and provide a safe migration path into modern Final Cut Pro.

If this project helps preserve even one family's memories, then it has achieved its purpose.
