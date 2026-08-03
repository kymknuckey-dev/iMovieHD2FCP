# CLI Reference

**iMovieHD2FCP Version 1.0.0**

---

# Introduction

The iMovieHD2FCP Command Line Interface (CLI) provides access to every feature of the application.

The general syntax is:

```bash
imoviehd2fcp COMMAND [OPTIONS]
```

Display general help at any time with:

```bash
imoviehd2fcp --help
```

Display help for an individual command:

```bash
imoviehd2fcp COMMAND --help
```

---

# Global Options

## Show Help

```bash
imoviehd2fcp --help
```

Displays the complete list of available commands.

---

## Show Version

```bash
imoviehd2fcp --version
```

Example:

```text
1.0.0
```

---

# Available Commands

Version 1.0 provides the following commands:

| Command | Purpose |
|----------|---------|
| doctor | Verify installation and dependencies |
| analyse | Scan an archive without converting media |
| convert | Convert an archive |
| verify | Verify conversion output |
| report | Generate archive reports |
| plan-events | Create an editable Event Plan |
| build-imports | Generate Final Cut Pro XML packages |

---

# doctor

Checks that the installation is complete and ready to use.

## Syntax

```bash
imoviehd2fcp doctor
```

## Example

```bash
imoviehd2fcp doctor
```

Typical output:

```text
Python environment
FFmpeg
FFprobe
Product components

READY
```

Run this command:

- after installation
- after upgrading
- after changing Python versions
- before reporting issues

---

# analyse

Scans an iMovie HD archive without converting media.

## Syntax

```bash
imoviehd2fcp analyse <archive> <output>
```

## Parameters

| Parameter | Description |
|------------|-------------|
| archive | Source iMovie HD archive |
| output | Output directory |

## Example

```bash
imoviehd2fcp analyse \
"/Volumes/Europe 2005" \
"/Volumes/Europe 2005 Output"
```

Produces:

- archive analysis
- media inventory
- project statistics
- HTML reports
- text reports

No media is modified.

---

# convert

Converts an archive into Final Cut Pro compatible media.

## Syntax

```bash
imoviehd2fcp convert <archive> <output>
```

## Parameters

| Parameter | Description |
|------------|-------------|
| archive | Source archive |
| output | Destination folder |

## Example

```bash
imoviehd2fcp convert \
"/Volumes/Europe 2005" \
"/Volumes/Europe 2005 Output"
```

Creates:

- converted media
- metadata
- verification information
- reports

Original media is never modified.

---

# verify

Checks a completed conversion.

## Syntax

```bash
imoviehd2fcp verify <archive> <output>
```

## Example

```bash
imoviehd2fcp verify \
"/Volumes/Europe 2005" \
"/Volumes/Europe 2005 Output"
```

Verification checks:

- converted media
- metadata
- reports
- expected output files

---

# report

Generates archive reports.

## Syntax

```bash
imoviehd2fcp report <archive> <output>
```

## Example

```bash
imoviehd2fcp report \
"/Volumes/Europe 2005" \
"/Volumes/Europe 2005 Output"
```

Produces readable:

- HTML reports
- text reports
- archive summaries

Useful for documenting large collections.

---

# plan-events

Creates an editable CSV describing how projects should be organised into Final Cut Pro Events.

## Syntax

```bash
imoviehd2fcp plan-events <output> --plan <csv-file>
```

## Parameters

| Parameter | Description |
|------------|-------------|
| output | Converted archive |
| --plan | CSV file to create |

## Example

```bash
imoviehd2fcp plan-events \
"/Volumes/Europe 2005 Output" \
--plan "/Volumes/Event Plan.csv"
```

The generated CSV can be edited in:

- Numbers
- Excel
- LibreOffice
- Google Sheets

---

# build-imports

Builds Final Cut Pro XML import packages using an Event Plan.

## Syntax

```bash
imoviehd2fcp build-imports \
--plan <csv-file> \
--output <folder>
```

## Parameters

| Parameter | Description |
|------------|-------------|
| --plan | Event Plan CSV |
| --output | XML destination |

## Example

```bash
imoviehd2fcp build-imports \
--plan "/Volumes/Event Plan.csv" \
--output "/Volumes/FCP Imports"
```

Produces one or more Final Cut Pro XML files ready for import.

---

# Typical Workflow

The recommended sequence is:

```text
doctor

↓

analyse

↓

convert

↓

verify

↓

plan-events

↓

build-imports

↓

Import XML into Final Cut Pro
```

---

# Getting Help

Display help for any command.

Example:

```bash
imoviehd2fcp analyse --help
```

Example:

```bash
imoviehd2fcp build-imports --help
```

Every command supports:

```bash
-h
```

or

```bash
--help
```

---

# Exit Status

A successful command returns:

```text
0
```

A failed command returns a non-zero exit status.

This allows iMovieHD2FCP to be incorporated into shell scripts and automated workflows.

---

# Examples

## Analyse an archive

```bash
imoviehd2fcp analyse \
"/Volumes/Holidays 2004" \
"/Volumes/Holidays Output"
```

---

## Convert

```bash
imoviehd2fcp convert \
"/Volumes/Holidays 2004" \
"/Volumes/Holidays Output"
```

---

## Verify

```bash
imoviehd2fcp verify \
"/Volumes/Holidays 2004" \
"/Volumes/Holidays Output"
```

---

## Create an Event Plan

```bash
imoviehd2fcp plan-events \
"/Volumes/Holidays Output" \
--plan "/Volumes/Event Plan.csv"
```

---

## Build XML Imports

```bash
imoviehd2fcp build-imports \
--plan "/Volumes/Event Plan.csv" \
--output "/Volumes/FCP Imports"
```

---

# Related Documentation

| Document | Purpose |
|----------|---------|
| README.md | Project overview |
| GETTING_STARTED.md | First conversion |
| USER_GUIDE.md | Complete operating guide |
| WORKFLOW.md | Recommended workflow |
| FAQ.md | Frequently asked questions |
| TROUBLESHOOTING.md | Problem solving |

---

## Version History

This reference applies to:

**iMovieHD2FCP Version 1.0.0**