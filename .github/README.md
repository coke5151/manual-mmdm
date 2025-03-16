# GitHub Automated Release Workflow

This directory contains GitHub Actions workflow files for automatically building and releasing cross-platform manual-mmdm applications.

## Release Process

When you're ready to release a new version, you only need to:

1. Make sure your code is ready for release
2. Create a new tag version in the format `v*`, for example `v1.0.0`
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

GitHub Actions will automatically:
1. Create a release page for this tag
2. Build the application on multiple platforms and architectures
3. Create ZIP files for each platform/architecture combination
4. Upload these ZIP files to the release page

## Supported Platforms

The workflow builds and packages the application for the following platforms:

### Windows
- Windows x64 (64-bit): `manual-mmdm-v1.0.0-windows-x64.zip`

### macOS
- macOS x64 (Intel): `manual-mmdm-v1.0.0-macos-x64.zip`
- macOS arm64 (Apple Silicon): `manual-mmdm-v1.0.0-macos-arm64.zip`
- macOS Universal (Intel + Apple Silicon): `manual-mmdm-v1.0.0-macos-universal.zip`

### Linux
- Linux x64 (64-bit): `manual-mmdm-v1.0.0-linux-x64.zip`
- Linux arm64 (64-bit ARM): `manual-mmdm-v1.0.0-linux-arm64.zip`

## Workflow Details

The workflow `.github/workflows/release.yml` contains the following jobs:

1. `create-release`: Creates the GitHub release page
2. `build-windows-x64`: Builds the application for Windows 64-bit
3. `build-macos-x64`: Builds the application for macOS Intel
4. `build-macos-arm64`: Builds the application for macOS Apple Silicon
5. `build-macos-universal`: Builds the application as a Universal macOS binary
6. `build-linux-x64`: Builds the application for Linux 64-bit
7. `build-linux-arm64`: Builds the application for Linux ARM64

## Known Limitations

### Windows
Windows x86 (32-bit) builds have been disabled due to PyQt6 compatibility issues with Python 3.13. The specific errors encountered include:
- `No candidate is found for 'pyqt6-qt6' that matches the environment or hashes`
- Missing Qt build toolchain (`qmake`) for 32-bit environments

If 32-bit Windows support is critically needed, consider:
- Using an older Python version (3.10/3.11)
- Using pre-compiled PyQt6 wheels
- Setting up a custom build environment with Qt6 SDK installed

### macOS
macOS builds require special handling due to PyInstaller's issues with Qt framework symbolic links. The workflow uses a custom wrapper script to handle these issues, specifically addressing:
- `FileExistsError` related to existing symbolic links in Qt frameworks
- Conflicts between framework `Resources` symbolic links during the collection phase

### Linux
Linux builds require specific system dependencies for Qt and graphical interfaces. The package names have been updated to match Ubuntu 24.04 (Noble):
- Replaced `libgl1-mesa-glx` with `libgl1`
- Replaced `libegl1-mesa` with `libegl1`
- Added additional dependencies like `libxcb-cursor0`, `libxcb-xkb1` and `libxcb-randr0`

For ARM64 Linux builds, a Docker container is used with QEMU emulation to build natively for the ARM architecture.

## Troubleshooting

If the workflow fails, check:
1. Make sure Python 3.13 is compatible with your application
2. Check the GitHub Actions logs for detailed error messages
3. Ensure GitHub token permissions are set correctly
4. Make sure your `build.py` script works on all platforms
5. For ARM64 builds, verify your dependencies support ARM architecture
6. For Universal macOS builds, verify your code is compatible with both Intel and Apple Silicon
7. For macOS builds, watch for framework symbolic link errors in the logs
8. For Linux builds, verify the correct system dependencies are installed (package names may change between Ubuntu versions) 