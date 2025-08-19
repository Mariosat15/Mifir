"""
Debug why the XML doesn't contain the CSV data properly.
"""

import pandas as pd
from mifir_xml_generator import MiFIRXMLGenerator
from custom_fields import CustomFieldManager
from datetime import datetime

def debug_xml_mapping():
    """Debug the XML mapping issue."""
    
    print("🔍 DEBUGGING XML MAPPING ISSUE")
    print("="*50)
    
    try:
        # Load the exact same CSV that was used
        df = pd.read_csv('Sample_MiFIR_Data.csv')
        print(f"✅ Loaded CSV: {len(df)} rows, {len(df.columns)} columns")
        
        # Show first row of CSV data
        print(f"\n📊 FIRST ROW OF CSV DATA:")
        first_row = df.iloc[0]
        for col, value in first_row.items():
            print(f"   {col}: {value}")
        
        # Create proper field mappings for the CSV
        field_mappings = {
            # Map CSV columns to MiFIR fields
            "reporting_party_lei": "reporting_party_lei",  # Direct mapping
            "transaction_id": "transaction_id",
            "instrument_isin": "instrument_isin", 
            "execution_datetime": "execution_datetime",
            "trade_datetime": "trade_datetime",
            "price_amount": "price_amount",
            "quantity": "quantity",
            "buyer_lei": "buyer_lei",  # This should create <Buyr> section
            "seller_lei": "seller_lei",  # This should create <Sellr> section
            "trading_venue": "trading_venue",
            "trading_capacity": "trading_capacity",
            "price_currency": "price_currency",
            "instrument_cfi": "instrument_cfi"
        }
        
        print(f"\n🗺️ FIELD MAPPINGS:")
        for mifir_field, csv_column in field_mappings.items():
            if csv_column in df.columns:
                sample_value = df[csv_column].iloc[0]
                print(f"   ✅ {mifir_field} → {csv_column} (sample: {sample_value})")
            else:
                print(f"   ❌ {mifir_field} → {csv_column} (COLUMN NOT FOUND)")
        
        # Constants (minimal)
        constants = {
            "from_org_id": "KD",
            "to_org_id": "CY",
            "biz_msg_id": f"DEBUG_TEST_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "creation_date": datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
        }
        
        # Generate XML with proper mappings
        print(f"\n🚀 GENERATING XML WITH PROPER MAPPINGS...")
        
        generator = MiFIRXMLGenerator()
        custom_manager = CustomFieldManager()
        
        # Test with just first row
        test_df = df.head(1)
        xml_content = generator.generate_xml(test_df, field_mappings, constants, custom_manager)
        
        print(f"✅ XML generated: {len(xml_content)} characters")
        
        # Save debug XML
        with open('debug_xml_output.xml', 'w', encoding='utf-8') as f:
            f.write(xml_content)
        print(f"✅ Saved to debug_xml_output.xml")
        
        # Check if buyer/seller sections are included
        print(f"\n🔍 XML CONTENT ANALYSIS:")
        print(f"   Contains <Buyr>: {'<Buyr>' in xml_content}")
        print(f"   Contains <Sellr>: {'<Sellr>' in xml_content}")
        print(f"   Contains buyer LEI: {'549300XYZABCDEFG5678' in xml_content}")
        print(f"   Contains seller LEI: {'213800ABCDEFGHIJ1234' in xml_content}")
        print(f"   Contains correct price: {'144.01' in xml_content}")
        print(f"   Contains correct quantity: {'0.01' in xml_content}")
        print(f"   Contains correct ISIN: {'XS2468135792' in xml_content}")
        
        # Show first transaction from XML
        print(f"\n📄 FIRST TRANSACTION IN XML:")
        lines = xml_content.split('\n')
        in_first_tx = False
        tx_lines = []
        
        for line in lines:
            if '<Tx>' in line:
                in_first_tx = True
            elif '</Tx>' in line and in_first_tx:
                tx_lines.append(line)
                break
            
            if in_first_tx:
                tx_lines.append(line)
        
        for line in tx_lines[:20]:  # Show first 20 lines of transaction
            print(f"   {line}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    debug_xml_mapping()
