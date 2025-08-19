"""
Custom-Only XML Generator - Generates XML using only user-defined custom fields.
"""

import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom
from custom_fields import CustomField, CustomFieldManager, CustomFieldCategory

class CustomOnlyXMLGenerator:
    """Generates XML using only custom fields defined by the user."""
    
    def __init__(self):
        self.namespaces = {
            "": "urn:iso:std:iso:20022:tech:xsd:head.003.001.01",
            "head": "urn:iso:std:iso:20022:tech:xsd:head.001.001.01", 
            "auth": "urn:iso:std:iso:20022:tech:xsd:auth.016.001.01",
            "xsi": "http://www.w3.org/2001/XMLSchema-instance"
        }
    
    def generate_custom_xml(self, df: pd.DataFrame, field_mappings: Dict[str, str], 
                           constants: Dict[str, str], custom_field_manager: CustomFieldManager) -> str:
        """Generate XML using only custom fields."""
        if constants is None:
            constants = {}
        
        # Create root element with namespaces
        root = Element("BizData")
        root.set("xmlns", self.namespaces[""])
        root.set("xmlns:xsi", self.namespaces["xsi"])
        root.set("xsi:schemaLocation", "urn:iso:std:iso:20022:tech:xsd:head.003.001.01 head.003.001.01.xsd")
        
        # Add header
        self._add_header(root, constants)
        
        # Add payload
        payload = SubElement(root, "Pyld")
        document = SubElement(payload, "Document")
        document.set("xmlns", self.namespaces["auth"])
        document.set("xmlns:xsi", self.namespaces["xsi"])
        document.set("xsi:schemaLocation", "urn:iso:std:iso:20022:tech:xsd:auth.016.001.01 auth.016.001.01_ESMAUG_Reporting_1.1.0.xsd")
        
        # Add financial instrument reporting
        fin_instrm_rptg = SubElement(document, "FinInstrmRptgTxRpt")
        
        # Add transactions (one per row) with only custom fields
        for index, row in df.iterrows():
            self._add_custom_transaction(fin_instrm_rptg, row, field_mappings, constants, custom_field_manager)
        
        # Convert to pretty-printed string
        rough_string = tostring(root, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        pretty_xml = reparsed.toprettyxml(indent="  ")
        
        # Remove empty lines and fix encoding declaration
        lines = [line for line in pretty_xml.split('\n') if line.strip()]
        lines[0] = '<?xml version="1.0" encoding="UTF-8"?>'
        
        return '\n'.join(lines)
    
    def _add_header(self, root: Element, constants: Dict[str, str]):
        """Add ISO 20022 header section."""
        hdr = SubElement(root, "Hdr")
        app_hdr = SubElement(hdr, "AppHdr")
        app_hdr.set("xmlns", self.namespaces["head"])
        app_hdr.set("xmlns:xsi", self.namespaces["xsi"])
        app_hdr.set("xsi:schemaLocation", "urn:iso:std:iso:20022:tech:xsd:head.001.001.01 head.001.001.01_ESMAUG_1.0.0.xsd")
        
        # From organization
        fr = SubElement(app_hdr, "Fr")
        fr_org_id = SubElement(fr, "OrgId")
        fr_id = SubElement(fr_org_id, "Id")
        fr_org_id_inner = SubElement(fr_id, "OrgId")
        fr_othr = SubElement(fr_org_id_inner, "Othr")
        fr_id_val = SubElement(fr_othr, "Id")
        fr_id_val.text = constants.get("from_org_id", "CUSTOM")
        
        # To organization
        to = SubElement(app_hdr, "To")
        to_org_id = SubElement(to, "OrgId")
        to_id = SubElement(to_org_id, "Id")
        to_org_id_inner = SubElement(to_id, "OrgId")
        to_othr = SubElement(to_org_id_inner, "Othr")
        to_id_val = SubElement(to_othr, "Id")
        to_id_val.text = constants.get("to_org_id", "CUSTOM")
        
        # Business message identifier
        biz_msg_idr = SubElement(app_hdr, "BizMsgIdr")
        biz_msg_idr.text = constants.get("biz_msg_id", f"CUSTOM_FIELDS_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        
        # Message definition identifier
        msg_def_idr = SubElement(app_hdr, "MsgDefIdr")
        msg_def_idr.text = "auth.016.001.01"  # Fixed for MiFIR
        
        # Creation date
        cre_dt = SubElement(app_hdr, "CreDt")
        cre_dt.text = constants.get("creation_date", datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'))
    
    def _add_custom_transaction(self, parent: Element, row: pd.Series, field_mappings: Dict[str, str], 
                               constants: Dict[str, str], custom_field_manager: CustomFieldManager):
        """Add a transaction using only custom fields."""
        tx = SubElement(parent, "Tx")
        new = SubElement(tx, "New")
        
        # Get all custom fields organized by category
        required_fields = custom_field_manager.get_required_custom_fields()
        conditional_fields = custom_field_manager.get_conditional_custom_fields()
        optional_fields = custom_field_manager.get_optional_custom_fields()
        constant_fields = custom_field_manager.get_constant_custom_fields()
        
        # Add fields in order: Required -> Conditional -> Optional -> Constants
        all_custom_fields = required_fields + conditional_fields + optional_fields + constant_fields
        
        for custom_field in all_custom_fields:
            self._add_single_custom_field(new, custom_field, row, field_mappings, constants)
    
    def _add_single_custom_field(self, parent: Element, custom_field: CustomField, row: pd.Series, 
                                field_mappings: Dict[str, str], constants: Dict[str, str]):
        """Add a single custom field to the XML."""
        # Get the value for this custom field
        value = ""
        
        if custom_field.name in field_mappings:
            mapping = field_mappings[custom_field.name]
            
            if mapping == "[Constant Value]":
                # Use constant value
                value = constants.get(custom_field.name, custom_field.default_value)
            elif mapping and mapping != "None":
                # Use CSV column value
                value = self._get_csv_value(row, mapping)
            else:
                # Use default value
                value = custom_field.default_value
        else:
            # Use default value
            value = custom_field.default_value
        
        # Add to XML if we have a value or if it's required
        if value or custom_field.is_required:
            # Determine parent element
            if custom_field.parent_element == "New":
                target_parent = parent
            else:
                # For now, just use the New element
                # In future, could support nested structures
                target_parent = parent
            
            # Create the XML element
            custom_element = SubElement(target_parent, custom_field.xml_element_name)
            custom_element.text = value if value else custom_field.default_value
            
            # Add category as comment (for debugging)
            if custom_field.category == CustomFieldCategory.REQUIRED:
                custom_element.set("data-category", "required")
            elif custom_field.category == CustomFieldCategory.CONDITIONAL:
                custom_element.set("data-category", "conditional")
            elif custom_field.category == CustomFieldCategory.OPTIONAL:
                custom_element.set("data-category", "optional")
            elif custom_field.category == CustomFieldCategory.CONSTANT:
                custom_element.set("data-category", "constant")
    
    def _get_csv_value(self, row: pd.Series, column_name: str) -> str:
        """Get value from CSV row, handling column names with spaces."""
        # Try exact match first
        if column_name in row.index:
            value = row[column_name]
            return str(value).strip() if pd.notna(value) else ""
        
        # Try to find column with stripped name
        for col in row.index:
            if col.strip() == column_name:
                value = row[col]
                return str(value).strip() if pd.notna(value) else ""
        
        return ""
