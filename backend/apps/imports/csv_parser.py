"""
CSV Parser for expense imports.

Parses uploaded CSV files into row dicts for anomaly detection.
The original file is NEVER modified.
"""

import csv
import io
from typing import List, Dict, Any, Tuple


EXPECTED_COLUMNS = {
    "title", "amount", "currency", "paid_by", "expense_date",
    "description", "split_type", "splits", "notes", "category",
}

REQUIRED_COLUMNS = {"title", "amount", "paid_by", "expense_date"}


def parse_csv(file_content: bytes) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Parse CSV bytes into a list of row dicts.

    Returns:
        (rows, warnings)
        - rows: list of {field: value} dicts, one per data row
        - warnings: list of structural warnings about the file itself
    """
    warnings = []
    rows = []

    try:
        text = file_content.decode("utf-8-sig")  # Handle BOM
    except UnicodeDecodeError:
        try:
            text = file_content.decode("latin-1")
            warnings.append("File encoding detected as Latin-1 (not UTF-8). Non-ASCII characters may be misread.")
        except UnicodeDecodeError:
            return [], ["Could not decode file. Please save as UTF-8."]

    reader = csv.DictReader(io.StringIO(text))

    if reader.fieldnames is None:
        return [], ["CSV file appears to be empty or has no headers."]

    # Normalize column names
    fieldnames = [f.strip().lower().replace(" ", "_") for f in reader.fieldnames if f is not None]
    
    # Map column aliases for validation
    mapped_fields = set(fieldnames)
    if "date" in mapped_fields:
        mapped_fields.add("expense_date")
    if "description" in mapped_fields:
        mapped_fields.add("title")

    missing_required = REQUIRED_COLUMNS - mapped_fields
    if missing_required:
        warnings.append(
            f"Missing required columns: {', '.join(sorted(missing_required))}. "
            "These fields are mandatory for import."
        )

    unknown_cols = set(fieldnames) - EXPECTED_COLUMNS - {"date", "description"}
    if unknown_cols:
        warnings.append(f"Unknown columns will be ignored: {', '.join(sorted(unknown_cols))}")

    for i, row in enumerate(reader):
        # Normalize keys
        normalized_row = {
            k.strip().lower().replace(" ", "_"): (v.strip() if v else "")
            for k, v in row.items() if k is not None
        }
        
        # Apply aliases
        if "date" in normalized_row and "expense_date" not in normalized_row:
            normalized_row["expense_date"] = normalized_row["date"]
        if "description" in normalized_row and "title" not in normalized_row:
            normalized_row["title"] = normalized_row["description"]
            
        normalized_row["_row_number"] = i + 1
        rows.append(normalized_row)

    if not rows:
        warnings.append("CSV file contains headers but no data rows.")

    return rows, warnings
