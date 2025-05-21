// File: backend/test_transactions.js
const request = require('supertest');
const express = require('express');
const multer = require('multer');
const path = require('path');
const parser = require('./utils/parser');
const transactions = require('./transactions');
const app = express();
app.use(express.json());
app.use('/api/transactions', transactions);

jest.mock('./utils/parser');

describe('Transaction processing endpoints', () => {
  it('should handle file upload and return parsed transactions', async () => {
    parser.parseFile.mockResolvedValue([{ symbol: 'AAPL', volume: 10 }]);
    parser.calculateRunningBalance.mockReturnValue([{ symbol: 'AAPL', balance: 1000 }]);
    const filePath = path.join(__dirname, 'test_data/test.csv');
  
    const res = await request(app)
      .post('/api/transactions/upload')
      .attach('file', filePath);
    
    expect(res.statusCode).toBe(200);
    expect(res.body).toEqual(expect.arrayContaining([
      expect.objectContaining({ symbol: 'AAPL', runningBalance: 1000 })
    ]));
  });

  it('should return errors if no file is uploaded', async () => {
    const res = await request(app).post('/api/transactions/upload');
    expect(res.statusCode).toBe(400);
    expect(res.body.error).toBe('No file uploaded');
  });

  it('should return error for unsupported file format', async () => {
    const filePath = path.join(__dirname, 'test_data/test.txt');
    const res = await request(app)
      .post('/api/transactions/upload')
      .attach('file', filePath);
    expect(res.statusCode).toBe(400);
    expect(res.body.error).toBe('Unsupported file format');
  });

  it('should handle transaction import', async () => {
    const mockTransactions = [{ symbol: 'AAPL', volume: 10, price: 150 }];
    const res = await request(app)
      .post('/api/transactions/import')
      .send({ transactions: mockTransactions, userId: 'user123' });

    expect(res.statusCode).toBe(200);
    expect(res.body.success).toBe(1);
    expect(res.body.errors).toEqual([]);
  });
});

// File: backend/test_server.js
const request = require('supertest');
const app = require('./server');

describe('API Endpoints', () => {
  it('should respond to an API request', async () => {
    const res = await request(app).get('/');
    expect(res.statusCode).toBe(404); 
  });

  it('should respond with a 404 for unknown endpoints', async () => {
    const res = await request(app).get('/unknown');
    expect(res.statusCode).toBe(404);
  });
});

// File: frontend/tests/TransactionUploader.spec.js
import { shallowMount } from '@vue/test-utils';
import TransactionUploader from '@/components/TransactionUploader.vue';
import axios from 'axios';
import { ElMessage } from 'element-plus';

jest.mock('axios');

describe('TransactionUploader.vue', () => {
  let wrapper;

  beforeEach(() => {
    wrapper = shallowMount(TransactionUploader);
  });

  it('should upload a file and handle success', async () => {
    const mockTransactions = [{ symbol: 'AAPL', tradeDate: '2021-12-10', volume: 10 }];
    axios.post.mockResolvedValue({ data: mockTransactions });

    wrapper.vm.handleFileSuccess(mockTransactions);
    expect(wrapper.vm.transactions).toEqual(mockTransactions);
  });

  it('should show an error message for unsupported file format', () => {
    const mockFile = new File(['test'], 'test.txt', { type: 'text/plain' });
    const result = wrapper.vm.beforeUpload(mockFile);
    expect(result).toBe(false);
  });

  it('should show an error message if import fails', async () => {
    axios.post.mockRejectedValue(new Error('Failed to import transactions.'));
    wrapper.vm.importTransactions();
    await wrapper.vm.$nextTick();
    expect(ElMessage.error).toHaveBeenCalledWith('Failed to import transactions.');
  });
});

// File: frontend/tests/App.spec.js
import { shallowMount } from '@vue/test-utils';
import App from '@/App.vue';
import TransactionUploader from '@/components/TransactionUploader.vue';

describe('App.vue', () => {
  it('renders TransactionUploader component', () => {
    const wrapper = shallowMount(App);
    const uploader = wrapper.findComponent(TransactionUploader);
    expect(uploader.exists()).toBe(true);
  });
});