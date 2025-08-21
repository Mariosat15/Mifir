"""
MiFIR RTS 22 Field Definitions for auth.016.001.01
"""

from dataclasses import dataclass
from typing import List, Optional, Dict
from enum import Enum

class FieldType(Enum):
    STRING = "string"
    DECIMAL = "decimal" 
    DATETIME = "datetime"
    BOOLEAN = "boolean"
    ENUM = "enum"

class RequirementLevel(Enum):
    REQUIRED = "required"
    CONDITIONAL = "conditional"
    OPTIONAL = "optional"

@dataclass
class MiFIRField:
    name: str
    xpath: str
    field_type: FieldType
    requirement: RequirementLevel
    description: str
    example_value: str = ""
    enum_values: Optional[List[str]] = None
    notes: str = ""

# MiFIR RTS 22 Fields for Transaction Reporting
MIFIR_FIELDS = [
    # A) Reporting/Envelope Fields
    MiFIRField(
        "reporting_party_lei", 
        "RptgPrty/LEI", 
        FieldType.STRING, 
        RequirementLevel.REQUIRED,
        "Reporting party LEI (your firm)",
        "2138001ME4Z9Z8DZNS52",
        notes="Your firm's LEI code"
    ),
    
    MiFIRField(
        "report_action_type", 
        "New/Crrctn/Cxl", 
        FieldType.ENUM, 
        RequirementLevel.OPTIONAL,
        "Report action type",
        "New",
        enum_values=["New", "Correction", "Cancel"],
        notes="Defaults to 'New' for new reports"
    ),
    
    MiFIRField(
        "tech_record_id", 
        "TechRcrdId", 
        FieldType.STRING, 
        RequirementLevel.OPTIONAL,
        "Unique technical record ID",
        "TXN_001_20250819",
        notes="Auto-generated if not provided"
    ),
    
    # B) Instrument identification (must be ISIN)
    MiFIRField(
        "instrument_isin", 
        "FinInstrmId/Id/ISIN", 
        FieldType.STRING, 
        RequirementLevel.REQUIRED,
        "Financial instrument ISIN from ANNA DSB",
        "US0231351067",
        notes="Must be DSB ISIN for the derivative, not crypto ticker"
    ),
    
    MiFIRField(
        "instrument_cfi", 
        "FinInstrmId/CFI", 
        FieldType.STRING, 
        RequirementLevel.OPTIONAL,
        "CFI classification code",
        "FXXXXX",
        notes="6-character CFI code - can be provided as constant"
    ),
    
    # C) Execution details
    MiFIRField(
        "execution_datetime", 
        "ExctnDtTm", 
        FieldType.DATETIME, 
        RequirementLevel.REQUIRED,
        "Execution date and time (UTC with milliseconds)",
        "2025-08-19T22:23:00.300Z",
        notes="Full ISO 8601 UTC timestamp with milliseconds"
    ),
    
    MiFIRField(
        "trade_datetime", 
        "TradDtTm", 
        FieldType.DATETIME, 
        RequirementLevel.REQUIRED,
        "Trade date and time (UTC)",
        "2025-08-19T22:23:00.300Z",
        notes="Full ISO 8601 UTC timestamp with milliseconds"
    ),
    
    MiFIRField(
        "settlement_date", 
        "SttlmDt", 
        FieldType.STRING, 
        RequirementLevel.CONDITIONAL,
        "Settlement date (if applicable)",
        "2025-08-21",
        notes="Format: YYYY-MM-DD, if applicable to the product"
    ),
    
    MiFIRField(
        "trading_venue", 
        "TradgVn/MIC", 
        FieldType.ENUM, 
        RequirementLevel.OPTIONAL,
        "Trading venue MIC code",
        "XOFF",
        enum_values=["XOFF", "SINT", "XXXX"],
        notes="Defaults to XOFF (OTC) for crypto exchanges"
    ),
    
    MiFIRField(
        "trading_capacity", 
        "TradgCpcty", 
        FieldType.ENUM, 
        RequirementLevel.OPTIONAL,
        "Trading capacity",
        "PRIN",
        enum_values=["PRIN", "AGEN", "MTCH"],
        notes="Defaults to PRIN (Principal)"
    ),
    
    MiFIRField(
        "price_amount", 
        "Pric/Amt", 
        FieldType.DECIMAL, 
        RequirementLevel.REQUIRED,
        "Transaction price",
        "144.01",
        notes="Price in contract currency"
    ),
    
    MiFIRField(
        "price_currency", 
        "Pric/Amt/@Ccy", 
        FieldType.STRING, 
        RequirementLevel.OPTIONAL,
        "Price currency",
        "USD",
        notes="Defaults to USD for crypto derivatives"
    ),
    
    MiFIRField(
        "quantity", 
        "Qty", 
        FieldType.DECIMAL, 
        RequirementLevel.REQUIRED,
        "Transaction quantity",
        "0.01",
        notes="Quantity in contract units"
    ),
    
    # Buyer Fields
    MiFIRField(
        "buyer_lei", 
        "Buyr/AcctOwnr/Id/Org/LEI", 
        FieldType.STRING, 
        RequirementLevel.CONDITIONAL,
        "Buyer LEI (if legal entity)",
        "506700N3EE6U50944T62",
        notes="Use LEI for legal entities, national ID for natural persons"
    ),
    
    MiFIRField(
        "buyer_national_id", 
        "Buyr/AcctOwnr/Id/Prsn/Othr/Id", 
        FieldType.STRING, 
        RequirementLevel.CONDITIONAL,
        "Buyer national ID (if natural person)",
        "BE592344987958",
        notes="Use when buyer is a natural person"
    ),
    
    MiFIRField(
        "buyer_first_name", 
        "Buyr/AcctOwnr/Id/Prsn/FrstNm", 
        FieldType.STRING, 
        RequirementLevel.CONDITIONAL,
        "Buyer first name (if natural person)",
        "MATHIEU MANUEL M"
    ),
    
    MiFIRField(
        "buyer_last_name", 
        "Buyr/AcctOwnr/Id/Prsn/Nm", 
        FieldType.STRING, 
        RequirementLevel.CONDITIONAL,
        "Buyer last name (if natural person)",
        "DE KONINCK"
    ),
    
    MiFIRField(
        "buyer_birth_date", 
        "Buyr/AcctOwnr/Id/Prsn/BirthDt", 
        FieldType.STRING, 
        RequirementLevel.CONDITIONAL,
        "Buyer birth date (if natural person)",
        "1994-08-31",
        notes="Format: YYYY-MM-DD"
    ),
    
    MiFIRField(
        "buyer_country", 
        "Buyr/AcctOwnr/CtryOfBrnch", 
        FieldType.STRING, 
        RequirementLevel.CONDITIONAL,
        "Buyer country of branch",
        "CY",
        notes="ISO 3166-1 alpha-2 country code"
    ),
    
    # Seller Fields  
    MiFIRField(
        "seller_lei", 
        "Sellr/AcctOwnr/Id/Org/LEI", 
        FieldType.STRING, 
        RequirementLevel.CONDITIONAL,
        "Seller LEI (if legal entity)",
        "506700N3EE6U50944T62"
    ),
    
    MiFIRField(
        "seller_national_id", 
        "Sellr/AcctOwnr/Id/Prsn/Othr/Id", 
        FieldType.STRING, 
        RequirementLevel.CONDITIONAL,
        "Seller national ID (if natural person)",
        "BE592344987958"
    ),
    
    MiFIRField(
        "seller_first_name", 
        "Sellr/AcctOwnr/Id/Prsn/FrstNm", 
        FieldType.STRING, 
        RequirementLevel.CONDITIONAL,
        "Seller first name (if natural person)",
        "SEBASTIAN"
    ),
    
    MiFIRField(
        "seller_last_name", 
        "Sellr/AcctOwnr/Id/Prsn/Nm", 
        FieldType.STRING, 
        RequirementLevel.CONDITIONAL,
        "Seller last name (if natural person)",
        "NEVADO"
    ),
    
    MiFIRField(
        "seller_birth_date", 
        "Sellr/AcctOwnr/Id/Prsn/BirthDt", 
        FieldType.STRING, 
        RequirementLevel.CONDITIONAL,
        "Seller birth date (if natural person)",
        "1978-10-31"
    ),
    
    MiFIRField(
        "seller_country", 
        "Sellr/AcctOwnr/CtryOfBrnch", 
        FieldType.STRING, 
        RequirementLevel.CONDITIONAL,
        "Seller country of branch",
        "CY"
    ),
    
    # E) Decision-maker fields (RTS 22 core controls)
    MiFIRField(
        "investment_decision_person", 
        "Buyr/DcsnMakr/Prsn/Id", 
        FieldType.STRING, 
        RequirementLevel.CONDITIONAL,
        "Investment decision maker (natural person national ID)",
        "BE592344987958",
        notes="National ID of person who made investment decision"
    ),
    
    MiFIRField(
        "investment_decision_algo", 
        "Buyr/DcsnMakr/Algo/Id", 
        FieldType.STRING, 
        RequirementLevel.CONDITIONAL,
        "Investment decision algorithm ID",
        "ALGO_001",
        notes="Algorithm ID if investment decision was algorithmic"
    ),
    
    MiFIRField(
        "execution_decision_person", 
        "ExctnWthnFirm/Prsn/Id", 
        FieldType.STRING, 
        RequirementLevel.CONDITIONAL,
        "Execution decision maker (natural person national ID)",
        "BE592344987958",
        notes="National ID of person who made execution decision"
    ),
    
    MiFIRField(
        "execution_decision_algo", 
        "ExctnWthnFirm/Algo/Id", 
        FieldType.STRING, 
        RequirementLevel.CONDITIONAL,
        "Execution decision algorithm ID",
        "ALGO_002",
        notes="Algorithm ID if execution decision was algorithmic"
    ),
    
    # F) Flags & indicators (defaults provided for crypto derivatives)
    MiFIRField(
        "short_sale_indicator", 
        "ShrtSellgInd", 
        FieldType.ENUM, 
        RequirementLevel.OPTIONAL,
        "Short sale indicator",
        "NSHO",
        enum_values=["SESH", "SSEX", "SELL", "NSHO"],
        notes="Defaults to NSHO (N/A for crypto derivatives)"
    ),
    
    MiFIRField(
        "commodity_derivative_indicator", 
        "CmmdtyDerivInd", 
        FieldType.ENUM, 
        RequirementLevel.OPTIONAL,
        "Commodity derivative indicator",
        "N",
        enum_values=["Y", "N"],
        notes="Defaults to N (not a commodity derivative for crypto)"
    ),
    
    MiFIRField(
        "clearing_indicator", 
        "ClrngInd", 
        FieldType.ENUM, 
        RequirementLevel.OPTIONAL,
        "Clearing indicator",
        "N",
        enum_values=["Y", "N"],
        notes="Defaults to N (not cleared)"
    ),
    
    MiFIRField(
        "securities_financing_indicator", 
        "SctiesFincgTxInd", 
        FieldType.ENUM, 
        RequirementLevel.OPTIONAL,
        "Securities financing transaction indicator",
        "N",
        enum_values=["Y", "N"],
        notes="Defaults to N (not SFT)"
    ),
    
    # G) Firm/branch context
    MiFIRField(
        "country_of_branch", 
        "CtryOfBrnch", 
        FieldType.STRING, 
        RequirementLevel.CONDITIONAL,
        "Country of branch responsible for report",
        "CY",
        notes="ISO 3166-1 alpha-2 country code of booking/execution branch"
    ),
    
    MiFIRField(
        "investment_firm_covered", 
        "InvstmtFirmCvrd", 
        FieldType.ENUM, 
        RequirementLevel.CONDITIONAL,
        "Investment firm covered indicator",
        "Y",
        enum_values=["Y", "N"],
        notes="Whether investment firm is covered by MiFID II"
    ),
    
    MiFIRField(
        "transaction_id", 
        "TxId", 
        FieldType.STRING, 
        RequirementLevel.REQUIRED,
        "Transaction identifier",
        "5068869479P90006167594",
        notes="Unique transaction identifier"
    ),
    

]

def get_required_fields() -> List[MiFIRField]:
    """Get only required MiFIR fields."""
    return [field for field in MIFIR_FIELDS if field.requirement == RequirementLevel.REQUIRED]

def get_conditional_fields() -> List[MiFIRField]:
    """Get conditional MiFIR fields."""
    return [field for field in MIFIR_FIELDS if field.requirement == RequirementLevel.CONDITIONAL]

def get_optional_fields() -> List[MiFIRField]:
    """Get optional MiFIR fields."""
    return [field for field in MIFIR_FIELDS if field.requirement == RequirementLevel.OPTIONAL]

def get_field_by_name(name: str) -> Optional[MiFIRField]:
    """Get MiFIR field by name."""
    for field in MIFIR_FIELDS:
        if field.name == name:
            return field
    return None

def get_buyer_seller_logic_fields() -> List[str]:
    """Get fields that help determine buyer/seller assignment."""
    return [
        "taker_side_ordertype_sellorbuy",  # buy/sell determines who is buyer/seller
        "maker_side_ordertype_sellorbuy",
        "taker_side_quote_askorbid",
        "maker_side_quote_askorbid"
    ]
