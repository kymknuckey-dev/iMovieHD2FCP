# iMovieHD2FCP

> **Migrate legacy iMovie HD projects into Final Cut Pro while preserving project structure, media, and edit decisions.**

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.9+-green)
![Platform](https://img.shields.io/badge/macOS-supported-lightgrey)
![Status](https://img.shields.io/badge/status-stable-brightgreen)

---

## Overview

**iMovieHD2FCP** is a migration toolkit designed to help preserve and modernise legacy **iMovie HD (2002–2006)** projects by converting them into a format that can be imported into modern versions of **Final Cut Pro**.

Many family historians, video enthusiasts, schools and organisations still possess valuable archives created with iMovie HD. Unfortunately these projects are no longer supported by current Apple software.

Rather than simply copying media files, iMovieHD2FCP analyses each archive, reconstructs project information where possible and generates Final Cut Pro import packages that preserve the original project organisation.

The goal is simple:

> **Keep your archive alive without losing years of editing work.**

---

# Features

Version 1.0 includes:

- Analyse complete iMovie HD archives
- Convert legacy media into Final Cut Pro compatible formats
- Verify completed conversions
- Produce detailed HTML and text reports
- Generate editable Final Cut Event plans
- Build Final Cut Pro XML import packages
- Preserve original media (read-only)
- Batch process multiple projects
- Comprehensive installation diagnostics (`doctor`)
- Command-line interface suitable for large archives

---

# What Version 1.0 Preserves

Where possible the conversion process preserves:

- Project organisation
- Clip timing
- Clip ordering
- Trim points
- Rendered transitions
- Rendered titles
- Audio synchronisation
- Original media references
- Project metadata

The software is designed to produce an import that closely matches the visual appearance of the original iMovie HD project while remaining compatible with current Final Cut Pro workflows.

---

# Current Limitations

Version 1.0 does **not** recreate every iMovie HD editing feature as native Final Cut Pro objects.

Some items are intentionally preserved using rendered media rather than editable timeline elements.

Examples include:

- Native title reconstruction
- Native transition recreation
- Motion effects
- Legacy iMovie themes
- Ken Burns editing controls
- Live effect parameters

These remain candidates for future development.

---

# Installation

Clone the repository:

```bash
git clone https://github.com/kymknuckey-dev/iMovieHD2FCP.git
cd iMovieHD2FCP
```

Create a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the product:

```bash
python3 install_product.py
```

Confirm the installation:

```bash
imoviehd2fcp doctor
```

You should see:

```
READY
```

---

# Quick Start

Analyse an archive:

```bash
imoviehd2fcp analyse "/Volumes/Archive" "/Volumes/Archive Output"
```

Convert the archive:

```bash
imoviehd2fcp convert "/Volumes/Archive" "/Volumes/Archive Output"
```

Verify the conversion:

```bash
imoviehd2fcp verify "/Volumes/Archive" "/Volumes/Archive Output"
```

Generate an Event Plan:

```bash
imoviehd2fcp plan-events \
"/Volumes/Archive Output" \
--plan "/Volumes/Event Plan.csv"
```

Generate Final Cut Pro import packages:

```bash
imoviehd2fcp build-imports \
--plan "/Volumes/Event Plan.csv" \
--output "/Volumes/FCP Imports"
```

Import the generated XML files into Final Cut Pro.

---

# Typical Workflow

```
Analyse Archive
        │
        ▼
Review Reports
        │
        ▼
Convert Media
        │
        ▼
Verify Results
        │
        ▼
Create Event Plan
        │
        ▼
Generate XML Imports
        │
        ▼
Import into Final Cut Pro
        │
        ▼
Review Projects
```

---

# Documentation

Complete documentation is available in the **docs** folder.

| Document | Description |
|-----------|-------------|
| GETTING_STARTED.md | Installation and first conversion |
| USER_GUIDE.md | Complete operating guide |
| CLI_REFERENCE.md | Command reference |
| WORKFLOW.md | Recommended migration workflow |
| FAQ.md | Frequently asked questions |
| TROUBLESHOOTING.md | Common problems and solutions |
| TESTING.md | Testing procedures |
| RELEASE_CHECKLIST.md | Release process |
| RELEASE_NOTES_1.0.0.md | Version history |

---

# Project Structure

```
iMovieHD2FCP/

docs/
legacy/
src/
tests/

install_product.py
pyproject.toml
README.md
```

---

# Designed For

This project is particularly useful for:

- Family historians
- Genealogists
- Historical societies
- Schools
- Community organisations
- Video preservation projects
- Long-term digital archives

---

# Roadmap

Planned future improvements include:

- Native Final Cut titles
- Native Final Cut transitions
- Motion template support
- Improved timeline reconstruction
- Enhanced metadata preservation
- GUI front-end
- Batch scheduling
- Additional report formats

---

# Contributing

Contributions, bug reports and feature suggestions are welcome.

Please include:

- macOS version
- Python version
- Final Cut Pro version
- Sample project (if possible)
- Complete console output

---

# Licence

This project is released under the MIT Licence.

See the LICENSE file for details.

---

# Acknowledgements

This project exists because thousands of legacy iMovie HD projects still contain irreplaceable family history.

The goal is to ensure those memories remain accessible for future generations.

---

**Version:** 1.0.0

**Status:** Stable