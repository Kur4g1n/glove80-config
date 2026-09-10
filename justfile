set positional-arguments

# List available commands.
default:
    @just --list

# Install missing tools and prepare Docker/Colima and the pinned Nix toolchain.
setup:
    bash scripts/setup.sh

# Check local tools, Docker and pinned firmware inputs.
doctor:
    python3 scripts/tasks.py doctor

# Generate firmware, MoErgo JSON and the interactive diagram from the source.
generate:
    python3 scripts/layout.py generate

# Import an edited MoErgo JSON export, validate it, and regenerate outputs.
import-layout file:
    python3 scripts/layout.py import "$1"

# Check generated files and run layout and immediate-input tests.
check:
    python3 scripts/tasks.py check

# Build both halves; choose a palette or comma-separated palettes in cycle order.
build theme="macchiato":
    python3 scripts/tasks.py build --theme "$1"

# Build English/Statica firmware for the device-specific host setup.
build-bilingual theme="macchiato":
    python3 scripts/tasks.py build --theme "$1" --profile bilingual

# Install host files for this OS; on Windows, supply the prepared AHI v2 folder.
install directory="":
    python3 scripts/tasks.py install --directory "$1"

# Serve only the interactive diagram on localhost.
docs port="8000":
    python3 scripts/tasks.py docs --port "$1"

# Flash the combined firmware to an explicitly selected bootloader volume.
flash mount:
    python3 scripts/tasks.py flash "$1"

# Validate firmware and open Finder before the keyboard stops typing in boot mode.
flash-ready:
    python3 scripts/tasks.py flash-ready

# Validate the firmware and destination without copying anything.
flash-dry-run mount:
    python3 scripts/tasks.py flash --dry-run "$1"
