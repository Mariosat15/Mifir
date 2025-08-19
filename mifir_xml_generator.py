"""
MiFIR RTS 22 XML Generator - Generates proper auth.016.001.01 XML
"""

import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom
from mifir_fields import MiFIRField, get_field_by_name
from custom_fields import CustomField, CustomFieldManager

class MiFIRXMLGenerator:
    """Generates MiFIR RTS 22 compliant XML."""
    
    def __init__(self):
        self.namespaces = {
            "": "urn:iso:std:iso:20022:tech:xsd:head.003.001.01",
            "head": "urn:iso:std:iso:20022:tech:xsd:head.001.001.01", 
            "auth": "urn:iso:std:iso:20022:tech:xsd:auth.016.001.01",
            "xsi": "http://www.w3.org/2001/XMLSchema-instance"
        }
    
    def generate_xml(self, df: pd.DataFrame, field_mappings: Dict[str, str], 
                    constants: Dict[str, str] = None, custom_field_manager: CustomFieldManager = None) -> str:
        """Generate MiFIR compliant XML from DataFrame and field mappings."""
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
        
        # Add transactions (one per row)
        for index, row in df.iterrows():
            self._add_mifir_transaction(fin_instrm_rptg, row, field_mappings, constants, custom_field_manager)
        
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
        fr_id_val.text = constants.get("from_org_id", "KD")
        
        # To organization
        to = SubElement(app_hdr, "To")
        to_org_id = SubElement(to, "OrgId")
        to_id = SubElement(to_org_id, "Id")
        to_org_id_inner = SubElement(to_id, "OrgId")
        to_othr = SubElement(to_org_id_inner, "Othr")
        to_id_val = SubElement(to_othr, "Id")
        to_id_val.text = constants.get("to_org_id", "CY")
        
        # Business message identifier
        biz_msg_idr = SubElement(app_hdr, "BizMsgIdr")
        biz_msg_idr.text = constants.get("biz_msg_id", f"KD_DATTRA_generated_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        
        # Message definition identifier
        msg_def_idr = SubElement(app_hdr, "MsgDefIdr")
        msg_def_idr.text = "auth.016.001.01"  # Fixed for MiFIR
        
        # Creation date
        cre_dt = SubElement(app_hdr, "CreDt")
        cre_dt.text = constants.get("creation_date", datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'))
    
    def _add_mifir_transaction(self, parent: Element, row: pd.Series, field_mappings: Dict[str, str], 
                              constants: Dict[str, str], custom_field_manager: CustomFieldManager = None):
        """Add a single MiFIR compliant transaction."""
        tx = SubElement(parent, "Tx")
        new = SubElement(tx, "New")
        
        # A) Reporting/Envelope Fields
        # Reporting Party (always include, use default if not mapped)
        rptg_pty = SubElement(new, "RptgPrty")
        lei = SubElement(rptg_pty, "LEI")
        if self._has_mapping("reporting_party_lei", field_mappings):
            lei.text = self._get_mapped_value("reporting_party_lei", row, field_mappings, constants)
        else:
            lei.text = constants.get("reporting_party_lei", "YOUR_FIRM_LEI_HERE")
        
        # Technical Record ID (auto-generate if not provided)
        tech_rcrd_id = SubElement(new, "TechRcrdId")
        if self._has_mapping("tech_record_id", field_mappings):
            tech_rcrd_id.text = self._get_mapped_value("tech_record_id", row, field_mappings, constants)
        else:
            # Auto-generate unique tech record ID
            tech_rcrd_id.text = f"TXN_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(str(row.to_dict())) % 10000}"
        
        # Transaction ID (always include, auto-generate if not mapped)
        tx_id = SubElement(new, "TxId")
        if self._has_mapping("transaction_id", field_mappings):
            tx_id.text = self._get_mapped_value("transaction_id", row, field_mappings, constants)
        else:
            # Auto-generate transaction ID
            tx_id.text = f"AUTO_TXN_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(str(row.to_dict())) % 10000}"
        
        # Financial Instrument
        self._add_financial_instrument(new, row, field_mappings, constants)
        
        # C) Execution details
        # Execution Date Time (always include, use current time if not mapped)
        exctn_dt_tm = SubElement(new, "ExctnDtTm")
        if self._has_mapping("execution_datetime", field_mappings):
            exctn_dt_tm.text = self._format_datetime(
                self._get_mapped_value("execution_datetime", row, field_mappings, constants)
            )
        else:
            exctn_dt_tm.text = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        
        # Trade Date Time (always include, use execution time if not mapped)
        trad_dt_tm = SubElement(new, "TradDtTm")
        if self._has_mapping("trade_datetime", field_mappings):
            trad_dt_tm.text = self._format_datetime(
                self._get_mapped_value("trade_datetime", row, field_mappings, constants)
            )
        else:
            trad_dt_tm.text = exctn_dt_tm.text  # Use same as execution time
        
        # Settlement Date
        if self._has_mapping("settlement_date", field_mappings):
            sttlm_dt = SubElement(new, "SttlmDt")
            sttlm_dt.text = self._get_mapped_value("settlement_date", row, field_mappings, constants)
        
        # Trading Venue
        trad_vn = SubElement(new, "TradgVn")
        mic = SubElement(trad_vn, "MIC")
        if self._has_mapping("trading_venue", field_mappings):
            mic.text = self._get_mapped_value("trading_venue", row, field_mappings, constants)
        else:
            mic.text = "XOFF"  # Default: OTC/off-venue for crypto exchanges
        
        # Trading Capacity
        trad_cpcty = SubElement(new, "TradgCpcty")
        if self._has_mapping("trading_capacity", field_mappings):
            trad_cpcty.text = self._get_mapped_value("trading_capacity", row, field_mappings, constants)
        else:
            trad_cpcty.text = "PRIN"  # Default: Principal
        
        # Price (always include, use default if not mapped)
        self._add_price(new, row, field_mappings, constants)
        
        # Quantity (always include, use default if not mapped)
        qty = SubElement(new, "Qty")
        if self._has_mapping("quantity", field_mappings):
            qty.text = self._get_mapped_value("quantity", row, field_mappings, constants)
        else:
            qty.text = "1.0"  # Default quantity
        
        # Buyer
        self._add_buyer(new, row, field_mappings, constants)
        
        # Seller
        self._add_seller(new, row, field_mappings, constants)
        
        # F) Flags & indicators (provide defaults for crypto derivatives)
        # Short Sale Indicator
        shrt_sellg_ind = SubElement(new, "ShrtSellgInd")
        if self._has_mapping("short_sale_indicator", field_mappings):
            shrt_sellg_ind.text = self._get_mapped_value("short_sale_indicator", row, field_mappings, constants)
        else:
            shrt_sellg_ind.text = "NSHO"  # Default: Not a short sale (N/A for crypto derivatives)
        
        # Commodity Derivative Indicator
        cmmdty_deriv_ind = SubElement(new, "CmmdtyDerivInd")
        if self._has_mapping("commodity_derivative_indicator", field_mappings):
            cmmdty_deriv_ind.text = self._get_mapped_value("commodity_derivative_indicator", row, field_mappings, constants)
        else:
            cmmdty_deriv_ind.text = "N"  # Default: Not a commodity derivative
        
        # Clearing Indicator
        clrng_ind = SubElement(new, "ClrngInd")
        if self._has_mapping("clearing_indicator", field_mappings):
            clrng_ind.text = self._get_mapped_value("clearing_indicator", row, field_mappings, constants)
        else:
            clrng_ind.text = "N"  # Default: Not cleared
        
        # Securities Financing Indicator
        scties_fincg_tx_ind = SubElement(new, "SctiesFincgTxInd")
        if self._has_mapping("securities_financing_indicator", field_mappings):
            scties_fincg_tx_ind.text = self._get_mapped_value("securities_financing_indicator", row, field_mappings, constants)
        else:
            scties_fincg_tx_ind.text = "N"  # Default: Not SFT
        
        # G) Firm/branch context
        if self._has_mapping("country_of_branch", field_mappings):
            ctry_of_brnch = SubElement(new, "CtryOfBrnch")
            ctry_of_brnch.text = self._get_mapped_value("country_of_branch", row, field_mappings, constants)
        
        if self._has_mapping("investment_firm_covered", field_mappings):
            invstmt_firm_cvrd = SubElement(new, "InvstmtFirmCvrd")
            invstmt_firm_cvrd.text = self._get_mapped_value("investment_firm_covered", row, field_mappings, constants)
        
        # Add custom fields
        if custom_field_manager:
            self._add_custom_fields(new, row, field_mappings, constants, custom_field_manager)
    
    def _add_financial_instrument(self, parent: Element, row: pd.Series, field_mappings: Dict[str, str], 
                                 constants: Dict[str, str]):
        """Add financial instrument identification."""
        # Financial Instrument (always include, use default if not mapped)
        fin_instrm_id = SubElement(parent, "FinInstrmId")
        id_elem = SubElement(fin_instrm_id, "Id")
        isin = SubElement(id_elem, "ISIN")
        
        if self._has_mapping("instrument_isin", field_mappings):
            isin.text = self._get_mapped_value("instrument_isin", row, field_mappings, constants)
        else:
            isin.text = constants.get("instrument_isin", "SAMPLE_ISIN_123456789012")
        
        # CFI code (provide default if not mapped)
        cfi = SubElement(fin_instrm_id, "CFI")
        if self._has_mapping("instrument_cfi", field_mappings):
            cfi.text = self._get_mapped_value("instrument_cfi", row, field_mappings, constants)
        else:
            cfi.text = "FXXXXX"  # Default CFI code
    
    def _add_price(self, parent: Element, row: pd.Series, field_mappings: Dict[str, str], 
                   constants: Dict[str, str]):
        """Add price information."""
        # Price (always include, use default if not mapped)
        pric = SubElement(parent, "Pric")
        amt = SubElement(pric, "Amt")
        
        if self._has_mapping("price_amount", field_mappings):
            amt.text = self._get_mapped_value("price_amount", row, field_mappings, constants)
        else:
            amt.text = "100.00"  # Default price
        
        # Currency attribute
        if self._has_mapping("price_currency", field_mappings):
            amt.set("Ccy", self._get_mapped_value("price_currency", row, field_mappings, constants))
        else:
            amt.set("Ccy", "USD")  # Default currency for crypto derivatives
    
    def _add_buyer(self, parent: Element, row: pd.Series, field_mappings: Dict[str, str], 
                   constants: Dict[str, str]):
        """Add buyer information."""
        # Determine if we have buyer information
        has_buyer_lei = self._has_mapping("buyer_lei", field_mappings)
        has_buyer_person = (self._has_mapping("buyer_first_name", field_mappings) or 
                           self._has_mapping("buyer_national_id", field_mappings))
        
        if has_buyer_lei or has_buyer_person:
            buyr = SubElement(parent, "Buyr")
            acct_ownr = SubElement(buyr, "AcctOwnr")
            id_elem = SubElement(acct_ownr, "Id")
            
            if has_buyer_lei:
                # Legal entity
                org = SubElement(id_elem, "Org")
                lei = SubElement(org, "LEI")
                lei.text = self._get_mapped_value("buyer_lei", row, field_mappings, constants)
            elif has_buyer_person:
                # Natural person
                prsn = SubElement(id_elem, "Prsn")
                
                if self._has_mapping("buyer_first_name", field_mappings):
                    frst_nm = SubElement(prsn, "FrstNm")
                    frst_nm.text = self._get_mapped_value("buyer_first_name", row, field_mappings, constants)
                
                if self._has_mapping("buyer_last_name", field_mappings):
                    nm = SubElement(prsn, "Nm")
                    nm.text = self._get_mapped_value("buyer_last_name", row, field_mappings, constants)
                
                if self._has_mapping("buyer_birth_date", field_mappings):
                    birth_dt = SubElement(prsn, "BirthDt")
                    birth_dt.text = self._get_mapped_value("buyer_birth_date", row, field_mappings, constants)
                
                if self._has_mapping("buyer_national_id", field_mappings):
                    othr = SubElement(prsn, "Othr")
                    id_val = SubElement(othr, "Id")
                    id_val.text = self._get_mapped_value("buyer_national_id", row, field_mappings, constants)
                    schme_nm = SubElement(othr, "SchmeNm")
                    cd = SubElement(schme_nm, "Cd")
                    cd.text = "NIDN"
            
            # Country of branch
            if self._has_mapping("buyer_country", field_mappings):
                ctry_of_brnch = SubElement(acct_ownr, "CtryOfBrnch")
                ctry_of_brnch.text = self._get_mapped_value("buyer_country", row, field_mappings, constants)
            
            # E) Decision-maker fields for buyer
            self._add_decision_makers(buyr, row, field_mappings, constants, "investment")
    
    def _add_seller(self, parent: Element, row: pd.Series, field_mappings: Dict[str, str], 
                    constants: Dict[str, str]):
        """Add seller information."""
        # Determine if we have seller information
        has_seller_lei = self._has_mapping("seller_lei", field_mappings)
        has_seller_person = (self._has_mapping("seller_first_name", field_mappings) or 
                            self._has_mapping("seller_national_id", field_mappings))
        
        if has_seller_lei or has_seller_person:
            sellr = SubElement(parent, "Sellr")
            acct_ownr = SubElement(sellr, "AcctOwnr")
            id_elem = SubElement(acct_ownr, "Id")
            
            if has_seller_lei:
                # Legal entity
                org = SubElement(id_elem, "Org")
                lei = SubElement(org, "LEI")
                lei.text = self._get_mapped_value("seller_lei", row, field_mappings, constants)
            elif has_seller_person:
                # Natural person
                prsn = SubElement(id_elem, "Prsn")
                
                if self._has_mapping("seller_first_name", field_mappings):
                    frst_nm = SubElement(prsn, "FrstNm")
                    frst_nm.text = self._get_mapped_value("seller_first_name", row, field_mappings, constants)
                
                if self._has_mapping("seller_last_name", field_mappings):
                    nm = SubElement(prsn, "Nm")
                    nm.text = self._get_mapped_value("seller_last_name", row, field_mappings, constants)
                
                if self._has_mapping("seller_birth_date", field_mappings):
                    birth_dt = SubElement(prsn, "BirthDt")
                    birth_dt.text = self._get_mapped_value("seller_birth_date", row, field_mappings, constants)
                
                if self._has_mapping("seller_national_id", field_mappings):
                    othr = SubElement(prsn, "Othr")
                    id_val = SubElement(othr, "Id")
                    id_val.text = self._get_mapped_value("seller_national_id", row, field_mappings, constants)
                    schme_nm = SubElement(othr, "SchmeNm")
                    cd = SubElement(schme_nm, "Cd")
                    cd.text = "NIDN"
            
            # Country of branch
            if self._has_mapping("seller_country", field_mappings):
                ctry_of_brnch = SubElement(acct_ownr, "CtryOfBrnch")
                ctry_of_brnch.text = self._get_mapped_value("seller_country", row, field_mappings, constants)
            
            # E) Decision-maker fields for seller (execution decisions)
            self._add_decision_makers(sellr, row, field_mappings, constants, "execution")
    
    def _add_decision_makers(self, parent: Element, row: pd.Series, field_mappings: Dict[str, str], 
                            constants: Dict[str, str], decision_type: str):
        """Add decision-maker information."""
        if decision_type == "investment":
            # Investment decision maker
            has_person = self._has_mapping("investment_decision_person", field_mappings)
            has_algo = self._has_mapping("investment_decision_algo", field_mappings)
            
            if has_person or has_algo:
                dcsn_makr = SubElement(parent, "DcsnMakr")
                
                if has_person:
                    prsn = SubElement(dcsn_makr, "Prsn")
                    id_elem = SubElement(prsn, "Id")
                    id_elem.text = self._get_mapped_value("investment_decision_person", row, field_mappings, constants)
                elif has_algo:
                    algo = SubElement(dcsn_makr, "Algo")
                    id_elem = SubElement(algo, "Id")
                    id_elem.text = self._get_mapped_value("investment_decision_algo", row, field_mappings, constants)
        
        elif decision_type == "execution":
            # Execution decision maker
            has_person = self._has_mapping("execution_decision_person", field_mappings)
            has_algo = self._has_mapping("execution_decision_algo", field_mappings)
            
            if has_person or has_algo:
                exctn_wthn_firm = SubElement(parent, "ExctnWthnFirm")
                
                if has_person:
                    prsn = SubElement(exctn_wthn_firm, "Prsn")
                    id_elem = SubElement(prsn, "Id")
                    id_elem.text = self._get_mapped_value("execution_decision_person", row, field_mappings, constants)
                elif has_algo:
                    algo = SubElement(exctn_wthn_firm, "Algo")
                    id_elem = SubElement(algo, "Id")
                    id_elem.text = self._get_mapped_value("execution_decision_algo", row, field_mappings, constants)
    
    def _add_custom_fields(self, parent: Element, row: pd.Series, field_mappings: Dict[str, str], 
                          constants: Dict[str, str], custom_field_manager: CustomFieldManager):
        """Add user-defined custom fields to the XML."""
        custom_fields = custom_field_manager.get_all_custom_fields()
        
        for custom_field in custom_fields:
            # Check if this custom field has a mapping
            if self._has_mapping(custom_field.name, field_mappings):
                # Get the value
                value = self._get_mapped_value(custom_field.name, row, field_mappings, constants)
                
                # Validate the value
                is_valid, validation_msg = custom_field_manager.validate_custom_field_values(custom_field, value)
                
                if is_valid and value:  # Only add if valid and not empty
                    # Determine parent element
                    if custom_field.parent_element == "New":
                        target_parent = parent
                    else:
                        # Try to find the specified parent element
                        target_parent = self._find_or_create_parent_element(parent, custom_field.parent_element)
                    
                    # Create the custom element
                    custom_element = SubElement(target_parent, custom_field.xml_element_name)
                    custom_element.text = value
                elif custom_field.is_required and not value:
                    # For required custom fields, use default value if available
                    if custom_field.default_value:
                        target_parent = parent if custom_field.parent_element == "New" else self._find_or_create_parent_element(parent, custom_field.parent_element)
                        custom_element = SubElement(target_parent, custom_field.xml_element_name)
                        custom_element.text = custom_field.default_value
    
    def _find_or_create_parent_element(self, root_parent: Element, parent_path: str) -> Element:
        """Find or create a parent element for custom fields."""
        # For now, just use the root parent (New element)
        # In a more advanced implementation, you could parse parent_path and create nested elements
        return root_parent
    
    def _has_mapping(self, mifir_field_name: str, field_mappings: Dict[str, str]) -> bool:
        """Check if a MiFIR field has a mapping."""
        return (mifir_field_name in field_mappings and 
                field_mappings[mifir_field_name] and 
                field_mappings[mifir_field_name] != "None")
    
    def _get_mapped_value(self, mifir_field_name: str, row: pd.Series, field_mappings: Dict[str, str], 
                         constants: Dict[str, str]) -> str:
        """Get value for a MiFIR field from mappings."""
        if mifir_field_name not in field_mappings:
            return ""
        
        mapping = field_mappings[mifir_field_name]
        
        # Check if it's a constant value
        if mapping == "[Constant Value]":
            return constants.get(mifir_field_name, "")
        
        # Check if it's mapped to a CSV column
        if mapping and mapping != "None":
            return self._get_csv_value(row, mapping)
        
        return ""
    
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
    
    def _format_datetime(self, timestamp_str: str) -> str:
        """Format timestamp to ISO 8601 UTC format."""
        if not timestamp_str:
            return datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        
        # Handle various timestamp formats
        try:
            # If it's already in ISO format, return as is
            if 'T' in timestamp_str and 'Z' in timestamp_str:
                return timestamp_str
            
            # Handle partial timestamps like "22:23.3"
            if ':' in timestamp_str and len(timestamp_str) < 15:
                # Create a proper datetime
                current_date = datetime.now().strftime('%Y-%m-%d')
                return f"{current_date}T{timestamp_str}:00.000Z"
            
            return timestamp_str
        except:
            return datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
