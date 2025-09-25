from .pretrip_config import REQUIRED_COLUMNS, ALL_VALID_COLUMNS

def validate_csv_headers(headers_from_csv):
    """
    Validates the headers from a CSV file against the defined schema.

    Args:
        headers_from_csv: A list of column names from the CSV header row.

    Returns:
        A tuple containing:
        - A boolean indicating if the headers are valid.
        - A message detailing the result.
    """
    incoming_headers_set = set(headers_from_csv)

    # 1. Check for missing required columns
    missing_required = []
    for required_col in REQUIRED_COLUMNS:
        if required_col not in incoming_headers_set:
            missing_required.append(required_col)

    if missing_required:
        # Sort for consistent error messages
        missing_required.sort()
        return False, f"Validation failed. Missing required columns: {', '.join(missing_required)}"

    # 2. Check for unknown columns that are not in any of our defined sets
    unknown_columns = []
    for incoming_col in incoming_headers_set:
        if incoming_col not in ALL_VALID_COLUMNS:
            unknown_columns.append(incoming_col)

    if unknown_columns:
        unknown_columns.sort()
        return False, f"Validation failed. Unknown columns found: {', '.join(unknown_columns)}"

    return True, "CSV headers are valid."