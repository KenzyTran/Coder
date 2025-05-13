import os
import pandas as pd
import gradio as gr
import tempfile
import json
from transactions import Transaction

# Constants
USER_ID = "123456"  # Assuming a fixed user ID for demonstration

def process_file(file):
    """Process the uploaded file and return a preview of transactions."""
    if file is None:
        return None, "Vui lòng tải lên một file.", None, None, None
    
    # Debug information
    print(f"File type: {type(file)}")
    print(f"File name: {file.name}")
    
    try:
        # Use the file directly from Gradio
        transaction = Transaction(file.name, USER_ID)
        
        # Validate file format
        transaction.validate_file_format()
        
        # Read file
        data = transaction.read_file()
        
        # Validate columns
        transaction.validate_columns(data)
        
        # Generate preview
        preview_data = transaction.generate_preview(data)
        
        # Calculate running balance
        balance_data = transaction.calculate_running_balance(preview_data)
        
        # Validate transaction data
        is_valid, errors = transaction.validate_transaction_data(balance_data)
        
        # Create a preview table for display
        preview_table = pd.DataFrame([
            {
                "STT": i+1,
                "Ngày GD": item["Ngày giao dịch"],
                "Mã CK": item["Mã CK"],
                "Loại GD": item["Loại giao dịch"],
                "Khối lượng": item["Khối lượng"],
                "Giá": f"{item['Giá thực hiện']/1000:,.2f} nghìn",
                "Tỷ lệ phí (%)": f"{item['Tỷ lệ phí']:.4f}%",
                "Tỷ lệ thuế (%)": f"{item['Tỷ lệ thuế']:.4f}%" if item["Loại giao dịch"] == "Bán" else "-",
                "Running Balance": item["Running Balance"]
            }
            for i, item in enumerate(balance_data)
        ])
        
        # Format warnings for display
        warnings_text = ""
        warnings_list = []
        if balance_data and len(balance_data) > 0:
            warnings = balance_data[0].get('warnings', [])
            for warning in warnings:
                warning_item = f"Mã CK: {warning['stock_code']} - Ngày: {warning['transaction_date']} - " \
                              f"Số lượng: {warning['volume']} - Dư: {warning['balance']} - {warning['suggestion']}"
                warnings_list.append(warning_item)
            
            if warnings_list:
                warnings_text = "⚠️ Cảnh báo: Phát hiện giao dịch gây âm dư:\n" + "\n".join(warnings_list)
        
        # Format errors for display
        error_text = ""
        if not is_valid:
            error_details = []
            for error in errors:
                err_msg = f"Dòng {error['index'] + 1} - Mã CK: {error['stock_code']} - Ngày: {error['transaction_date']}\n"
                for e in error['errors']:
                    err_msg += f"  - {e}\n"
                error_details.append(err_msg)
            
            if error_details:
                error_text = "❌ Lỗi dữ liệu:\n" + "\n".join(error_details)
        
        return balance_data, "Đã tải file thành công!", preview_table, warnings_text, error_text
    
    except Exception as e:
        print(f"Error processing file: {str(e)}")  # Debug print
        return None, f"Lỗi: {str(e)}", None, None, None

def import_transactions(data, skip_errors):
    """Import transactions to database."""
    if data is None:
        return "Vui lòng tải lên và xử lý file trước khi import."
    
    # Initialize Transaction object and use the imported data
    temp_dir = tempfile.mkdtemp()
    temp_file_path = os.path.join(temp_dir, "temp_data.json")
    
    # Write data to temporary file
    with open(temp_file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    
    transaction = Transaction(temp_file_path, USER_ID)
    
    # Validate transaction data
    is_valid, errors = transaction.validate_transaction_data(data)
    
    if not is_valid and not skip_errors:
        # Clean up
        os.remove(temp_file_path)
        os.rmdir(temp_dir)
        return "❌ Import thất bại. Vui lòng sửa lỗi hoặc chọn 'Bỏ qua lỗi' để tiếp tục."
    
    # Import to database
    success, message = transaction.import_to_db(data)
    
    # Clean up
    os.remove(temp_file_path)
    os.rmdir(temp_dir)
    
    if success:
        return f"✅ {message}"
    else:
        return f"❌ {message}"

def create_dataframe_with_highlights(data):
    """Create a DataFrame with highlights for negative balances."""
    if not data:
        return None
    
    df = pd.DataFrame(data)
    
    # Define a function for highlighting rows with negative balance
    def highlight_negative_balance(row):
        if row['Negative Balance']:
            return ['background-color: #FFF59D; color: red' if col == 'Running Balance' else 'background-color: #FFF59D' for col in row.index]
        else:
            return [''] * len(row)
    
    # Apply the highlighting function
    styled_df = df.style.apply(highlight_negative_balance, axis=1)
    
    return styled_df

def format_table_for_gradio(table_data):
    """Format table data for Gradio DataTable component."""
    if not table_data:
        return None
    
    # Create a list of dictionaries for the DataTable
    table = []
    for row in table_data:
        # Use CSS to highlight negative balance rows
        style = "background-color: #FFF59D; color: red;" if row.get("Running Balance", 0) < 0 else ""
        
        formatted_row = {
            "STT": row["STT"],
            "Ngày GD": row["Ngày GD"],
            "Mã CK": row["Mã CK"],
            "Loại GD": row["Loại GD"],
            "Khối lượng": row["Khối lượng"],
            "Giá": row["Giá"],
            "Tỷ lệ phí (%)": row["Tỷ lệ phí (%)"],
            "Tỷ lệ thuế (%)": row["Tỷ lệ thuế (%)"],
            "Running Balance": f"<span style='{style}'>{row['Running Balance']}</span>" if style else row["Running Balance"]
        }
        table.append(formatted_row)
    
    return table

# Define the Gradio interface
with gr.Blocks(title="Nhập và Xử Lý Nhật Ký Giao Dịch") as app:
    gr.Markdown("# Nhập và Xử Lý Nhật Ký Giao Dịch")
    
    with gr.Row():
        with gr.Column(scale=3):
            file_input = gr.File(label="Tải lên file CSV/XLSX", file_types=[".csv", ".xlsx"], type="filepath")
            upload_button = gr.Button("Xử lý File")
            result_msg = gr.Textbox(label="Thông báo", interactive=False)
        
        with gr.Column(scale=7):
            warnings_box = gr.Textbox(label="Cảnh báo", interactive=False)
            errors_box = gr.Textbox(label="Lỗi dữ liệu", interactive=False)
    
    preview_data = gr.State(None)
    
    gr.Markdown("## Preview Dữ Liệu")
    preview_table = gr.Dataframe(
        label="Preview Giao Dịch",
        headers=["STT", "Ngày GD", "Mã CK", "Loại GD", "Khối lượng", "Giá", "Tỷ lệ phí (%)", "Tỷ lệ thuế (%)", "Running Balance"],
        datatype=["number", "str", "str", "str", "number", "str", "str", "str", "number"],
        col_count=(9, "fixed")
    )
    
    with gr.Row():
        skip_errors_checkbox = gr.Checkbox(label="Bỏ qua lỗi", value=False)
        import_button = gr.Button("Import vào Hệ thống")
    
    import_result = gr.Textbox(label="Kết quả Import", interactive=False)
    
    # Set up event handlers
    upload_button.click(
        process_file,
        inputs=[file_input],
        outputs=[preview_data, result_msg, preview_table, warnings_box, errors_box]
    )
    
    import_button.click(
        import_transactions,
        inputs=[preview_data, skip_errors_checkbox],
        outputs=[import_result]
    )

# Launch the app
if __name__ == "__main__":
    app.launch()