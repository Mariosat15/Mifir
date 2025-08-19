"""
Test that CSV data is properly mapped to XML.
"""

import pandas as pd
from mifir_xml_generator import MiFIRXMLGenerator
from custom_fields import CustomFieldManager
from datetime import datetime

def test_csv_to_xml_mapping():
    """Test proper CSV to XML mapping."""
    
    print("🔍 TESTING CSV TO XML MAPPING")
    print("="*50)
    
    try:
        # Load the Sample_MiFIR_Data.csv
        df = pd.read_csv('Sample_MiFIR_Data.csv')
        print(f"✅ Loaded CSV: {len(df)} rows")
        
        # Show first row data
        print(f"\n📊 FIRST ROW CSV DATA:")
        first_row = df.iloc[0]
        print(f"   transaction_id: {first_row['transaction_id']}")
        print(f"   price_amount: {first_row['price_amount']}")
        print(f"   quantity: {first_row['quantity']}")
        print(f"   buyer_lei: {first_row['buyer_lei']}")
        print(f"   seller_lei: {first_row['seller_lei']}")
        print(f"   instrument_isin: {first_row['instrument_isin']}")
        
        # Create DIRECT field mappings (CSV column names = MiFIR field names)
        field_mappings = {
            "reporting_party_lei": "reporting_party_lei",
            "transaction_id": "transaction_id",
            "instrument_isin": "instrument_isin",
            "execution_datetime": "execution_datetime", 
            "trade_datetime": "trade_datetime",
            "price_amount": "price_amount",
            "quantity": "quantity",
            "buyer_lei": "buyer_lei",      # CRITICAL: Should create <Buyr>
            "seller_lei": "seller_lei",    # CRITICAL: Should create <Sellr>
            "trading_venue": "trading_venue",
            "trading_capacity": "trading_capacity",
            "price_currency": "price_currency",
            "instrument_cfi": "instrument_cfi"
        }
        
        # Minimal constants
        constants = {
            "from_org_id": "KD",
            "to_org_id": "CY",
            "biz_msg_id": "CSV_TEST_MAPPING",
            "creation_date": datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
        }
        
        print(f"\n🗺️ TESTING FIELD MAPPINGS:")
        for mifir_field, csv_column in field_mappings.items():
            if csv_column in df.columns:
                sample_value = first_row[csv_column]
                print(f"   ✅ {mifir_field} → {csv_column} = '{sample_value}'")
            else:
                print(f"   ❌ {mifir_field} → {csv_column} (NOT FOUND)")
        
        # Generate XML with first row only
        print(f"\n🚀 GENERATING XML...")
        generator = MiFIRXMLGenerator()
        custom_manager = CustomFieldManager()
        
        test_df = df.head(1)  # Just first row
        xml_content = generator.generate_xml(test_df, field_mappings, constants, custom_manager)
        
        # Save and analyze
        with open('csv_mapped_output.xml', 'w', encoding='utf-8') as f:
            f.write(xml_content)
        
        print(f"✅ Generated XML: {len(xml_content)} characters")
        print(f"✅ Saved to csv_mapped_output.xml")
        
        # Verify CSV data appears in XML
        print(f"\n🔍 VERIFICATION - CSV DATA IN XML:")
        
        # Check transaction data
        csv_tx_id = str(first_row['transaction_id'])
        csv_price = str(first_row['price_amount'])
        csv_quantity = str(first_row['quantity'])
        csv_buyer = str(first_row['buyer_lei'])
        csv_seller = str(first_row['seller_lei'])
        csv_isin = str(first_row['instrument_isin'])
        
        print(f"   Transaction ID '{csv_tx_id}': {'✅' if csv_tx_id in xml_content else '❌'}")
        print(f"   Price '{csv_price}': {'✅' if csv_price in xml_content else '❌'}")
        print(f"   Quantity '{csv_quantity}': {'✅' if csv_quantity in xml_content else '❌'}")
        print(f"   Buyer LEI '{csv_buyer}': {'✅' if csv_buyer in xml_content else '❌'}")
        print(f"   Seller LEI '{csv_seller}': {'✅' if csv_seller in xml_content else '❌'}")
        print(f"   ISIN '{csv_isin}': {'✅' if csv_isin in xml_content else '❌'}")
        
        # Check XML structure
        print(f"\n🏗️ XML STRUCTURE CHECK:")
        print(f"   <Buyr> section: {'✅' if '<Buyr>' in xml_content else '❌'}")
        print(f"   <Sellr> section: {'✅' if '<Sellr>' in xml_content else '❌'}")
        print(f"   <RptgPrty> section: {'✅' if '<RptgPrty>' in xml_content else '❌'}")
        
        # Show relevant XML excerpt
        print(f"\n📄 XML EXCERPT (Transaction section):")
        lines = xml_content.split('\n')
        for i, line in enumerate(lines):
            if '<TxId>' in line:
                # Show 10 lines around TxId
                start = max(0, i-2)
                end = min(len(lines), i+15)
                for j in range(start, end):
                    print(f"   {lines[j]}")
                break
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_csv_to_xml_mapping()
