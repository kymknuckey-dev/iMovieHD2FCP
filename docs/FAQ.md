# Frequently Asked Questions (FAQ)

**Version 1.0.0**

---

# Contents

1. General Questions
2. Installation
3. Archives
4. Conversion
5. Final Cut Pro
6. Reports
7. Performance
8. Troubleshooting
9. Future Development

---

# General Questions

## What is iMovieHD2FCP?

iMovieHD2FCP is a migration toolkit that helps preserve legacy **iMovie HD (iMovie 6)** projects by converting them into formats suitable for modern versions of **Final Cut Pro**.

Unlike a simple media converter, it analyses the archive, documents its contents, converts compatible media, generates reports, and prepares Final Cut Pro XML import files.

---

## Does it modify my original archive?

No.

One of the design goals of iMovieHD2FCP is that the original archive is **never modified**.

You can safely run the software multiple times against the same archive.

---

## Is this an official Apple product?

No.

iMovieHD2FCP is an independent open-source project and is not affiliated with or endorsed by Apple.

---

## Which version of iMovie does it support?

Version 1.0.0 is designed for **iMovie HD (iMovie 6)** project archives.

Support for later iMovie project formats may be considered in future releases.

---

# Installation

## Which operating systems are supported?

Version 1.0.0 has been developed and tested on macOS.

---

## Which version of Python is required?

Python 3.11 or newer is recommended.

Verify your installation with:

```bash
python3 --version
```

---

## Why do I need FFmpeg?

FFmpeg performs the media conversion required for compatibility with modern editing software.

Verify the installation:

```bash
ffmpeg -version
```

---

## How do I know everything is installed correctly?

Run:

```bash
imoviehd2fcp doctor
```

If everything is configured correctly the final status will be:

```
READY
```

---

# Archives

## Can I analyse an archive without converting it?

Yes.

```bash
imoviehd2fcp analyse "<archive>"
```

This scans the archive without modifying any files.

---

## Can I convert only one project?

Version 1.0.0 is designed to process complete archives.

Future releases may support more selective conversion workflows.

---

## What happens if media is missing?

The analysis and verification reports identify missing media.

The conversion continues where possible, but affected projects may require manual review.

---

## Are my original files preserved?

Yes.

Original media is never overwritten or deleted.

---

# Conversion

## How long does a conversion take?

It depends on:

- Number of projects
- Total media size
- Media codecs
- Computer performance
- Storage speed

Large archives may take several hours.

---

## Can I stop and restart a conversion?

Generally, yes.

Depending on the stage reached, rerunning the conversion will recreate the required outputs.

Review the generated reports before importing into Final Cut Pro.

---

## Does the converter preserve folder structure?

Yes.

Where practical, the original project organisation is preserved to make the migrated archive familiar and easier to navigate.

---

# Final Cut Pro

## How do I import the results?

Open Final Cut Pro.

Choose:

```
File

    Import

        XML...
```

Select one of the generated XML files.

---

## Will every transition be preserved?

Many transitions can be represented successfully.

Some legacy iMovie HD transitions do not have direct equivalents in modern Final Cut Pro and may require manual adjustment after import.

---

## Are titles preserved?

Where supported by the available project information, title information is carried across.

Some legacy title styles may not exist in modern Final Cut Pro.

---

## Can I import into an existing Library?

It is recommended to import into a **new Library** first.

Once you have reviewed the imported projects, they can be moved or copied into an existing production Library if required.

---

# Reports

## Why are reports generated?

Reports provide:

- Archive documentation
- Conversion statistics
- Media inventories
- Warning summaries
- Long-term preservation records

They are intended to remain with the converted archive.

---

## Can I regenerate reports later?

Yes.

Run:

```bash
imoviehd2fcp report "<archive>"
```

---

# Performance

## Is SSD storage recommended?

Yes.

Solid-state storage significantly improves conversion speed.

---

## Can I store archives on a NAS?

Yes.

However:

- Local SSD storage generally provides the best performance.
- Large conversions may be slower over a network connection.

---

## Can I process multiple archives simultaneously?

This is not recommended.

Running one migration at a time simplifies verification and reduces resource contention.

---

# Troubleshooting

## The Doctor command reports an error.

Run:

```bash
imoviehd2fcp doctor
```

Review each reported component.

Common causes include:

- Missing FFmpeg
- Incorrect Python environment
- Missing legacy modules

---

## Final Cut Pro reports XML import errors.

Check:

- XML files were generated successfully.
- Converted media is available.
- Verification completed without errors.

---

## My archive contains unsupported media.

Unsupported media will be identified in the reports.

Where possible, affected items can be converted manually before rerunning the migration.

---

# Future Development

## Will additional iMovie features be supported?

Future releases may expand support for:

- Additional transitions
- Legacy title styles
- Effects
- Timeline reconstruction
- Improved metadata preservation

Support depends on the capabilities of the Final Cut Pro XML format.

---

## How can I contribute?

Contributions are welcome.

Useful contributions include:

- Bug reports
- Feature requests
- Documentation improvements
- Testing with additional iMovie HD archives
- Code contributions

Please include sufficient information to reproduce any reported issues.

---

# Still Need Help?

If your question is not answered here:

1. Run:

```bash
imoviehd2fcp doctor
```

2. Review:

- USER_GUIDE.md
- TROUBLESHOOTING.md
- CLI_REFERENCE.md

3. Include the following when requesting assistance:

- iMovieHD2FCP version
- macOS version
- Python version
- FFmpeg version
- Command executed
- Error messages
- Relevant log files

Providing this information makes it much easier to diagnose problems.

---

© 2026 iMovieHD2FCP Project