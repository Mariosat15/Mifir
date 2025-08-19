# CSV/XLSX to KD_DATTRA XML Converter

A Streamlit application that converts CSV or XLSX files to XML format following the exact structure of KD_DATTRA_CY_000030-0-000029_22.xml.

## Features

- **File Upload**: Support for CSV and XLSX files
- **Smart Field Mapping**: Auto-suggest column mappings using fuzzy matching
- **Interactive UI**: Easy-to-use interface for mapping columns to XML fields
- **Data Transformation**: Built-in transformations for dates, numbers, and text
- **Constants Support**: Set constant values for fields that don't vary per row
- **Validation**: Comprehensive validation of required fields and data types
- **XML Preview**: Preview generated XML before download
- **Configuration Save/Load**: Save and reuse mapping configurations

## Installation

1. Clone or download this repository
2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Start the Streamlit application:
   ```bash
   streamlit run app.py
   ```

2. Open your browser and navigate to the displayed URL (typically `http://localhost:8501`)

3. Follow the application workflow:
   - **Step 1**: Upload your CSV or XLSX file
   - **Step 2**: Map your columns to XML fields
   - **Step 3**: Validate and generate XML

## File Structure

- `app.py` - Main Streamlit application
- `xml_schema.py` - XML schema definitions and field configurations
- `field_mapper.py` - Auto-mapping logic using fuzzy matching
- `data_transformer.py` - Data transformation and normalization utilities
- `xml_generator.py` - XML generation following KD_DATTRA structure
- `requirements.txt` - Python dependencies

## XML Structure

The application generates XML files that strictly follow the structure of:
- ISO 20022 standard
- KD_DATTRA format
- Exact namespaces, element order, and hierarchy as the sample file

## Field Mapping

### Required Fields
These fields must be mapped or have constant values:
- Transaction ID
- Executing Party
- Trade Date
- Quantity
- Price
- Currency
- Instrument Name
- And more...

### Optional/Conditional Fields
- Buyer/Seller information (LEI for legal entities, personal details for individuals)
- Additional transaction attributes
- Instrument-specific details

### Transformations
- **Date Formatting**: Automatic conversion to ISO format
- **Number Formatting**: Decimal normalization
- **Text Transformations**: Uppercase, lowercase, custom expressions
- **Boolean Values**: Standardization to true/false

## Example Usage

1. Upload `Test trades.csv` (sample file included)
2. Use auto-suggest to map common fields like:
   - `fills_trade_id` → `tx_id`
   - `fills_timestamp` → `trade_date`
   - `fills_symbol` → `instrument_name`
   - `fills_price` → `price`
   - `fills_quantity` → `quantity`
3. Set constants for header fields like organization IDs
4. Generate and download the XML file

## Validation

The application validates:
- All required fields are mapped
- Data types match field requirements
- Enum values are valid
- Date/time formats are correct
- Numeric values are properly formatted

## Configuration Management

- **Save Configuration**: Export field mappings as JSON for reuse
- **Load Configuration**: Import previously saved mapping configurations
- **Session Persistence**: Mappings persist during the current session

## Troubleshooting

### Common Issues

1. **File Upload Errors**
   - Ensure file is valid CSV or XLSX format
   - Check for encoding issues (UTF-8 recommended)

2. **Mapping Validation Errors**
   - Verify all required fields are mapped
   - Check constant values are provided where needed

3. **XML Generation Errors**
   - Validate data formats match field requirements
   - Check for missing or invalid enum values

### Support

For issues or questions, please review the field definitions in `xml_schema.py` and ensure your data matches the expected formats.
