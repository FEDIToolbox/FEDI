# FEDI Package Build and Upload

This directory contains scripts for building and uploading the FEDI package to PyPI.

## Quick Start

Before pushing changes to the main repository, run:

```bash
./scripts/build_and_upload.sh
```

This will:
1. Clean previous build artifacts
2. Verify version consistency
3. Build source distribution and wheel
4. Check package contents
5. Upload to PyPI (with confirmation prompt)

## Options

### Test Upload (TestPyPI)

To test the upload process without affecting the production PyPI:

```bash
./scripts/build_and_upload.sh --test
```

### Build Only (No Upload)

To build the package without uploading (useful for testing):

```bash
./scripts/build_and_upload.sh --no-upload
```

The built packages will be in the `dist/` directory.

## Prerequisites

- Python 3.7 or higher
- `twine` installed: `pip install twine`
- PyPI credentials configured (for upload)

## Manual Upload

If you prefer to upload manually after building:

```bash
# Build only
./scripts/build_and_upload.sh --no-upload

# Then upload manually
twine upload dist/*
```

## Version Management

The script checks for version consistency between:
- `setup.py` (main version)
- `FEDI/__init__.py` (package version)

Make sure both are updated before building a new release.

## Workflow

1. Make your changes
2. Update version numbers in `setup.py` and `FEDI/__init__.py`
3. Run `./scripts/build_and_upload.sh`
4. Push changes to the repository

## Troubleshooting

### "twine is not installed"
```bash
pip install twine
```

### "Build failed"
- Check for syntax errors in Python files
- Verify all dependencies are listed in `setup.py`
- Check that all required files are included in `MANIFEST.in`

### "Upload failed"
- Verify PyPI credentials
- Check if the version already exists on PyPI (must be unique)
- For TestPyPI, use `--test` flag

