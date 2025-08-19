"""
Custom field management for user-defined MiFIR fields.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum
import json

class CustomFieldCategory(Enum):
    REQUIRED = "required"
    CONDITIONAL = "conditional" 
    OPTIONAL = "optional"
    CONSTANT = "constant"

class CustomFieldType(Enum):
    STRING = "string"
    DECIMAL = "decimal"
    INTEGER = "integer"
    DATETIME = "datetime"
    BOOLEAN = "boolean"
    ENUM = "enum"

@dataclass
class CustomField:
    name: str
    xml_element_name: str
    field_type: CustomFieldType
    category: CustomFieldCategory
    description: str
    default_value: str = ""
    enum_values: Optional[List[str]] = None
    parent_element: str = "New"  # Where in XML to place this field
    notes: str = ""
    
    @property
    def is_required(self) -> bool:
        """Check if field is required based on category."""
        return self.category == CustomFieldCategory.REQUIRED
    
    @property
    def is_conditional(self) -> bool:
        """Check if field is conditional."""
        return self.category == CustomFieldCategory.CONDITIONAL
    
    @property
    def is_optional(self) -> bool:
        """Check if field is optional."""
        return self.category == CustomFieldCategory.OPTIONAL
    
    @property
    def is_constant(self) -> bool:
        """Check if field is a constant."""
        return self.category == CustomFieldCategory.CONSTANT

class CustomFieldManager:
    """Manages user-defined custom fields."""
    
    def __init__(self):
        self.custom_fields: List[CustomField] = []
    
    def add_custom_field(self, field: CustomField) -> bool:
        """Add a new custom field."""
        # Check if field name already exists
        if any(f.name == field.name for f in self.custom_fields):
            return False
        
        self.custom_fields.append(field)
        return True
    
    def remove_custom_field(self, field_name: str) -> bool:
        """Remove a custom field by name."""
        self.custom_fields = [f for f in self.custom_fields if f.name != field_name]
        return True
    
    def get_custom_field(self, field_name: str) -> Optional[CustomField]:
        """Get a custom field by name."""
        for field in self.custom_fields:
            if field.name == field_name:
                return field
        return None
    
    def get_all_custom_fields(self) -> List[CustomField]:
        """Get all custom fields."""
        return self.custom_fields.copy()
    
    def get_custom_fields_by_category(self, category: CustomFieldCategory) -> List[CustomField]:
        """Get custom fields by category."""
        return [f for f in self.custom_fields if f.category == category]
    
    def get_required_custom_fields(self) -> List[CustomField]:
        """Get required custom fields."""
        return self.get_custom_fields_by_category(CustomFieldCategory.REQUIRED)
    
    def get_conditional_custom_fields(self) -> List[CustomField]:
        """Get conditional custom fields."""
        return self.get_custom_fields_by_category(CustomFieldCategory.CONDITIONAL)
    
    def get_optional_custom_fields(self) -> List[CustomField]:
        """Get optional custom fields."""
        return self.get_custom_fields_by_category(CustomFieldCategory.OPTIONAL)
    
    def get_constant_custom_fields(self) -> List[CustomField]:
        """Get constant custom fields."""
        return self.get_custom_fields_by_category(CustomFieldCategory.CONSTANT)
    
    def validate_field_name(self, name: str) -> tuple[bool, str]:
        """Validate a custom field name."""
        if not name:
            return False, "Field name cannot be empty"
        
        if not name.replace('_', '').replace('-', '').isalnum():
            return False, "Field name can only contain letters, numbers, underscores, and hyphens"
        
        if any(f.name == name for f in self.custom_fields):
            return False, "Field name already exists"
        
        # Check against standard MiFIR field names
        from mifir_fields import MIFIR_FIELDS
        if any(f.name == name for f in MIFIR_FIELDS):
            return False, "Field name conflicts with standard MiFIR field"
        
        return True, "Valid field name"
    
    def validate_xml_element_name(self, name: str) -> tuple[bool, str]:
        """Validate XML element name."""
        if not name:
            return False, "XML element name cannot be empty"
        
        if not name[0].isalpha():
            return False, "XML element name must start with a letter"
        
        if not name.replace('_', '').replace('-', '').isalnum():
            return False, "XML element name can only contain letters, numbers, underscores, and hyphens"
        
        return True, "Valid XML element name"
    
    def export_custom_fields(self) -> str:
        """Export custom fields to JSON string."""
        fields_data = []
        for field in self.custom_fields:
            field_dict = {
                "name": field.name,
                "xml_element_name": field.xml_element_name,
                "field_type": field.field_type.value,
                "category": field.category.value,
                "description": field.description,
                "default_value": field.default_value,
                "enum_values": field.enum_values,
                "parent_element": field.parent_element,
                "notes": field.notes
            }
            fields_data.append(field_dict)
        
        return json.dumps(fields_data, indent=2)
    
    def import_custom_fields(self, json_str: str) -> tuple[bool, str]:
        """Import custom fields from JSON string."""
        try:
            fields_data = json.loads(json_str)
            imported_fields = []
            
            for field_dict in fields_data:
                field = CustomField(
                    name=field_dict["name"],
                    xml_element_name=field_dict["xml_element_name"],
                    field_type=CustomFieldType(field_dict["field_type"]),
                    category=CustomFieldCategory(field_dict.get("category", "optional")),
                    description=field_dict["description"],
                    default_value=field_dict.get("default_value", ""),
                    enum_values=field_dict.get("enum_values"),
                    parent_element=field_dict.get("parent_element", "New"),
                    notes=field_dict.get("notes", "")
                )
                imported_fields.append(field)
            
            # Replace current fields
            self.custom_fields = imported_fields
            return True, f"Successfully imported {len(imported_fields)} custom fields"
            
        except Exception as e:
            return False, f"Error importing custom fields: {str(e)}"
    
    def get_field_mapping_options(self, csv_columns: List[str]) -> Dict[str, List[str]]:
        """Get mapping options for custom fields."""
        options = {}
        base_options = ["None", "[Constant Value]"] + csv_columns
        
        for field in self.custom_fields:
            options[field.name] = base_options.copy()
        
        return options
    
    def validate_custom_field_values(self, field: CustomField, value: str) -> tuple[bool, str]:
        """Validate a value for a custom field."""
        if not value and field.is_required:
            return False, f"Required field '{field.name}' cannot be empty"
        
        if not value:
            return True, "Valid (empty value for optional field)"
        
        # Type-specific validation
        if field.field_type == CustomFieldType.DECIMAL:
            try:
                float(value)
                return True, "Valid decimal"
            except ValueError:
                return False, "Must be a valid decimal number"
        
        elif field.field_type == CustomFieldType.INTEGER:
            try:
                int(value)
                return True, "Valid integer"
            except ValueError:
                return False, "Must be a valid integer"
        
        elif field.field_type == CustomFieldType.BOOLEAN:
            if value.lower() in ['true', 'false', '1', '0', 'yes', 'no', 'y', 'n']:
                return True, "Valid boolean"
            else:
                return False, "Must be true/false, 1/0, yes/no, or y/n"
        
        elif field.field_type == CustomFieldType.ENUM:
            if field.enum_values and value not in field.enum_values:
                return False, f"Must be one of: {', '.join(field.enum_values)}"
            return True, "Valid enum value"
        
        elif field.field_type == CustomFieldType.DATETIME:
            # Basic datetime format check
            if 'T' in value and ('Z' in value or '+' in value or '-' in value[-6:]):
                return True, "Valid datetime format"
            else:
                return False, "Must be ISO 8601 format (e.g., 2025-08-19T08:22:23.294Z)"
        
        # STRING type - always valid
        return True, "Valid string"
