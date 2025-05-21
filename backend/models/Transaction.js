const Joi = require('joi');

const transactionSchema = Joi.object({
  userId: Joi.string().required(),
  symbol: Joi.string().required().min(1).max(10),
  tradeDate: Joi.string().required().pattern(/^\d{4}-\d{2}-\d{2}$/),
  type: Joi.string().required().valid('BUY', 'SELL'),
  price: Joi.number().required().min(0),
  volume: Joi.number().required().integer().min(1),
  fee: Joi.number().required().min(0),
  tax: Joi.number().required().min(0),
  feeRate: Joi.number().required().min(0),
  taxRate: Joi.number().required().min(0),
  id: Joi.string().optional()
});

class Transaction {
  static validate(transaction) {
    return transactionSchema.validate(transaction, {
      abortEarly: false,
      stripUnknown: true
    });
  }

  static validateBatch(transactions) {
    const errors = [];
    transactions.forEach((transaction, index) => {
      const { error } = this.validate(transaction);
      if (error) {
        errors.push({
          index,
          details: error.details.map(detail => detail.message)
        });
      }
    });
    return errors;
  }
}

module.exports = Transaction; 