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
        # Use provided value or generate a unique one
        if "biz_msg_id" in constants and constants["biz_msg_id"]:
            biz_msg_idr.text = constants["biz_msg_id"]
        else:
            biz_msg_idr.text = f"KD_DATTRA_generated_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Message definition identifier
        msg_def_idr = SubElement(app_hdr, "MsgDefIdr")
        msg_def_idr.text = "auth.016.001.01"  # Fixed for MiFIR
        
        # Creation date
        cre_dt = SubElement(app_hdr, "CreDt")
        cre_dt.text = constants.get("creation_date", datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'))
    
    def _add_mifir_transaction(self, parent: Element, row: pd.Series, field_mappings: Dict[str, str], 
                              constants: Dict[str, str], custom_field_manager: CustomFieldManager = None):
        """Add a single MiFIR compliant transaction following ESMAUG 1.1.0 schema order."""
        tx = SubElement(parent, "Tx")
        new = SubElement(tx, "New")
        
        # ESMAUG 1.1.0 SCHEMA ORDER - MUST FOLLOW EXACT SEQUENCE
        
        # 1. TxId (MUST BE FIRST) - Schema pattern: [A-Z0-9]{1,52}
        tx_id = SubElement(new, "TxId")
        if self._has_mapping("transaction_id", field_mappings):
            tx_id_value = self._get_mapped_value("transaction_id", row, field_mappings, constants)
            # Clean TxId to match schema pattern (only A-Z and 0-9, max 52 chars)
            clean_tx_id = ''.join(c for c in tx_id_value.upper() if c.isalnum())[:52]
            tx_id.text = clean_tx_id if clean_tx_id else "AUTOTXN001"
        else:
            # Generate schema-compliant auto ID
            auto_id = f"AUTOTXN{datetime.now().strftime('%Y%m%d%H%M%S')}{hash(str(row.to_dict())) % 1000:03d}"
            tx_id.text = auto_id[:52]  # Ensure max 52 characters
        
        # 2. ExctgPty (Executing Party LEI)
        exctg_pty = SubElement(new, "ExctgPty")
        if self._has_mapping("executing_party", field_mappings):
            exctg_pty.text = self._get_mapped_value("executing_party", row, field_mappings, constants)
        else:
            # Use reporting party LEI as executing party
            exctg_pty.text = self._get_mapped_value("reporting_party_lei", row, field_mappings, constants) or "YOUR_FIRM_LEI_HERE"
        
        # 3. InvstmtPtyInd (Investment Party Indicator)
        invstmt_pty_ind = SubElement(new, "InvstmtPtyInd")
        if self._has_mapping("investment_party_ind", field_mappings):
            invstmt_pty_ind.text = self._get_mapped_value("investment_party_ind", row, field_mappings, constants)
        else:
            invstmt_pty_ind.text = "true"  # Default
        
        # 4. SubmitgPty (Submitting Party LEI) - This is where RptgPrty LEI goes
        submitg_pty = SubElement(new, "SubmitgPty")
        if self._has_mapping("reporting_party_lei", field_mappings):
            submitg_pty.text = self._get_mapped_value("reporting_party_lei", row, field_mappings, constants)
        else:
            submitg_pty.text = constants.get("reporting_party_lei", "YOUR_FIRM_LEI_HERE")
        
        # 5. Buyer (Schema position 5)
        self._add_buyer(new, row, field_mappings, constants)
        
        # 6. Seller (Schema position 6)
        self._add_seller(new, row, field_mappings, constants)
        
        # 7. OrdrTrnsmssn (Order Transmission)
        ordr_trnsmssn = SubElement(new, "OrdrTrnsmssn")
        trnsmssn_ind = SubElement(ordr_trnsmssn, "TrnsmssnInd")
        if self._has_mapping("transmission_indicator", field_mappings):
            trnsmssn_ind.text = self._get_mapped_value("transmission_indicator", row, field_mappings, constants)
        else:
            trnsmssn_ind.text = "false"  # Default
        
        # 8. Tx (Trading details - MUST be under New/Tx per schema)
        tx_details = SubElement(new, "Tx")
        
        # TradDt (Trade Date - inside Tx block)
        trad_dt = SubElement(tx_details, "TradDt")
        if self._has_mapping("trade_datetime", field_mappings):
            trad_dt.text = self._format_datetime(
                self._get_mapped_value("trade_datetime", row, field_mappings, constants)
            )
        else:
            trad_dt.text = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        
        # TradgCpcty (Trading Capacity - MUST be DEAL/MTCH/AOTC)
        trad_cpcty = SubElement(tx_details, "TradgCpcty")
        if self._has_mapping("trading_capacity", field_mappings):
            capacity_value = self._get_mapped_value("trading_capacity", row, field_mappings, constants)
            # Map common values to schema-compliant values
            if capacity_value.lower() in ['buy', 'sell', 'prin', 'principal']:
                trad_cpcty.text = "AOTC"  # Any other capacity
            elif capacity_value.upper() in ['DEAL', 'MTCH', 'AOTC']:
                trad_cpcty.text = capacity_value.upper()
            else:
                trad_cpcty.text = "AOTC"  # Default
        else:
            trad_cpcty.text = "AOTC"  # Default
        
        # Qty (Quantity - inside Tx block)
        qty = SubElement(tx_details, "Qty")
        unit = SubElement(qty, "Unit")
        if self._has_mapping("quantity", field_mappings):
            unit.text = self._get_mapped_value("quantity", row, field_mappings, constants)
        else:
            unit.text = "1.0"
        
        # Pric (Price - inside Tx block) - Schema-compliant structure
        pric = SubElement(tx_details, "Pric")
        pric_inner = SubElement(pric, "Pric")
        mntry_val = SubElement(pric_inner, "MntryVal")
        
        amt = SubElement(mntry_val, "Amt")
        if self._has_mapping("price_amount", field_mappings):
            amt.text = self._get_mapped_value("price_amount", row, field_mappings, constants)
        else:
            amt.text = "100.00"
        
        # Currency attribute
        if self._has_mapping("price_currency", field_mappings):
            amt.set("Ccy", self._get_mapped_value("price_currency", row, field_mappings, constants))
        else:
            amt.set("Ccy", "USD")
        
        # Sgn (Sign indicator)
        sgn = SubElement(mntry_val, "Sgn")
        sgn.text = "true"  # Default positive
        
        # TradVn (Trading Venue - simple element, not MIC structure)
        trad_vn = SubElement(tx_details, "TradVn")
        if self._has_mapping("trading_venue", field_mappings):
            trad_vn.text = self._get_mapped_value("trading_venue", row, field_mappings, constants)
        else:
            trad_vn.text = "XOFF"
        
        # 9. FinInstrm (Financial Instrument - correct ESMAUG 1.1.0 structure)
        self._add_financial_instrument_correct(new, row, field_mappings, constants)
        
        # 10. ExctgPrsn (Executing Person)
        exctg_prsn = SubElement(new, "ExctgPrsn")
        clnt = SubElement(exctg_prsn, "Clnt")
        if self._has_mapping("executing_person", field_mappings):
            clnt.text = self._get_mapped_value("executing_person", row, field_mappings, constants)
        else:
            clnt.text = "NORE"  # Default
        
        # 11. AddtlAttrbts (Additional Attributes)
        addtl_attrbts = SubElement(new, "AddtlAttrbts")
        
        # ShrtSellgInd (MUST be Side5Code values: SESH, SELL, SSEX, UNDI)
        shrt_sellg_ind = SubElement(addtl_attrbts, "ShrtSellgInd")
        if self._has_mapping("short_sale_indicator", field_mappings):
            ssi_value = self._get_mapped_value("short_sale_indicator", row, field_mappings, constants)
            # Map common values to schema-compliant values
            if ssi_value.upper() in ['NSHO', 'LONG', 'BUY']:
                shrt_sellg_ind.text = "UNDI"  # Undisclosed/not applicable
            elif ssi_value.lower() in ['short', 'sell']:
                shrt_sellg_ind.text = "SELL"  # Short sale
            elif ssi_value.upper() in ['SESH', 'SELL', 'SSEX', 'UNDI']:
                shrt_sellg_ind.text = ssi_value.upper()
            else:
                shrt_sellg_ind.text = "UNDI"  # Default
        else:
            shrt_sellg_ind.text = "UNDI"  # Default for crypto derivatives
        
        # SctiesFincgTxInd (Securities Financing Transaction Indicator)
        scties_fincg_tx_ind = SubElement(addtl_attrbts, "SctiesFincgTxInd")
        if self._has_mapping("securities_financing_indicator", field_mappings):
            scties_fincg_tx_ind.text = self._get_mapped_value("securities_financing_indicator", row, field_mappings, constants)
        else:
            scties_fincg_tx_ind.text = "false"  # Default
        
        # Add custom fields at the end
        if custom_field_manager:
            self._add_custom_fields(new, row, field_mappings, constants, custom_field_manager)
    
    def _add_financial_instrument_correct(self, parent: Element, row: pd.Series, field_mappings: Dict[str, str], 
                                         constants: Dict[str, str]):
        """Add financial instrument with correct ESMAUG 1.1.0 structure."""
        fin_instrm = SubElement(parent, "FinInstrm")
        
        # Check if ISIN is provided - if so, use ISIN structure instead of Othr
        if self._has_mapping("instrument_isin", field_mappings):
            isin_value = self._get_mapped_value("instrument_isin", row, field_mappings, constants)
            if isin_value and isin_value.strip():
                # Use ISIN structure
                isin_elem = SubElement(fin_instrm, "ISIN")
                isin_elem.text = isin_value.strip()
                return  # Skip the Othr structure when ISIN is present
        
        # Use Othr choice for non-standard instruments
        othr = SubElement(fin_instrm, "Othr")
        
        # FinInstrmGnlAttrbts
        fin_instrm_gnl_attrbts = SubElement(othr, "FinInstrmGnlAttrbts")
        
        # FullNm (Instrument full name) - configurable
        full_nm = SubElement(fin_instrm_gnl_attrbts, "FullNm")
        if self._has_mapping("instrument_full_name", field_mappings):
            full_nm.text = self._get_mapped_value("instrument_full_name", row, field_mappings, constants)
        elif self._has_mapping("instrument_name", field_mappings):
            full_nm.text = self._get_mapped_value("instrument_name", row, field_mappings, constants)
        elif self._has_mapping("instrument_symbol", field_mappings):
            full_nm.text = self._get_mapped_value("instrument_symbol", row, field_mappings, constants)
        else:
            full_nm.text = "CRYPTO_DERIVATIVE"  # Fallback default
        
        # ClssfctnTp (Classification type) - configurable
        clssfctn_tp = SubElement(fin_instrm_gnl_attrbts, "ClssfctnTp")
        if self._has_mapping("instrument_classification", field_mappings):
            clssfctn_tp.text = self._get_mapped_value("instrument_classification", row, field_mappings, constants)
        elif self._has_mapping("classification_type", field_mappings):
            clssfctn_tp.text = self._get_mapped_value("classification_type", row, field_mappings, constants)
        else:
            clssfctn_tp.text = "SESTXC"  # Default CFI code
        
        # NtnlCcy (Notional currency) - configurable
        ntnl_ccy = SubElement(fin_instrm_gnl_attrbts, "NtnlCcy")
        if self._has_mapping("instrument_notional_currency", field_mappings):
            ntnl_ccy.text = self._get_mapped_value("instrument_notional_currency", row, field_mappings, constants)
        elif self._has_mapping("notional_currency", field_mappings):
            ntnl_ccy.text = self._get_mapped_value("notional_currency", row, field_mappings, constants)
        else:
            ntnl_ccy.text = "USD"  # Default currency
        
        # DerivInstrmAttrbts (for derivatives)
        deriv_instrm_attrbts = SubElement(othr, "DerivInstrmAttrbts")
        
        # PricMltplr
        pric_mltplr = SubElement(deriv_instrm_attrbts, "PricMltplr")
        if self._has_mapping("price_multiplier", field_mappings):
            pric_mltplr.text = self._get_mapped_value("price_multiplier", row, field_mappings, constants)
        else:
            pric_mltplr.text = "1"
        
        # UndrlygInstrm (Underlying instrument) - Schema requires Othr/Sngl/ISIN structure
        undrlyg_instrm = SubElement(deriv_instrm_attrbts, "UndrlygInstrm")
        
        # Use Othr choice as required by schema
        othr_instrm = SubElement(undrlyg_instrm, "Othr")
        
        # Sngl (Single instrument)
        sngl = SubElement(othr_instrm, "Sngl")
        
        # ISIN goes inside Sngl
        if self._has_mapping("instrument_isin", field_mappings):
            isin_value = self._get_mapped_value("instrument_isin", row, field_mappings, constants)
            isin_elem = SubElement(sngl, "ISIN")
            isin_elem.text = isin_value
        else:
            # Use Id for non-ISIN instruments
            id_elem = SubElement(sngl, "Id")
            id_elem.text = "UNKNOWN_INSTRUMENT"
        
        # DlvryTp (Delivery type)
        dlvry_tp = SubElement(deriv_instrm_attrbts, "DlvryTp")
        if self._has_mapping("delivery_type", field_mappings):
            dlvry_tp.text = self._get_mapped_value("delivery_type", row, field_mappings, constants)
        else:
            dlvry_tp.text = "CASH"
    

    
    def _add_buyer(self, parent: Element, row: pd.Series, field_mappings: Dict[str, str], 
                   constants: Dict[str, str]):
        """Add buyer information with firm-specific logic."""
        FIRM_LEI = "2138005EFA978Y43G944"
        
        # Determine buyer LEI - prefer direct mapping, fallback to taker/maker logic
        buyer_lei = self._get_mapped_value("buyer_lei", row, field_mappings, constants)
        
        if not buyer_lei:
            # Fallback to taker/maker logic if no direct buyer_lei mapping
            taker_side = self._get_mapped_value("taker_side_ordertype_sellorbuy", row, field_mappings, constants).lower()
            
            if taker_side == "buy":
                # Taker is buyer
                buyer_lei = self._get_mapped_value("fills_taker_user_id", row, field_mappings, constants)
            else:
                # Maker is buyer (when taker sells, maker buys)
                buyer_lei = self._get_mapped_value("fills_maker_user_id", row, field_mappings, constants)
        
        # Final fallback
        if not buyer_lei:
            buyer_lei = "BUYER_LEI_HERE"
        
        # Always create buyer section (required by schema)
        buyr = SubElement(parent, "Buyr")
        acct_ownr = SubElement(buyr, "AcctOwnr")
        id_elem = SubElement(acct_ownr, "Id")
        
        # Check if buyer is a legal entity (has LEI) or a person
        if self._is_lei_format(buyer_lei):
            # Legal entity - use LEI, no person info
            lei = SubElement(id_elem, "LEI")
            lei.text = buyer_lei
        else:
            # Natural person - include person info, no LEI
            prsn = SubElement(id_elem, "Prsn")
            
            # Add person name
            if self._has_mapping("buyer_first_name", field_mappings):
                frst_nm = SubElement(prsn, "FrstNm")
                frst_nm.text = self._get_mapped_value("buyer_first_name", row, field_mappings, constants)
            
            if self._has_mapping("buyer_last_name", field_mappings):
                nm = SubElement(prsn, "Nm")
                nm.text = self._get_mapped_value("buyer_last_name", row, field_mappings, constants)
            else:
                # Default name if not mapped
                nm = SubElement(prsn, "Nm")
                nm.text = "Counterparty Buyer"
            
            # Only add birth date for natural persons, not legal entities
            if self._has_mapping("buyer_birth_date", field_mappings):
                birth_dt = SubElement(prsn, "BirthDt")
                birth_date_value = self._get_mapped_value("buyer_birth_date", row, field_mappings, constants)
                birth_dt.text = self._format_date(birth_date_value)
            
            # National ID or other identification
            if self._has_mapping("buyer_national_id", field_mappings):
                othr = SubElement(prsn, "Othr")
                id_val = SubElement(othr, "Id")
                id_val.text = self._get_mapped_value("buyer_national_id", row, field_mappings, constants)
                schme_nm = SubElement(othr, "SchmeNm")
                cd = SubElement(schme_nm, "Cd")
                cd.text = "NIDN"
            else:
                # Default other identification
                othr = SubElement(prsn, "Othr")
                id_val = SubElement(othr, "Id")
                id_val.text = "UNKNOWN_ID"
                schme_nm = SubElement(othr, "SchmeNm")
                cd = SubElement(schme_nm, "Cd")
                cd.text = "NOID"
        
        # Country of branch - only for natural persons, not for LEI entities
        if not self._is_lei_format(buyer_lei) and self._has_mapping("buyer_country", field_mappings):
            ctry_of_brnch = SubElement(acct_ownr, "CtryOfBrnch")
            ctry_of_brnch.text = self._get_mapped_value("buyer_country", row, field_mappings, constants)
        
        # Decision-maker fields only for your firm (LEI entities)
        if self._is_lei_format(buyer_lei) and buyer_lei == FIRM_LEI:
            self._add_decision_makers(buyr, row, field_mappings, constants, "investment")
    
    def _add_seller(self, parent: Element, row: pd.Series, field_mappings: Dict[str, str], 
                    constants: Dict[str, str]):
        """Add seller information with firm-specific logic."""
        FIRM_LEI = "2138005EFA978Y43G944"
        
        # Determine seller LEI - prefer direct mapping, fallback to taker/maker logic
        seller_lei = self._get_mapped_value("seller_lei", row, field_mappings, constants)
        
        if not seller_lei:
            # Fallback to taker/maker logic if no direct seller_lei mapping
            taker_side = self._get_mapped_value("taker_side_ordertype_sellorbuy", row, field_mappings, constants).lower()
            
            if taker_side == "sell":
                # Taker is seller
                seller_lei = self._get_mapped_value("fills_taker_user_id", row, field_mappings, constants)
            else:
                # Maker is seller (when taker buys, maker sells)
                seller_lei = self._get_mapped_value("fills_maker_user_id", row, field_mappings, constants)
        
        # Final fallback
        if not seller_lei:
            seller_lei = "SELLER_LEI_HERE"
        
        # Always create seller section (required by schema)
        sellr = SubElement(parent, "Sellr")
        acct_ownr = SubElement(sellr, "AcctOwnr")
        id_elem = SubElement(acct_ownr, "Id")
        
        # Check if seller is a legal entity (has LEI) or a person
        if self._is_lei_format(seller_lei):
            # Legal entity - use LEI, no person info
            lei = SubElement(id_elem, "LEI")
            lei.text = seller_lei
        else:
            # Natural person - include person info, no LEI
            prsn = SubElement(id_elem, "Prsn")
            
            # Add person name
            if self._has_mapping("seller_first_name", field_mappings):
                frst_nm = SubElement(prsn, "FrstNm")
                frst_nm.text = self._get_mapped_value("seller_first_name", row, field_mappings, constants)
            
            if self._has_mapping("seller_last_name", field_mappings):
                nm = SubElement(prsn, "Nm")
                nm.text = self._get_mapped_value("seller_last_name", row, field_mappings, constants)
            else:
                # Default name if not mapped
                nm = SubElement(prsn, "Nm")
                nm.text = "Counterparty Seller"
            
            # Only add birth date for natural persons, not legal entities
            if self._has_mapping("seller_birth_date", field_mappings):
                birth_dt = SubElement(prsn, "BirthDt")
                birth_date_value = self._get_mapped_value("seller_birth_date", row, field_mappings, constants)
                birth_dt.text = self._format_date(birth_date_value)
            
            # National ID or other identification
            if self._has_mapping("seller_national_id", field_mappings):
                othr = SubElement(prsn, "Othr")
                id_val = SubElement(othr, "Id")
                id_val.text = self._get_mapped_value("seller_national_id", row, field_mappings, constants)
                schme_nm = SubElement(othr, "SchmeNm")
                cd = SubElement(schme_nm, "Cd")
                cd.text = "NIDN"
            else:
                # Default other identification
                othr = SubElement(prsn, "Othr")
                id_val = SubElement(othr, "Id")
                id_val.text = "UNKNOWN_ID"
                schme_nm = SubElement(othr, "SchmeNm")
                cd = SubElement(schme_nm, "Cd")
                cd.text = "NOID"
        
        # Country of branch - only for natural persons, not for LEI entities
        if not self._is_lei_format(seller_lei) and self._has_mapping("seller_country", field_mappings):
            ctry_of_brnch = SubElement(acct_ownr, "CtryOfBrnch")
            ctry_of_brnch.text = self._get_mapped_value("seller_country", row, field_mappings, constants)
        
        # Decision-maker fields only for your firm (LEI entities)
        if self._is_lei_format(seller_lei) and seller_lei == FIRM_LEI:
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
    
    def _add_all_mapped_fields(self, parent: Element, row: pd.Series, field_mappings: Dict[str, str], 
                              constants: Dict[str, str]):
        """Add ALL mapped fields that aren't already handled by specific methods."""
        from mifir_fields import MIFIR_FIELDS
        
        # Fields that are already handled by specific methods
        handled_fields = {
            "reporting_party_lei", "tech_record_id", "transaction_id", "instrument_isin", 
            "instrument_cfi", "execution_datetime", "trade_datetime", "settlement_date",
            "trading_venue", "trading_capacity", "price_amount", "price_currency", 
            "quantity", "buyer_lei", "buyer_first_name", "buyer_last_name", 
            "buyer_birth_date", "buyer_national_id", "buyer_country",
            "seller_lei", "seller_first_name", "seller_last_name", 
            "seller_birth_date", "seller_national_id", "seller_country",
            "short_sale_indicator", "commodity_derivative_indicator", 
            "clearing_indicator", "securities_financing_indicator",
            "country_of_branch", "investment_firm_covered"
        }
        
        # Add any other mapped fields that aren't handled yet
        for mifir_field in MIFIR_FIELDS:
            field_name = mifir_field.name
            
            # Skip if already handled by specific methods
            if field_name in handled_fields:
                continue
            
            # Skip if not mapped
            if not self._has_mapping(field_name, field_mappings):
                continue
            
            # Get the value
            value = self._get_mapped_value(field_name, row, field_mappings, constants)
            
            # Only add if we have a value
            if value and value.strip():
                # Create element with simple name (could be enhanced for complex paths)
                element_name = self._get_xml_element_name(mifir_field)
                if element_name:
                    element = SubElement(parent, element_name)
                    element.text = value
    
    def _get_xml_element_name(self, mifir_field) -> str:
        """Get simple XML element name from MiFIR field xpath."""
        # Extract the last element from xpath
        xpath = mifir_field.xpath
        if '/' in xpath:
            return xpath.split('/')[-1]
        return xpath
    
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
    
    def _is_lei_format(self, identifier: str) -> bool:
        """Check if identifier is in LEI format (20 alphanumeric characters)."""
        if not identifier or identifier in ["BUYER_LEI_HERE", "SELLER_LEI_HERE", "YOUR_FIRM_LEI_HERE"]:
            return False
        
        # LEI format: exactly 20 alphanumeric characters
        return len(identifier) == 20 and identifier.isalnum()
    
    def _format_date(self, date_str: str) -> str:
        """Format date string to YYYY-MM-DD format (remove time component)."""
        if not date_str:
            return ""
        
        try:
            # Parse the date string and extract only the date part
            dt = pd.to_datetime(date_str)
            return dt.strftime('%Y-%m-%d')
        except:
            # If parsing fails, try to extract just the date part manually
            if ' ' in date_str:
                # Remove time component (everything after the first space)
                return date_str.split(' ')[0]
            return date_str
