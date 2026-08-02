# Troubleshooting

## `imoviehd2fcp: command not found`

Activate the project environment:

```bash
cd ~/Development/iMovieHD2FCP
source .venv/bin/activate
```

Then reinstall:

```bash
python3 install_product.py
```

## Doctor reports pip outside `.venv`

Recreate the environment rather than committing or repairing its contents:

```bash
deactivate
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
python3 -m ensurepip --upgrade
python3 -m pip install --upgrade pip setuptools wheel
python3 install_product.py
```

## Conversion was interrupted

Rerun the identical `convert` command. The batch state and project verification
allow completed projects to be skipped.

## Report cannot be built

Confirm this exists in the conversion destination:

```text
batch-conversion-summary.json
```

Run `imoviehd2fcp verify` to regenerate the verification summary where needed.
