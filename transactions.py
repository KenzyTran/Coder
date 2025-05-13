import os
import pandas as pd
import json
from datetime import datetime
from typing import List, Dict, Tuple, Optional
import re

class Transaction:
    def __init__(self, file_path: str, user_id: str) -> None:
        """
        Initializes the Transaction object with the file path and user ID.
        
        Args:
            file_path (str): Path to the CSV or XLSX file
            user_id (str): User identifier
        """
        self.file_path = file_path
        self.user_id = user_id
        self.data = []
        self.required_columns = [
            'Mã CK', 'Ngày giao dịch', 'Loại giao dịch', 
            'Giá thực hiện', 'Khối lượng', 'Phí thực hiện'
        ]
        # Column 'Thuế bán' is required only for 'Bán' transactions
        
    def validate_file_format(self) -> bool:
        """
        Checks if the uploaded file is in a supported format (.csv or .xlsx).
        
        Returns:
            bool: True if format is valid, otherwise raises an error
        
        Raises:
            ValueError: If file format is not supported
        """
        _, file_extension = os.path.splitext(self.file_path)
        if file_extension.lower() not in ['.csv', '.xlsx']:
            raise ValueError(f"Định dạng file {file_extension} không được hỗ trợ. Vui lòng sử dụng file CSV hoặc XLSX.")
        return True
        
    def read_file(self) -> List[Dict]:
        """
        Reads the CSV/XLSX file and converts it to a list of dictionaries.
        
        Returns:
            List[Dict]: List of transactions as dictionaries
            
        Raises:
            ValueError: If file cannot be read
        """
        try:
            _, file_extension = os.path.splitext(self.file_path)
            if file_extension.lower() == '.csv':
                df = pd.read_csv(self.file_path)
            elif file_extension.lower() == '.xlsx':
                df = pd.read_excel(self.file_path, engine='openpyxl')
            else:
                raise ValueError(f"Định dạng file {file_extension} không được hỗ trợ. Vui lòng sử dụng file CSV hoặc XLSX.")
                
            # Convert DataFrame to list of dictionaries
            self.data = df.to_dict('records')
            return self.data
        except Exception as e:
            raise ValueError(f"Không thể đọc file: {str(e)}")
            
    def validate_columns(self, data: List[Dict]) -> bool:
        """
        Validates the presence and correctness of required columns in the file.
        
        Args:
            data (List[Dict]): List of transactions as dictionaries
            
        Returns:
            bool: True if columns are valid, otherwise raises an error
            
        Raises:
            ValueError: If required columns are missing
        """
        if not data:
            raise ValueError("File không chứa dữ liệu.")
            
        # Get columns from first row
        columns = list(data[0].keys())
        
        # Check required columns
        missing_columns = [col for col in self.required_columns if col not in columns]
        if missing_columns:
            raise ValueError(f"Thiếu các cột bắt buộc: {', '.join(missing_columns)}")
            
        # Check if 'Thuế bán' column exists when there are 'Bán' transactions
        sell_transactions = [t for t in data if t.get('Loại giao dịch') == 'Bán']
        if sell_transactions and 'Thuế bán' not in columns:
            raise ValueError("Thiếu cột 'Thuế bán' cho các giao dịch Bán.")
            
        return True
        
    def convert_date_format(self, date_str: str) -> str:
        """
        Converts 'Ngày giao dịch' from 'dd/MM/yyyy HH:mm:ss' to 'YYYY-MM-dd HH:mm:ss'.
        
        Args:
            date_str (str): Date string in format dd/MM/yyyy HH:mm:ss
            
        Returns:
            str: Date string in format YYYY-MM-dd HH:mm:ss
        """
        try:
            # Parse the input date string
            dt = datetime.strptime(date_str, "%d/%m/%Y %H:%M:%S")
            # Format to the desired output format
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            # Return original string if parsing fails
            return date_str
            
    def normalize_price(self, price_str: str) -> float:
        """
        Normalizes 'Giá thực hiện' by removing thousands separators and converting to float.
        
        Args:
            price_str (str): Price string with thousands separators
            
        Returns:
            float: Normalized price value
        """
        try:
            # Remove commas, spaces, and other thousand separators
            if isinstance(price_str, str):
                # Remove any non-numeric characters except decimal point
                price_clean = re.sub(r'[^\d.]', '', price_str)
                return float(price_clean)
            return float(price_str)
        except (ValueError, TypeError):
            return 0.0
            
    def calculate_fee_tax_rates(self, transaction: Dict) -> Dict:
        """
        Calculates 'Tỷ lệ phí' and if applicable, 'Tỷ lệ thuế' for the transaction.
        
        Args:
            transaction (Dict): Transaction data
            
        Returns:
            Dict: Transaction with fee and tax rates added
        """
        result = transaction.copy()
        
        # Calculate fee rate (Tỷ lệ phí)
        price = self.normalize_price(result['Giá thực hiện'])
        volume = int(result['Khối lượng']) if result['Khối lượng'] else 0
        fee = self.normalize_price(result['Phí thực hiện']) if result['Phí thực hiện'] else 0
        
        total_value = price * volume
        if total_value > 0:
            result['Tỷ lệ phí'] = (fee / total_value) * 100  # as percentage
        else:
            result['Tỷ lệ phí'] = 0
            
        # Calculate tax rate (Tỷ lệ thuế) for 'Bán' transactions
        if result['Loại giao dịch'] == 'Bán' and 'Thuế bán' in result:
            tax = self.normalize_price(result['Thuế bán']) if result['Thuế bán'] else 0
            if total_value > 0:
                result['Tỷ lệ thuế'] = (tax / total_value) * 100  # as percentage
            else:
                result['Tỷ lệ thuế'] = 0
        else:
            result['Tỷ lệ thuế'] = 0
            
        return result
        
    def generate_preview(self, data: List[Dict]) -> List[Dict]:
        """
        Generates a preview consisting of the formatted and calculated fields for each transaction.
        
        Args:
            data (List[Dict]): Original transaction data
            
        Returns:
            List[Dict]: Preview data with formatted fields
        """
        preview_data = []
        
        for transaction in data:
            # Create a new dict for the normalized transaction
            normalized = {}
            
            # Convert date format
            normalized['Ngày giao dịch'] = self.convert_date_format(transaction['Ngày giao dịch'])
            
            # Copy stock code
            normalized['Mã CK'] = transaction['Mã CK']
            
            # Copy transaction type
            normalized['Loại giao dịch'] = transaction['Loại giao dịch']
            
            # Copy and validate volume
            try:
                normalized['Khối lượng'] = int(transaction['Khối lượng'])
            except (ValueError, TypeError):
                normalized['Khối lượng'] = 0
                
            # Normalize price
            normalized['Giá thực hiện'] = self.normalize_price(transaction['Giá thực hiện'])
            
            # Normalize fee
            normalized['Phí thực hiện'] = self.normalize_price(transaction['Phí thực hiện'])
            
            # Normalize tax for sell transactions
            if transaction['Loại giao dịch'] == 'Bán' and 'Thuế bán' in transaction:
                normalized['Thuế bán'] = self.normalize_price(transaction['Thuế bán'])
            else:
                normalized['Thuế bán'] = 0
                
            # Calculate fee and tax rates
            calculated = self.calculate_fee_tax_rates(normalized)
            preview_data.append(calculated)
            
        return preview_data
        
    def calculate_running_balance(self, preview_data: List[Dict]) -> List[Dict]:
        """
        Calculates the running balance for each 'Mã CK'. Highlights negative balances.
        
        Args:
            preview_data (List[Dict]): Preview data
            
        Returns:
            List[Dict]: Preview data with running balance
        """
        # Sort by date
        sorted_data = sorted(preview_data, key=lambda x: x['Ngày giao dịch'])
        
        # Track balance by stock code
        balances = {}
        
        for transaction in sorted_data:
            stock_code = transaction['Mã CK']
            volume = transaction['Khối lượng']
            
            # Initialize balance for this stock code if it doesn't exist
            if stock_code not in balances:
                balances[stock_code] = 0
                
            # Update balance based on transaction type
            if transaction['Loại giao dịch'] == 'Mua':
                balances[stock_code] += volume
            else:  # 'Bán'
                balances[stock_code] -= volume
                
            # Add running balance to transaction
            transaction['Running Balance'] = balances[stock_code]
            
            # Flag negative balances
            if balances[stock_code] < 0:
                transaction['Negative Balance'] = True
            else:
                transaction['Negative Balance'] = False
                
        # Track transactions causing negative balances
        negative_balance_warnings = []
        
        for i, transaction in enumerate(sorted_data):
            if transaction['Negative Balance']:
                warning = {
                    'index': i,
                    'stock_code': transaction['Mã CK'],
                    'transaction_date': transaction['Ngày giao dịch'],
                    'transaction_type': transaction['Loại giao dịch'],
                    'volume': transaction['Khối lượng'],
                    'balance': transaction['Running Balance'],
                    'suggestion': "Kiểm tra lại khối lượng hoặc thêm giao dịch Mua trước đó."
                }
                negative_balance_warnings.append(warning)
                
        # Add warnings to the result
        for transaction in sorted_data:
            transaction['warnings'] = negative_balance_warnings
            
        return sorted_data
        
    def validate_transaction_data(self, preview_data: List[Dict]) -> Tuple[bool, List[Dict]]:
        """
        Validates transaction data, checks for parsing errors, negative or zero values.
        
        Args:
            preview_data (List[Dict]): Preview data
            
        Returns:
            Tuple[bool, List[Dict]]: (is_valid, list_of_errors)
        """
        errors = []
        
        for i, transaction in enumerate(preview_data):
            transaction_errors = []
            
            # Check if price is valid
            if transaction['Giá thực hiện'] <= 0:
                transaction_errors.append(f"Giá thực hiện phải lớn hơn 0")
                
            # Check if volume is valid
            if transaction['Khối lượng'] <= 0:
                transaction_errors.append(f"Khối lượng phải lớn hơn 0")
                
            # Check if fee is valid
            if transaction['Phí thực hiện'] < 0:
                transaction_errors.append(f"Phí thực hiện không được âm")
                
            # Check if tax is valid for sell transactions
            if transaction['Loại giao dịch'] == 'Bán' and transaction['Thuế bán'] < 0:
                transaction_errors.append(f"Thuế bán không được âm")
                
            # If any errors, add to the error list
            if transaction_errors:
                errors.append({
                    'index': i,
                    'stock_code': transaction['Mã CK'],
                    'transaction_date': transaction['Ngày giao dịch'],
                    'errors': transaction_errors
                })
                
        # Check for negative balances
        for transaction in preview_data:
            if transaction.get('Negative Balance', False):
                # These errors are warnings, not critical errors
                # They're already captured in the calculate_running_balance method
                pass
                
        return len(errors) == 0, errors
        
    def import_to_db(self, preview_data: List[Dict]) -> Tuple[bool, str]:
        """
        Simulates importing validated data into a database with a JSON object including user_id.
        
        Args:
            preview_data (List[Dict]): Validated preview data
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            # Create a copy of data without warnings
            import_data = []
            for transaction in preview_data:
                clean_transaction = {k: v for k, v in transaction.items() 
                                    if k not in ['warnings', 'Negative Balance']}
                import_data.append(clean_transaction)
                
            # Add user ID
            data_to_import = {
                'user_id': self.user_id,
                'transactions': import_data,
                'import_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Simulate database import by writing to a JSON file
            output_file = f"transactions_{self.user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data_to_import, f, ensure_ascii=False, indent=4)
                
            return True, f"Import thành công {len(import_data)} giao dịch."
        except Exception as e:
            return False, f"Lỗi khi import: {str(e)}"
            
    def display_results(self, success: bool, error_details: Optional[List[Dict]] = None) -> None:
        """
        Displays the import result indicating success or detailed errors for review.
        
        Args:
            success (bool): Whether the import was successful
            error_details (Optional[List[Dict]]): List of errors if success is False
        """
        if success:
            print("✅ Import thành công các giao dịch.")
            return
            
        print("❌ Lỗi import giao dịch:")
        for error in error_details:
            print(f"Dòng {error['index'] + 1} - Mã CK: {error['stock_code']} - Ngày: {error['transaction_date']}")
            for err_msg in error['errors']:
                print(f"  - {err_msg}")
            print("---")
            
        print("Bạn có thể bỏ qua các lỗi và tiếp tục import hoặc hủy để điều chỉnh dữ liệu.")