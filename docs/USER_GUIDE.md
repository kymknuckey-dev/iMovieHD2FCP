# User Guide

## Introduction

Welcome to iMovieHD2FCP.

![alt text](<Main Window-1.png>)

This guide explains every feature of the application and provides detailed information about the complete migration workflow.

If this is your first time using the application, read **GETTING_STARTED.md** first.

---

# Overview

iMovieHD2FCP converts legacy iMovie HD projects into Final Cut Pro projects while preserving the original project organisation wherever possible.

The migration consists of six stages:

1. Analyse Archive
2. Convert Archive
3. Create Event Plan
4. Prepare Final Cut Project Files
5. Import into Final Cut Pro
6. Review the results

---

# Main Window

Describe each section of the application:

- Source Archive
- Output Folder
- Progress summary
- Workflow navigation
- Activity log

Include annotated screenshots in the final release.

---

# Analyse Archive

Purpose

What happens during analysis

What reports are generated

What the summary statistics mean

How to interpret warnings

---

# Convert Archive

What conversion actually does

How converted media is organised

Expected running time

Resume behaviour

Force rebuilds

---

# Converted Project Structure

Explain every file created.

Example

projects/
    Disney Final/
        Small World/
            Converted Media/
            Small World.fcpxml
            Small World-analysis.txt
            Small World-report.txt
            Small World-timeline.json

Describe each file.

---

# Event Plan

Purpose

CSV format

Columns

Typical edits

Renaming Events

Moving Projects

Disabling projects

Examples

---

# Prepare Final Cut Project Files

Explain:

- Reads Event Plan
- Updates each project's FCPXML
- No duplicate XML files
- Existing project XML updated in place

---

# Importing into Final Cut Pro

Recommended workflow

Importing multiple projects

Importing one project

Creating libraries

Organising Events

---

# Reports

Archive Summary

Analysis reports

Conversion reports

Build reports

Log files

What each report is used for.

---

# Settings

Explain every preference.

Current defaults.

Recommended settings.

---

# Command Line

Brief overview.

Link to CLI_REFERENCE.md.

---

# Tips

Recommended workflow

Working with large archives

Backing up archives

Network storage

External drives

---

# Frequently Asked Questions

Point readers to FAQ.md.

---

# Troubleshooting

Point readers to TROUBLESHOOTING.md.

---

# Appendix

Glossary

Archive

Event

FCPXML

Timeline

Converted Media

Project Folder