set positional-arguments

default:
    @just --list

# Install build tools with Homebrew and start Colima.
setup:
    bash scripts/setup.sh

# Regenerate config/glove80.keymap, host/Glove80.bundle and docs/layout-data.js from config/.
generate:
    python3 scripts/glove80.py generate

# Validate config/, generated files and run the tests.
check:
    python3 scripts/glove80.py check
    python3 -m unittest discover -s tests

# Build build/glove80.uf2 (both halves) for a Catppuccin flavor: latte, frappe, macchiato, mocha.
build flavor="macchiato":
    bash scripts/build.sh "$1"

# Install the Russian input source and the Karabiner rule (log out and back in afterwards).
install:
    mkdir -p ~/Library/"Keyboard Layouts" ~/.config/karabiner/assets/complex_modifications
    rm -rf ~/Library/"Keyboard Layouts"/Glove80.bundle
    cp -R host/Glove80.bundle ~/Library/"Keyboard Layouts"/
    cp host/glove80.json ~/.config/karabiner/assets/complex_modifications/

# Copy build/glove80.uf2 to the mounted Glove80 bootloader volume.
flash:
    bash scripts/flash.sh

# Open the firmware folder and /Volumes in Finder for flashing with the mouse.
flash-ready:
    open build /Volumes

# Serve the interactive layout diagram.
docs port="8000":
    python3 -m http.server "$1" --bind 127.0.0.1 --directory docs
