import os
import pandas as pd
import json
from datetime import datetime
import unittest
from unittest.mock import patch, mock_open, MagicMock
import tempfile
import sys
from transactions import Transaction

class TestTransaction(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_csv_path = os.path.join(self.temp_dir.name, "test_data.csv")
        self.test_xlsx_path = os.path.join(self.temp_dir.name, "test_data.xlsx")
        self.user_id = "test_user_123"
        
        # Create test CSV data
        self.csv_data = pd.DataFrame({
            'Mã CK': ['VIC', 'VNM', 'FPT'],
            'Ngày giao dịch': ['01/01/2023 10:30:00', '02/01/2023 11:15:00', '03/01/2023 09:45:00'],
            'Loại giao dịch': ['Mua', 'Bán', 'Mua'],
            'Giá thực hiện': ['100,000', '200,000', '150,000'],
            'Khối lượng': [100, 50, 200],
            'Phí thực hiện': ['10,000', '20,000', '15,000'],
            'Thuế bán': ['0', '5,000', '0']
        })
        
        # Save test data
        self.csv_data.to_csv(self.test_csv_path, index=False)
        self.csv_data.to_excel(self.test_xlsx_path, index=False)
        
        # Initialize Transaction object
        self.transaction = Transaction(self.test_csv_path, self.user_id)
    
    def tearDown(self):
        self.temp_dir.cleanup()
    
    def test_init(self):
        """Test the initialization of Transaction class"""
        self.assertEqual(self.transaction.file_path, self.test_csv_path)
        self.assertEqual(self.transaction.user_id, self.user_id)
        self.assertEqual(self.transaction.data, [])
        self.assertIn('Mã CK', self.transaction.required_columns)
        self.assertIn('Ngày giao dịch', self.transaction.required_columns)
        self.assertIn('Loại giao dịch', self.transaction.required_columns)
        self.assertIn('Giá thực hiện', self.transaction.required_columns)
        self.assertIn('Khối lượng', self.transaction.required_columns)
        self.assertIn('Phí thực hiện', self.transaction.required_columns)
    
    def test_validate_file_format_valid(self):
        """Test validation of supported file formats"""
        # Test CSV
        self.assertTrue(self.transaction.validate_file_format())
        
        # Test XLSX
        transaction_xlsx = Transaction(self.test_xlsx_path, self.user_id)
        self.assertTrue(transaction_xlsx.validate_file_format())
    
    def test_validate_file_format_invalid(self):
        """Test validation rejects unsupported file formats"""
        with tempfile.NamedTemporaryFile(suffix='.txt') as temp_file:
            transaction = Transaction(temp_file.name, self.user_id)
            with self.assertRaises(ValueError) as context:
                transaction.validate_file_format()
            self.assertIn("không được hỗ trợ", str(context.exception))
    
    def test_read_file_csv(self):
        """Test reading CSV files"""
        data = self.transaction.read_file()
        self.assertEqual(len(data), 3)
        self.assertEqual(data[0]['Mã CK'], 'VIC')
        self.assertEqual(data[1]['Mã CK'], 'VNM')
        self.assertEqual(data[2]['Mã CK'], 'FPT')
    
    def test_read_file_xlsx(self):
        """Test reading XLSX files"""
        transaction = Transaction(self.test_xlsx_path, self.user_id)
        data = transaction.read_file()
        self.assertEqual(len(data), 3)
        self.assertEqual(data[0]['Mã CK'], 'VIC')
        self.assertEqual(data[1]['Mã CK'], 'VNM')
        self.assertEqual(data[2]['Mã CK'], 'FPT')
    
    def test_read_file_error(self):
        """Test error handling when reading files"""
        transaction = Transaction("nonexistent_file.csv", self.user_id)
        with self.assertRaises(ValueError) as context:
            transaction.read_file()
        self.assertIn("Không thể đọc file", str(context.exception))
    
    def test_validate_columns_valid(self):
        """Test validation of columns with valid data"""
        data = self.transaction.read_file()
        self.assertTrue(self.transaction.validate_columns(data))
    
    def test_validate_columns_empty(self):
        """Test validation with empty data"""
        with self.assertRaises(ValueError) as context:
            self.transaction.validate_columns([])
        self.assertIn("File không chứa dữ liệu", str(context.exception))
    
    def test_validate_columns_missing(self):
        """Test validation with missing required columns"""
        # Create data with missing columns
        incomplete_data = [{'Mã CK': 'VIC', 'Ngày giao dịch': '01/01/2023'}]
        
        with self.assertRaises(ValueError) as context:
            self.transaction.validate_columns(incomplete_data)
        self.assertIn("Thiếu các cột bắt buộc", str(context.exception))
    
    def test_validate_columns_missing_tax(self):
        """Test validation with missing tax column for sell transactions"""
        # Create data with sell transaction but no tax column
        incomplete_data = [
            {
                'Mã CK': 'VIC', 
                'Ngày giao dịch': '01/01/2023', 
                'Loại giao dịch': 'Bán',
                'Giá thực hiện': '100000',
                'Khối lượng': 100,
                'Phí thực hiện': '1000'
            }
        ]
        
        with self.assertRaises(ValueError) as context:
            self.transaction.validate_columns(incomplete_data)
        self.assertIn("Thiếu cột 'Thuế bán'", str(context.exception))
    
    def test_convert_date_format(self):
        """Test date format conversion"""
        input_date = "01/02/2023 10:30:45"
        expected_output = "2023-02-01 10:30:45"
        self.assertEqual(self.transaction.convert_date_format(input_date), expected_output)
        
        # Test with invalid format - should return the original string
        invalid_date = "2023/01/02"
        self.assertEqual(self.transaction.convert_date_format(invalid_date), invalid_date)
    
    def test_normalize_price(self):
        """Test price normalization"""
        # Test with thousands separator
        self.assertEqual(self.transaction.normalize_price("1,000,000"), 1000000.0)
        
        # Test with decimal
        self.assertEqual(self.transaction.normalize_price("1,234.56"), 1234.56)
        
        # Test with already numeric value
        self.assertEqual(self.transaction.normalize_price(1000), 1000.0)
        
        # Test with invalid value
        self.assertEqual(self.transaction.normalize_price("not a number"), 0.0)
        
        # Test with None
        self.assertEqual(self.transaction.normalize_price(None), 0.0)
    
    def test_calculate_fee_tax_rates(self):
        """Test calculation of fee and tax rates"""
        # Create a test transaction for buying
        buy_transaction = {
            'Mã CK': 'VIC', 
            'Ngày giao dịch': '2023-01-01 10:30:45',
            'Loại giao dịch': 'Mua',
            'Giá thực hiện': 100000.0,
            'Khối lượng': 100,
            'Phí thực hiện': 1000.0,
            'Thuế bán': 0.0
        }
        
        result = self.transaction.calculate_fee_tax_rates(buy_transaction)
        
        # Calculate expected values
        total_value = 100000.0 * 100
        expected_fee_rate = (1000.0 / total_value) * 100
        
        self.assertAlmostEqual(result['Tỷ lệ phí'], expected_fee_rate)
        self.assertEqual(result['Tỷ lệ thuế'], 0)
        
        # Create a test transaction for selling
        sell_transaction = {
            'Mã CK': 'VNM', 
            'Ngày giao dịch': '2023-01-02 11:15:00',
            'Loại giao dịch': 'Bán',
            'Giá thực hiện': 200000.0,
            'Khối lượng': 50,
            'Phí thực hiện': 2000.0,
            'Thuế bán': 5000.0
        }
        
        result = self.transaction.calculate_fee_tax_rates(sell_transaction)
        
        # Calculate expected values
        total_value = 200000.0 * 50
        expected_fee_rate = (2000.0 / total_value) * 100
        expected_tax_rate = (5000.0 / total_value) * 100
        
        self.assertAlmostEqual(result['Tỷ lệ phí'], expected_fee_rate)
        self.assertAlmostEqual(result['Tỷ lệ thuế'], expected_tax_rate)
        
        # Test with zero values
        zero_transaction = {
            'Mã CK': 'FPT', 
            'Ngày giao dịch': '2023-01-03 09:45:00',
            'Loại giao dịch': 'Mua',
            'Giá thực hiện': 0.0,
            'Khối lượng': 0,
            'Phí thực hiện': 0.0,
            'Thuế bán': 0.0
        }
        
        result = self.transaction.calculate_fee_tax_rates(zero_transaction)
        self.assertEqual(result['Tỷ lệ phí'], 0)
        self.assertEqual(result['Tỷ lệ thuế'], 0)
    
    def test_generate_preview(self):
        """Test preview generation with formatting and calculations"""
        # Read the test data
        self.transaction.read_file()
        
        # Generate preview
        preview_data = self.transaction.generate_preview(self.transaction.data)
        
        # Check length
        self.assertEqual(len(preview_data), 3)
        
        # Check specific values for each transaction
        self.assertEqual(preview_data[0]['Mã CK'], 'VIC')
        self.assertEqual(preview_data[0]['Ngày giao dịch'], '2023-01-01 10:30:00')
        self.assertEqual(preview_data[0]['Loại giao dịch'], 'Mua')
        self.assertEqual(preview_data[0]['Giá thực hiện'], 100000.0)
        self.assertEqual(preview_data[0]['Khối lượng'], 100)
        self.assertEqual(preview_data[0]['Phí thực hiện'], 10000.0)
        self.assertEqual(preview_data[0]['Thuế bán'], 0.0)
        
        # Check second transaction (sell)
        self.assertEqual(preview_data[1]['Mã CK'], 'VNM')
        self.assertEqual(preview_data[1]['Loại giao dịch'], 'Bán')
        self.assertEqual(preview_data[1]['Thuế bán'], 5000.0)
        
        # Check if fee and tax rates are calculated
        for transaction in preview_data:
            self.assertIn('Tỷ lệ phí', transaction)
            self.assertIn('Tỷ lệ thuế', transaction)
    
    def test_calculate_running_balance(self):
        """Test calculation of running balance"""
        # Create test preview data
        preview_data = [
            {
                'Mã CK': 'VIC', 
                'Ngày giao dịch': '2023-01-01 10:30:00',
                'Loại giao dịch': 'Mua',
                'Giá thực hiện': 100000.0,
                'Khối lượng': 100,
                'Phí thực hiện': 1000.0,
                'Thuế bán': 0.0,
                'Tỷ lệ phí': 0.01,
                'Tỷ lệ thuế': 0.0
            },
            {
                'Mã CK': 'VIC', 
                'Ngày giao dịch': '2023-01-02 11:15:00',
                'Loại giao dịch': 'Bán',
                'Giá thực hiện': 110000.0,
                'Khối lượng': 50,
                'Phí thực hiện': 1100.0,
                'Thuế bán': 2750.0,
                'Tỷ lệ phí': 0.01,
                'Tỷ lệ thuế': 0.05
            },
            {
                'Mã CK': 'VNM', 
                'Ngày giao dịch': '2023-01-03 09:45:00',
                'Loại giao dịch': 'Mua',
                'Giá thực hiện': 200000.0,
                'Khối lượng': 100,
                'Phí thực hiện': 2000.0,
                'Thuế bán': 0.0,
                'Tỷ lệ phí': 0.01,
                'Tỷ lệ thuế': 0.0
            },
            {
                'Mã CK': 'VIC', 
                'Ngày giao dịch': '2023-01-04 14:20:00',
                'Loại giao dịch': 'Bán',
                'Giá thực hiện': 120000.0,
                'Khối lượng': 100,
                'Phí thực hiện': 1200.0,
                'Thuế bán': 6000.0,
                'Tỷ lệ phí': 0.01,
                'Tỷ lệ thuế': 0.05
            }
        ]
        
        result = self.transaction.calculate_running_balance(preview_data)
        
        # Check if running balance is calculated correctly
        self.assertEqual(result[0]['Running Balance'], 100)  # VIC: Buy 100
        self.assertEqual(result[1]['Running Balance'], 50)   # VIC: 100 - 50 = 50
        self.assertEqual(result[2]['Running Balance'], 100)  # VNM: Buy 100
        self.assertEqual(result[3]['Running Balance'], -50)  # VIC