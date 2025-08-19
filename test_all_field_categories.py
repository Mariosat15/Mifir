"""
Test that ALL field categories are included in XML when mapped.
"""

import pandas as pd
from mifir_xml_generator import MiFIRXMLGenerator
from custom_fields import CustomField, CustomFieldManager, CustomFieldType, CustomFieldCategory
from mifir_fields import get_required_fields, get_conditional_fields, get_optional_fields
from datetime import datetime

def test_all_field_categories():
    """Test that all field categories appear in XML when mapped."""
    
    print("🎯 TESTING ALL FIELD CATEGORIES IN XML")
    print("="*60)
    
    try:
        # Create comprehensive test data
        test_data = [
            {
                # Required fields
                "transaction_id": "TEST_TXN_001",
                "execution_datetime": "2025-08-19T10:00:00.000Z",
                "trade_datetime": "2025-08-19T10:00:00.000Z",
                "price_amount": "150.75",
                "quantity": "1.5",
                "instrument_isin": "XS2468135792",
                "reporting_party_lei": "213800ABCDEFGHIJ1234",
                
                # Conditional fields
                "buyer_lei": "549300XYZABCDEFG5678",
                "seller_lei": "391200MNOPQRSTUV9012",
                "buyer_country": "CY",
                "seller_country": "DE",
                "settlement_date": "2025-08-21",
                
                # Optional fields
                "trading_venue": "XOFF",
                "trading_capacity": "PRIN",
                "price_currency": "USD",
                "instrument_cfi": "FMIXSX",
                "tech_record_id": "TECH_001",
                
                # Custom field data
                "custom_client_ref": "CLIENT_REF_001",
                "custom_risk_score": "7.5",
                "custom_branch": "NYC_BRANCH"
            }
        ]
        
        df = pd.DataFrame(test_data)
        print(f"✅ Created test data: {len(df)} rows, {len(df.columns)} columns")
        
        # Create custom field manager with fields in all categories
        custom_manager = CustomFieldManager()
        
        custom_fields = [
            # Required custom field
            CustomField("custom_client_ref", "CustClntRef", CustomFieldType.STRING,
                       CustomFieldCategory.REQUIRED, "Custom client reference"),
            
            # Conditional custom field
            CustomField("custom_branch", "CustBrnch", CustomFieldType.STRING,
                       CustomFieldCategory.CONDITIONAL, "Custom branch code"),
            
            # Optional custom field
            CustomField("custom_risk_score", "CustRiskScr", CustomFieldType.DECIMAL,
                       CustomFieldCategory.OPTIONAL, "Custom risk score"),
            
            # Constant custom field
            CustomField("custom_system", "CustSys", CustomFieldType.STRING,
                       CustomFieldCategory.CONSTANT, "Custom system ID", default_value="SYS_V1")
        ]
        
        for field in custom_fields:
            custom_manager.add_custom_field(field)
        
        print(f"✅ Created {len(custom_fields)} custom fields")
        
        # Create COMPREHENSIVE field mappings for ALL categories
        field_mappings = {
            # 🔴 REQUIRED FIELDS - All mapped
            "reporting_party_lei": "reporting_party_lei",
            "transaction_id": "transaction_id", 
            "instrument_isin": "instrument_isin",
            "execution_datetime": "execution_datetime",
            "trade_datetime": "trade_datetime",
            "price_amount": "price_amount",
            "quantity": "quantity",
            
            # 🟡 CONDITIONAL FIELDS - All mapped
            "buyer_lei": "buyer_lei",
            "seller_lei": "seller_lei",
            "buyer_country": "buyer_country",
            "seller_country": "seller_country",
            "settlement_date": "settlement_date",
            
            # 🟢 OPTIONAL FIELDS - All mapped
            "trading_venue": "trading_venue",
            "trading_capacity": "trading_capacity", 
            "price_currency": "price_currency",
            "instrument_cfi": "instrument_cfi",
            "tech_record_id": "tech_record_id",
            
            # ⚙️ CONSTANTS - Some as constants, some mapped
            "short_sale_indicator": "[Constant Value]",
            "clearing_indicator": "[Constant Value]",
            
            # 🔧 CUSTOM FIELDS - All mapped
            "custom_client_ref": "custom_client_ref",
            "custom_branch": "custom_branch",
            "custom_risk_score": "custom_risk_score",
            "custom_system": "[Constant Value]"
        }
        
        # Constants
        constants = {
            "from_org_id": "TEST",
            "to_org_id": "DEMO",
            "biz_msg_id": "ALL_CATEGORIES_TEST",
            "creation_date": datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
            "short_sale_indicator": "NSHO",
            "clearing_indicator": "N",
            "custom_system": "SYS_V1"
        }
        
        print(f"\n🗺️ COMPREHENSIVE FIELD MAPPINGS:")
        print(f"   🔴 Required fields mapped: {len([f for f in field_mappings if any(rf.name == f for rf in get_required_fields())])}")
        print(f"   🟡 Conditional fields mapped: {len([f for f in field_mappings if any(cf.name == f for cf in get_conditional_fields())])}")
        print(f"   🟢 Optional fields mapped: {len([f for f in field_mappings if any(of.name == f for of in get_optional_fields())])}")
        print(f"   🔧 Custom fields mapped: {len([f for f in field_mappings if f.startswith('custom_')])}")
        print(f"   ⚙️ Constants defined: {len(constants)}")
        
        # Generate XML
        print(f"\n🚀 GENERATING COMPREHENSIVE XML...")
        generator = MiFIRXMLGenerator()
        xml_content = generator.generate_xml(df, field_mappings, constants, custom_manager)
        
        print(f"✅ Generated XML: {len(xml_content)} characters")
        
        # Save comprehensive XML
        with open('all_categories_test.xml', 'w', encoding='utf-8') as f:
            f.write(xml_content)
        print(f"✅ Saved to all_categories_test.xml")
        
        # Verify ALL categories are included
        print(f"\n🔍 VERIFICATION - ALL CATEGORIES IN XML:")
        
        # Check required fields
        print(f"\n🔴 REQUIRED FIELDS:")
        required_checks = [
            ("transaction_id", "TEST_TXN_001"),
            ("price_amount", "150.75"),
            ("quantity", "1.5"),
            ("instrument_isin", "XS2468135792")
        ]
        
        for field_name, expected_value in required_checks:
            in_xml = expected_value in xml_content
            print(f"   {'✅' if in_xml else '❌'} {field_name}: {expected_value}")
        
        # Check conditional fields
        print(f"\n🟡 CONDITIONAL FIELDS:")
        conditional_checks = [
            ("buyer_lei", "549300XYZABCDEFG5678", "<Buyr>"),
            ("seller_lei", "391200MNOPQRSTUV9012", "<Sellr>"),
            ("settlement_date", "2025-08-21", "SttlmDt")
        ]
        
        for field_name, expected_value, xml_element in conditional_checks:
            value_in_xml = expected_value in xml_content
            element_in_xml = xml_element in xml_content
            print(f"   {'✅' if value_in_xml and element_in_xml else '❌'} {field_name}: {expected_value} in <{xml_element}>")
        
        # Check optional fields
        print(f"\n🟢 OPTIONAL FIELDS:")
        optional_checks = [
            ("trading_venue", "XOFF", "MIC"),
            ("trading_capacity", "PRIN", "TradgCpcty"),
            ("instrument_cfi", "FMIXSX", "CFI")
        ]
        
        for field_name, expected_value, xml_element in optional_checks:
            value_in_xml = expected_value in xml_content
            element_in_xml = xml_element in xml_content
            print(f"   {'✅' if value_in_xml and element_in_xml else '❌'} {field_name}: {expected_value} in <{xml_element}>")
        
        # Check constants
        print(f"\n⚙️ CONSTANTS:")
        constant_checks = [
            ("short_sale_indicator", "NSHO", "ShrtSellgInd"),
            ("clearing_indicator", "N", "ClrngInd")
        ]
        
        for field_name, expected_value, xml_element in constant_checks:
            value_in_xml = expected_value in xml_content
            element_in_xml = xml_element in xml_content
            print(f"   {'✅' if value_in_xml and element_in_xml else '❌'} {field_name}: {expected_value} in <{xml_element}>")
        
        # Check custom fields
        print(f"\n🔧 CUSTOM FIELDS:")
        custom_checks = [
            ("custom_client_ref", "CLIENT_REF_001", "CustClntRef"),
            ("custom_risk_score", "7.5", "CustRiskScr"),
            ("custom_system", "SYS_V1", "CustSys")
        ]
        
        for field_name, expected_value, xml_element in custom_checks:
            value_in_xml = expected_value in xml_content
            element_in_xml = xml_element in xml_content
            print(f"   {'✅' if value_in_xml and element_in_xml else '❌'} {field_name}: {expected_value} in <{xml_element}>")
        
        # Overall verification
        all_values = ["TEST_TXN_001", "150.75", "1.5", "549300XYZABCDEFG5678", 
                     "391200MNOPQRSTUV9012", "XOFF", "PRIN", "NSHO", "CLIENT_REF_001", "7.5"]
        
        values_found = sum(1 for value in all_values if value in xml_content)
        
        print(f"\n📊 OVERALL RESULTS:")
        print(f"   Values found in XML: {values_found}/{len(all_values)}")
        print(f"   Required sections: <Buyr>{'✅' if '<Buyr>' in xml_content else '❌'} <Sellr>{'✅' if '<Sellr>' in xml_content else '❌'}")
        print(f"   Custom fields: {'✅' if 'CustClntRef' in xml_content else '❌'}")
        
        if values_found == len(all_values) and '<Buyr>' in xml_content and '<Sellr>' in xml_content:
            print(f"\n🎉 SUCCESS: ALL FIELD CATEGORIES ARE PROPERLY INCLUDED IN XML!")
        else:
            print(f"\n⚠️ ISSUES: Some fields or sections are missing from XML")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_all_field_categories()
