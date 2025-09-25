"""
This file defines the expected schema for CSV files used to create pretrip blueprints.
It serves as a single source of truth for validation and data mapping.
"""

# These are the columns we absolutely require in the CSV.
REQUIRED_COLUMNS = {
    'equipment',
    'section',
    'inspection_item',
    'pass_fail',
    'numeric_required',
    'date_required'
}

# These are columns that are optional.
OPTIONAL_COLUMNS = {
    'details',
    'notes'
}

# These are columns we know about but will ignore during blueprint creation.
# They typically contain result data, not definition data.
IGNORED_COLUMNS = {
    'numeric',
    'date'
}

# A set of all columns that are considered valid.
ALL_VALID_COLUMNS = REQUIRED_COLUMNS | OPTIONAL_COLUMNS | IGNORED_COLUMNS

# This maps the CSV column names to the Blueprint/BlueprintItem model attributes.
# The format is: 'csv_column_name': ('ModelName', 'model_attribute_name')
COLUMN_MAPPING = {
    'equipment': ('Blueprint', 'equipment_type'),
    'section': ('BlueprintItem', 'section'),
    'inspection_item': ('BlueprintItem', 'name'),
    'details': ('BlueprintItem', 'details'),
    'notes': ('BlueprintItem', 'notes'),
    'pass_fail': ('BlueprintItem', 'boolean_field_required'),
    'numeric_required': ('BlueprintItem', 'numeric_field_required'),
    'date_required': ('BlueprintItem', 'date_field_required'),
}
