# RC1 Test Checklist

## Installation

- [ ] Activate the project virtual environment
- [ ] Install the editable package
- [ ] Confirm `imoviehd2fcp --version` reports `1.1.0rc1`
- [ ] Run `imoviehd2fcp doctor`
- [ ] Launch `imoviehd2fcp-app`

## Guided workflow

- [ ] Choose a valid source archive
- [ ] Choose a fresh output folder
- [ ] Analyse completes
- [ ] Analysis results are readable
- [ ] Archive Summary opens correctly
- [ ] Convert completes
- [ ] Project folders are beneath `projects/`
- [ ] Converted Media is inside each project folder
- [ ] FCPXML filenames do not contain `-v1`
- [ ] Event Plan can be created
- [ ] Event Plan can be edited
- [ ] Project files can be prepared
- [ ] No duplicate XML tree is created
- [ ] Completion page opens Converted Projects

## Final Cut Pro

- [ ] Import one project FCPXML
- [ ] Import multiple project FCPXML files
- [ ] Projects appear in the Event names specified by Event Plan
- [ ] Media links resolve
- [ ] Project duration is correct
- [ ] Titles and transitions appear as expected
- [ ] Audio remains synchronised

## Compatibility

- [ ] Existing older root-level outputs remain detectable
- [ ] Existing `-v1.fcpxml` files remain usable
- [ ] CLI `convert --dry-run` remains available
