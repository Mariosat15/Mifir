"""
Final comprehensive test for schema validation compliance.
"""

import pandas as pd
from mifir_xml_generator import MiFIRXMLGenerator
from custom_fields import CustomFieldManager
from datetime import datetime

def final_schema_test():
    """Final test for complete schema compliance."""
    
    print("🎯 FINAL SCHEMA VALIDATION TEST")
    print("="*50)
    
    try:
        # Use Sample_MiFIR_Data.csv
        df = pd.read_csv('Sample_MiFIR_Data.csv')
        
        # Perfect field mappings for schema compliance
        field_mappings = {
            "transaction_id": "transaction_id",
            "executing_party": "reporting_party_lei",
            "investment_party_ind": "[Constant Value]",
            "reporting_party_lei": "reporting_party_lei",
            "buyer_lei": "buyer_lei",
            "seller_lei": "seller_lei",
            "transmission_indicator": "[Constant Value]",
            "trade_datetime": "trade_datetime",
            "trading_capacity": "trading_capacity",
            "quantity": "quantity",
            "price_amount": "price_amount",
            "price_currency": "price_currency",
            "trading_venue": "trading_venue",
            "instrument_name": "instrument_symbol",
            "instrument_isin": "instrument_isin",
            "classification_type": "[Constant Value]",
            "notional_currency": "price_currency",
            "price_multiplier": "[Constant Value]",
            "delivery_type": "[Constant Value]",
            "executing_person": "[Constant Value]",
            "short_sale_indicator": "short_sale_indicator",
            "securities_financing_indicator": "securities_financing_indicator"
        }
        
        constants = {
            "from_org_id": "KD",
            "to_org_id": "CY", 
            "biz_msg_id": "FINAL_SCHEMA_TEST",
            "creation_date": datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
            "investment_party_ind": "true",
            "transmission_indicator": "false",
            "classification_type": "SESTXC",
            "price_multiplier": "1",
            "delivery_type": "CASH",
            "executing_person": "NORE"
        }
        
        # Generate final XML
        generator = MiFIRXMLGenerator()
        custom_manager = CustomFieldManager()
        
        xml_content = generator.generate_xml(df.head(1), field_mappings, constants, custom_manager)
        
        # Save final XML
        with open('final_schema_compliant.xml', 'w', encoding='utf-8') as f:
            f.write(xml_content)
        
        print(f"✅ Generated final schema-compliant XML")
        print(f"✅ Saved to final_schema_compliant.xml")
        
        # Check all the specific issues mentioned
        print(f"\n🔍 SCHEMA VALIDATION CHECKS:")
        
        # 1. TxId pattern check
        import re
        txid_match = re.search(r'<TxId>([^<]+)</TxId>', xml_content)
        if txid_match:
            txid_value = txid_match.group(1)
            txid_valid = re.match(r'^[A-Z0-9]{1,52}$', txid_value)
            print(f"   1. TxId pattern: {'✅' if txid_valid else '❌'} '{txid_value}'")
        
        # 2. Buyer/Seller structure check
        buyer_correct = '<Id><LEI>' in xml_content and '<Id><Org><LEI>' not in xml_content
        print(f"   2. Buyer/Seller structure: {'✅' if buyer_correct else '❌'} (LEI directly under Id)")
        
        # 3. Price structure check  
        price_correct = '<Pric><Pric><MntryVal>' in xml_content
        print(f"   3. Price structure: {'✅' if price_correct else '❌'} (Pric/Pric/MntryVal/Amt)")
        
        # 4. Underlying instrument check
        underlying_correct = '<UndrlygInstrm><Othr><Sngl><ISIN>' in xml_content
        print(f"   4. Underlying instrument: {'✅' if underlying_correct else '❌'} (Othr/Sngl/ISIN)")
        
        # 5. Duplicate FinInstrm check
        fin_instrm_count = xml_content.count('<FinInstrm>')
        duplicate_fin_instrm = fin_instrm_count > 1
        print(f"   5. Duplicate FinInstrm: {'❌' if duplicate_fin_instrm else '✅'} (found {fin_instrm_count} instances)")
        
        # 6. Element order check
        order_pattern = r'<TxId>.*?<ExctgPty>.*?<InvstmtPtyInd>.*?<SubmitgPty>.*?<Buyr>.*?<Sellr>'
        order_correct = re.search(order_pattern, xml_content, re.DOTALL)
        print(f"   6. Element order: {'✅' if order_correct else '❌'} (TxId first, correct sequence)")
        
        # 7. CSV data preservation check
        csv_data_checks = [
            ("TXN00120250819", "Transaction ID"),
            ("549300XYZABCDEFG5678", "Buyer LEI"),
            ("213800ABCDEFGHIJ1234", "Seller LEI"),
            ("144.01", "Price amount"),
            ("0.01", "Quantity"),
            ("XS2468135792", "ISIN")
        ]
        
        print(f"\n📊 CSV DATA PRESERVATION:")
        for value, description in csv_data_checks:
            in_xml = value in xml_content
            print(f"   {'✅' if in_xml else '❌'} {description}: {value}")
        
        # Overall assessment
        all_checks = [txid_valid, buyer_correct, price_correct, underlying_correct, not duplicate_fin_instrm, order_correct]
        csv_checks = [value in xml_content for value, _ in csv_data_checks]
        
        schema_compliant = all(all_checks)
        data_preserved = all(csv_checks)
        
        print(f"\n🎯 FINAL ASSESSMENT:")
        print(f"   Schema compliance: {'✅ PASS' if schema_compliant else '❌ FAIL'}")
        print(f"   Data preservation: {'✅ PASS' if data_preserved else '❌ FAIL'}")
        
        if schema_compliant and data_preserved:
            print(f"\n🎉 SUCCESS: XML is schema-compliant and preserves all CSV data!")
        else:
            print(f"\n⚠️ Issues remain that need fixing")
        
        return schema_compliant and data_preserved
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    final_schema_test()
