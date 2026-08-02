# Changelog

## 1.0.0rc2

- Added timestamp provenance for media and soundtrack assets.
- Records filesystem creation time, filesystem modification time, embedded
  container creation time, the selected value and the selection reason.
- Prefers embedded creation time, then macOS creation time, then modification
  time.
- Cleans iMovie duplicate suffixes such as `/1` for Browser display.
- Numbers duplicate Browser names as `(2)`, `(3)`, while preserving source
  filenames and UIDs.
- Added manifest version 2 and product-version metadata.
- Hardened installer against user-site fallback and non-local pip.
- Expanded `doctor` to validate the active virtual environment and pip path.

## 1.0.0rc1

- Added one installed `imoviehd2fcp` command.
- Consolidated archive analysis, conversion, verification, Event planning and
  safe Event-import generation.
- Preserved the proven conversion scripts under `legacy/`.
