# Command Line Reference

## Introduction

iMovieHD2FCP includes a comprehensive command-line interface (CLI) for automation, scripting and batch processing.

Most users should use the graphical application.

The CLI provides direct access to the same conversion engine used by the GUI.

---

# Display Help

```bash
imoviehd2fcp --help
```

Displays all available commands and options.

---

# Display Version

```bash
imoviehd2fcp --version
```

Example

```text
1.1.0rc1
```

---

# System Check

```bash
imoviehd2fcp doctor
```

Checks that the required software is installed.

The Doctor command verifies:

- Python environment
- FFmpeg
- FFprobe
- Required Python packages
- Application installation

Run this command before reporting problems.

---

# Analyse Archive

```bash
imoviehd2fcp analyse <archive> \
    --output <output-folder>
```

Example

```bash
imoviehd2fcp analyse \
    "/Volumes/Media/My Archive" \
    --output "/Volumes/Media/Converted"
```

Purpose

- Analyse every iMovie HD project
- Generate Archive Summary
- Produce analysis reports

No media is converted.

---

# Convert Archive

```bash
imoviehd2fcp convert <archive> \
    --output <output-folder>
```

Example

```bash
imoviehd2fcp convert \
    "/Volumes/Media/My Archive" \
    --output "/Volumes/Media/Converted"
```

Purpose

Converts all supported projects into Final Cut Pro compatible project folders.

---

## Dry Run

For advanced users.

```bash
imoviehd2fcp convert \
    <archive> \
    --output <folder> \
    --dry-run
```

The dry run performs conversion validation without writing converted media.

The graphical application does not expose this option because the **Analyse Archive** step already performs the recommended validation workflow.

---

# Create Event Plan

```bash
imoviehd2fcp plan-events \
    <converted-folder> \
    --plan "Event Plan.csv"
```

Purpose

Creates an editable Event Plan.

---

## Event Organisation

Choose how Events should be created.

### Parent folders

```bash
--event-mode parent
```

Projects are grouped using their parent folder.

---

### Top-level folders

```bash
--event-mode top
```

Projects are grouped using the top archive folder.

---

### Event depth

```bash
--event-level 1
```

Controls folder depth when determining Event names.

---

# Prepare Final Cut Project Files

```bash
imoviehd2fcp build-imports \
    --plan "Event Plan.csv" \
    --output "Final Cut Build Reports"
```

Purpose

Reads the Event Plan and updates each project's existing FCPXML file.

No duplicate XML files are created.

Reports are written to the specified output folder.

---

# Resume Existing Conversion

Running Convert again automatically detects completed work.

Example

```bash
imoviehd2fcp convert \
    <archive> \
    --output <folder>
```

Existing converted projects are reused where possible.

---

# Force Rebuild

```bash
imoviehd2fcp convert \
    <archive> \
    --output <folder> \
    --force
```

Rebuilds converted outputs even if they already exist.

---

# Typical Workflow

```bash
# Analyse

imoviehd2fcp analyse ...

# Convert

imoviehd2fcp convert ...

# Create Event Plan

imoviehd2fcp plan-events ...

# Edit Event Plan.csv

# Prepare Project Files

imoviehd2fcp build-imports ...
```

---

# Exit Codes

| Code | Meaning |
|------:|---------|
| 0 | Success |
| 1 | General error |
| 2 | Invalid command or arguments |
| 3 | Missing dependency |
| 4 | Invalid project or archive |

---

# Tips

- Analyse before converting.
- Use a fresh output folder.
- Keep the Event Plan under version control if multiple people are editing it.
- Use `--dry-run` only for advanced validation or scripting.
- Import each project's `.fcpxml` file into Final Cut Pro after preparing project files.

---

# Related Documentation

- GETTING_STARTED.md
- USER_GUIDE.md
- WORKFLOW.md
- FAQ.md
- TROUBLESHOOTING.md