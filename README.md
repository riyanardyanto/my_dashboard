# My Dashboard

A modern dashboard GUI built with ttkbootstrap and Python.

## Features

- Modern UI with Bootstrap themes
- Sidebar navigation with functional views
- Home: Interactive dashboard with data visualizations from dh.csv
- Table: Interactive data table with search and pagination
- Reports: Text-based summary report generated from CSV data
- Settings: Configuration form
- Help: Support information
- Interactive table view with search and pagination
- CSV data import and display
- Responsive layout

## Installation

1. Ensure you have uv installed.
2. Install dependencies:
   ```
   uv sync
   ```

## Running the Application

Run the dashboard:

```
python main.py
```

Or using the virtual environment:

```
.venv/Scripts/python.exe main.py
```

## Usage

- Navigate through different views using the sidebar
- Home view displays interactive charts showing maintenance data insights
- Table view automatically loads data from dh.csv on startup
- Reports view shows a comprehensive text summary of maintenance data
- Use the table features for searching and pagination

## Requirements

- Python 3.14+
- ttkbootstrap
- pandas
- matplotlib
