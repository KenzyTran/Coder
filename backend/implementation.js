```
// File: backend/server.js
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const dotenv = require('dotenv');
dotenv.config();

const transactionsRouter = require('./transactions.js');

const app = express();

app.use(cors());
app.use(helmet());
app.use(express.json());

app.use('/api/transactions', transactionsRouter);

const PORT = process.env.PORT || 4000;
app.listen(PORT, () => {
  console.log(`Server is running on http://localhost:${PORT}`);
});

// File: backend/transactions.js
const express = require('express');
const multer = require('multer');
const parser = require('./utils/parser');
const Transaction = require('./models/Transaction');
const lowdb = require('lowdb');
const FileSync = require('lowdb/adapters/FileSync');
const path = require('path');

const router = express.Router();

const storage = multer.memoryStorage();
const upload = multer({ storage });

const adapter = new FileSync(path.join(__dirname, 'mockdb/db.json'));
const db = lowdb(adapter);
db.defaults({ transactions: [] }).write();

router.post('/upload', upload.single('file'), async (req, res) => {
  const { file } = req;
  const { userId } = req.body;

  if (!file) {
    return res.status(400).json({ error: 'No file uploaded' });
  }

  const fileExt = path.extname(file.originalname).toLowerCase();
  if (fileExt !== '.csv' && fileExt !== '.xlsx') {
    return res.status(400).json({ error: 'Unsupported file format' });
  }

  try {
    const transactions = await parser.parseFile(file, userId);
    const runningBalances = parser.calculateRunningBalance(transactions);

    transactions.forEach((transaction, index) => {
      const balance = runningBalances.find(rb => rb.symbol === transaction.symbol);
      transaction.runningBalance = balance ? balance.balance : 0;
      transaction.balanceStatus = transaction.runningBalance < 0 ? 'negative' : 'positive';
    })

    const preview = transactions.map((t, index) => ({
      rowIndex: index + 1,
      symbol: t.symbol,
      tradeDate: t.tradeDate,
      type: t.type,
      price: t.price,
      volume: t.volume,
      fee: t.fee,
      tax: t.tax,
      feeRate: t.feeRate,
      taxRate: t.taxRate,
      validation: (t.price > 0 && t.volume > 0) ? 'ok' : 'error',
      runningBalance: t.runningBalance,
      balanceStatus: t.balanceStatus
    }));

    res.json(preview);
  } catch (error) {
    res.status(500).json({ error: 'Failed to process file', details: error.message });
  }
});

router.post('/import', (req, res) => {
  const { transactions, userId } = req.body;
  const errors = [];

  transactions.forEach((transaction, index) => {
    const { error } = Transaction.validate(transaction);
    if (error) {
      errors.push({ index, error: error.details[0].message });
    } else {
      transaction.id = `${userId}-${Date.now()}-${index}`;
      db.get('transactions').push(transaction).write();
    }
  });

  const successCount = transactions.length - errors.length;
  res.json({
    success: successCount,
    errors
  });
});

module.exports = router;

// File: backend/package.json
{
  "name": "transaction-import-system",
  "version": "1.0.0",
  "main": "server.js",
  "scripts": {
    "start": "node server.js",
    "dev": "nodemon server.js"
  },
  "dependencies": {
    "cors": "^2.8.5",
    "csv-parse": "^5.3.0",
    "date-fns": "^2.29.2",
    "dotenv": "^16.0.0",
    "express": "^4.18.0",
    "helmet": "^5.0.2",
    "joi": "^17.6.0",
    "lowdb": "^6.0.1",
    "multer": "^1.4.5",
    "xlsx": "^0.18.5"
  },
  "devDependencies": {
    "eslint": "^8.9.0",
    "jest": "^28.0.2",
    "nodemon": "^2.0.15"
  }
}

// File: backend/.env
PORT=4000
```