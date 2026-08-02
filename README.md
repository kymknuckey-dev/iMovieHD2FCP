# iMovieHD2FCP v1.0.0 Release Candidate 2

`iMovieHD2FCP` migrates legacy iMovie HD projects into modern Final Cut Pro.

This release candidate consolidates the proven archive analyser, v1 converter,
resumable batch workflow, verification, Event planning and safe Event imports
behind one command.

## Current production workflow

```text
Analyse archive
→ Convert projects
→ Verify outputs
→ Plan Final Cut Events
→ Build safe Event import set
→ Import XML files into Final Cut
```

The product deliberately creates one intact FCPXML per original iMovie project.
It does not merge complete XML documents. This preserves the internally proven
timeline and resource relationships.

## Install over the existing project

Extract this package into:

```text
~/Development/iMovieHD2FCP
```

The existing proven scripts must remain in that folder. Then run:

```bash
cd ~/Development/iMovieHD2FCP
source .venv/bin/activate
python3 install_product.py
imoviehd2fcp doctor
```

## Commands

### Check the installation

```bash
imoviehd2fcp doctor
```

### Analyse an archive

```bash
imoviehd2fcp analyse \
  "/Volumes/10TB Seagate/Europe 2005 Final Projects" \
  "/Volumes/10TB Seagate/Europe 2005 Analysis"
```

### Convert an archive

```bash
imoviehd2fcp convert \
  "/Volumes/10TB Seagate/Europe 2005 Final Projects" \
  "/Volumes/10TB Seagate/Europe 2005 Final Projects Converted v1"
```

The batch conversion is resume-safe. Rerunning the same command skips completed
projects unless `--force` is supplied.

### Verify existing outputs

```bash
imoviehd2fcp verify \
  "/Volumes/10TB Seagate/Europe 2005 Final Projects" \
  "/Volumes/10TB Seagate/Europe 2005 Final Projects Converted v1"
```

### Create the Event plan

```bash
imoviehd2fcp plan-events \
  "/Volumes/10TB Seagate/Europe 2005 Final Projects Converted v1" \
  --plan "/Volumes/10TB Seagate/Europe 2005 Event Plan.csv" \
  --event-mode parent
```

Edit the `event_name` column in Numbers or Excel.

### Build safe Event imports

```bash
imoviehd2fcp build-imports \
  --plan "/Volumes/10TB Seagate/Europe 2005 Event Plan.csv" \
  --output "/Volumes/10TB Seagate/Europe 2005 Final Cut Imports"
```

Import the numbered XML files into the intended Final Cut library.

## Known metadata behaviour

The v1 converter preserves source filesystem dates and writes QuickTime
`creation_time` metadata. Some original iMovie assets have inconsistent dates
or duplicate logical names. These are reported rather than silently rewritten.

A later metadata refinement will add full timestamp provenance and cleaner
duplicate display-name numbering without changing underlying media identity.


## RC2 refinements

RC2 adds:

- full timestamp provenance in every media and soundtrack manifest entry;
- deterministic timestamp selection with a recorded reason;
- embedded media creation-time preference where available;
- clean duplicate Browser names such as `Clip 13 (2)`;
- unchanged source filenames, hashes and UIDs;
- installer refusal when the active Python or pip is outside `.venv`;
- expanded `doctor` checks for the Python environment.

After installing RC2, reconvert a representative project with `--force` or use a
fresh output folder to see the new manifest format and duplicate naming.
