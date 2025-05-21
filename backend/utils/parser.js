const XLSX = require('xlsx');
const { parse } = require('csv-parse/sync');
const dateFns = require('date-fns');

class Parser {
  static async parseFile(file, userId) {
    console.log('Parser: Starting file parse...');
    const fileExt = file.originalname.split('.').pop().toLowerCase();
    const buffer = file.buffer;

    console.log('Parser: File details:', {
      name: file.originalname,
      size: buffer.length,
      type: file.mimetype,
      ext: fileExt
    });

    let rows = [];
    try {
      if (fileExt === 'csv') {
        console.log('Parser: Parsing CSV file...');
        rows = parse(buffer, {
          columns: true,
          skip_empty_lines: true,
          trim: true
        });
        console.log('Parser: CSV parsed, rows:', rows.length);
      } else if (fileExt === 'xlsx') {
        console.log('Parser: Parsing XLSX file...');
        const workbook = XLSX.read(buffer, { type: 'buffer' });
        const sheetName = workbook.SheetNames[0];
        console.log('Parser: Using sheet:', sheetName);
        const worksheet = workbook.Sheets[sheetName];
        rows = XLSX.utils.sheet_to_json(worksheet);
        console.log('Parser: XLSX parsed, rows:', rows.length);
      } else {
        throw new Error(`Unsupported file extension: ${fileExt}`);
      }
    } catch (error) {
      console.error('Parser: Error parsing file:', error);
      throw new Error(`Failed to parse file: ${error.message}`);
    }

    if (rows.length === 0) {
      throw new Error('File is empty or has no valid data');
    }

    console.log('Parser: First row sample:', rows[0]);
    return this.processRows(rows, userId);
  }

  static processRows(rows, userId) {
    console.log('Parser: Processing rows...');
    const processedRows = rows.map((row, index) => {
      try {
        // Normalize column names
        const normalizedRow = this.normalizeColumnNames(row);
        console.log(`Parser: Row ${index + 1} normalized:`, normalizedRow);
        
        // Convert date format
        const tradeDate = this.parseDate(normalizedRow.tradeDate);
        
        // Calculate fees and taxes
        const price = parseFloat(normalizedRow.price);
        if (isNaN(price)) {
          throw new Error(`Invalid price value: ${normalizedRow.price}`);
        }

        const volume = parseInt(normalizedRow.volume);
        if (isNaN(volume)) {
          throw new Error(`Invalid volume value: ${normalizedRow.volume}`);
        }

        const feeRate = parseFloat(normalizedRow.feeRate) || 0.0005;
        const taxRate = parseFloat(normalizedRow.taxRate) || 0.001;
        
        const fee = price * volume * feeRate;
        const tax = price * volume * taxRate;

        const processed = {
          userId,
          symbol: normalizedRow.symbol,
          tradeDate,
          type: normalizedRow.type,
          price,
          volume,
          fee,
          tax,
          feeRate,
          taxRate
        };

        console.log(`Parser: Row ${index + 1} processed:`, processed);
        return processed;
      } catch (error) {
        console.error(`Parser: Error processing row ${index + 1}:`, error);
        throw new Error(`Error in row ${index + 1}: ${error.message}`);
      }
    });

    console.log('Parser: All rows processed successfully');
    return processedRows;
  }

  static normalizeColumnNames(row) {
    const columnMap = {
      // Vietnamese column names
      'Ngày giao dịch': 'tradeDate',
      'Mã CK': 'symbol',
      'Loại giao dịch': 'type',
      'Khối lượng': 'volume',
      'Giá thực hiện': 'price',
      'Phí thực hiện': 'fee',
      'Thuế bán': 'tax',
      // English column names
      'Trade Date': 'tradeDate',
      'Symbol': 'symbol',
      'Type': 'type',
      'Volume': 'volume',
      'Price': 'price',
      'Fee Rate': 'feeRate',
      'Tax Rate': 'taxRate',
      // Additional mappings
      'Ngày GD': 'tradeDate',
      'Loại GD': 'type',
      'Giá': 'price'
    };

    const normalized = {};
    const missingColumns = new Set(['tradeDate', 'symbol', 'type', 'volume', 'price']);
    
    Object.keys(row).forEach(key => {
      const normalizedKey = columnMap[key] || key;
      normalized[normalizedKey] = row[key];
      missingColumns.delete(normalizedKey);
    });

    // Convert Vietnamese transaction types to English
    if (normalized.type) {
      normalized.type = normalized.type.toUpperCase();
      if (normalized.type === 'BÁN') normalized.type = 'SELL';
      if (normalized.type === 'MUA') normalized.type = 'BUY';
    }

    // Convert price from string with comma to number
    if (normalized.price && typeof normalized.price === 'string') {
      normalized.price = normalized.price.replace(',', '');
    }

    if (missingColumns.size > 0) {
      console.error('Available columns:', Object.keys(row));
      console.error('Normalized columns:', Object.keys(normalized));
      throw new Error(`Missing required columns: ${Array.from(missingColumns).join(', ')}`);
    }

    return normalized;
  }

  static parseDate(dateStr) {
    if (!dateStr) {
      throw new Error('Date is required');
    }

    // Remove time part if exists
    const dateOnly = dateStr.split(' ')[0];
    
    // Try different date formats
    const formats = ['dd/MM/yyyy', 'yyyy-MM-dd', 'MM/dd/yyyy'];
    for (const fmt of formats) {
      try {
        const parsedDate = dateFns.parse(dateOnly, fmt, new Date());
        if (!isNaN(parsedDate.getTime())) {
          return dateFns.format(parsedDate, 'yyyy-MM-dd');
        }
      } catch (e) {
        continue;
      }
    }
    throw new Error(`Invalid date format: ${dateStr}. Supported formats: ${formats.join(', ')} (time part will be ignored)`);
  }

  static calculateRunningBalance(transactions) {
    const balances = {};
    
    transactions.forEach(transaction => {
      const { symbol, type, volume } = transaction;
      if (!balances[symbol]) {
        balances[symbol] = 0;
      }
      
      // Update balance based on transaction type
      if (type === 'BUY') {
        balances[symbol] += volume;
      } else if (type === 'SELL') {
        balances[symbol] -= volume;
      }
    });

    return Object.entries(balances).map(([symbol, balance]) => ({
      symbol,
      balance
    }));
  }
}

module.exports = Parser; 