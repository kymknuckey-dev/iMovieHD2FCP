# Architecture

## Product layer

`src/imoviehd2fcp/cli.py` provides the stable user-facing command.

## Proven engine layer

The `legacy/` folder contains the real-world-tested parser and conversion tools.
The product invokes them with explicit paths and checks their exit status.

Keeping this layer intact avoids changing the conversion engine while the
product interface, packaging, reporting and workflow are consolidated.

## Migration path

The proven scripts will be moved into first-class package modules one at a time.
Each replacement must reproduce the existing output for the regression projects
before the corresponding legacy script is retired.

## Supported import strategy

Version 1 uses one intact FCPXML per original iMovie project, grouped by intended
Final Cut Event. A single merged archive XML remains experimental because it can
disturb internal resource relationships in complex projects.
