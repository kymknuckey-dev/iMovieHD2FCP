# CLI Reference

**Version 1.0.0**

---

# Contents

- Introduction
- General Syntax
- Global Options
- Commands
  - doctor
  - analyse
  - convert
  - verify
  - report
  - plan-events
  - build-imports
- Typical Workflows
- Exit Codes
- Examples

---

# Introduction

This document describes every command supported by **iMovieHD2FCP**.

Unlike the *Getting Started Guide*, which explains the migration process, this document is intended as a command reference for day-to-day use.

---

# General Syntax

Every command follows the same structure.

```bash
imoviehd2fcp [global options] command [command options]
```

Examples:

```bash
imoviehd2fcp doctor
```

```bash
imoviehd2fcp analyse "/Volumes/Archives/Europe 2005"
```

```bash
imoviehd2fcp convert "/Volumes/Archives/Europe 2005"
```

---

# Global Options

Display help.

```bash
imoviehd2fcp --help
```

Display version.

```bash
imoviehd2fcp --version
```

Example output

```
1.0.0
```

---

# doctor

## Purpose

Checks the installation and reports whether the application is ready to use.

---

## Syntax

```bash
imoviehd2fcp doctor
```

---

## Checks Performed

The Doctor command verifies:

- Product installation
- Python environment
- FFmpeg
- FFprobe
- Core application modules
- Legacy conversion modules

---

## Successful Output

```
READY
```

---

## Typical Uses

Run after:

- installation
- upgrading Python
- updating FFmpeg
- moving the application
- restoring from backup

---

# analyse

## Purpose

Scans an archive without modifying it.

---

## Syntax

```bash
imoviehd2fcp analyse <archive>
```

Example

```bash
imoviehd2fcp analyse "/Volumes/Archives/Europe 2005"
```

---

## Reports

Analysis includes:

- Projects
- Media
- Missing assets
- Statistics
- Conversion requirements

No files are changed.

---

# convert

## Purpose

Converts an archive into Final Cut Pro compatible media.

---

## Syntax

```bash
imoviehd2fcp convert <archive>
```

Example

```bash
imoviehd2fcp convert "/Volumes/Archives/Europe 2005"
```

---

## Conversion Process

The converter:

1. Analyses the archive
2. Converts media
3. Preserves folder structure
4. Generates reports
5. Creates Final Cut Pro assets

Original media is never modified.

---

# verify

## Purpose

Checks the results of a completed conversion.

---

## Syntax

```bash
imoviehd2fcp verify <archive>
```

---

## Verification

Checks include:

- Converted media
- Missing files
- Reports
- XML files
- Folder structure

Verification should always be run before importing into Final Cut Pro.

---

# report

## Purpose

Creates documentation describing the archive.

---

## Syntax

```bash
imoviehd2fcp report <archive>
```

---

## Output

Reports include:

- HTML summary
- Text summary
- Media inventory
- Statistics
- Warnings

Reports are intended to be kept with the archive.

---

# plan-events

## Purpose

Creates an editable Event Plan for Final Cut Pro.

---

## Syntax

```bash
imoviehd2fcp plan-events <archive>
```

---

## Output

Produces a CSV file containing:

- Project names
- Suggested Event names
- Groupings

Edit the CSV before generating import XML.

---

# build-imports

## Purpose

Creates Final Cut Pro XML import files.

---

## Syntax

```bash
imoviehd2fcp build-imports <archive>
```

---

## Output

Creates XML files suitable for:

```
File

    Import

        XML...
```

inside Final Cut Pro.

---

# Typical Workflow

A complete migration usually consists of:

```bash
imoviehd2fcp doctor
```

↓

```bash
imoviehd2fcp analyse "/Volumes/Archives/Europe 2005"
```

↓

```bash
imoviehd2fcp convert "/Volumes/Archives/Europe 2005"
```

↓

```bash
imoviehd2fcp verify "/Volumes/Archives/Europe 2005"
```

↓

```bash
imoviehd2fcp report "/Volumes/Archives/Europe 2005"
```

↓

```bash
imoviehd2fcp plan-events "/Volumes/Archives/Europe 2005"
```

↓

```bash
imoviehd2fcp build-imports "/Volumes/Archives/Europe 2005"
```

↓

Import into Final Cut Pro.

---

# Exit Codes

| Code | Meaning |
|-------|---------|
| 0 | Command completed successfully |
| 1 | General error |
| 2 | Invalid command line arguments |
| 3 | Missing dependency |
| 4 | Archive could not be analysed |
| 5 | Conversion failed |
| 6 | Verification failed |

> **Note:** Some exit codes may be expanded in future releases as additional diagnostics are added.

---

# Examples

Display the installed version.

```bash
imoviehd2fcp --version
```

Check installation.

```bash
imoviehd2fcp doctor
```

Analyse an archive.

```bash
imoviehd2fcp analyse "/Volumes/Archives/Family Videos"
```

Convert an archive.

```bash
imoviehd2fcp convert "/Volumes/Archives/Family Videos"
```

Verify the results.

```bash
imoviehd2fcp verify "/Volumes/Archives/Family Videos"
```

Generate reports.

```bash
imoviehd2fcp report "/Volumes/Archives/Family Videos"
```

Plan Final Cut Pro Events.

```bash
imoviehd2fcp plan-events "/Volumes/Archives/Family Videos"
```

Create Final Cut Pro XML imports.

```bash
imoviehd2fcp build-imports "/Volumes/Archives/Family Videos"
```

---

# Related Documentation

| Document | Description |
|----------|-------------|
| GETTING_STARTED.md | First installation and migration |
| USER_GUIDE.md | Complete user manual |
| WORKFLOW.md | Recommended migration process |
| TROUBLESHOOTING.md | Solving common issues |
| FAQ.md | Frequently asked questions |

---

© 2026 iMovieHD2FCP Project