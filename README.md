# iMovieHD2FCP

**A guided migration assistant for converting legacy iMovie HD projects into modern Final Cut Pro projects.**

iMovieHD2FCP analyses legacy iMovie HD archives, converts compatible media, recreates project timelines, and prepares Final Cut Pro XML files while preserving the original project organisation.

Version: **1.1 Release Candidate 1**

---

## Why iMovieHD2FCP?

Many family historians, videographers and long-time Mac users still have valuable projects created with **iMovie HD (2002–2006)**. These projects are increasingly difficult to access on modern versions of macOS.

iMovieHD2FCP provides a guided workflow to help preserve those projects by converting them into a format that can be imported into Final Cut Pro.

The application is designed to:

- Preserve original project structure
- Preserve media organisation
- Convert supported media formats
- Generate one Final Cut Pro XML per project
- Allow projects to be organised into Final Cut Events before import
- Produce clear reports and logs for every conversion

---

# Features

- Guided migration workflow
- Archive analysis
- Conversion readiness checking
- Batch conversion
- Automatic media organisation
- Editable Event Plan
- One FCPXML file per project
- Resume interrupted conversions
- Comprehensive reports and logs
- Command-line automation

---

# Workflow

The recommended workflow is:

```
Choose Archive
        ↓
Analyse Archive
        ↓
Review Analysis
        ↓
Convert Archive
        ↓
Create or Edit Event Plan
        ↓
Prepare Final Cut Project Files
        ↓
Import Project XML files into Final Cut Pro
```

---

# Output Structure

```
Output/
├── projects/
│   └── <Archive Folder>/
│       └── <Project>/
│           ├── Converted Media/
│           ├── Project.fcpxml
│           ├── Project-analysis.txt
│           ├── Project-report.txt
│           └── Project-timeline.json
│
├── Event Plan.csv
├── Final Cut Build Reports/
├── Logs/
└── _Batch Logs/
```

Each converted project remains self-contained.

---

# Installation

Clone the repository

```bash
git clone https://github.com/kymknuckey-dev/iMovieHD2FCP.git
cd iMovieHD2FCP
```

Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install

```bash
python3 -m pip install -e .
```

Optional GUI support

```bash
python3 install_gui.py
```

---

# Quick Start

Launch the application

```bash
imoviehd2fcp-app
```

or use the command line

```bash
imoviehd2fcp --help
```

---

# Documentation

- Getting Started
- User Guide
- Workflow Guide
- CLI Reference
- FAQ
- Troubleshooting
- Architecture
- Testing Guide

---

# Requirements

- macOS
- Python 3.10+
- FFmpeg
- FFprobe
- Final Cut Pro (recommended)

---

# Current Status

Version 1.1 RC1

Feature complete.

Current development is focused on:

- Bug fixes
- Compatibility
- Documentation
- Performance improvements

---

# Contributing

Bug reports, testing feedback and sample iMovie HD projects are welcome.

---

# License

(Add preferred licence here.)

---

# Acknowledgements

iMovieHD2FCP was created to help preserve legacy iMovie HD projects by providing a reliable migration path into modern Final Cut Pro workflows.

Special thanks to the community of users who continue to preserve historical video archives.