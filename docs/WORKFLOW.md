# iMovieHD2FCP Workflow Guide

**Version 1.0.0**

---

# Contents

1. Introduction
2. Migration Philosophy
3. Recommended Workflow
4. Stage 1 – Prepare the Archive
5. Stage 2 – Verify the Installation
6. Stage 3 – Analyse the Archive
7. Stage 4 – Review the Analysis
8. Stage 5 – Convert the Archive
9. Stage 6 – Verify the Conversion
10. Stage 7 – Review Reports
11. Stage 8 – Plan Final Cut Pro Events
12. Stage 9 – Build Import XML
13. Stage 10 – Import into Final Cut Pro
14. Stage 11 – Validate the Imported Projects
15. Long-Term Archiving
16. Best Practices
17. Common Mistakes
18. Related Documentation

---

# 1. Introduction

This guide describes the recommended workflow for migrating legacy **iMovie HD (iMovie 6)** projects into **Final Cut Pro** using iMovieHD2FCP.

Following this workflow helps ensure that your original media remains preserved while producing a clean and reliable Final Cut Pro library.

Although individual commands can be run independently, following the complete workflow is strongly recommended.

---

# 2. Migration Philosophy

iMovieHD2FCP follows three core principles:

- **Never modify the original archive**
- **Preserve as much project information as possible**
- **Produce a repeatable and verifiable migration**

Think of the original archive as a master copy. Every migration should be repeatable without changing the source material.

---

# 3. Recommended Workflow

```
Original Archive
        │
        ▼
Verify Installation
        │
        ▼
Analyse Archive
        │
        ▼
Review Results
        │
        ▼
Convert Archive
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
Build Import XML
        │
        ▼
Import into Final Cut Pro
        │
        ▼
Validate Imported Projects
```

Each stage is described below.

---

# 4. Stage 1 – Prepare the Archive

Before running the software:

- Make a backup of the original archive.
- Ensure all media is present.
- Do not rename folders or files.
- Store the archive on a reliable local or network drive.

Recommended folder structure:

```
Archives/
    Europe 2005/
    Family Movies/
    Holidays/
```

---

# 5. Stage 2 – Verify the Installation

Before each migration, confirm the installation is healthy.

```bash
imoviehd2fcp doctor
```

A successful result ends with:

```
READY
```

If any component fails, resolve the issue before continuing.

---

# 6. Stage 3 – Analyse the Archive

Run an analysis.

```bash
imoviehd2fcp analyse "/Volumes/Archives/Europe 2005"
```

The analysis identifies:

- Projects
- Clips
- Media formats
- Missing files
- Potential issues

No files are modified.

---

# 7. Stage 4 – Review the Analysis

Before converting:

- Review warnings.
- Confirm the expected number of projects.
- Check for missing media.
- Resolve any obvious archive issues.

Correcting problems now avoids unnecessary conversion work.

---

# 8. Stage 5 – Convert the Archive

Convert the archive.

```bash
imoviehd2fcp convert "/Volumes/Archives/Europe 2005"
```

The conversion process:

- Preserves the folder structure.
- Converts compatible media.
- Creates reports.
- Prepares Final Cut Pro assets.

Original media remains unchanged.

---

# 9. Stage 6 – Verify the Conversion

After conversion:

```bash
imoviehd2fcp verify "/Volumes/Archives/Europe 2005"
```

Verification checks:

- Converted media
- Generated reports
- XML output
- Folder structure
- Missing assets

Always resolve verification errors before importing into Final Cut Pro.

---

# 10. Stage 7 – Review Reports

Generate reports if they have not already been created.

```bash
imoviehd2fcp report "/Volumes/Archives/Europe 2005"
```

Review:

- HTML report
- Text report
- Warnings
- Media inventory
- Conversion statistics

Retain these reports as part of the archive documentation.

---

# 11. Stage 8 – Plan Final Cut Pro Events

Generate the Event Plan.

```bash
imoviehd2fcp plan-events "/Volumes/Archives/Europe 2005"
```

The resulting CSV allows you to:

- Rename Events
- Group related projects
- Organise the Final Cut Pro Library

Review the Event Plan before continuing.

---

# 12. Stage 9 – Build Import XML

Create Final Cut Pro XML files.

```bash
imoviehd2fcp build-imports "/Volumes/Archives/Europe 2005"
```

These XML files reference the converted media and Event Plan.

---

# 13. Stage 10 – Import into Final Cut Pro

Create a new Final Cut Pro Library.

Choose:

```
File
    Import
        XML...
```

Select the generated XML file.

Allow Final Cut Pro to complete the import before reviewing the projects.

---

# 14. Stage 11 – Validate the Imported Projects

Inspect each imported project.

Check:

- Timeline order
- Clip placement
- Audio
- Transitions
- Titles
- Media links

Minor adjustments may be required depending on the original iMovie HD project.

---

# 15. Long-Term Archiving

Retain:

- Original archive
- Converted media
- Reports
- Event Plan
- XML files
- Final Cut Pro Library

Keeping all outputs together ensures the migration can be reviewed or repeated in the future.

---

# 16. Best Practices

- Analyse before converting.
- Verify before importing.
- Work on one archive at a time.
- Keep reports with the archive.
- Back up both the original archive and the converted output.

---

# 17. Common Mistakes

Avoid:

- Editing the original archive.
- Deleting generated reports.
- Skipping verification.
- Importing directly into an existing production library.
- Ignoring warnings reported during analysis.

---

# 18. Related Documentation

| Document | Purpose |
|----------|---------|
| README.md | Project overview |
| GETTING_STARTED.md | First installation |
| USER_GUIDE.md | Complete user guide |
| CLI_REFERENCE.md | Command reference |
| FAQ.md | Frequently asked questions |
| TROUBLESHOOTING.md | Resolving common issues |

---

## Summary

Following this workflow provides the safest and most repeatable path for migrating legacy iMovie HD projects into Final Cut Pro.

By preserving the original archive, reviewing each stage, and validating the imported projects, you can ensure that valuable historical media remains accessible for years to come.

---

© 2026 iMovieHD2FCP Project