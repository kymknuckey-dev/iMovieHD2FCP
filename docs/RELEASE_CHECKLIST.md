# Release Checklist

```bash
source .venv/bin/activate
imoviehd2fcp doctor
python3 -m pytest
git status
```

Then:

```bash
git add .
git commit -m "Release iMovieHD2FCP 1.0.0"
git tag -a v1.0.0 -m "iMovieHD2FCP 1.0.0"
git push origin v1
git push origin v1.0.0
```

Create a GitHub Release from `v1.0.0`, use `docs/RELEASE_NOTES_1.0.0.md`, and attach the ZIP.
