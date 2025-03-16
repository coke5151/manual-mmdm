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
- Windows x86 (32-bit): `manual-mmdm-v1.0.0-windows-x86.zip`

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
3. `build-windows-x86`: Builds the application for Windows 32-bit
4. `build-macos-x64`: Builds the application for macOS Intel
5. `build-macos-arm64`: Builds the application for macOS Apple Silicon
6. `build-macos-universal`: Builds the application as a Universal macOS binary
7. `build-linux-x64`: Builds the application for Linux 64-bit
8. `build-linux-arm64`: Builds the application for Linux ARM64

Each platform's build job includes:
- Installing Python 3.13
- Installing PDM
- Installing dependencies
- Running the build script
- Verifying the build output
- Creating a ZIP file
- Uploading to the release page

## Troubleshooting

If the workflow fails, check:
1. Make sure Python 3.13 is compatible with your application
2. Check the GitHub Actions logs for detailed error messages
3. Ensure GitHub token permissions are set correctly
4. Make sure your `build.py` script works on all platforms
5. For ARM64 builds, verify your dependencies support ARM architecture
6. For Universal macOS builds, verify your code is compatible with both Intel and Apple Silicon 