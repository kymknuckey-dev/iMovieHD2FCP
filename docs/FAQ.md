# Frequently Asked Questions

## General

### What is iMovieHD2FCP?

iMovieHD2FCP converts legacy iMovie HD projects into projects that can be imported into Final Cut Pro.

It preserves project organisation, converts supported media and generates one Final Cut Pro XML file for each project.

---

### Which versions of iMovie are supported?

Version 1.1 is designed for **iMovie HD** project archives.

Support for later versions of iMovie is outside the scope of this release.

---

### Does the application modify my original archive?

No.

The original archive is never modified.

All converted files are written to the output folder that you select.

---

### Can I convert multiple projects at once?

Yes.

The application analyses and converts every supported project found within the selected archive.

---

## Conversion

### What happens during Analyse Archive?

Analyse Archive examines every project and:

- Locates media
- Reads project timelines
- Detects potential issues
- Produces an Archive Summary

No media is converted during this step.

---

### Why is there no Preview Conversion button?

Earlier versions included a Preview Conversion step.

In Version 1.1 the Analyse Archive step provides the same validation without requiring an additional step, simplifying the workflow.

Advanced users can still use the `--dry-run` option from the command line.

---

### Can I resume an interrupted conversion?

Yes.

Existing converted outputs are detected and reused where possible.

---

### Can I force a complete rebuild?

Yes.

Use the **Force Rebuild** option from the command line if you want to regenerate all converted outputs.

---

## Event Plan

### What is the Event Plan?

The Event Plan is an editable CSV file that determines how projects will be organised into Final Cut Pro Events.

It allows you to reorganise projects without repeating the conversion.

---

### Do I have to edit the Event Plan?

No.

If you are happy with the suggested Event names you can use the Event Plan without making any changes.

---

### Can I move projects between Events?

Yes.

Simply edit the Event name in the CSV file and prepare the Final Cut Project Files again.

---

## Final Cut Pro

### Why does every project have its own FCPXML file?

Each project remains independent.

This makes it easy to:

- Import a single project
- Re-import a project after changes
- Troubleshoot individual projects
- Keep media and project files together

---

### Why isn't there one large XML file?

Using one XML file per project keeps projects self-contained and avoids creating very large import files.

---

### How do I import my projects?

In Final Cut Pro choose:

**File → Import → XML…**

Select the required project's `.fcpxml` file.

Repeat for additional projects if required.

---

### Will my projects appear in the correct Events?

Yes.

Projects are placed into the Events defined in your Event Plan.

---

## Output Folder

### Where are converted projects stored?

Converted projects are written beneath:

```text
Output/
└── projects/
```

Each project has its own folder containing converted media, reports and its Final Cut Pro XML file.

---

### What is stored in Final Cut Build Reports?

This folder contains reports generated while preparing the Final Cut Project Files.

It does not contain duplicate project XML files.

---

### Can I delete the reports?

Yes.

However, keeping them can assist with troubleshooting or verifying a previous migration.

---

## Compatibility

### Do I need FFmpeg?

Yes.

FFmpeg is used to convert supported media into formats suitable for Final Cut Pro.

---

### Which operating systems are supported?

Version 1.1 is designed for macOS.

---

### Can I store my output on an external drive?

Yes.

External SSDs, hard drives and NAS storage can all be used, provided they are writable.

Performance may vary depending on the storage device.

---

## Troubleshooting

### The application cannot find my media.

Check that the original iMovie HD archive is complete and that all media files are available.

Run Analyse Archive again after restoring any missing files.

---

### Final Cut Pro will not import a project.

Check that:

- The project XML file exists.
- The Event Plan has been prepared.
- The converted media is still in its original location.

---

### Where can I get more help?

See:

- GETTING_STARTED.md
- USER_GUIDE.md
- TROUBLESHOOTING.md

or open an issue on the project's GitHub repository.