# WTG Toolbox Tools

This folder contains the tool modules that the main application loads dynamically.

## Structure

- `tools/`
  - `scripts/`
  - `network/`
  - `system/`
  - `utilities/`

Each module in a category folder exposes the following items:

- `TOOL_NAME` — the display name shown in the app
- `TOOL_DESCRIPTION` — a short description shown in the app
- `run()` — the function executed when the user clicks RUN

## Adding a new tool

1. Create a new Python module in the appropriate category folder.
2. Define `TOOL_NAME`, `TOOL_DESCRIPTION`, and a callable `run()`.
3. Save the file.
4. Run the app again; the tool will appear automatically.
