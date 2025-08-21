"""
MiFIR Field Mapping App - Dynamic mapping from CSV/Excel to MiFIR RTS 22 fields
"""

import streamlit as st
import pandas as pd
from mifir_xml_generator import MiFIRXMLGenerator
from mifir_fields import (MIFIR_FIELDS, get_required_fields, get_conditional_fields, 
                         get_optional_fields, get_buyer_seller_logic_fields)
from auto_mapper import AutoMapper
from custom_fields import CustomField, CustomFieldManager, CustomFieldType, CustomFieldCategory
from custom_only_xml_generator import CustomOnlyXMLGenerator
from datetime import datetime
import io
import json

def main():
    st.set_page_config(page_title="MiFIR RTS 22 Mapper", page_icon="🏦", layout="wide")
    
    st.title("🏦 MiFIR RTS 22 Field Mapper & XML Generator")
    st.markdown("""
    **Map your trading data to MiFIR RTS 22 fields and generate compliant auth.016.001.01 XML**
    
    📋 Upload CSV/Excel → 🔗 Map to MiFIR fields → 📄 Generate compliant XML
    """)
    
    # Add comprehensive help section
    with st.expander("📚 COMPREHENSIVE HELP GUIDE", expanded=False):
        st.markdown("""
        # 🎯 Complete MiFIR RTS 22 Mapping Guide
        
        ## 🔍 Field Types Explained
        
        ### 🔴 **Required Fields** (MUST be mapped)
        These are **essential for MiFIR RTS 22 compliance** and cannot be omitted:
        
        | Field | Description | Example | Notes |
        |-------|-------------|---------|-------|
        | `reporting_party_lei` | Your firm's LEI code | `2138001ME4Z9Z8DZNS52` | **Legal requirement** - identifies who submits the report |
        | `instrument_isin` | DSB ISIN for derivative | `US0231351067` | **Must be ANNA DSB ISIN**, not venue ticker like SOL_USDC_PERP |
        | `execution_datetime` | Trade execution timestamp | `2025-08-19T22:23:00.300Z` | **Full UTC timestamp** with milliseconds |
        | `trade_datetime` | Trade date/time | `2025-08-19T22:23:00.300Z` | Usually same as execution datetime |
        | `price_amount` | Transaction price | `144.01` | Price in contract currency |
        | `quantity` | Transaction quantity | `0.01` | Quantity in contract units |
        | `transaction_id` | Unique transaction ID | `3208418` | Must uniquely identify each transaction |
        
        ### 🟡 **Conditional Fields** (Map IF you have the data)
        Required only when certain conditions are met:
        
        #### **Buyer Information** (Required IF buyer is identified):
        - **Legal Entity**: Use `buyer_lei` (20-character LEI code)
        - **Natural Person**: Use `buyer_first_name`, `buyer_last_name`, `buyer_birth_date`, `buyer_national_id`
        - **Optional**: `buyer_country` (country of branch)
        
        #### **Seller Information** (Required IF seller is identified):
        - **Legal Entity**: Use `seller_lei` (20-character LEI code)  
        - **Natural Person**: Use `seller_first_name`, `seller_last_name`, `seller_birth_date`, `seller_national_id`
        - **Optional**: `seller_country` (country of branch)
        
        #### **Decision Makers** (Required IF you track decision makers):
        - `investment_decision_person` - National ID of person who made investment decision
        - `investment_decision_algo` - Algorithm ID if investment decision was algorithmic
        - `execution_decision_person` - National ID of person who made execution decision  
        - `execution_decision_algo` - Algorithm ID if execution decision was algorithmic
        
        ### 🟢 **Optional Fields** (Auto-populated with defaults)
        These have **smart defaults** so you don't need to map them unless you want different values:
        
        | Field | Default Value | Description |
        |-------|---------------|-------------|
        | `tech_record_id` | Auto-generated | Your internal record ID |
        | `instrument_cfi` | `FXXXXX` | CFI classification code |
        | `settlement_date` | Not included | Settlement date (if applicable) |
        | `trading_venue` | `XOFF` | OTC/off-venue for crypto exchanges |
        | `trading_capacity` | `PRIN` | Principal trading |
        | `price_currency` | `USD` | Currency for crypto derivatives |
        | `short_sale_indicator` | `NSHO` | Not applicable for crypto derivatives |
        | `commodity_derivative_indicator` | `N` | Not a commodity derivative |
        | `clearing_indicator` | `N` | Not centrally cleared |
        | `securities_financing_indicator` | `N` | Not a securities financing transaction |
        
        ### ⚙️ **Constants** (Fixed values for all transactions)
        
        #### **Header Constants** (ISO 20022 envelope):
        - `from_org_id` - Your organization code (e.g., "KD")
        - `to_org_id` - Regulator code (e.g., "CY" for Cyprus)  
        - `biz_msg_id` - Business message identifier
        
        #### **Field Constants** (When you select [Constant Value]):
        When you map a field to **[Constant Value]**, you set the value here that applies to ALL transactions.
        
        **Example:**
        - `reporting_party_lei` = **[Constant Value]** → Set your firm's LEI: `"2138001ME4Z9Z8DZNS52"`
        - `instrument_isin` = **[Constant Value]** → Set DSB ISIN: `"US0231351067"`
        
        ---
        
        ## 🚀 Quick Start Guide
        
        ### **Step 1: Upload Your Data**
        Upload CSV or Excel file with your trading data.
        
        ### **Step 2: Map Required Fields (Minimum 7)**
        1. `reporting_party_lei` → **[Constant Value]** → Enter your firm's LEI in Constants
        2. `instrument_isin` → **[Constant Value]** → Enter DSB ISIN in Constants
        3. `execution_datetime` → **fills_timestamp** (your timestamp column)
        4. `trade_datetime` → **fills_timestamp** (same column)
        5. `price_amount` → **fills_price** (your price column)
        6. `quantity` → **fills_quantity** (your quantity column)  
        7. `transaction_id` → **fills_trade_id** (your trade ID column)
        
        ### **Step 3: Map Buyer/Seller (Conditional)**
        8. `buyer_lei` → **fills_maker_user_id** (replace with actual LEI)
        9. `seller_lei` → **fills_taker_user_id** (replace with actual LEI)
        
        ### **Step 4: Generate XML**
        Click "Generate MiFIR XML" - everything else auto-populates!
        
        ---
        
        ## 📋 MiFIR RTS 22 Compliance Checklist
        
        ### ✅ **A) Reporting/Envelope**
        - ✅ ISO 20022 envelope (BizData → AppHdr → Document)
        - ✅ Message definition: `auth.016.001.01`
        - ✅ ESMA usage guideline schema locations
        - ✅ Proper Fr/To organization codes
        
        ### ✅ **B) Instrument Identification**
        - ✅ **ISIN from ANNA DSB** (not venue tickers)
        - ✅ CFI classification code
        - ⚠️ **Important**: Replace `SOL_USDC_PERP` with proper DSB ISIN
        
        ### ✅ **C) Execution Details**
        - ✅ Full UTC timestamps with milliseconds
        - ✅ Trading venue MIC codes (XOFF for OTC)
        - ✅ Trading capacity (PRIN/AGEN/MTCH)
        - ✅ Price with currency
        - ✅ Quantity in contract units
        - ✅ Settlement date (if applicable)
        
        ### ✅ **D) Buyer/Seller Identification**
        - ✅ LEI for legal entities
        - ✅ National ID for natural persons
        - ✅ Proper buyer/seller logic (not maker/taker)
        - ⚠️ **Important**: Replace internal IDs with actual LEIs/National IDs
        
        ### ✅ **E) Decision-Maker Fields**
        - ✅ Investment decision person/algorithm
        - ✅ Execution decision person/algorithm
        - ✅ Client-side decision makers (if applicable)
        
        ### ✅ **F) Flags & Indicators**
        - ✅ Short sale indicator (NSHO for crypto derivatives)
        - ✅ Commodity derivative indicator
        - ✅ Clearing indicator (Y/N)
        - ✅ Securities financing indicator (N for non-SFT)
        
        ### ✅ **G) Firm/Branch Context**
        - ✅ Country of branch responsible
        - ✅ Investment firm coverage indicator
        
        ---
        
        ## 🔄 Buyer/Seller Assignment Logic
        
        **From your CSV data, determine who bought and who sold:**
        
        ```
        If taker_side_ordertype_sellorbuy = "buy":
        → Taker is BUYER, Maker is SELLER
        
        If taker_side_ordertype_sellorbuy = "sell":  
        → Taker is SELLER, Maker is BUYER
        ```
        
        **Typical mapping:**
        - When taker bought: `fills_taker_user_id` → Buyer LEI, `fills_maker_user_id` → Seller LEI
        - When taker sold: `fills_taker_user_id` → Seller LEI, `fills_maker_user_id` → Buyer LEI
        
        ---
        
        ## ⚠️ **Critical Requirements**
        
        ### **1. ISIN Requirement**
        - ❌ **Don't use**: `SOL_USDC_PERP`, `BTC_USDC_PERP` (venue tickers)
        - ✅ **Must use**: DSB ISIN from ANNA DSB for each derivative
        - 🔗 **Get ISINs**: [ANNA DSB Portal](https://www.anna-dsb.com)
        
        ### **2. LEI/National ID Requirement**  
        - ❌ **Don't use**: Internal IDs like `1656799`, `241086`
        - ✅ **Must use**: 20-character LEI codes for legal entities
        - ✅ **Must use**: National IDs for natural persons
        - 📋 **Follow**: Annex II identification hierarchy
        
        ### **3. Timestamp Requirement**
        - ❌ **Don't use**: Partial times like `22:23.3`
        - ✅ **Must use**: Full UTC timestamps like `2025-08-19T22:23:00.300Z`
        
        ### **4. Venue Requirement**
        - ✅ **Use XOFF**: For OTC/off-venue crypto exchanges
        - ✅ **Use MIC codes**: For regulated trading venues
        - ✅ **Use SINT**: If you're a Systematic Internaliser
        
        ---
        
        ## 🛠️ **Troubleshooting**
        
        ### **"Missing required field mappings" Error**
        ➡️ **Solution**: Map the 7 required fields listed above
        
        ### **"Invalid ISIN" Warning**
        ➡️ **Solution**: Replace venue tickers with DSB ISINs
        
        ### **"Invalid LEI" Warning** 
        ➡️ **Solution**: Replace internal user IDs with 20-character LEI codes
        
        ### **"Invalid timestamp" Error**
        ➡️ **Solution**: Ensure timestamps are in full ISO 8601 UTC format
        
        ---
        
        ## 📞 **Regulatory Resources**
        
        - **ESMA Guidelines**: [esma.europa.eu](https://esma.europa.eu)
        - **ANNA DSB Portal**: [anna-dsb.com](https://www.anna-dsb.com) (for ISINs)
        - **LEI Search**: [gleif.org](https://www.gleif.org) (for LEI codes)
        - **MIC Codes**: [iso20022.org](https://www.iso20022.org) (for venue codes)
        
        ---
        
        ## 💡 **Pro Tips**
        
        1. **Start Simple**: Map only the 7 required fields first
        2. **Use Constants**: For values that don't change (LEI, ISIN, venue)
        3. **Test Small**: Upload a few rows first to test your mapping
        4. **Validate Early**: Check with your NCA's validator before bulk processing
        5. **Keep Records**: Save your mapping configuration for future use
        """)
    
    # Add quick setup assistant
    with st.expander("🚀 QUICK SETUP ASSISTANT", expanded=False):
        st.markdown("""
        ### For Crypto Derivatives Trading (Most Common Setup)
        
        **If your data looks like this:**
        ```
        fills_trade_id, fills_symbol, fills_price, fills_quantity, fills_timestamp, 
        fills_maker_user_id, fills_taker_user_id, taker_side_ordertype_sellorbuy
        ```
        
        **Use this mapping:**
        
        | MiFIR Field | Mapping | Value |
        |-------------|---------|-------|
        | `reporting_party_lei` | **[Constant Value]** | Your firm's LEI |
        | `instrument_isin` | **[Constant Value]** | DSB ISIN for your derivative |
        | `execution_datetime` | **fills_timestamp** | Your timestamp column |
        | `trade_datetime` | **fills_timestamp** | Same as execution |
        | `price_amount` | **fills_price** | Your price column |
        | `quantity` | **fills_quantity** | Your quantity column |
        | `transaction_id` | **fills_trade_id** | Your trade ID column |
        | `buyer_lei` | **fills_maker_user_id** | ⚠️ Replace with actual LEI |
        | `seller_lei` | **fills_taker_user_id** | ⚠️ Replace with actual LEI |
        
        **Everything else gets smart defaults!**
        
        ### 🔧 **Pre-Processing Required:**
        
        1. **Get DSB ISINs**: 
           - `SOL_USDC_PERP` → Get proper DSB ISIN from ANNA
           - `BTC_USDC_PERP` → Get proper DSB ISIN from ANNA
        
        2. **Replace Internal IDs with LEIs**:
           - `1656799` → `213800ABCDEFGHIJ1234` (20-char LEI)
           - `241086` → `549300XYZABCDEFG5678` (20-char LEI)
        
        3. **Fix Timestamps**:
           - `22:23.3` → `2025-08-19T22:23:18.300Z`
           - `35:31.0` → `2025-08-19T08:35:31.000Z`
        """)
    
    # Add regulatory compliance section
    with st.expander("⚖️ REGULATORY COMPLIANCE (A-G Requirements)", expanded=False):
        st.markdown("""
        # 📋 MiFIR RTS 22 Requirements (A-G)
        
        ## A) Reporting/Envelope ✅
        - **ISO 20022 Structure**: BizData → AppHdr → Document (auth.016.001.01)
        - **Message Definition**: `auth.016.001.01` (fixed)
        - **Schema Locations**: ESMAUG versions for your NCA
        - **Fr/To Codes**: Confirm with your NCA's onboarding pack
        
        ## B) Instrument Identification ✅
        - **ISIN Required**: Must be from ANNA DSB for derivatives
        - **CFI Code**: 6-character classification (defaults to FXXXXX)
        - **No Venue Tickers**: Replace SOL_USDC_PERP with DSB ISIN
        
        ## C) Execution Details ✅
        - **UTC Timestamps**: Full ISO 8601 with milliseconds
        - **Trading Venue**: MIC codes or XOFF for OTC
        - **Trading Capacity**: PRIN (Principal) / AGEN (Agent) / MTCH (Matched)
        - **Price & Currency**: Numeric price with ISO 4217 currency
        - **Quantity**: In contract units per specification
        
        ## D) Buyer/Seller Identification ✅
        - **LEI for Legal Entities**: 20-character codes
        - **National ID for Persons**: Per Annex II hierarchy
        - **Side Logic**: Based on buy/sell, not maker/taker
        - **No Internal IDs**: Must use regulatory identifiers
        
        ## E) Decision-Maker Fields ✅
        - **Investment Decisions**: Person or algorithm who decided to invest
        - **Execution Decisions**: Person or algorithm who executed
        - **Client Decisions**: If required by scenario
        
        ## F) Flags & Indicators ✅
        - **Short Sale**: NSHO (not applicable) for crypto derivatives
        - **Commodity Derivative**: N (typically for crypto)
        - **Clearing**: Y/N (centrally cleared?)
        - **Securities Financing**: N (not SFT)
        
        ## G) Firm/Branch Context ✅
        - **Country of Branch**: ISO 3166-1 alpha-2 code
        - **Investment Firm Coverage**: MiFID II coverage indicator
        
        ---
        
        ## 🎯 **Field Mapping Strategy**
        
        ### **1. Core Transaction Data (Required)**
        ```
        Your CSV Column          →  MiFIR Field
        =====================================
        fills_trade_id          →  transaction_id
        fills_timestamp         →  execution_datetime & trade_datetime  
        fills_price             →  price_amount
        fills_quantity          →  quantity
        fills_symbol            →  Get DSB ISIN → instrument_isin
        ```
        
        ### **2. Party Identification (Conditional)**
        ```
        Your CSV Column          →  MiFIR Field
        =====================================
        fills_maker_user_id     →  buyer_lei (if maker bought)
        fills_taker_user_id     →  seller_lei (if maker bought)
        
        OR (if taker bought):
        fills_taker_user_id     →  buyer_lei  
        fills_maker_user_id     →  seller_lei
        ```
        
        ### **3. Constants (Set Once)**
        ```
        Field                   →  Typical Value
        =====================================
        reporting_party_lei     →  Your firm's LEI
        instrument_isin         →  DSB ISIN for derivative
        trading_venue           →  XOFF (for crypto exchanges)
        trading_capacity        →  PRIN (principal trading)
        price_currency          →  USD
        ```
        
        ---
        
        ## ⚠️ **Common Issues & Solutions**
        
        ### **Issue 1: "SOL_USDC_PERP not valid ISIN"**
        **Problem**: Using venue ticker instead of ISIN
        **Solution**: Get DSB ISIN from ANNA for SOL/USD perpetual derivative
        
        ### **Issue 2: "1656799 not valid LEI"**  
        **Problem**: Using internal user ID instead of LEI
        **Solution**: Replace with 20-character LEI code from GLEIF
        
        ### **Issue 3: "22:23.3 not valid timestamp"**
        **Problem**: Partial timestamp missing date/timezone
        **Solution**: Convert to full UTC: `2025-08-19T22:23:18.300Z`
        
        ### **Issue 4: "Missing buyer information"**
        **Problem**: Not mapping buyer identification
        **Solution**: Map either `buyer_lei` OR person fields (`buyer_first_name`, etc.)
        
        ---
        
        ## 📞 **Need Help?**
        
        1. **Technical Issues**: Check field mapping and data format
        2. **Regulatory Questions**: Consult your NCA's guidance
        3. **ISIN Questions**: Contact ANNA DSB
        4. **LEI Questions**: Check GLEIF database
        
        **Remember**: This tool generates the XML structure, but you must ensure:
        - ISINs are correct DSB codes
        - LEIs are valid and current  
        - Timestamps are accurate
        - Buyer/seller logic is correct for your trades
        """)
        
    st.markdown("---")
    
    # File upload
    uploaded_file = st.file_uploader(
        "Upload your trading data (CSV or Excel)", 
        type=['csv', 'xlsx', 'xls'],
        help="Upload your trading data file with transaction details"
    )
    
    if uploaded_file is not None:
        try:
            # Read file
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            # Fix data type issues for Streamlit display
            # Convert all object columns to string to avoid Arrow serialization errors
            for col in df.select_dtypes(include=['object']).columns:
                df[col] = df[col].astype(str)
            
            st.success(f"✅ File loaded: {len(df)} rows, {len(df.columns)} columns")
            
            # Show data preview
            with st.expander("📊 View Data Preview", expanded=False):
                st.dataframe(df.head(10))
            
            # Auto-mapper functionality
            st.markdown("---")
            st.subheader("🤖 Auto-Mapper")
            
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                if st.button("🚀 Auto-Suggest Field Mappings", type="primary", use_container_width=True):
                    try:
                        # Create auto-mapper and get suggestions
                        with st.spinner("Analyzing your data..."):
                            auto_mapper = AutoMapper(df)
                            suggestions = auto_mapper.auto_suggest_mappings()
                            confidence_scores = auto_mapper.get_confidence_score(suggestions)
                            explanations = auto_mapper.get_mapping_explanations(suggestions)
                        
                        # Store in session state
                        st.session_state.auto_suggestions = suggestions
                        st.session_state.auto_confidence = confidence_scores
                        st.session_state.auto_explanations = explanations
                        
                        st.success(f"✅ Auto-mapped {len(suggestions)} fields!")
                        
                        # Debug info
                        st.info(f"🔍 Debug: Found {len(suggestions)} mappings, stored in session state")
                        
                    except Exception as e:
                        st.error(f"❌ Auto-mapping error: {str(e)}")
                        st.exception(e)
            
            with col2:
                if st.button("📋 Apply Auto-Suggestions", use_container_width=True):
                    if 'auto_suggestions' in st.session_state:
                        try:
                            # Apply suggestions to field mappings AND selectbox session state
                            applied_count = 0
                            for field_name, csv_column in st.session_state.auto_suggestions.items():
                                # Update field mappings
                                st.session_state.field_mappings[field_name] = csv_column
                                
                                # Update selectbox session state - try all possible key patterns
                                # For custom fields, we need to find the actual keys with unique IDs
                                keys_to_update = []
                                
                                # Find all keys that match this field name
                                for session_key in st.session_state.keys():
                                    if (session_key.endswith(f"mapping_{field_name}") or 
                                        f"mapping_{field_name}_" in session_key):
                                        keys_to_update.append(session_key)
                                
                                # Also try standard patterns
                                standard_keys = [
                                    f"std_req_mapping_{field_name}",
                                    f"buyer_mapping_{field_name}",
                                    f"seller_mapping_{field_name}",
                                    f"std_opt_mapping_{field_name}",
                                    f"mapping_{field_name}"  # Fallback
                                ]
                                
                                keys_to_update.extend(standard_keys)
                                
                                # Set all found keys
                                for key_to_update in keys_to_update:
                                    st.session_state[key_to_update] = csv_column
                                
                                applied_count += 1
                            
                            st.success(f"✅ Applied {applied_count} auto-suggestions to field mappings!")
                            
                            # Debug info
                            st.info(f"🔍 Debug: Applied to session state keys and field_mappings")
                            
                            # Force rerun to update UI
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"❌ Error applying suggestions: {str(e)}")
                            st.exception(e)
                    else:
                        st.warning("⚠️ No auto-suggestions available. Click 'Auto-Suggest' first.")
            
            with col3:
                if st.button("💾 Prepare Configuration for Download", use_container_width=True):
                    # Prepare COMPLETE mapping configuration including custom fields and their mappings
                    
                    # Get all custom fields and their current mappings
                    custom_fields_with_mappings = []
                    all_custom_fields = st.session_state.custom_field_manager.get_all_custom_fields()
                    
                    for custom_field in all_custom_fields:
                        field_mapping = st.session_state.field_mappings.get(custom_field.name, "None")
                        custom_fields_with_mappings.append({
                            "field_definition": {
                                "name": custom_field.name,
                                "xml_element_name": custom_field.xml_element_name,
                                "field_type": custom_field.field_type.value,
                                "category": custom_field.category.value,
                                "description": custom_field.description,
                                "default_value": custom_field.default_value,
                                "enum_values": custom_field.enum_values,
                                "parent_element": custom_field.parent_element,
                                "notes": custom_field.notes
                            },
                            "field_mapping": field_mapping
                        })
                    
                    mapping_config = {
                        "field_mappings": st.session_state.field_mappings,
                        "constants": st.session_state.constants,
                        "custom_fields_definitions": st.session_state.custom_field_manager.export_custom_fields(),
                        "custom_fields_with_mappings": custom_fields_with_mappings,
                        "created_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        "data_columns": list(df.columns),
                        "total_custom_fields": len(all_custom_fields),
                        "app_version": "1.0"
                    }
                    
                    # Store in session state for download
                    st.session_state.prepared_config = json.dumps(mapping_config, indent=2)
                    st.session_state.config_filename = f"mifir_complete_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    
                    st.success(f"✅ Configuration prepared! Includes {len(all_custom_fields)} custom fields + all mappings")
            
            # Show download button if config is prepared
            if 'prepared_config' in st.session_state:
                st.download_button(
                    label="📥 Download Complete Configuration",
                    data=st.session_state.prepared_config,
                    file_name=st.session_state.config_filename,
                    mime="application/json",
                    help="Complete configuration: mappings + custom fields + constants",
                    use_container_width=True
                )
            
            # Add load mapping functionality
            st.markdown("**Load Previous Mapping:**")
            
            col_load1, col_load2 = st.columns([2, 1])
            
            with col_load1:
                uploaded_mapping = st.file_uploader(
                    "📤 Upload Mapping Configuration",
                    type=['json'],
                    key="mapping_config_uploader",
                    help="Upload a previously saved mapping configuration"
                )
            
            with col_load2:
                if st.button("🔄 Apply Loaded Config", use_container_width=True):
                    if 'loaded_config' in st.session_state:
                        try:
                            mapping_config = st.session_state.loaded_config
                            
                            # Load field mappings
                            if 'field_mappings' in mapping_config:
                                for field_name, mapping in mapping_config['field_mappings'].items():
                                    st.session_state.field_mappings[field_name] = mapping
                                    
                                    # Update selectbox session state - find all matching keys
                                    keys_to_update = []
                                    
                                    # Find all keys that match this field name (including unique IDs)
                                    for session_key in st.session_state.keys():
                                        if (session_key.endswith(f"mapping_{field_name}") or 
                                            f"mapping_{field_name}_" in session_key):
                                            keys_to_update.append(session_key)
                                    
                                    # Also try standard patterns
                                    standard_keys = [
                                        f"std_req_mapping_{field_name}",
                                        f"buyer_mapping_{field_name}",
                                        f"seller_mapping_{field_name}",
                                        f"std_opt_mapping_{field_name}",
                                        f"mapping_{field_name}"  # Fallback
                                    ]
                                    
                                    keys_to_update.extend(standard_keys)
                                    
                                    # Set all found keys
                                    for key_to_update in keys_to_update:
                                        st.session_state[key_to_update] = mapping
                            
                            # Load constants
                            if 'constants' in mapping_config:
                                for const_name, const_value in mapping_config['constants'].items():
                                    st.session_state.constants[const_name] = const_value
                            
                            # Load custom fields and their mappings
                            custom_fields_loaded = 0
                            
                            # First, load custom field definitions
                            if 'custom_fields_definitions' in mapping_config and mapping_config['custom_fields_definitions']:
                                success, message = st.session_state.custom_field_manager.import_custom_fields(mapping_config['custom_fields_definitions'])
                                if success:
                                    custom_fields_loaded = len(st.session_state.custom_field_manager.get_all_custom_fields())
                                else:
                                    st.warning(f"⚠️ Custom fields import issue: {message}")
                            
                            # Then, restore custom field mappings if available
                            if 'custom_fields_with_mappings' in mapping_config:
                                for custom_field_data in mapping_config['custom_fields_with_mappings']:
                                    field_name = custom_field_data['field_definition']['name']
                                    field_mapping = custom_field_data['field_mapping']
                                    
                                    # Update field mapping
                                    st.session_state.field_mappings[field_name] = field_mapping
                                    
                                    # Find and update all matching keys for this custom field
                                    for session_key in list(st.session_state.keys()):
                                        if (session_key.endswith(f"mapping_{field_name}") or 
                                            f"mapping_{field_name}_" in session_key):
                                            st.session_state[session_key] = field_mapping
                            
                            success_msg = "✅ Complete configuration applied successfully!"
                            if custom_fields_loaded > 0:
                                success_msg += f" Restored {custom_fields_loaded} custom fields with their mappings."
                            
                            st.success(success_msg)
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"❌ Error applying configuration: {str(e)}")
                    else:
                        st.warning("⚠️ No configuration loaded. Upload a file first.")
            
            # Process uploaded file
            if uploaded_mapping is not None:
                try:
                    config_content = uploaded_mapping.read().decode('utf-8')
                    mapping_config = json.loads(config_content)
                    
                    # Store in session state for later application
                    st.session_state.loaded_config = mapping_config
                    
                    st.info("📋 Configuration file loaded. Click 'Apply Loaded Config' to apply the mappings.")
                    
                    # Show preview of what will be loaded
                    if 'field_mappings' in mapping_config:
                        st.write(f"**Preview**: {len(mapping_config['field_mappings'])} field mappings")
                    if 'constants' in mapping_config:
                        st.write(f"**Preview**: {len(mapping_config['constants'])} constants")
                    if 'custom_fields_with_mappings' in mapping_config:
                        st.write(f"**Preview**: {len(mapping_config['custom_fields_with_mappings'])} custom fields with mappings")
                    if 'created_date' in mapping_config:
                        st.write(f"**Created**: {mapping_config['created_date']}")
                    if 'app_version' in mapping_config:
                        st.write(f"**Version**: {mapping_config['app_version']}")
                        
                except Exception as e:
                    st.error(f"❌ Error reading configuration file: {str(e)}")
            
            # Clear all button
            if st.button("🗑️ Clear All Mappings", use_container_width=True):
                # Clear all mapping session state (all key patterns including unique IDs)
                keys_to_clear = [key for key in st.session_state.keys() 
                               if 'mapping_' in key and key != 'field_mappings']
                
                for key in keys_to_clear:
                    del st.session_state[key]
                
                # Clear field mappings
                st.session_state.field_mappings = {}
                
                # Clear auto-suggestions
                if 'auto_suggestions' in st.session_state:
                    del st.session_state.auto_suggestions
                if 'auto_confidence' in st.session_state:
                    del st.session_state.auto_confidence
                if 'auto_explanations' in st.session_state:
                    del st.session_state.auto_explanations
                
                st.success("✅ All mappings cleared!")
                st.rerun()
            
            # Show auto-suggestions if available
            if 'auto_suggestions' in st.session_state:
                st.subheader("🎯 Auto-Mapping Results")
                
                # Create suggestions dataframe
                suggestions_data = []
                for field_name, csv_column in st.session_state.auto_suggestions.items():
                    confidence = st.session_state.auto_confidence.get(field_name, 0.0)
                    explanation = st.session_state.auto_explanations.get(field_name, "")
                    
                    suggestions_data.append({
                        "MiFIR Field": field_name,
                        "Suggested CSV Column": csv_column,
                        "Confidence": f"{confidence:.1%}",
                        "Reasoning": explanation
                    })
                
                suggestions_df = pd.DataFrame(suggestions_data)
                st.dataframe(suggestions_df, use_container_width=True)
                
                # Show data quality report
                with st.expander("📊 Data Quality Report", expanded=False):
                    auto_mapper = AutoMapper(df)
                    quality_report = auto_mapper.get_data_quality_report()
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Rows", quality_report["total_rows"])
                    with col2:
                        st.metric("Total Columns", quality_report["total_columns"])
                    with col3:
                        st.metric("Potential Issues", len(quality_report["potential_issues"]))
                    
                    if quality_report["potential_issues"]:
                        st.warning("⚠️ **Potential Data Issues:**")
                        for issue in quality_report["potential_issues"]:
                            st.write(f"- {issue}")
                    
                    # Missing data summary
                    st.write("**Missing Data Summary:**")
                    missing_data = []
                    for col, missing_info in quality_report["missing_data"].items():
                        if missing_info["percentage"] > 0:
                            missing_data.append({
                                "Column": col,
                                "Missing Count": missing_info["count"],
                                "Missing %": f"{missing_info['percentage']:.1f}%"
                            })
                    
                    if missing_data:
                        st.dataframe(pd.DataFrame(missing_data), use_container_width=True)
                    else:
                        st.success("✅ No missing data detected!")
            
            # Available columns
            available_columns = ["None"] + list(df.columns)
            
            st.markdown("---")
            st.subheader("🔗 Field Mapping")
            st.info("Map your CSV columns to MiFIR RTS 22 fields. Required fields must be mapped.")
            
            # Initialize session state for mappings and custom fields
            if 'field_mappings' not in st.session_state:
                st.session_state.field_mappings = {}
            if 'custom_field_manager' not in st.session_state:
                st.session_state.custom_field_manager = CustomFieldManager()
            
            # Create tabs for different field types
            tab1, tab2, tab3, tab4, tab5 = st.tabs(["🔴 Required Fields", "🟡 Conditional Fields", "🟢 Optional Fields", "⚙️ Constants", "🔧 Custom Fields"])
            
            with tab1:
                st.markdown("**Required MiFIR Fields** - These must be mapped or provided as constants")
                
                # Standard required fields
                required_fields = get_required_fields()
                
                # Add custom required fields
                custom_required_fields = st.session_state.custom_field_manager.get_required_custom_fields()
                
                # Display standard required fields
                if required_fields:
                    st.markdown("***Standard Required Fields:***")
                    
                    # Add column headers for better alignment
                    col1, col2, col3 = st.columns([3, 3, 4])
                    with col1:
                        st.markdown("**Field Name**")
                    with col2:
                        st.markdown("**Map to CSV Column**")
                    with col3:
                        st.markdown("**Description & Details**")
                    st.markdown("---")
                    
                    for field in required_fields:
                        col1, col2, col3 = st.columns([3, 3, 4])
                        
                        with col1:
                            st.write(f"**{field.name}**")
                            st.caption(f"`{field.xpath}`")
                        
                        with col2:
                            # Mapping selection
                            key = f"std_req_mapping_{field.name}"  # Unique prefix for standard required
                            options = ["None", "[Constant Value]"] + list(df.columns)
                            
                            # Check if we have a pre-existing value (from auto-suggestions)
                            current_value = st.session_state.get(key, "None")
                            if current_value not in options:
                                current_value = "None"
                            
                            try:
                                default_index = options.index(current_value)
                            except ValueError:
                                default_index = 0
                            
                            selected = st.selectbox(
                                "Map to:",
                                options,
                                index=default_index,
                                key=key,
                                label_visibility="collapsed",
                                help=f"{field.description}\nExample: {field.example_value}"
                            )
                            st.session_state.field_mappings[field.name] = selected
                        
                        with col3:
                            st.caption(f"📝 {field.description}")
                            if field.example_value:
                                st.caption(f"💡 Example: {field.example_value}")
                            if field.notes:
                                st.caption(f"📌 {field.notes}")
                            if field.enum_values:
                                st.caption(f"🎯 Values: {', '.join(field.enum_values)}")
                
                # Display custom required fields
                if custom_required_fields:
                    st.markdown("***Custom Required Fields:***")
                    for field in custom_required_fields:
                        col1, col2, col3 = st.columns([3, 3, 4])
                        
                        with col1:
                            st.write(f"**{field.name}** 🔧")
                            st.caption(f"XML: `<{field.xml_element_name}>`")
                        
                        with col2:
                            key = f"cust_req_mapping_{field.name}_{id(field)}"
                            options = ["None", "[Constant Value]"] + list(df.columns)
                            
                            current_value = st.session_state.get(key, "None")
                            if current_value not in options:
                                current_value = "None"
                            
                            try:
                                default_index = options.index(current_value)
                            except ValueError:
                                default_index = 0
                            
                            selected = st.selectbox(
                                "Map to:",
                                options,
                                index=default_index,
                                key=key,
                                label_visibility="collapsed",
                                help=f"{field.description}"
                            )
                            st.session_state.field_mappings[field.name] = selected
                        
                        with col3:
                            st.caption(f"📝 {field.description}")
                            st.caption(f"🔧 Custom {field.category.value}")
                            if field.enum_values:
                                st.caption(f"🎯 Values: {', '.join(field.enum_values)}")
                
                if not required_fields and not custom_required_fields:
                    st.info("💡 No required fields defined. All fields are optional with smart defaults.")
            
            with tab5:
                st.markdown("**Custom Fields** - Create your own fields for additional data")
                
                # Custom field creation form
                with st.expander("➕ Create New Custom Field", expanded=False):
                    with st.form("custom_field_form"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            custom_name = st.text_input(
                                "Field Name",
                                help="Internal name for this field (e.g., 'client_reference')"
                            )
                            custom_xml_name = st.text_input(
                                "XML Element Name", 
                                help="Name that will appear in XML (e.g., 'ClntRef')"
                            )
                            custom_description = st.text_area(
                                "Description",
                                help="Description of what this field contains"
                            )
                        
                        with col2:
                            custom_type = st.selectbox(
                                "Field Type",
                                options=[t.value for t in CustomFieldType],
                                help="Data type for validation"
                            )
                            custom_category = st.selectbox(
                                "Field Category",
                                options=[c.value for c in CustomFieldCategory],
                                help="Whether field is required, conditional, optional, or constant"
                            )
                            custom_default = st.text_input(
                                "Default Value",
                                help="Default value if not mapped (optional)"
                            )
                            
                            # Enum values for enum type
                            if custom_type == "enum":
                                custom_enum_values = st.text_input(
                                    "Enum Values (comma-separated)",
                                    help="e.g., 'Y,N' or 'LOW,MEDIUM,HIGH'"
                                )
                            else:
                                custom_enum_values = ""
                        
                        custom_notes = st.text_input(
                            "Notes (optional)",
                            help="Additional notes or usage instructions"
                        )
                        
                        submitted = st.form_submit_button("➕ Add Custom Field")
                        
                        if submitted:
                            # Validate inputs
                            if not custom_name:
                                st.error("❌ Field name is required")
                            elif not custom_xml_name:
                                st.error("❌ XML element name is required")
                            else:
                                # Validate field name
                                name_valid, name_msg = st.session_state.custom_field_manager.validate_field_name(custom_name)
                                xml_valid, xml_msg = st.session_state.custom_field_manager.validate_xml_element_name(custom_xml_name)
                                
                                if not name_valid:
                                    st.error(f"❌ Invalid field name: {name_msg}")
                                elif not xml_valid:
                                    st.error(f"❌ Invalid XML element name: {xml_msg}")
                                else:
                                    # Create custom field
                                    enum_list = None
                                    if custom_type == "enum" and custom_enum_values:
                                        enum_list = [v.strip() for v in custom_enum_values.split(",")]
                                    
                                    custom_field = CustomField(
                                        name=custom_name,
                                        xml_element_name=custom_xml_name,
                                        field_type=CustomFieldType(custom_type),
                                        category=CustomFieldCategory(custom_category),
                                        description=custom_description,
                                        default_value=custom_default,
                                        enum_values=enum_list,
                                        parent_element="New",
                                        notes=custom_notes
                                    )
                                    
                                    # Add to manager
                                    if st.session_state.custom_field_manager.add_custom_field(custom_field):
                                        st.success(f"✅ Added custom field: {custom_name}")
                                        st.rerun()
                                    else:
                                        st.error("❌ Failed to add custom field (name may already exist)")
                
                # Show existing custom fields
                custom_fields = st.session_state.custom_field_manager.get_all_custom_fields()
                
                if custom_fields:
                    st.markdown("**Your Custom Fields:**")
                    
                    for field in custom_fields:
                        with st.container():
                            col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
                            
                            with col1:
                                st.write(f"**{field.name}**")
                                st.caption(f"XML: `<{field.xml_element_name}>`")
                            
                            with col2:
                                # Show current mapping (read-only in this tab)
                                current_mapping = st.session_state.field_mappings.get(field.name, "None")
                                st.write(f"**Current Mapping:**")
                                st.code(current_mapping)
                                st.caption("💡 Map this field in its category tab")
                            
                            with col3:
                                st.caption(f"📝 {field.description}")
                                st.caption(f"🔧 Type: {field.field_type.value}")
                                if field.is_required:
                                    st.caption("🔴 Required")
                                if field.enum_values:
                                    st.caption(f"🎯 Values: {', '.join(field.enum_values)}")
                            
                            with col4:
                                if st.button("🗑️", key=f"delete_{field.name}_{id(field)}", help="Delete this custom field"):
                                    st.session_state.custom_field_manager.remove_custom_field(field.name)
                                    # Also remove from field mappings
                                    if field.name in st.session_state.field_mappings:
                                        del st.session_state.field_mappings[field.name]
                                    # Remove from session state
                                    key_to_remove = f"mapping_{field.name}"
                                    if key_to_remove in st.session_state:
                                        del st.session_state[key_to_remove]
                                    st.success(f"✅ Deleted custom field: {field.name}")
                                    st.rerun()
                            
                            st.markdown("---")
                
                # Export/Import custom fields
                if custom_fields:
                    st.markdown("**Export/Import Custom Fields:**")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Export
                        export_json = st.session_state.custom_field_manager.export_custom_fields()
                        st.download_button(
                            "📥 Export Custom Fields",
                            data=export_json,
                            file_name=f"custom_fields_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json",
                            help="Save your custom fields configuration"
                        )
                    
                    with col2:
                        # Import
                        uploaded_config = st.file_uploader(
                            "📤 Import Custom Fields",
                            type=['json'],
                            help="Upload a previously exported custom fields configuration"
                        )
                        
                        if uploaded_config is not None:
                            try:
                                config_content = uploaded_config.read().decode('utf-8')
                                success, message = st.session_state.custom_field_manager.import_custom_fields(config_content)
                                
                                if success:
                                    st.success(f"✅ {message}")
                                    st.rerun()
                                else:
                                    st.error(f"❌ {message}")
                            except Exception as e:
                                st.error(f"❌ Error importing: {str(e)}")
                
                else:
                    st.info("💡 No custom fields created yet. Use the form above to create your first custom field.")
            
            with tab2:
                st.markdown("**Conditional Fields** - Map based on your data structure")
                conditional_fields = get_conditional_fields()
                custom_conditional_fields = st.session_state.custom_field_manager.get_conditional_custom_fields()
                
                # Group by buyer/seller
                st.markdown("**Buyer Information**")
                buyer_fields = [f for f in conditional_fields if f.name.startswith('buyer_')]
                
                if buyer_fields:
                    # Add column headers
                    col1, col2, col3 = st.columns([3, 3, 4])
                    with col1:
                        st.markdown("**Field Name**")
                    with col2:
                        st.markdown("**Map to CSV Column**")
                    with col3:
                        st.markdown("**Description & Details**")
                    st.markdown("---")
                
                for field in buyer_fields:
                    col1, col2, col3 = st.columns([3, 3, 4])
                    
                    with col1:
                        st.write(f"**{field.name}**")
                        st.caption(f"`{field.xpath}`")
                    
                    with col2:
                        key = f"buyer_mapping_{field.name}"
                        options = ["None", "[Constant Value]"] + list(df.columns)
                        
                        # Check for pre-existing value
                        current_value = st.session_state.get(key, "None")
                        if current_value not in options:
                            current_value = "None"
                        
                        try:
                            default_index = options.index(current_value)
                        except ValueError:
                            default_index = 0
                        
                        selected = st.selectbox("Map to:", options, index=default_index, key=key, label_visibility="collapsed")
                        st.session_state.field_mappings[field.name] = selected
                    
                    with col3:
                        st.caption(f"📝 {field.description}")
                        if field.example_value:
                            st.caption(f"💡 Example: {field.example_value}")
                
                st.markdown("**Seller Information**")
                seller_fields = [f for f in conditional_fields if f.name.startswith('seller_')]
                
                if seller_fields:
                    # Add column headers
                    col1, col2, col3 = st.columns([3, 3, 4])
                    with col1:
                        st.markdown("**Field Name**")
                    with col2:
                        st.markdown("**Map to CSV Column**")
                    with col3:
                        st.markdown("**Description & Details**")
                    st.markdown("---")
                
                for field in seller_fields:
                    col1, col2, col3 = st.columns([3, 3, 4])
                    
                    with col1:
                        st.write(f"**{field.name}**")
                        st.caption(f"`{field.xpath}`")
                    
                    with col2:
                        key = f"seller_mapping_{field.name}"
                        options = ["None", "[Constant Value]"] + list(df.columns)
                        
                        # Check for pre-existing value
                        current_value = st.session_state.get(key, "None")
                        if current_value not in options:
                            current_value = "None"
                        
                        try:
                            default_index = options.index(current_value)
                        except ValueError:
                            default_index = 0
                        
                        selected = st.selectbox("Map to:", options, index=default_index, key=key, label_visibility="collapsed")
                        st.session_state.field_mappings[field.name] = selected
                    
                    with col3:
                        st.caption(f"📝 {field.description}")
                        if field.example_value:
                            st.caption(f"💡 Example: {field.example_value}")
                
                # Display custom conditional fields
                if custom_conditional_fields:
                    st.markdown("***Custom Conditional Fields:***")
                    for field in custom_conditional_fields:
                        col1, col2, col3 = st.columns([2, 2, 3])
                        
                        with col1:
                            st.write(f"**{field.name}** 🔧")
                            st.caption(f"XML: `<{field.xml_element_name}>`")
                        
                        with col2:
                            key = f"cust_cond_mapping_{field.name}_{id(field)}"
                            options = ["None", "[Constant Value]"] + list(df.columns)
                            
                            current_value = st.session_state.get(key, "None")
                            if current_value not in options:
                                current_value = "None"
                            
                            try:
                                default_index = options.index(current_value)
                            except ValueError:
                                default_index = 0
                            
                            selected = st.selectbox("Map to:", options, index=default_index, key=key)
                            st.session_state.field_mappings[field.name] = selected
                        
                        with col3:
                            st.caption(f"📝 {field.description}")
                            st.caption(f"🔧 Custom {field.category.value}")
                            if field.enum_values:
                                st.caption(f"🎯 Values: {', '.join(field.enum_values)}")
            
            with tab3:
                st.markdown("**Optional Fields** - Additional information if available")
                optional_fields = get_optional_fields()
                custom_optional_fields = st.session_state.custom_field_manager.get_optional_custom_fields()
                
                # Display standard optional fields
                if optional_fields:
                    st.markdown("***Standard Optional Fields:***")
                    
                    # Add column headers
                    col1, col2, col3 = st.columns([3, 3, 4])
                    with col1:
                        st.markdown("**Field Name**")
                    with col2:
                        st.markdown("**Map to CSV Column**")
                    with col3:
                        st.markdown("**Description & Details**")
                    st.markdown("---")
                    
                    for field in optional_fields:
                        col1, col2, col3 = st.columns([3, 3, 4])
                        
                        with col1:
                            st.write(f"**{field.name}**")
                            st.caption(f"`{field.xpath}`")
                        
                        with col2:
                            key = f"std_opt_mapping_{field.name}"
                            options = ["None", "[Constant Value]"] + list(df.columns)
                            
                            # Check for pre-existing value
                            current_value = st.session_state.get(key, "None")
                            if current_value not in options:
                                current_value = "None"
                            
                            try:
                                default_index = options.index(current_value)
                            except ValueError:
                                default_index = 0
                            
                            selected = st.selectbox("Map to:", options, index=default_index, key=key, label_visibility="collapsed")
                            st.session_state.field_mappings[field.name] = selected
                        
                        with col3:
                            st.caption(f"📝 {field.description}")
                            if field.example_value:
                                st.caption(f"💡 Example: {field.example_value}")
                            if field.notes:
                                st.caption(f"📌 {field.notes}")
                            if field.enum_values:
                                st.caption(f"🎯 Values: {', '.join(field.enum_values)}")
                
                # Display custom optional fields
                if custom_optional_fields:
                    st.markdown("***Custom Optional Fields:***")
                    for field in custom_optional_fields:
                        col1, col2, col3 = st.columns([3, 3, 4])
                        
                        with col1:
                            st.write(f"**{field.name}** 🔧")
                            st.caption(f"XML: `<{field.xml_element_name}>`")
                        
                        with col2:
                            key = f"cust_opt_mapping_{field.name}_{id(field)}"
                            options = ["None", "[Constant Value]"] + list(df.columns)
                            
                            current_value = st.session_state.get(key, "None")
                            if current_value not in options:
                                current_value = "None"
                            
                            try:
                                default_index = options.index(current_value)
                            except ValueError:
                                default_index = 0
                            
                            selected = st.selectbox("Map to:", options, index=default_index, key=key, label_visibility="collapsed")
                            st.session_state.field_mappings[field.name] = selected
                        
                        with col3:
                            st.caption(f"📝 {field.description}")
                            st.caption(f"🔧 Custom {field.category.value}")
                            if field.enum_values:
                                st.caption(f"🎯 Values: {', '.join(field.enum_values)}")
            
            with tab4:
                st.markdown("**Constant Values** - Values that apply to all transactions")
                
                # Initialize constants in session state
                if 'constants' not in st.session_state:
                    st.session_state.constants = {}
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Header Information**")
                    st.session_state.constants["from_org_id"] = st.text_input("From Organization ID", value="KD")
                    st.session_state.constants["to_org_id"] = st.text_input("To Organization ID", value="CY")
                    st.session_state.constants["biz_msg_id"] = st.text_input(
                        "Business Message ID", 
                        value=f"KD_DATTRA_generated_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    )
                
                with col2:
                    st.markdown("**Default Field Values**")
                    # Show constant input fields for mapped constant values
                    for field_name, mapping in st.session_state.field_mappings.items():
                        if mapping == "[Constant Value]":
                            field_info = next((f for f in MIFIR_FIELDS if f.name == field_name), None)
                            if field_info:
                                if field_info.enum_values:
                                    st.session_state.constants[field_name] = st.selectbox(
                                        f"{field_name}",
                                        field_info.enum_values,
                                        help=f"{field_info.description}"
                                    )
                                else:
                                    st.session_state.constants[field_name] = st.text_input(
                                        f"{field_name}",
                                        value=field_info.example_value,
                                        help=f"{field_info.description}"
                                    )
                
                # Display custom constant fields
                custom_constant_fields = st.session_state.custom_field_manager.get_constant_custom_fields()
                if custom_constant_fields:
                    st.markdown("**Custom Constant Fields**")
                    for field in custom_constant_fields:
                        if field.field_type.value == "enum" and field.enum_values:
                            st.session_state.constants[field.name] = st.selectbox(
                                f"{field.name} (Custom)",
                                field.enum_values,
                                value=field.default_value if field.default_value in field.enum_values else field.enum_values[0],
                                help=f"{field.description}"
                            )
                        else:
                            st.session_state.constants[field.name] = st.text_input(
                                f"{field.name} (Custom)",
                                value=field.default_value,
                                help=f"{field.description}"
                            )
            
            # Buyer/Seller Logic Helper
            st.markdown("---")
            with st.expander("🔄 Buyer/Seller Assignment Logic", expanded=False):
                st.markdown("""
                **How to determine Buyer vs Seller from your trading data:**
                
                If your data has `taker_side_ordertype_sellorbuy`:
                - When = "buy" → Taker is **Buyer**, Maker is **Seller**
                - When = "sell" → Taker is **Seller**, Maker is **Buyer**
                
                **Typical mapping:**
                - `fills_taker_user_id` → Buyer LEI (when taker bought)
                - `fills_maker_user_id` → Seller LEI (when taker bought)
                - Reverse when taker sold
                """)
                
                # Show buyer/seller logic fields if available
                logic_fields = get_buyer_seller_logic_fields()
                available_logic_fields = [col for col in df.columns if any(logic in col.lower() for logic in ['buy', 'sell', 'side', 'taker', 'maker'])]
                
                if available_logic_fields:
                    st.write("**Available logic fields in your data:**")
                    for col in available_logic_fields[:10]:  # Show first 10
                        sample_values = df[col].dropna().unique()[:3]
                        st.write(f"- `{col}`: {', '.join(str(v) for v in sample_values)}")
            
            # Validation and Generation
            st.markdown("---")
            st.subheader("🚀 Generate MiFIR XML")
            
            # Check required field mappings (including custom required fields)
            required_fields = get_required_fields()
            missing_mappings = []
            
            # Check standard required fields
            for field in required_fields:
                mapping = st.session_state.field_mappings.get(field.name)
                if not mapping or mapping == "None":
                    missing_mappings.append(field.name)
            
            # Check custom required fields
            custom_fields = st.session_state.custom_field_manager.get_all_custom_fields()
            for custom_field in custom_fields:
                if custom_field.is_required:
                    mapping = st.session_state.field_mappings.get(custom_field.name)
                    if not mapping or mapping == "None":
                        missing_mappings.append(f"{custom_field.name} (custom)")
            
            if missing_mappings:
                st.warning(f"⚠️ Missing recommended field mappings: {', '.join(missing_mappings)}")
                st.info("💡 You can still generate XML - missing fields will use defaults or be empty")
            else:
                st.success("✅ All required fields are mapped!")
            
            # Generate buttons (always enabled)
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                generate_button = st.button(
                    "🚀 Generate MiFIR XML", 
                    type="primary", 
                    use_container_width=True,
                    help="Generate full MiFIR XML with standard + custom fields"
                )
            
            with col2:
                custom_only_button = st.button(
                    "🔧 Generate Custom Fields Only XML",
                    use_container_width=True,
                    help="Generate XML using only your custom fields"
                )
            
            with col3:
                # Show custom fields count
                custom_count = len(st.session_state.custom_field_manager.get_all_custom_fields())
                st.metric("Custom Fields", custom_count)
                if custom_count > 0:
                    st.caption("Available for custom XML")
            
            if generate_button:  # Always allow generation
                try:
                    # Add creation date to constants
                    st.session_state.constants["creation_date"] = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
                    
                    # Generate XML (including custom fields)
                    generator = MiFIRXMLGenerator()
                    xml_content = generator.generate_xml(
                        df, 
                        st.session_state.field_mappings, 
                        st.session_state.constants,
                        st.session_state.custom_field_manager
                    )
                    
                    st.success("✅ MiFIR compliant XML generated successfully!")
                    
                    # Show statistics
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Transactions", len(df))
                    with col2:
                        st.metric("XML Size", f"{len(xml_content):,} chars")
                    with col3:
                        mapped_fields = sum(1 for v in st.session_state.field_mappings.values() if v and v != "None")
                        st.metric("Mapped Fields", mapped_fields)
                    with col4:
                        total_fields = len(MIFIR_FIELDS) + len(st.session_state.custom_field_manager.get_all_custom_fields())
                        st.metric("Total Fields", total_fields)
                        if len(st.session_state.custom_field_manager.get_all_custom_fields()) > 0:
                            st.caption(f"({len(st.session_state.custom_field_manager.get_all_custom_fields())} custom)")
                    
                    # Show XML preview
                    st.subheader("📄 Generated XML Preview")
                    st.code(xml_content[:2000] + "\n..." if len(xml_content) > 2000 else xml_content, language="xml")
                    
                    # Download button
                    st.download_button(
                        label="📥 Download MiFIR XML",
                        data=xml_content,
                        file_name=f"mifir_rts22_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml",
                        mime="application/xml",
                        use_container_width=True
                    )
                    
                    # Show mapping summary
                    with st.expander("📋 Mapping Summary", expanded=False):
                        mapping_df = pd.DataFrame([
                            {"MiFIR Field": k, "Mapping": v, "Type": "Constant" if v == "[Constant Value]" else "CSV Column"}
                            for k, v in st.session_state.field_mappings.items()
                            if v and v != "None"
                        ])
                        st.dataframe(mapping_df, use_container_width=True)
                
                except Exception as e:
                    st.error(f"❌ Error generating XML: {str(e)}")
                    st.exception(e)
            
            # Custom-only XML generation
            if custom_only_button:
                custom_fields = st.session_state.custom_field_manager.get_all_custom_fields()
                
                if not custom_fields:
                    st.warning("⚠️ No custom fields defined. Create custom fields first in the 'Custom Fields' tab.")
                else:
                    try:
                        # Add creation date to constants
                        st.session_state.constants["creation_date"] = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
                        
                        # Generate custom-only XML
                        custom_generator = CustomOnlyXMLGenerator()
                        custom_xml_content = custom_generator.generate_custom_xml(
                            df,
                            st.session_state.field_mappings,
                            st.session_state.constants,
                            st.session_state.custom_field_manager
                        )
                        
                        st.success("✅ Custom fields only XML generated successfully!")
                        
                        # Show statistics
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Transactions", len(df))
                        with col2:
                            st.metric("XML Size", f"{len(custom_xml_content):,} chars")
                        with col3:
                            mapped_custom_fields = sum(1 for field in custom_fields 
                                                     if st.session_state.field_mappings.get(field.name, "None") != "None")
                            st.metric("Mapped Custom Fields", mapped_custom_fields)
                        with col4:
                            st.metric("Total Custom Fields", len(custom_fields))
                        
                        # Show XML preview
                        st.subheader("📄 Custom Fields XML Preview")
                        st.code(custom_xml_content[:2000] + "\n..." if len(custom_xml_content) > 2000 else custom_xml_content, 
                               language="xml")
                        
                        # Download button
                        st.download_button(
                            label="📥 Download Custom Fields XML",
                            data=custom_xml_content,
                            file_name=f"custom_fields_only_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml",
                            mime="application/xml",
                            use_container_width=True
                        )
                        
                        # Show custom fields breakdown
                        with st.expander("📋 Custom Fields Breakdown", expanded=False):
                            breakdown_data = []
                            for field in custom_fields:
                                mapping = st.session_state.field_mappings.get(field.name, "None")
                                breakdown_data.append({
                                    "Custom Field": field.name,
                                    "XML Element": f"<{field.xml_element_name}>",
                                    "Category": field.category.value,
                                    "Type": field.field_type.value,
                                    "Mapping": mapping,
                                    "Status": "✅ Mapped" if mapping != "None" else "⚠️ Using default"
                                })
                            
                            breakdown_df = pd.DataFrame(breakdown_data)
                            st.dataframe(breakdown_df, use_container_width=True)
                        
                        st.success(f"🎉 Generated XML with {len(custom_fields)} custom fields!")
                        
                    except Exception as e:
                        st.error(f"❌ Error generating custom XML: {str(e)}")
                        st.exception(e)
        
        except Exception as e:
            st.error(f"❌ Error reading file: {str(e)}")
    
    else:
        st.info("👆 Upload a CSV or Excel file to begin mapping")
        
        # Show information about MiFIR fields
        st.subheader("ℹ️ About MiFIR RTS 22 Fields")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Required Fields", len(get_required_fields()))
            st.caption("Must be mapped or provided as constants")
        
        with col2:
            st.metric("Conditional Fields", len(get_conditional_fields()))
            st.caption("Buyer/Seller information based on data")
        
        with col3:
            st.metric("Optional Fields", len(get_optional_fields()))
            st.caption("Additional information if available")
        
        st.markdown("""
        **Key MiFIR Requirements:**
        
        1. **ISIN from ANNA DSB** - Use proper DSB ISIN, not venue tickers
        2. **LEI or National ID** - Replace internal IDs with proper identifiers
        3. **Full UTC timestamps** - Complete ISO 8601 format
        4. **Proper venue codes** - MIC codes or XOFF for OTC
        5. **Buyer/Seller assignment** - Based on actual transaction sides
        """)
        
        # Add detailed field explanation
        st.subheader("🔍 Field Types Detailed")
        
        info_tab1, info_tab2, info_tab3, info_tab4 = st.tabs(["🔴 Required", "🟡 Conditional", "🟢 Optional", "⚙️ Constants"])
        
        with info_tab1:
            st.markdown("""
            ### 🔴 **Required Fields** (MUST be mapped)
            **Essential for MiFIR RTS 22 compliance - cannot be omitted:**
            
            | Field | Description | Why Required |
            |-------|-------------|--------------|
            | `reporting_party_lei` | Your firm's LEI code | Legal requirement - identifies report submitter |
            | `instrument_isin` | DSB ISIN for derivative | Core requirement - must use ANNA DSB ISIN |
            | `execution_datetime` | Trade execution timestamp | Regulatory timing requirement |
            | `trade_datetime` | Trade date/time | Settlement/clearing requirement |
            | `price_amount` | Transaction price | Core economic data |
            | `quantity` | Transaction quantity | Core economic data |
            | `transaction_id` | Unique transaction ID | Audit trail requirement |
            
            **💡 Only 7 fields required** - everything else has smart defaults!
            """)
        
        with info_tab2:
            st.markdown("""
            ### 🟡 **Conditional Fields** (Map IF you have the data)
            **Required only when certain conditions are met:**
            
            #### **Buyer Information** (IF buyer is identified):
            - **Legal Entity**: `buyer_lei` (20-character LEI code)
            - **Natural Person**: `buyer_first_name`, `buyer_last_name`, `buyer_birth_date`, `buyer_national_id`
            - **Optional**: `buyer_country` (country of branch)
            
            #### **Seller Information** (IF seller is identified):
            - **Legal Entity**: `seller_lei` (20-character LEI code)
            - **Natural Person**: `seller_first_name`, `seller_last_name`, `seller_birth_date`, `seller_national_id`
            - **Optional**: `seller_country` (country of branch)
            
            #### **Decision Makers** (IF you track decision makers):
            - `investment_decision_person` - National ID of investment decision maker
            - `investment_decision_algo` - Algorithm ID for investment decisions
            - `execution_decision_person` - National ID of execution decision maker
            - `execution_decision_algo` - Algorithm ID for execution decisions
            
            **💡 Logic**: Use either LEI (companies) OR person details (individuals), not both.
            """)
        
        with info_tab3:
            st.markdown("""
            ### 🟢 **Optional Fields** (Auto-populated with smart defaults)
            **You don't need to map these - they have sensible defaults:**
            
            | Field | Default | Description |
            |-------|---------|-------------|
            | `tech_record_id` | Auto-generated | Internal record ID |
            | `instrument_cfi` | `FXXXXX` | CFI classification |
            | `settlement_date` | Not included | Settlement date |
            | `trading_venue` | `XOFF` | OTC for crypto exchanges |
            | `trading_capacity` | `PRIN` | Principal trading |
            | `price_currency` | `USD` | Crypto derivative currency |
            | `short_sale_indicator` | `NSHO` | Not applicable for crypto |
            | `commodity_derivative_indicator` | `N` | Not commodity |
            | `clearing_indicator` | `N` | Not cleared |
            | `securities_financing_indicator` | `N` | Not SFT |
            
            **💡 Override defaults**: Map these fields if you need different values.
            """)
        
        with info_tab4:
            st.markdown("""
            ### ⚙️ **Constants** (Fixed values for all transactions)
            
            #### **Header Constants** (ISO 20022 envelope):
            - `from_org_id` - Your organization code (e.g., "KD")
            - `to_org_id` - Regulator code (e.g., "CY" for Cyprus)
            - `biz_msg_id` - Business message identifier
            
            #### **Field Constants** (When you select [Constant Value]):
            When you map a field to **[Constant Value]**, set the value here for ALL transactions.
            
            **Examples:**
            - `reporting_party_lei` = [Constant Value] → `"2138001ME4Z9Z8DZNS52"`
            - `instrument_isin` = [Constant Value] → `"US0231351067"`
            - `trading_venue` = [Constant Value] → `"XOFF"`
            
            **💡 Use constants for**: Values that don't change between transactions.
            """)
        
        st.markdown("---")
        
        # Add status indicator
        st.success("🎉 **MiFIR RTS 22 Mapper Ready!** Upload your CSV/Excel file above to begin mapping.")

if __name__ == "__main__":
    main()
