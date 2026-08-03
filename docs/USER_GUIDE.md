# User Guide

**Version 1.0.0**

---

# Introduction

Welcome to the **iMovieHD2FCP User Guide**.

This guide provides a comprehensive overview of the complete migration process from **iMovie HD** to **Final Cut Pro**.

Unlike the *Getting Started Guide*, which walks through a single conversion, this guide explains:

- how the software works
- what each processing stage produces
- how to organise large archives
- recommended workflows
- best practices
- current limitations

The goal of iMovieHD2FCP is to preserve valuable video archives while making them accessible in modern versions of Final Cut Pro.

---

# Understanding the Conversion Process

iMovieHD2FCP is designed around a staged workflow.

Each stage performs a single task and produces information for the next stage.

```
Doctor
    │
    ▼
Analyse
    │
    ▼
Convert
    │
    ▼
Verify
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

Keeping these stages separate makes it easier to:

- inspect results
- detect problems early
- rerun individual stages
- work with large archives

---

# Project Philosophy

The software follows several important design principles.

## Original media is never modified

Your iMovie HD archive is treated as read-only.

All converted files are written to a separate output location.

This allows:

- repeatable conversions
- safe experimentation
- long-term archive preservation

---

## Every stage is repeatable

You can rerun:

- analysis
- conversion
- verification
- Event planning
- XML generation

without affecting the original archive.

---

## Reports are first-class outputs

Every stage produces information intended for review.

Rather than treating reporting as an afterthought, iMovieHD2FCP considers reports an essential part of archive preservation.

---

# Stage 1 — Doctor

The Doctor command checks the installation.

Run:

```bash
imoviehd2fcp doctor
```

Doctor verifies:

- Python environment
- FFmpeg
- FFprobe
- product modules
- legacy conversion modules

Always run Doctor after:

- installing
- upgrading
- moving the project
- changing Python versions

---

# Stage 2 — Analyse

Analysis reads the archive without changing it.

Typical command:

```bash
imoviehd2fcp analyse \
"/Volumes/Archives/Europe 2005" \
"/Volumes/Archives/Europe 2005 Output"
```

Analysis identifies:

- projects
- clips
- media
- transitions
- titles
- timelines
- missing files
- archive statistics

No media conversion occurs during this stage.

---

# Reviewing Analysis Reports

Before converting, review the generated reports.

Pay particular attention to:

- missing media
- unexpected project counts
- duplicate clips
- unsupported media
- timeline warnings

Resolving issues now usually produces better Final Cut Pro imports later.

---

# Stage 3 — Convert

Conversion creates Final Cut Pro compatible media.

Example:

```bash
imoviehd2fcp convert \
"/Volumes/Archives/Europe 2005" \
"/Volumes/Archives/Europe 2005 Output"
```

During conversion the software:

- processes source media
- creates compatible output media
- preserves project relationships
- generates metadata
- prepares verification data

The original archive remains unchanged.

---

# Stage 4 — Verify

Verification checks that conversion completed successfully.

Run:

```bash
imoviehd2fcp verify \
"/Volumes/Archives/Europe 2005" \
"/Volumes/Archives/Europe 2005 Output"
```

Verification confirms:

- expected files exist
- converted media is available
- metadata is complete
- reports are consistent

Verification should always be completed before importing into Final Cut Pro.

---

# Stage 5 — Event Planning

Final Cut Pro organises Projects inside Events.

Rather than making assumptions, iMovieHD2FCP allows you to define this organisation using an editable CSV.

Generate a plan:

```bash
imoviehd2fcp plan-events \
"/Volumes/Archives/Europe 2005 Output" \
--plan "/Volumes/Event Plan.csv"
```

The CSV can be edited using:

- Apple Numbers
- Microsoft Excel
- LibreOffice
- Google Sheets

You may:

- rename Events
- regroup Projects
- split large collections
- organise by year
- organise by trip
- organise by family member

---

# Stage 6 — Build Import Packages

Once the Event Plan has been reviewed, generate Final Cut Pro XML imports.

```bash
imoviehd2fcp build-imports \
--plan "/Volumes/Event Plan.csv" \
--output "/Volumes/FCP Imports"
```

The output folder contains XML files ready for Final Cut Pro import.

---

# Importing into Final Cut Pro

Create or open a Library.

Choose:

```
File
    Import
        XML…
```

Import one XML package at a time.

Final Cut Pro creates:

- Events
- Projects
- media references

according to the generated import package.

---

# Understanding the Output Folder

A converted archive typically contains:

```
Archive Output/

Converted Media/

Reports/

Metadata/

Verification/

Imports/
```

These folders should be retained together.

Deleting metadata or reports may make future verification more difficult.

---

# Best Practices

## Keep the original archive

Never overwrite or modify the original iMovie HD archive.

Store it separately from converted media.

---

## Convert to a new location

Always choose a dedicated output folder.

For example:

```
Europe 2005/
Europe 2005 Output/
```

This keeps original and converted files clearly separated.

---

## Review reports before importing

Importing without reviewing reports may result in unexpected missing media or incomplete projects.

---

## Back up converted archives

The converted archive represents significant processing work.

Include it in your normal backup strategy.

---

# Current Limitations

Version 1.0 focuses on preserving project appearance and structure.

The following are not currently recreated as native Final Cut Pro objects:

- editable titles
- editable transitions
- Motion templates
- Ken Burns editing controls
- legacy themes
- effect parameters

Where possible these elements are preserved visually using rendered media.

---

# Working with Large Archives

For large collections:

- analyse first
- review reports
- convert in stages if required
- verify regularly
- organise Event Plans carefully

Large archives often benefit from grouping by:

- year
- holiday
- event
- client
- family branch

rather than importing everything into a single Event.

---

# Troubleshooting

If problems occur:

1. Run Doctor.
2. Review Verification.
3. Read:

```
docs/TROUBLESHOOTING.md
```

Most issues can be resolved before XML import.

---

# Related Documentation

| Document | Purpose |
|----------|---------|
| GETTING_STARTED.md | First conversion |
| CLI_REFERENCE.md | Complete command reference |
| WORKFLOW.md | Recommended archive workflow |
| FAQ.md | Frequently asked questions |
| TROUBLESHOOTING.md | Problem solving |
| TESTING.md | Testing procedures |

---

# Summary

iMovieHD2FCP is designed to preserve valuable iMovie HD projects while making them usable inside modern Final Cut Pro.

Following the recommended workflow—

1. Doctor
2. Analyse
3. Convert
4. Verify
5. Plan Events
6. Build XML Imports
7. Import into Final Cut Pro

—provides the highest likelihood of a successful migration while keeping your original archive completely intact.