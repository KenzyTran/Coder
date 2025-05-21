const express = require('express');
const multer = require('multer');
const parser = require('./utils/parser');
const Transaction = require('./models/Transaction');
const fs = require('fs').promises;
const path = require('path');

const router = express.Router();

const storage = multer.memoryStorage();
const upload = multer({ storage });

const DB_FILE = path.join(__dirname, 'mockdb/db.json');

// Helper function to read/write database
async function readDB() {
  try {
    const data = await fs.readFile(DB_FILE, 'utf8');
    return JSON.parse(data);
  } catch (error) {
    // If file doesn't exist or is empty, return default structure
    return { transactions: [] };
  }
}

async function writeDB(data) {
  await fs.writeFile(DB_FILE, JSON.stringify(data, null, 2), 'utf8');
}

// Initialize database if it doesn't exist
async function initDB() {
  try {
    await fs.access(DB_FILE);
  } catch {
    await writeDB({ transactions: [] });
  }
}

// Initialize database on startup
initDB().catch(console.error);

router.post('/upload', upload.single('file'), async (req, res) => {
  const { file } = req;
  const { userId } = req.body;

  console.log('Upload request received:', {
    fileName: file?.originalname,
    fileSize: file?.size,
    fileType: file?.mimetype,
    userId
  });

  if (!userId) {
    console.error('No userId provided');
    return res.status(400).json({ 
      error: 'userId is required',
      details: 'Please provide a userId in the request'
    });
  }

  if (!file) {
    console.error('No file uploaded');
    return res.status(400).json({ error: 'No file uploaded' });
  }

  const fileExt = path.extname(file.originalname).toLowerCase();
  if (fileExt !== '.csv' && fileExt !== '.xlsx') {
    console.error('Unsupported file format:', fileExt);
    return res.status(400).json({ error: 'Unsupported file format' });
  }

  try {
    console.log('Parsing file...');
    const transactions = await parser.parseFile(file, userId);
    console.log('File parsed successfully, transactions:', transactions.length);

    // Sort transactions by date
    transactions.sort((a, b) => new Date(a.tradeDate) - new Date(b.tradeDate));

    // Calculate running balance for each transaction
    const symbolBalances = {};
    transactions.forEach(transaction => {
      const { symbol, type, volume } = transaction;
      if (!symbolBalances[symbol]) {
        symbolBalances[symbol] = 0;
      }
      
      // Update balance based on transaction type
      symbolBalances[symbol] += (type === 'BUY' ? volume : -volume);
      
      // Store the running balance at this point
      transaction.runningBalance = symbolBalances[symbol];
      transaction.balanceStatus = transaction.runningBalance < 0 ? 'negative' : 'positive';
    });

    console.log('Running balances calculated for each transaction');

    const preview = transactions.map((t, index) => {
      // Calculate fee rate and tax rate
      const totalAmount = t.price * t.volume;
      const feeRate = t.fee / totalAmount;
      const taxRate = t.type === 'SELL' ? t.tax / totalAmount : null;

      return {
        rowIndex: index + 1,
        symbol: t.symbol,
        tradeDate: t.tradeDate,
        type: t.type,
        price: t.price,
        volume: t.volume,
        fee: t.fee,
        tax: t.tax,
        feeRate,
        taxRate,
        validation: (t.price > 0 && t.volume > 0) ? 'ok' : 'error',
        runningBalance: t.runningBalance,
        balanceStatus: t.balanceStatus
      };
    });

    console.log('Sending preview response...');
    res.json(preview);
  } catch (error) {
    console.error('Error processing file:', error);
    res.status(500).json({ 
      error: 'Failed to process file', 
      details: error.message,
      stack: process.env.NODE_ENV === 'development' ? error.stack : undefined
    });
  }
});

router.post('/import', async (req, res) => {
  console.log('Import request received:', {
    transactionCount: req.body.transactions?.length,
    userId: req.body.userId,
    ignoreNegativeBalances: req.body.ignoreNegativeBalances
  });

  const { transactions, userId, ignoreNegativeBalances } = req.body;

  if (!userId) {
    console.error('No userId provided');
    return res.status(400).json({ 
      error: 'userId is required',
      details: 'Please provide a userId in the request'
    });
  }

  if (!Array.isArray(transactions)) {
    console.error('Invalid request: transactions is not an array');
    return res.status(400).json({ 
      error: 'Invalid request format',
      details: 'transactions must be an array'
    });
  }

  const errors = [];
  const importedTransactions = [];

  try {
    // Read current database state
    const db = await readDB();
    
    for (const [index, transaction] of transactions.entries()) {
      // Add userId to each transaction
      transaction.userId = userId;

      console.log(`Processing transaction ${index + 1}:`, {
        symbol: transaction.symbol,
        type: transaction.type,
        volume: transaction.volume,
        price: transaction.price,
        userId: transaction.userId
      });

      try {
        const { error } = Transaction.validate(transaction);
        if (error) {
          console.error(`Validation error in transaction ${index + 1}:`, error.details);
          errors.push({ 
            index, 
            error: error.details[0].message,
            transaction: {
              symbol: transaction.symbol,
              type: transaction.type,
              volume: transaction.volume,
              price: transaction.price
            }
          });
          continue;
        }

        // Additional validation
        if (transaction.price <= 0) {
          throw new Error(`Giá giao dịch phải lớn hơn 0 (giá hiện tại: ${transaction.price})`);
        }
        if (transaction.volume <= 0) {
          throw new Error(`Khối lượng phải lớn hơn 0 (khối lượng hiện tại: ${transaction.volume})`);
        }
        if (!['BUY', 'SELL'].includes(transaction.type)) {
          throw new Error(`Loại giao dịch không hợp lệ: ${transaction.type}`);
        }

        // Add transaction to database
        const transactionWithId = {
          ...transaction,
          id: `${userId}-${Date.now()}-${index}`,
          userId // Add userId to transaction
        };
        
        db.transactions.push(transactionWithId);
        importedTransactions.push(transactionWithId);
        
        console.log(`Transaction ${index + 1} imported successfully:`, {
          symbol: transaction.symbol,
          type: transaction.type,
          volume: transaction.volume,
          runningBalance: transaction.runningBalance
        });
      } catch (err) {
        console.error(`Error processing transaction ${index + 1}:`, err);
        errors.push({ 
          index, 
          error: err.message,
          transaction: {
            symbol: transaction.symbol,
            type: transaction.type,
            volume: transaction.volume,
            price: transaction.price
          }
        });
      }
    }

    // Save all transactions to database
    if (importedTransactions.length > 0) {
      await writeDB(db);
    }

    const successCount = importedTransactions.length;
    console.log('Import completed:', {
      total: transactions.length,
      success: successCount,
      errors: errors.length
    });

    res.json({
      success: successCount,
      errors: errors.map(e => ({
        index: e.index,
        error: e.error,
        symbol: e.transaction.symbol
      }))
    });
  } catch (error) {
    console.error('Unexpected error during import:', error);
    res.status(500).json({ 
      error: 'Failed to import transactions',
      details: error.message
    });
  }
});

module.exports = router; 