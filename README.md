# LLM Export UI 

A simple GUI application that allows you to select specific files and folders for export in an LLM-friendly format, similar to Gitingest. The application remembers your selections between sessions.

## Features

- Browse and select files/folders via a tree view interface
- Filter files by extension patterns (e.g., `*.py, *.md`)
- Remember selections for multiple folders
- Export selected content in LLM-friendly format

## Requirements

- Python 3.7+
- PyQt6

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/LeanSight/llmexportui
   cd llexportui
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```


## Usage

### Running the Application

```
python llmexportui.py
```

You can also specify a folder to open automatically:

```
python llmexportui.py /path/to/folder
```

### Basic Workflow

1. Click **Open Folder** to select a directory
2. Use checkboxes to select files/folders for export
   - When you check a folder, all its children will be automatically selected
3. Use the filter field to show only specific extensions (e.g., `*.py, *.md`)
4. Click **Export** to save the contents in LLM-friendly format

### Building an Executable

For a standard executable:
```
python -m PyInstaller --onefile --windowed llmexportui.py
```


## Output Format

The exported file follows this format:

```
Directory structure:
└── ProjectName/
    ├── file1.txt
    └── folder1/
        └── file2.py

================================================
File: file1.txt
================================================
Content of file1.txt

================================================
File: folder1/file2.py
================================================
Content of file2.py
```

This format is optimized for use with Large Language Models.
