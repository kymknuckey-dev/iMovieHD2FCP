# Getting Started

## 1. Activate the development environment

```bash
cd ~/Development/iMovieHD2FCP
source .venv/bin/activate
```

## 2. Check the installation

```bash
imoviehd2fcp doctor
```

The final line should be `READY`.

## 3. Convert a small test

```bash
imoviehd2fcp convert \
  "/Volumes/Archive/Disney Final" \
  "/Volumes/Archive/Disney Converted RC3" \
  --limit 1
```

RC3 writes:

- converted project output;
- batch state and summary files;
- a persistent command log under `Logs/`;
- text and HTML reports under `Reports/`.

## 4. Resume after interruption

Rerun the same conversion command. Completed and verified projects are skipped.
Use `--force` only when deliberate reconversion is required.

## 5. Verify without reconverting

```bash
imoviehd2fcp verify \
  "/Volumes/Archive/Europe 2005 Final Projects" \
  "/Volumes/Archive/Europe 2005 Converted"
```

## 6. Build a report again

```bash
imoviehd2fcp report "/Volumes/Archive/Europe 2005 Converted"
```
