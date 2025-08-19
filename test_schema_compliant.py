"""
Test schema-compliant XML generation following ESMAUG 1.1.0 order.
"""

import pandas as pd
from mifir_xml_generator import MiFIRXMLGenerator
from custom_fields import CustomFieldManager
from datetime import datetime

def test_schema_compliant():
    """Test schema-compliant XML generation."""
    
    print("🎯 TESTING SCHEMA-COMPLIANT XML (ESMAUG 1.1.0)")
    print("="*60)
    
    try:
        # Use the Sample_MiFIR_Data.csv
        df = pd.read_csv('Sample_MiFIR_Data.csv')
        print(f"✅ Loaded CSV: {len(df)} rows")
        
        # Show first row
        first_row = df.iloc[0]
        print(f"\n📊 FIRST ROW DATA:")
        print(f"   transaction_id: {first_row['transaction_id']}")
        print(f"   buyer_lei: {first_row['buyer_lei']}")
        print(f"   seller_lei: {first_row['seller_lei']}")
        print(f"   price_amount: {first_row['price_amount']}")
        print(f"   trading_capacity: {first_row['trading_capacity']}")
        
        # Create schema-compliant field mappings
        field_mappings = {
            # Required in schema order
            "transaction_id": "transaction_id",
            "executing_party": "reporting_party_lei",  # Use reporting party as executing party
            "investment_party_ind": "[Constant Value]",
            "reporting_party_lei": "reporting_party_lei",  # Maps to SubmitgPty
            
            # Buyer/Seller
            "buyer_lei": "buyer_lei",
            "seller_lei": "seller_lei",
            
            # Trading details (go under Tx block)
            "trade_datetime": "trade_datetime",
            "trading_capacity": "trading_capacity", 
            "quantity": "quantity",
            "price_amount": "price_amount",
            "price_currency": "price_currency",
            "trading_venue": "trading_venue",
            
            # Instrument
            "instrument_name": "instrument_symbol",
            "instrument_isin": "instrument_isin",
            "classification_type": "[Constant Value]",
            "notional_currency": "price_currency",
            
            # Additional attributes
            "short_sale_indicator": "short_sale_indicator",
            "securities_financing_indicator": "securities_financing_indicator"
        }
        
        # Constants with schema-compliant values
        constants = {
            "from_org_id": "KD",
            "to_org_id": "CY",
            "biz_msg_id": "SCHEMA_COMPLIANT_TEST",
            "creation_date": datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
            "investment_party_ind": "true",
            "classification_type": "SESTXC",
            "transmission_indicator": "false"
        }
        
        print(f"\n🗺️ SCHEMA-COMPLIANT MAPPINGS:")
        for mifir_field, csv_column in field_mappings.items():
            if csv_column in df.columns:
                sample_value = first_row[csv_column]
                print(f"   ✅ {mifir_field} → {csv_column} = '{sample_value}'")
            elif csv_column == "[Constant Value]":
                const_value = constants.get(mifir_field, "DEFAULT")
                print(f"   ⚙️ {mifir_field} → [Constant] = '{const_value}'")
            else:
                print(f"   ❌ {mifir_field} → {csv_column} (NOT FOUND)")
        
        # Generate schema-compliant XML
        print(f"\n🚀 GENERATING SCHEMA-COMPLIANT XML...")
        generator = MiFIRXMLGenerator()
        custom_manager = CustomFieldManager()
        
        # Test with first row only
        test_df = df.head(1)
        xml_content = generator.generate_xml(test_df, field_mappings, constants, custom_manager)
        
        print(f"✅ Generated XML: {len(xml_content)} characters")
        
        # Save schema-compliant XML
        with open('schema_compliant_output.xml', 'w', encoding='utf-8') as f:
            f.write(xml_content)
        print(f"✅ Saved to schema_compliant_output.xml")
        
        # Verify schema order
        print(f"\n🔍 SCHEMA ORDER VERIFICATION:")
        
        # Extract the New block
        lines = xml_content.split('\n')
        new_block_lines = []
        in_new_block = False
        
        for line in lines:
            if '<New>' in line:
                in_new_block = True
            elif '</New>' in line:
                new_block_lines.append(line)
                break
            
            if in_new_block:
                new_block_lines.append(line)
        
        # Check element order
        elements_found = []
        for line in new_block_lines:
            line = line.strip()
            if line.startswith('<') and not line.startswith('</') and not line.startswith('<!--'):
                # Extract element name
                element = line.split('>')[0].replace('<', '')
                if ' ' in element:
                    element = element.split(' ')[0]
                elements_found.append(element)
        
        # Expected schema order
        expected_order = [
            "New", "TxId", "ExctgPty", "InvstmtPtyInd", "SubmitgPty", 
            "Buyr", "Sellr", "OrdrTrnsmssn", "Tx", "FinInstrm", "ExctgPrsn", "AddtlAttrbts"
        ]
        
        print(f"   Expected order: {' → '.join(expected_order)}")
        print(f"   Actual order:   {' → '.join(elements_found[:len(expected_order)])}")
        
        # Check if order matches
        order_correct = True
        for i, expected in enumerate(expected_order):
            if i < len(elements_found):
                actual = elements_found[i]
                if actual == expected:
                    print(f"   ✅ Position {i+1}: {expected}")
                else:
                    print(f"   ❌ Position {i+1}: Expected {expected}, got {actual}")
                    order_correct = False
            else:
                print(f"   ❌ Position {i+1}: Missing {expected}")
                order_correct = False
        
        # Check schema-compliant values
        print(f"\n🔍 SCHEMA-COMPLIANT VALUES:")
        print(f"   TradgCpcty (DEAL/MTCH/AOTC): {'AOTC' in xml_content or 'DEAL' in xml_content or 'MTCH' in xml_content}")
        print(f"   ShrtSellgInd (SESH/SELL/SSEX/UNDI): {'UNDI' in xml_content or 'SELL' in xml_content}")
        print(f"   TradVn (simple): {'<TradVn>' in xml_content and '<MIC>' not in xml_content}")
        print(f"   Buyer LEI: {'549300XYZABCDEFG5678' in xml_content}")
        print(f"   Seller LEI: {'213800ABCDEFGHIJ1234' in xml_content}")
        
        if order_correct:
            print(f"\n🎉 SUCCESS: XML follows ESMAUG 1.1.0 schema order!")
        else:
            print(f"\n⚠️ ISSUES: XML order needs adjustment for schema compliance")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_schema_compliant()
