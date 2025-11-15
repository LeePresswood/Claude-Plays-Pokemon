"""
Setup script for Claude Plays Pokemon
Creates virtual environment and installs dependencies
"""
import subprocess
import sys
import os
from pathlib import Path


def main():
    """Setup the project with virtual environment"""
    project_dir = Path(__file__).parent
    venv_dir = project_dir / "venv"

    # Check if virtual environment already exists
    if venv_dir.exists():
        print(f"Virtual environment already exists. Skipping creation.")
        skip_venv_creation = True
    else:
        skip_venv_creation = False

    # Create virtual environment
    if not skip_venv_creation:
        print("Creating virtual environment...")
        try:
            subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)
            print("✓ Created venv")
        except subprocess.CalledProcessError as e:
            print(f"Failed to create virtual environment: {e}")
            return 1

    # Determine pip path based on OS
    if os.name == 'nt':  # Windows
        pip_path = venv_dir / "Scripts" / "pip.exe"
        activate_cmd = f".\\venv\\Scripts\\activate"
    else:  # Unix-like
        pip_path = venv_dir / "bin" / "pip"
        activate_cmd = "source venv/bin/activate"

    # Install dependencies
    print("Installing dependencies...")
    try:
        subprocess.run(
            [str(pip_path), "install", "-r", "requirements.txt"],
            check=True,
            cwd=project_dir
        )
        print("✓ Installed dependencies")
    except subprocess.CalledProcessError as e:
        print(f"Failed to install dependencies: {e}")
        return 1

    # Create .env file if it doesn't exist
    env_file = project_dir / ".env"
    env_example = project_dir / ".env.example"

    if not env_file.exists() and env_example.exists():
        print("\nCreating .env file from template...")
        import shutil
        shutil.copy(env_example, env_file)
        print("✓ Created .env file")
        print("  → Edit .env and add your ANTHROPIC_API_KEY")
    elif env_file.exists():
        print("\n.env file already exists")
    else:
        print("\nWarning: .env.example not found, skipping .env creation")

    # Success message
    print("\nSetup complete!")
    print(f"\nNext steps:")
    print(f"1. Activate: {activate_cmd}")
    print(f"2. Edit .env and add your API key")
    print(f"3. Test: python test_setup.py")

    return 0


if __name__ == "__main__":
    sys.exit(main())
