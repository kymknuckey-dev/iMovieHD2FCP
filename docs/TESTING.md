# Testing Guide

## Introduction

This document describes the recommended testing process for iMovieHD2FCP.

The objective is to verify that every release correctly analyses, converts and prepares iMovie HD projects for import into Final Cut Pro while preserving project organisation.

Testing should be performed before every Release Candidate and public release.

---

# Test Environment

Record the environment before testing.

| Item | Value |
|------|-------|
| Application Version | |
| macOS Version | |
| Python Version | |
| FFmpeg Version | |
| Final Cut Pro Version | |
| Test Date | |
| Tester | |

---

# Test Data

The following archives should be maintained for regression testing.

| Archive | Purpose |
|----------|---------|
| Small Archive | Basic functionality |
| Medium Archive | Multiple projects |
| Large Archive | Performance |
| Missing Media | Error handling |
| Shared Media | Media linking |
| Audio Heavy | Audio validation |
| Titles | Title recreation |
| Mixed Codecs | Media conversion |
| Unicode Names | Filename compatibility |

Every release should be tested using at least one small, one medium and one large archive.

---

# Test 1 – Installation

## Objective

Verify that the application installs correctly.

### Procedure

1. Create a new virtual environment.
2. Install the package.
3. Launch the application.

### Expected Result

- Installation succeeds.
- Version is reported correctly.
- GUI launches.

---

# Test 2 – Doctor

## Procedure

Run

```bash
imoviehd2fcp doctor
```

### Expected Result

- Python detected.
- FFmpeg detected.
- FFprobe detected.
- GUI dependencies detected.
- No errors reported.

---

# Test 3 – Analyse Archive

## Procedure

1. Select a test archive.
2. Select a new output folder.
3. Click **Analyse Archive**.

### Expected Result

- Archive Summary generated.
- Correct project count.
- Reports generated.
- No media modified.

---

# Test 4 – Convert Archive

## Procedure

Click **Convert Archive**.

### Expected Result

- Project folders created beneath:

```text
Output/
└── projects/
```

Each project contains:

- Converted Media
- Project.fcpxml
- Analysis report
- Conversion report
- Timeline data

No duplicate project folders are created.

---

# Test 5 – Event Plan

## Procedure

Create an Event Plan.

Edit several Event names.

Save the CSV.

### Expected Result

The CSV contains the updated Event names.

---

# Test 6 – Prepare Final Cut Project Files

## Procedure

Click **Prepare Final Cut Project Files**.

### Expected Result

- Existing project FCPXML files updated.
- No duplicate XML files created.
- Build reports generated.

---

# Test 7 – Final Cut Pro Import

## Procedure

Import several project XML files into Final Cut Pro.

### Expected Result

- Projects import successfully.
- Projects appear in the expected Events.
- Media is online.
- Timeline duration matches the original project.
- Audio is synchronised.
- Titles and transitions appear correctly where supported.

---

# Test 8 – Resume Conversion

## Procedure

Interrupt a conversion.

Restart the conversion.

### Expected Result

Completed work is reused.

Remaining projects continue processing.

---

# Test 9 – Force Rebuild

## Procedure

Run a forced conversion.

### Expected Result

Existing converted outputs are regenerated.

---

# Test 10 – Output Structure

Verify the final output.

```text
Output/
├── projects/
├── Event Plan.csv
├── Final Cut Build Reports/
├── Logs/
└── _Batch Logs/
```

Each project should contain:

```text
Project.fcpxml
Converted Media/
Project-analysis.txt
Project-report.txt
Project-timeline.json
```

---

# Regression Checklist

## GUI

- [ ] Application launches
- [ ] Navigation updates correctly
- [ ] Progress information updates
- [ ] Buttons enable and disable correctly
- [ ] Activity log updates
- [ ] Completion page displays

---

## Conversion

- [ ] Analyse
- [ ] Convert
- [ ] Event Plan
- [ ] Prepare Project Files
- [ ] Resume
- [ ] Force Rebuild

---

## Output

- [ ] Correct folder structure
- [ ] Correct filenames
- [ ] Reports generated
- [ ] Logs generated
- [ ] One FCPXML per project

---

## Final Cut Pro

- [ ] XML imports
- [ ] Event names correct
- [ ] Media online
- [ ] Timeline correct
- [ ] Audio correct

---

# Known Limitations

Document any current limitations for the release.

Examples:

- Unsupported iMovie HD effects.
- Unsupported legacy codecs.
- Manual review may be required for complex titles.

---

# Pass Criteria

A release is considered ready when:

- All critical tests pass.
- No data loss is observed.
- Final Cut Pro imports every supported project.
- No duplicate project XML files are created.
- Documentation matches the release.
- All regression tests pass.

---

# Future Test Cases

Future releases should expand testing to include:

- Very large archives (500+ projects)
- NAS storage
- External SSDs
- International filenames
- Corrupted archives
- Unsupported media
- Performance benchmarking