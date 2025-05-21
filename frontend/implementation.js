<!-- File: frontend/src/components/TransactionUploader.vue -->
<template>
  <div>
    <el-upload
      class="upload-demo"
      drag
      action="/api/transactions/upload"
      :show-file-list="false"
      accept=".csv,.xlsx"
      :before-upload="beforeUpload"
      :on-success="handleFileSuccess"
      :on-error="handleFileError">
      <i class="el-icon-upload"></i>
      <div class="el-upload__text">Drag the CSV/XLSX file here or <em>click to upload</em></div>
    </el-upload>
    <el-table
      v-if="transactions.length > 0"
      :data="transactions"
      style="width: 100%">
      <el-table-column type="index" label="#" width="50"></el-table-column>
      <el-table-column prop="tradeDate" label="Ngày GD"></el-table-column>
      <el-table-column prop="symbol" label="Mã CK"></el-table-column>
      <el-table-column prop="type" label="Loại GD"></el-table-column>
      <el-table-column prop="volume" label="Khối lượng"></el-table-column>
      <el-table-column prop="price" label="Giá"></el-table-column>
      <el-table-column prop="feeRate" label="Tỷ lệ phí"></el-table-column>
      <el-table-column prop="taxRate" label="Tỷ lệ thuế"></el-table-column>
      <el-table-column
        prop="runningBalance"
        label="Running Balance"
        :cell-class-name="getBalanceClass">
      </el-table-column>
    </el-table>
    <el-button type="primary" @click="importTransactions" :disabled="transactions.length === 0">Import</el-button>
  </div>
</template>

<script>
import { ElMessage } from 'element-plus';
import axios from 'axios';

export default {
  data() {
    return {
      transactions: []
    };
  },
  methods: {
    beforeUpload(file) {
      const isCSVOrXLSX = file.type.includes('csv') || file.type.includes('sheet');
      if (!isCSVOrXLSX) {
        ElMessage.error('Unsupported file format, please upload CSV/XLSX.');
      }
      return isCSVOrXLSX;
    },
    handleFileSuccess(response) {
      this.transactions = response.map((transaction, index) => ({
        ...transaction,
        rowIndex: index + 1
      }));
    },
    handleFileError() {
      ElMessage.error('There was an error processing your file.');
    },
    async importTransactions() {
      try {
        const { data } = await axios.post('/api/transactions/import', {
          transactions: this.transactions,
          userId: 'user123' // Hardcoded user id for the example
        });
        if (data.errors.length === 0) {
          ElMessage.success(`✅ Import thành công ${data.success} giao dịch.`);
        } else {
          data.errors.forEach((error) => {
            ElMessage.error(`❌ Lỗi parsing/giá/khối lượng <= 0 at row: ${error.index + 1}`);
          });
        }
      } catch (error) {
        ElMessage.error('Failed to import transactions.');
      }
    },
    getBalanceClass({ row }) {
      return row.runningBalance < 0 ? 'negative-balance' : '';
    }
  }
};
</script>

<style scoped>
.upload-demo {
  margin-bottom: 20px;
}
.el-upload__text {
  font-size: 16px;
}
.negative-balance {
  background-color: yellow;
  color: red;
}
</style>

<!-- File: frontend/src/App.vue -->
<template>
  <div id="app">
    <transaction-uploader />
  </div>
</template>

<script>
import TransactionUploader from './components/TransactionUploader.vue';

export default {
  components: {
    TransactionUploader
  }
};
</script>

<!-- File: frontend/src/main.js -->
import { createApp } from 'vue';
import ElementPlus from 'element-plus';
import 'element-plus/dist/index.css';
import App from './App.vue';
import axios from 'axios';

axios.defaults.baseURL = process.env.VUE_APP_API_BASE_URL || 'http://localhost:4000';

createApp(App).use(ElementPlus).mount('#app');

<!-- File: frontend/public/index.html -->
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Transaction Import</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body>
  <div id="app"></div>
  <!-- built files will be auto injected -->
</body>
</html>

<!-- File: frontend/package.json -->
{
  "name": "transaction-import-frontend",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "serve": "vue-cli-service serve",
    "build": "vue-cli-service build",
    "lint": "vue-cli-service lint"
  },
  "dependencies": {
    "axios": "^0.24.0",
    "element-plus": "^1.1.0-beta.19",
    "vue": "^3.2.20"
  },
  "devDependencies": {
    "@vue/cli-plugin-babel": "^5.0.0-beta.3",
    "@vue/cli-plugin-eslint": "^5.0.0-beta.3",
    "@vue/cli-service": "^5.0.0-beta.3",
    "babel-eslint": "^10.1.0",
    "eslint": "^7.32.0",
    "eslint-plugin-vue": "^7.18.0"
  },
  "eslintConfig": {
    "root": true,
    "env": {
      "node": true
    },
    "extends": [
      "plugin:vue/vue3-essential",
      "eslint:recommended"
    ],
    "parserOptions": {
      "parser": "babel-eslint"
    }
  }
}

<!-- File: frontend/vue.config.js -->
module.exports = {
  devServer: {
    proxy: {
      '/api': {
        target: 'http://localhost:4000',
        changeOrigin: true
      }
    }
  },
  publicPath: '/'
};