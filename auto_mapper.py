"""
Auto-mapper for MiFIR fields - Intelligently suggests field mappings based on CSV data.
"""

import pandas as pd
import re
from typing import Dict, List, Tuple, Optional
from difflib import SequenceMatcher
from mifir_fields import MIFIR_FIELDS, MiFIRField

class AutoMapper:
    """Automatically suggests field mappings based on CSV column analysis."""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.columns = [col.strip() for col in df.columns]
        self.column_samples = self._get_column_samples()
        
        # Define mapping patterns for common field names
        self.mapping_patterns = {
            # Transaction core fields
            'transaction_id': ['trade_id', 'tx_id', 'transaction', 'fill_id', 'order_id'],
            'price_amount': ['price', 'amount', 'rate', 'px'],
            'quantity': ['quantity', 'qty', 'size', 'volume', 'amount'],
            'execution_datetime': ['timestamp', 'time', 'datetime', 'date', 'execution', 'trade_time'],
            'trade_datetime': ['timestamp', 'time', 'datetime', 'date', 'trade_time'],
            
            # Instrument identification
            'instrument_isin': ['isin', 'instrument', 'symbol', 'ticker', 'product'],
            
            # Party identification
            'buyer_lei': ['buyer', 'maker_user', 'maker_id', 'client_id'],
            'seller_lei': ['seller', 'taker_user', 'taker_id', 'counterparty'],
            
            # Trading details
            'trading_capacity': ['capacity', 'role', 'type'],
            'trading_venue': ['venue', 'exchange', 'mic'],
            
            # Fees and additional data
            'buyer_fee': ['maker_fee', 'buyer_fee', 'fee'],
            'seller_fee': ['taker_fee', 'seller_fee', 'fee'],
            
            # Side and position information
            'short_sale_indicator': ['position', 'side', 'long_short', 'direction'],
            'clearing_indicator': ['clearing', 'cleared', 'ccp'],
            
            # Order information
            'maker_order_id': ['maker_order', 'order_id'],
            'taker_order_id': ['taker_order', 'order_id'],
            
            # System information
            'tech_record_id': ['record_id', 'system_id', 'internal_id'],
        }
        
        # Define value patterns for content-based detection
        self.value_patterns = {
            'lei_pattern': r'^[A-Z0-9]{18}[0-9]{2}$',  # 20-character LEI
            'isin_pattern': r'^[A-Z]{2}[A-Z0-9]{9}[0-9]$',  # 12-character ISIN
            'timestamp_pattern': r'\d{1,2}:\d{1,2}',  # Time pattern
            'price_pattern': r'^\d+\.?\d*$',  # Numeric price
            'boolean_pattern': r'^(true|false|0|1|y|n|yes|no)$',  # Boolean values
            'currency_pattern': r'^[A-Z]{3}$',  # 3-letter currency codes
        }
    
    def _get_column_samples(self) -> Dict[str, List[str]]:
        """Get sample values from each column for analysis."""
        samples = {}
        for col in self.df.columns:
            # Get non-null, non-empty samples
            col_data = self.df[col].dropna()
            col_data = col_data[col_data.astype(str).str.strip() != '']
            
            if len(col_data) > 0:
                # Get up to 5 unique samples
                unique_samples = col_data.unique()[:5]
                samples[col] = [str(sample).strip() for sample in unique_samples]
            else:
                samples[col] = []
        
        return samples
    
    def auto_suggest_mappings(self) -> Dict[str, str]:
        """Automatically suggest field mappings based on column analysis."""
        suggestions = {}
        
        # First pass: exact and fuzzy name matching
        for mifir_field in MIFIR_FIELDS:
            best_match = self._find_best_column_match(mifir_field)
            if best_match:
                suggestions[mifir_field.name] = best_match
        
        # Second pass: content-based analysis for remaining fields
        self._analyze_content_patterns(suggestions)
        
        # Third pass: logical field relationships
        self._apply_logical_relationships(suggestions)
        
        return suggestions
    
    def _find_best_column_match(self, mifir_field: MiFIRField) -> Optional[str]:
        """Find the best matching column for a MiFIR field."""
        field_name = mifir_field.name
        
        # Check if we have predefined patterns for this field
        if field_name in self.mapping_patterns:
            patterns = self.mapping_patterns[field_name]
            
            # Look for exact matches first
            for pattern in patterns:
                for col in self.columns:
                    if pattern.lower() in col.lower():
                        return col
            
            # Look for fuzzy matches
            best_score = 0.0
            best_match = None
            
            for pattern in patterns:
                for col in self.columns:
                    score = SequenceMatcher(None, pattern.lower(), col.lower()).ratio()
                    if score > best_score and score > 0.6:  # 60% similarity threshold
                        best_score = score
                        best_match = col
            
            if best_match:
                return best_match
        
        return None
    
    def _analyze_content_patterns(self, suggestions: Dict[str, str]):
        """Analyze column content to suggest mappings."""
        for col, samples in self.column_samples.items():
            if not samples or col in suggestions.values():
                continue  # Skip if already mapped or no samples
            
            # Analyze sample values
            sample_str = ' '.join(samples)
            
            # Check for LEI pattern
            if re.search(self.value_patterns['lei_pattern'], sample_str, re.IGNORECASE):
                if 'buyer_lei' not in suggestions:
                    suggestions['buyer_lei'] = col
                elif 'seller_lei' not in suggestions:
                    suggestions['seller_lei'] = col
            
            # Check for ISIN pattern
            elif re.search(self.value_patterns['isin_pattern'], sample_str, re.IGNORECASE):
                if 'instrument_isin' not in suggestions:
                    suggestions['instrument_isin'] = col
            
            # Check for timestamp pattern
            elif re.search(self.value_patterns['timestamp_pattern'], sample_str):
                if 'execution_datetime' not in suggestions:
                    suggestions['execution_datetime'] = col
                elif 'trade_datetime' not in suggestions:
                    suggestions['trade_datetime'] = col
            
            # Check for price pattern (numeric values > 1)
            elif self._is_price_column(samples):
                if 'price_amount' not in suggestions:
                    suggestions['price_amount'] = col
            
            # Check for quantity pattern (small decimal values)
            elif self._is_quantity_column(samples):
                if 'quantity' not in suggestions:
                    suggestions['quantity'] = col
            
            # Check for boolean pattern
            elif all(re.match(self.value_patterns['boolean_pattern'], str(sample), re.IGNORECASE) for sample in samples):
                if 'clearing_indicator' not in suggestions and 'clear' in col.lower():
                    suggestions['clearing_indicator'] = col
    
    def _is_price_column(self, samples: List[str]) -> bool:
        """Check if column contains price-like values."""
        try:
            numeric_samples = []
            for sample in samples:
                try:
                    value = float(sample)
                    numeric_samples.append(value)
                except:
                    continue
            
            if len(numeric_samples) == 0:
                return False
            
            # Price characteristics: typically > 1, reasonable range
            avg_value = sum(numeric_samples) / len(numeric_samples)
            return avg_value > 1 and avg_value < 1000000  # Reasonable price range
        except:
            return False
    
    def _is_quantity_column(self, samples: List[str]) -> bool:
        """Check if column contains quantity-like values."""
        try:
            numeric_samples = []
            for sample in samples:
                try:
                    value = float(sample)
                    numeric_samples.append(value)
                except:
                    continue
            
            if len(numeric_samples) == 0:
                return False
            
            # Quantity characteristics: typically small positive numbers
            avg_value = sum(numeric_samples) / len(numeric_samples)
            return 0 < avg_value <= 100  # Reasonable quantity range
        except:
            return False
    
    def _apply_logical_relationships(self, suggestions: Dict[str, str]):
        """Apply logical relationships between fields."""
        # If we found a timestamp column, use it for both execution and trade datetime
        timestamp_col = suggestions.get('execution_datetime')
        if timestamp_col and 'trade_datetime' not in suggestions:
            suggestions['trade_datetime'] = timestamp_col
        
        # If we have taker/maker user IDs, suggest buyer/seller mapping based on side logic
        taker_user_col = self._find_column_containing(['taker_user', 'taker_id'])
        maker_user_col = self._find_column_containing(['maker_user', 'maker_id'])
        side_col = self._find_column_containing(['ordertype', 'side', 'buy_sell'])
        
        if taker_user_col and maker_user_col and side_col:
            # Analyze the side column to determine buyer/seller logic
            side_samples = self.column_samples.get(side_col, [])
            
            if any('buy' in str(sample).lower() for sample in side_samples):
                # Taker side indicates buy/sell, so:
                # When taker buys → taker is buyer, maker is seller
                suggestions['buyer_lei'] = taker_user_col
                suggestions['seller_lei'] = maker_user_col
            else:
                # Default mapping
                suggestions['buyer_lei'] = maker_user_col
                suggestions['seller_lei'] = taker_user_col
    
    def _find_column_containing(self, patterns: List[str]) -> Optional[str]:
        """Find column containing any of the patterns."""
        for pattern in patterns:
            for col in self.columns:
                if pattern.lower() in col.lower():
                    return col
        return None
    
    def get_confidence_score(self, suggestions: Dict[str, str]) -> Dict[str, float]:
        """Get confidence scores for each suggestion."""
        scores = {}
        
        for mifir_field, csv_column in suggestions.items():
            if csv_column not in self.columns:
                scores[mifir_field] = 0.0
                continue
            
            # Calculate confidence based on multiple factors
            name_score = self._calculate_name_similarity(mifir_field, csv_column)
            content_score = self._calculate_content_confidence(mifir_field, csv_column)
            
            # Weighted average
            scores[mifir_field] = (name_score * 0.6) + (content_score * 0.4)
        
        return scores
    
    def _calculate_name_similarity(self, mifir_field: str, csv_column: str) -> float:
        """Calculate similarity between field name and column name."""
        # Check if field has mapping patterns
        if mifir_field in self.mapping_patterns:
            patterns = self.mapping_patterns[mifir_field]
            max_score = 0.0
            
            for pattern in patterns:
                score = SequenceMatcher(None, pattern.lower(), csv_column.lower()).ratio()
                max_score = max(max_score, score)
            
            return max_score
        
        # Direct name comparison
        return SequenceMatcher(None, mifir_field.lower(), csv_column.lower()).ratio()
    
    def _calculate_content_confidence(self, mifir_field: str, csv_column: str) -> float:
        """Calculate confidence based on column content."""
        if csv_column not in self.column_samples:
            return 0.0
        
        samples = self.column_samples[csv_column]
        if not samples:
            return 0.0
        
        sample_str = ' '.join(samples)
        
        # Field-specific content analysis
        if mifir_field in ['buyer_lei', 'seller_lei', 'reporting_party_lei']:
            # Check for LEI-like pattern
            if re.search(self.value_patterns['lei_pattern'], sample_str):
                return 1.0
            # Check for numeric IDs (lower confidence)
            elif all(sample.isdigit() for sample in samples):
                return 0.7
        
        elif mifir_field == 'instrument_isin':
            # Check for ISIN pattern
            if re.search(self.value_patterns['isin_pattern'], sample_str):
                return 1.0
            # Check for symbol-like strings
            elif all('_' in sample or len(sample) > 3 for sample in samples):
                return 0.8
        
        elif mifir_field in ['execution_datetime', 'trade_datetime']:
            # Check for timestamp patterns
            if re.search(self.value_patterns['timestamp_pattern'], sample_str):
                return 0.9
            elif any('T' in sample and 'Z' in sample for sample in samples):
                return 1.0
        
        elif mifir_field == 'price_amount':
            if self._is_price_column(samples):
                return 0.9
        
        elif mifir_field == 'quantity':
            if self._is_quantity_column(samples):
                return 0.9
        
        return 0.5  # Default confidence
    
    def _is_price_column(self, samples: List[str]) -> bool:
        """Check if samples look like prices."""
        try:
            numeric_samples = []
            for sample in samples:
                try:
                    value = float(sample)
                    numeric_samples.append(value)
                except:
                    continue
            
            if len(numeric_samples) == 0:
                return False
            
            avg_value = sum(numeric_samples) / len(numeric_samples)
            return avg_value > 1 and avg_value < 1000000
        except:
            return False
    
    def _is_quantity_column(self, samples: List[str]) -> bool:
        """Check if samples look like quantities."""
        try:
            numeric_samples = []
            for sample in samples:
                try:
                    value = float(sample)
                    numeric_samples.append(value)
                except:
                    continue
            
            if len(numeric_samples) == 0:
                return False
            
            avg_value = sum(numeric_samples) / len(numeric_samples)
            return 0 < avg_value <= 100
        except:
            return False
    
    def get_mapping_explanations(self, suggestions: Dict[str, str]) -> Dict[str, str]:
        """Get explanations for why each mapping was suggested."""
        explanations = {}
        confidence_scores = self.get_confidence_score(suggestions)
        
        for mifir_field, csv_column in suggestions.items():
            if csv_column not in self.columns:
                continue
            
            confidence = confidence_scores.get(mifir_field, 0.0)
            samples = self.column_samples.get(csv_column, [])
            
            explanation_parts = []
            
            # Name-based reasoning
            if mifir_field in self.mapping_patterns:
                patterns = self.mapping_patterns[mifir_field]
                matching_patterns = [p for p in patterns if p.lower() in csv_column.lower()]
                if matching_patterns:
                    explanation_parts.append(f"Name contains '{matching_patterns[0]}'")
            
            # Content-based reasoning
            if samples:
                sample_preview = ", ".join(samples[:3])
                explanation_parts.append(f"Sample values: {sample_preview}")
                
                # Specific content analysis
                if mifir_field in ['buyer_lei', 'seller_lei'] and all(s.isdigit() for s in samples[:3]):
                    explanation_parts.append("⚠️ Contains internal IDs - replace with LEIs")
                elif mifir_field == 'instrument_isin' and any('_' in s for s in samples[:3]):
                    explanation_parts.append("⚠️ Contains venue ticker - replace with DSB ISIN")
                elif mifir_field in ['execution_datetime', 'trade_datetime'] and any(':' in s for s in samples[:3]):
                    explanation_parts.append("⚠️ Partial timestamp - needs full UTC format")
            
            # Confidence indicator
            if confidence >= 0.8:
                confidence_emoji = "🟢 High"
            elif confidence >= 0.6:
                confidence_emoji = "🟡 Medium"
            else:
                confidence_emoji = "🔴 Low"
            
            explanations[mifir_field] = f"{confidence_emoji} confidence: {' | '.join(explanation_parts)}"
        
        return explanations
    
    def suggest_constants(self) -> Dict[str, str]:
        """Suggest constant values based on data analysis."""
        constants = {
            # Smart defaults for crypto derivatives
            "reporting_party_lei": "YOUR_FIRM_LEI_HERE",
            "instrument_isin": "DSB_ISIN_FOR_DERIVATIVE",
            "instrument_cfi": "FXXXXX",
            "trading_venue": "XOFF",  # OTC for crypto
            "trading_capacity": "PRIN",  # Principal
            "price_currency": "USD",  # Common for crypto
            "short_sale_indicator": "NSHO",  # N/A for crypto derivatives
            "commodity_derivative_indicator": "N",  # Not commodity
            "clearing_indicator": "N",  # Not cleared
            "securities_financing_indicator": "N",  # Not SFT
        }
        
        # Analyze symbol column to suggest ISIN mapping
        symbol_col = self._find_column_containing(['symbol', 'instrument', 'product'])
        if symbol_col:
            symbols = self.column_samples.get(symbol_col, [])
            unique_symbols = list(set(symbols))
            
            if len(unique_symbols) == 1:
                # Single instrument - suggest specific ISIN
                symbol = unique_symbols[0]
                constants["instrument_isin"] = f"DSB_ISIN_FOR_{symbol.replace('_', '_').upper()}"
            elif len(unique_symbols) <= 5:
                # Multiple instruments - suggest mapping strategy
                constants["instrument_isin"] = f"MULTIPLE_INSTRUMENTS_DETECTED_{len(unique_symbols)}"
        
        return constants
    
    def get_data_quality_report(self) -> Dict[str, any]:
        """Generate a data quality report for the uploaded data."""
        report = {
            "total_rows": len(self.df),
            "total_columns": len(self.df.columns),
            "missing_data": {},
            "data_types": {},
            "unique_values": {},
            "potential_issues": []
        }
        
        # Analyze each column
        for col in self.df.columns:
            col_data = self.df[col]
            
            # Missing data analysis
            missing_count = col_data.isnull().sum()
            missing_pct = (missing_count / len(self.df)) * 100
            report["missing_data"][col] = {"count": missing_count, "percentage": missing_pct}
            
            # Data type analysis
            non_null_data = col_data.dropna()
            if len(non_null_data) > 0:
                sample_value = non_null_data.iloc[0]
                if isinstance(sample_value, (int, float)):
                    report["data_types"][col] = "numeric"
                elif isinstance(sample_value, str):
                    report["data_types"][col] = "text"
                else:
                    report["data_types"][col] = "other"
            
            # Unique values analysis
            unique_count = col_data.nunique()
            report["unique_values"][col] = unique_count
            
            # Identify potential issues
            if missing_pct > 50:
                report["potential_issues"].append(f"Column '{col}' has {missing_pct:.1f}% missing data")
            
            if unique_count == 1 and len(non_null_data) > 1:
                report["potential_issues"].append(f"Column '{col}' has only one unique value - consider as constant")
        
        return report
