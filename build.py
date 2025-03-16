import glob
import os
import shutil
import sys

import PyInstaller.__main__


def build():
    # Clean up dist and build directories
    for dir_name in ["dist", "build"]:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name, ignore_errors=True)

    # Get absolute paths
    base_dir = os.path.abspath(os.path.dirname(__file__))
    static_dir = os.path.join(base_dir, "static")

    # Create spec file first for better control
    spec_file = "manual-mmdm.spec"

    # Determine the appropriate path separator based on the platform
    separator = ";" if sys.platform.startswith("win") else ":"

    # Basic PyInstaller arguments
    args = [
        "src/main.py",
        f"--specpath={base_dir}",
        "--name=manual-mmdm",
        "--noconsole",
        "--clean",
        "-y",  # Auto-confirm removal of output directory
        # Add hidden imports for PyQt6
        "--hidden-import=PyQt6.QtCore",
        "--hidden-import=PyQt6.QtGui",
        "--hidden-import=PyQt6.QtWidgets",
        "--hidden-import=PyQt6.sip",
        # Add SQLAlchemy related imports
        "--hidden-import=sqlalchemy.sql.default_comparator",
        "--hidden-import=sqlalchemy.ext.baked",
        # Collect all Qt plugins
        "--collect-all=PyQt6",
        # Output to spec file
        f"--specpath={base_dir}",
    ]

    # Add data files - specify static folder explicitly
    data_args = [
        f"--add-data={static_dir}{separator}static",
    ]

    if os.path.exists(".venv/Lib/site-packages/PyQt6/Qt6/plugins"):
        data_args.append(f"--add-data=.venv/Lib/site-packages/PyQt6/Qt6/plugins{separator}PyQt6/Qt6/plugins")

    # Add icon if it exists
    icon_path = os.path.join(static_dir, "mmdm-icon.png")
    if os.path.exists(icon_path):
        data_args.append(f"--icon={icon_path}")

    # Combine arguments
    args.extend(data_args)

    # First generate spec file
    print("Generating spec file...")
    PyInstaller.__main__.run(args)

    # Run the build using the spec file
    print("Building from spec file...")
    PyInstaller.__main__.run(["--clean", "-y", spec_file])

    # Post-process: manually copy static folder if needed
    dist_dir = os.path.join(base_dir, "dist", "manual-mmdm")
    dist_static_dir = os.path.join(dist_dir, "static")

    if not os.path.exists(dist_static_dir):
        print("Static folder not found in dist, manually copying...")
        os.makedirs(dist_static_dir, exist_ok=True)
        for file in glob.glob(os.path.join(static_dir, "*")):
            if os.path.isfile(file):
                print(f"Copying {file} to {dist_static_dir}")
                shutil.copy2(file, dist_static_dir)

    # Verify the static folder was copied
    if os.path.exists(dist_static_dir) and len(os.listdir(dist_static_dir)) > 0:
        print("Static folder successfully copied to dist")
    else:
        print("Warning: Static folder may not have been copied correctly")

    print("Build completed! Output can be found in the dist directory.")


if __name__ == "__main__":
    build()
