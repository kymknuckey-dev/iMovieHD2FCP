# Getting Started

Welcome to **iMovieHD2FCP**.

This guide walks you through your first migration from an iMovie HD archive to Final Cut Pro.

By the end of this guide you will have:

- Analysed an iMovie HD archive
- Converted the archive
- Organised projects into Final Cut Events
- Prepared Final Cut Pro project files
- Imported your projects into Final Cut Pro

The process usually takes less than 30 minutes for a small archive.

---

# Before You Begin

You will need:

- macOS
- Python 3.10 or later
- FFmpeg installed
- Final Cut Pro (recommended)
- An iMovie HD archive

The application supports archives containing one or many iMovie HD projects.

---

# Installation

Clone the repository.

```bash
git clone https://github.com/kymknuckey-dev/iMovieHD2FCP.git
cd iMovieHD2FCP
```

Create a virtual environment.

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the application.

```bash
python3 -m pip install -e .
```

Install the optional graphical interface.

```bash
python3 install_gui.py
```

---

# Starting the Application

Launch the graphical application.

```bash
imoviehd2fcp-app
```

The opening screen guides you through each stage of the migration.

---

# Step 1 – Select Your Archive

Click **Browse** beside **Source Archive**.

Choose the folder containing your iMovie HD projects.

Next choose an empty **Output Folder**.

The application writes all converted files into this folder and does not modify the original archive.

**Expected result**

Both paths are displayed and the **Analyse Archive** button is enabled.

---

# Step 2 – Analyse Archive

Click **Analyse Archive**.

The application examines every project and produces an archive summary.

During this step it:

- Locates every project
- Checks media files
- Reads project timelines
- Detects potential issues
- Estimates the conversion workload

No media files are modified.

**Expected result**

The Archive Summary opens automatically and the application reports that the archive is ready for conversion.

---

# Step 3 – Convert Archive

Click **Convert Archive**.

The application converts each project into its own Final Cut Pro project folder.

Converted media, reports and project files are written beneath the output folder.

Depending on archive size this may take several minutes.

**Expected result**

Each project has its own folder beneath:

```text
Output/
└── projects/
```

---

# Step 4 – Review or Edit the Event Plan

Click **Create Event Plan**.

An editable CSV file is created.

Each row represents one project.

You may:

- Leave the suggested Event names unchanged
- Rename Events
- Move projects between Events

Save the CSV when finished.

**Expected result**

The Event Plan reflects the Event organisation you want to see inside Final Cut Pro.

---

# Step 5 – Prepare Final Cut Project Files

Click **Prepare Final Cut Project Files**.

The application updates each project's Final Cut Pro XML file using the Event names from the Event Plan.

No duplicate XML files are created.

Each project retains one Final Cut Pro XML file beside its converted media.

**Expected result**

Each project folder contains:

```text
Project.fcpxml
Converted Media/
Project-analysis.txt
Project-report.txt
Project-timeline.json
```

---

# Step 6 – Import into Final Cut Pro

Open Final Cut Pro.

Choose:

**File → Import → XML…**

Navigate to the required project folder.

Select:

```text
Project.fcpxml
```

Repeat for additional projects if required.

Projects will appear in the Events defined by your Event Plan.

---

# Understanding the Output Folder

A completed conversion looks like:

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

The original archive is never modified.

---

# If Something Goes Wrong

Most problems are caused by:

- Missing media
- Unsupported codecs
- Insufficient disk space
- Incomplete project folders

See **TROUBLESHOOTING.md** for detailed solutions.

---

# Next Steps

Now that you've successfully migrated one archive, you can:

- Convert additional archives
- Customise Event Plans
- Use the command-line interface for batch processing
- Review the complete **User Guide**

---

# Need More Help?

The following documents provide additional information:

- USER_GUIDE.md
- WORKFLOW.md
- CLI_REFERENCE.md
- FAQ.md
- TROUBLESHOOTING.md

Happy migrating!