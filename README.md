<div align="center">

# Manual-MMDM
A desktop application for managing Minecraft mods and their dependencies with a user-friendly interface.

![Manual-MMDM banner](static/Manual-MMDM-banner.png)

</div>


## Features

- Manage Minecraft mods with an intuitive GUI
- Track mod dependencies and prevent deletion of mods that others depend on
- Organize mods by categories
- Track mod requirements (client/server-side)
- Mark translated mods
- Search and filter mods
- Expandable/collapsible dependency view
- Automatic file management

## Installation

### Pre-built Binaries

We provide pre-built binaries for multiple platforms. Visit the [Releases](https://github.com/coke5151/manual-mmdm/releases) page to download the version for your platform:

#### Windows
- Windows x64 (64-bit)

#### macOS
- macOS Universal (Intel & Apple Silicon)
- macOS x64 (Intel only)
- macOS arm64 (Apple Silicon only)

#### Linux
- Linux x64 (64-bit)
- Linux arm64 (ARM 64-bit)

Simply download the appropriate ZIP file for your platform, extract it, and run the executable.

### Building from Source

If you prefer to build from source, follow these steps:

#### Requirements

- Python 3.13+
- PyQt6
- SQLAlchemy
- PDM (Python package manager)

#### Steps

1. Clone the repository:
```bash
git clone https://github.com/coke5151/manual-mmdm.git
cd manual-mmdm
```

2. Install dependencies using PDM:
```bash
pdm install
```

3. Run the application:
```bash
pdm run main
```

## Usage

### Basic Operations

- **Add Mod**: Click "Add Module" button or use File menu
- **Edit Mod**: Double-click a mod or use the Edit button
- **Delete Mod**: Select a mod and click Delete button
- **Manage Categories**: Use the Manage Categories button
- **Search**: Use the search bar to filter mods
- **View Dependencies**: Toggle the "Expand Dependencies" button

## Project Structure

- `src/main.py`: Main application and GUI implementation
- `src/models.py`: Database models and relationships
- `src/database.py`: Database configuration

## Contributing

### Releasing New Versions

When releasing a new version:

1. Create and push a tag in the format `v*` (e.g., `v1.0.0`):
```bash
git tag v1.0.0
git push origin v1.0.0
```

This will trigger the automatic build process for all supported platforms.

## Platform Support Notes

### Windows
Currently, only 64-bit Windows (x64) is supported with Python 3.13 due to PyQt6 compatibility limitations with 32-bit platforms.

### macOS
All macOS variants are supported:
- Universal builds work on both Intel and Apple Silicon Macs
- Architecture-specific builds are available if needed

### Linux
Both x64 and ARM64 builds are supported through the Docker-based build system.

## License

See the [LICENSE](LICENSE) file for details.
