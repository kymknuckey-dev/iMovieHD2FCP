# Getting Started

Welcome to **iMovieHD2FCP**.

This guide will take you from installing the software to importing your first converted iMovie HD project into Final Cut Pro.

Most users can complete these steps in **10–15 minutes**.

---

## Contents

- [Overview](#overview)
- [System Requirements](#system-requirements)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Verify the Installation](#verify-the-installation)
- [Your First Analysis](#your-first-analysis)
- [Your First Conversion](#your-first-conversion)
- [Generate Reports](#generate-reports)
- [Plan Final Cut Pro Events](#plan-final-cut-pro-events)
- [Build Import XMLs](#build-import-xmls)
- [Import into Final Cut Pro](#import-into-final-cut-pro)
- [Recommended Workflow](#recommended-workflow)
- [Next Steps](#next-steps)

---

# Overview

iMovieHD2FCP helps preserve legacy **iMovie HD (iMovie 6)** projects by converting them into formats suitable for modern versions of **Final Cut Pro**.

The application can:

- Analyse iMovie HD archives
- Convert media into modern formats
- Preserve project structure
- Generate HTML and text reports
- Plan Final Cut Pro Events
- Create Final Cut Pro XML import files
- Verify completed conversions

No original files are modified.

---

# System Requirements

### Operating System

- macOS 13 Ventura or later
- Apple Silicon or Intel

### Software

- Python 3.11 or newer
- FFmpeg
- FFprobe
- Final Cut Pro (recommended)

---

# Prerequisites

Install Python if it is not already available.

Verify:

```bash
python3 --version
```

Example:

```text
Python 3.14.0
```

---

Install FFmpeg.

Verify:

```bash
ffmpeg -version
ffprobe -version
```

Both commands should display version information.

---

# Installation

Clone the repository.

```bash
git clone https://github.com/kymknuckey-dev/iMovieHD2FCP.git
cd iMovieHD2FCP
```

Create a virtual environment.

```bash
python3 -m venv .venv
```

Activate it.

```bash
source .venv/bin/activate
```

Install dependencies.

```bash
pip install -r requirements.txt
```

Run the installer.

```bash
python3 install_product.py
```

The installer configures the project and verifies required components.

---

# Verify the Installation

Confirm the application is installed correctly.

```bash
imoviehd2fcp doctor
```

Expected result:

```text
READY
```

You can also check the installed version.

```bash
imoviehd2fcp --version
```

Example:

```text
1.0.0
```

---

# Your First Analysis

Before converting an archive, analyse it.

Example:

```bash
imoviehd2fcp analyse "/Volumes/Archives/Europe 2005"
```

The analysis reports:

- Projects discovered
- Media statistics
- Missing files
- Timeline information
- Conversion requirements

No files are modified.

---

# Your First Conversion

Convert an archive.

Example:

```bash
imoviehd2fcp convert "/Volumes/Archives/Europe 2005"
```

During conversion the application will:

- analyse the archive
- convert compatible media
- preserve project structure
- create reports
- prepare Final Cut Pro assets

Original files remain unchanged.

---

# Generate Reports

Reports provide a permanent record of the archive.

Create reports with:

```bash
imoviehd2fcp report "/Volumes/Archives/Europe 2005"
```

Reports include:

- HTML summary
- Text summary
- Media inventory
- Conversion statistics
- Warnings
- Missing assets

These reports are useful for archival purposes.

---

# Plan Final Cut Pro Events

Many archives contain multiple projects.

Generate an editable Event plan.

```bash
imoviehd2fcp plan-events "/Volumes/Archives/Europe 2005"
```

This creates a CSV file that allows projects to be grouped into Final Cut Pro Events before XML files are generated.

---

# Build Import XMLs

Once the Event plan has been reviewed, build the Final Cut Pro XML import files.

```bash
imoviehd2fcp build-imports "/Volumes/Archives/Europe 2005"
```

The generated XML files can then be imported into Final Cut Pro.

---

# Import into Final Cut Pro

Open Final Cut Pro.

Create a Library for the migrated archive.

Choose:

```
File
    Import
        XML...
```

Select the generated XML file.

Final Cut Pro will recreate the project structure using the converted media.

---

# Recommended Workflow

The recommended migration process is:

```
Analyse Archive
        │
        ▼
Review Reports
        │
        ▼
Convert Archive
        │
        ▼
Verify Results
        │
        ▼
Plan Events
        │
        ▼
Build Import XMLs
        │
        ▼
Import into Final Cut Pro
```

Following this workflow ensures that problems are identified before import.

---

# Next Steps

Once you have completed your first migration, the following guides provide more detailed information.

| Guide | Description |
|--------|-------------|
| USER_GUIDE.md | Complete user documentation |
| CLI_REFERENCE.md | Full command reference |
| WORKFLOW.md | Recommended migration workflow |
| TROUBLESHOOTING.md | Solving common issues |
| FAQ.md | Frequently asked questions |

---

# Need Help?

If something does not work as expected:

1. Run

```bash
imoviehd2fcp doctor
```

2. Review

```
docs/TROUBLESHOOTING.md
```

3. Check the generated reports.

4. Submit an issue on GitHub, including:

- iMovieHD2FCP version
- macOS version
- Python version
- FFmpeg version
- error messages
- relevant log files

---

© 2026 iMovieHD2FCP Project