# Getting Started

Welcome to **iMovieHD2FCP**.

This guide walks you through your first successful conversion of an iMovie HD archive into Final Cut Pro.

By the end of this guide you will have:

- Installed the software
- Verified your installation
- Analysed an archive
- Converted the archive
- Verified the conversion
- Created an Event Plan
- Generated Final Cut Pro import packages
- Imported the projects into Final Cut Pro

No previous knowledge of the software is assumed.

---

# Before You Begin

## Requirements

Before installing iMovieHD2FCP ensure you have:

- macOS
- Python 3.9 or later
- FFmpeg installed and available in your PATH
- Final Cut Pro
- A copy of your iMovie HD archive

---

## Verify Python

Open Terminal.

Run:

```bash
python3 --version
```

Example:

```text
Python 3.14.0
```

---

## Verify FFmpeg

Run:

```bash
ffmpeg -version
```

If FFmpeg is installed you will see version information.

If not, install it using Homebrew:

```bash
brew install ffmpeg
```

---

# Installation

Clone the repository.

```bash
git clone https://github.com/kymknuckey-dev/iMovieHD2FCP.git
```

Enter the project directory.

```bash
cd iMovieHD2FCP
```

Create a virtual environment.

```bash
python3 -m venv .venv
```

Activate it.

```bash
source .venv/bin/activate
```

Install the product.

```bash
python3 install_product.py
```

---

# Verify the Installation

Run:

```bash
imoviehd2fcp doctor
```

A successful installation finishes with:

```text
READY
```

The Doctor command also confirms:

- Python environment
- FFmpeg installation
- FFprobe installation
- Product components
- Legacy conversion modules

If Doctor reports any problems, see **TROUBLESHOOTING.md**.

---

# Understanding the Workflow

Every archive follows the same sequence.

```
Analyse

↓

Convert

↓

Verify

↓

Plan Events

↓

Build XML Imports

↓

Import into Final Cut Pro
```

Each step produces information used by the next step.

---

# Step 1 – Analyse Your Archive

The Analyse command inspects the archive without changing any files.

Example:

```bash
imoviehd2fcp analyse \
"/Volumes/Media/Europe 2005" \
"/Volumes/Media/Europe 2005 Output"
```

The output folder will contain reports describing:

- Projects discovered
- Media files
- Missing media
- Titles
- Transitions
- Timeline information
- Overall archive statistics

Review these reports before converting.

---

# Step 2 – Convert the Archive

Once you are satisfied with the analysis, convert the archive.

```bash
imoviehd2fcp convert \
"/Volumes/Media/Europe 2005" \
"/Volumes/Media/Europe 2005 Output"
```

During conversion the software:

- Processes project media
- Preserves original files
- Creates Final Cut Pro compatible assets
- Builds project metadata
- Generates reports

The original archive is never modified.

---

# Step 3 – Verify the Conversion

Verify confirms that every expected output has been created.

Run:

```bash
imoviehd2fcp verify \
"/Volumes/Media/Europe 2005" \
"/Volumes/Media/Europe 2005 Output"
```

Verification checks:

- Converted media
- Missing files
- Generated metadata
- XML preparation
- Report consistency

If problems are found they should be corrected before importing into Final Cut Pro.

---

# Step 4 – Create an Event Plan

Final Cut Pro stores projects inside Events.

iMovieHD2FCP allows you to decide how projects should be grouped before XML is generated.

Generate an editable Event Plan.

```bash
imoviehd2fcp plan-events \
"/Volumes/Media/Europe 2005 Output" \
--plan "/Volumes/Media/Event Plan.csv"
```

Open the CSV in:

- Numbers
- Excel
- LibreOffice
- Google Sheets

You may rename Events or reorganise projects.

Save the edited CSV.

---

# Step 5 – Build Final Cut Pro Imports

Generate Final Cut Pro XML packages.

```bash
imoviehd2fcp build-imports \
--plan "/Volumes/Media/Event Plan.csv" \
--output "/Volumes/Media/FCP Imports"
```

The output folder will contain one XML import package for each project.

---

# Step 6 – Import into Final Cut Pro

Open Final Cut Pro.

Create a Library.

Select:

```
File
    Import
        XML...
```

Choose one of the generated XML files.

Repeat for additional projects if required.

Final Cut Pro will create:

- Events
- Projects
- Media links

based on the generated XML.

---

# Reviewing the Imported Projects

After importing:

- Check project duration
- Review transitions
- Review titles
- Confirm media links
- Play the project from beginning to end

Minor adjustments may occasionally be required depending on the original iMovie HD project.

---

# Common Workflow

The complete workflow can be summarised as:

```text
Doctor

↓

Analyse

↓

Review Reports

↓

Convert

↓

Verify

↓

Create Event Plan

↓

Generate XML

↓

Import into Final Cut Pro

↓

Review Projects
```

---

# Next Steps

Once you are comfortable with the workflow you can explore:

- batch conversions
- partial conversions
- advanced Event planning
- archive reporting

See:

- USER_GUIDE.md
- CLI_REFERENCE.md
- WORKFLOW.md

for more detailed information.

---

# Need Help?

If something does not work as expected:

1. Run:

```bash
imoviehd2fcp doctor
```

2. Review:

```
docs/TROUBLESHOOTING.md
```

3. Include the following when requesting support:

- macOS version
- Python version
- Final Cut Pro version
- Doctor output
- Console output
- Sample project (if possible)

This information greatly assists troubleshooting.

---

**Congratulations!**

You have successfully completed your first iMovie HD to Final Cut Pro migration.

The remainder of the documentation explains each command and workflow in greater depth.