# Workflow Guide

## Introduction

iMovieHD2FCP is designed as a guided migration assistant rather than a simple conversion utility.

Instead of performing every operation in a single step, the application breaks the migration into a series of stages. Each stage has a single purpose and can be verified before moving to the next.

This approach makes the migration process easier to understand, easier to troubleshoot and safer for valuable video archives.

---

# Workflow Overview

The recommended workflow is:

```
Choose Archive
        │
        ▼
Analyse Archive
        │
        ▼
Review Analysis
        │
        ▼
Convert Archive
        │
        ▼
Create or Edit Event Plan
        │
        ▼
Prepare Final Cut Project Files
        │
        ▼
Import into Final Cut Pro
```

Each stage builds on the previous stage.

---

# Stage 1 – Choose Archive

Select the folder containing one or more iMovie HD projects.

Also choose an output folder.

The original archive is never modified.

Purpose

- Select the source archive
- Select the destination for converted projects

Output

No files are created.

---

# Stage 2 – Analyse Archive

The application examines every project without making changes.

During analysis it:

- Finds every iMovie HD project
- Reads project timelines
- Locates media
- Detects missing items
- Produces an Archive Summary
- Estimates the work required

Purpose

To confirm that the archive is suitable for conversion.

Output

- Archive Summary
- Project reports
- Analysis reports

No converted media is created.

---

# Stage 3 – Convert Archive

Each project is converted independently.

Converted media is written into a dedicated project folder.

Purpose

Create Final Cut Pro compatible project assets while preserving the original archive.

Output

```
projects/
    Archive/
        Project/
```

Each project contains:

- Converted Media
- Project.fcpxml
- Analysis report
- Conversion report
- Timeline data

---

# Stage 4 – Create or Edit the Event Plan

The Event Plan controls how projects will appear inside Final Cut Pro.

Each row represents one project.

You may:

- Rename Events
- Move projects between Events
- Exclude projects from preparation

Purpose

Allow project organisation without repeating the conversion process.

Output

```
Event Plan.csv
```

---

# Stage 5 – Prepare Final Cut Project Files

The Event Plan is applied to each project's existing FCPXML file.

The application updates each project's Event name in place.

No duplicate XML files are created.

Purpose

Prepare each project for import into Final Cut Pro.

Output

Updated:

```
Project.fcpxml
```

Build reports are also generated.

---

# Stage 6 – Import into Final Cut Pro

Open Final Cut Pro.

Choose:

```
File → Import → XML…
```

Import the required project XML files.

Projects appear inside the Events defined by the Event Plan.

Purpose

Complete the migration.

---

# Why One XML Per Project?

Each converted project retains its own Final Cut Pro XML file.

This approach:

- Keeps projects independent
- Makes troubleshooting easier
- Allows individual projects to be re-imported
- Avoids creating very large XML files
- Keeps project media and metadata together

Each project is completely self-contained.

---

# Why Use an Event Plan?

Separating Event organisation from media conversion provides several advantages.

You can:

- Reorganise projects without reconverting media
- Experiment with different Event layouts
- Exclude projects
- Rebuild project XML files quickly

The Event Plan is therefore an organisational step rather than a conversion step.

---

# Resume Capability

If a conversion is interrupted, the application detects existing outputs.

Completed work is reused where possible.

This avoids unnecessary reconversion.

---

# Output Structure

A completed migration produces:

```text
Output/
├── projects/
│   └── Archive/
│       └── Project/
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

---

# Design Principles

The workflow is based on five principles.

## Preserve the original archive

The source archive is never modified.

## One project at a time

Each project is converted independently.

## Clear organisation

Converted media, reports and project files remain together.

## Simple recovery

Interrupted conversions can be resumed.

## User control

Users decide how projects are organised inside Final Cut Pro through the Event Plan.

---

# Best Practices

- Always work from a backup of your original archive.
- Use a new output folder for each migration.
- Review the Archive Summary before converting.
- Edit the Event Plan before preparing project files.
- Import project XML files into the desired Final Cut Pro library.
- Keep the generated project folders together after import for future reference.

---

# Related Documentation

- GETTING_STARTED.md
- USER_GUIDE.md
- CLI_REFERENCE.md
- FAQ.md
- TROUBLESHOOTING.md