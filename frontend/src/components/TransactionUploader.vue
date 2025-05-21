<template>
  <div class="transaction-uploader">
    <div class="upload-section">
      <div v-if="!currentFile" class="upload-area">
        <el-upload
          class="upload-demo"
          drag
          action="/api/transactions/upload"
          :show-file-list="false"
          accept=".csv,.xlsx"
          :before-upload="beforeUpload"
          :on-success="handleFileSuccess"
          :on-error="handleFileError"
          :data="{ userId: 'user123' }">
          <div class="upload-content">
            <i class="el-icon-upload upload-icon"></i>
            <div class="upload-text">
              <div class="main-text">Kéo thả file CSV/XLSX vào đây</div>
              <div class="sub-text">hoặc</div>
              <el-button type="primary" class="select-button">Chọn file</el-button>
            </div>
            <div class="upload-tip">
              <i class="el-icon-info"></i>
              <span>Chỉ hỗ trợ file CSV/XLSX</span>
            </div>
            <div class="template-link">
              <i class="el-icon-document"></i>
              <a 
                href="https://docs.google.com/spreadsheets/d/15SqeWc1Yp10TXqMn0SDFufrLte0kBud6fvhdjtIoUmI/edit?gid=0#gid=0" 
                target="_blank"
                rel="noopener noreferrer">
                Tải file mẫu để điền thông tin giao dịch
              </a>
            </div>
          </div>
        </el-upload>
      </div>

      <div v-else class="file-info">
        <el-alert
          :title="`File đã chọn: ${currentFile.name}`"
          type="success"
          :closable="false"
          show-icon>
          <template #default>
            <div class="file-actions">
              <span class="file-size">{{ formatFileSize(currentFile.size) }}</span>
              <el-button 
                type="danger" 
                size="small" 
                @click="handleFileRemove"
                icon="Delete">
                Xóa file
              </el-button>
            </div>
          </template>
        </el-alert>
      </div>
    </div>

    <div v-if="transactions.length > 0" class="transactions-section">
      <!-- Main transactions table -->
      <div class="section-header">
        <h3>Danh sách giao dịch</h3>
        <el-button 
          type="primary" 
          size="large"
          @click="importTransactions" 
          :disabled="transactions.length === 0 || (hasNegativeBalances && !ignoreNegativeBalances)">
          Import Giao Dịch
        </el-button>
      </div>

      <el-table
        :data="transactions"
        style="width: 100%; margin-bottom: 20px"
        border>
        <el-table-column type="index" label="#" width="50"></el-table-column>
        <el-table-column prop="tradeDate" label="Ngày GD"></el-table-column>
        <el-table-column prop="symbol" label="Mã CK"></el-table-column>
        <el-table-column prop="type" label="Loại GD"></el-table-column>
        <el-table-column prop="volume" label="Khối lượng"></el-table-column>
        <el-table-column label="Giá (nghìn đồng)">
          <template #default="scope">
            {{ formatPrice(scope.row.price) }}
          </template>
        </el-table-column>
        <el-table-column label="Tỷ lệ phí">
          <template #default="scope">
            {{ formatPercentage(scope.row.feeRate) }}
          </template>
        </el-table-column>
        <el-table-column label="Tỷ lệ thuế">
          <template #default="scope">
            {{ scope.row.type === 'SELL' ? formatPercentage(scope.row.taxRate) : '-' }}
          </template>
        </el-table-column>
        <el-table-column
          prop="runningBalance"
          label="Running Balance"
          :cell-class-name="getBalanceClass">
        </el-table-column>
      </el-table>

      <!-- Negative balance warning table -->
      <div v-if="hasNegativeBalances" class="negative-balance-warning">
        <el-alert
          title="Cảnh báo: Có giao dịch dẫn đến số dư âm"
          type="warning"
          :closable="false"
          show-icon>
          <template #default>
            <p>Vui lòng kiểm tra các giao dịch sau:</p>
          </template>
        </el-alert>

        <el-table
          :data="negativeBalanceTransactions"
          style="width: 100%; margin: 10px 0 20px 0"
          border>
          <el-table-column type="index" label="#" width="50"></el-table-column>
          <el-table-column prop="symbol" label="Mã CK"></el-table-column>
          <el-table-column prop="runningBalance" label="Số dư cuối"></el-table-column>
          <el-table-column label="Chi tiết giao dịch">
            <template #default="scope">
              <el-table
                :data="getTransactionsForSymbol(scope.row.symbol)"
                style="width: 100%"
                size="small">
                <el-table-column prop="tradeDate" label="Ngày GD" width="120"></el-table-column>
                <el-table-column prop="type" label="Loại GD" width="100"></el-table-column>
                <el-table-column prop="volume" label="Khối lượng" width="100"></el-table-column>
                <el-table-column label="Giá (nghìn đồng)" width="120">
                  <template #default="scope">
                    {{ formatPrice(scope.row.price) }}
                  </template>
                </el-table-column>
              </el-table>
            </template>
          </el-table-column>
        </el-table>

        <el-checkbox v-model="ignoreNegativeBalances" style="margin-bottom: 20px">
          Bỏ qua cảnh báo số dư âm và tiếp tục import
        </el-checkbox>
      </div>
    </div>
  </div>
</template>

<script>
import { ElMessage } from 'element-plus';
import axios from 'axios';

export default {
  data() {
    return {
      transactions: [],
      ignoreNegativeBalances: false,
      userId: 'user123',
      currentFile: null
    };
  },
  computed: {
    hasNegativeBalances() {
      return this.transactions.some(t => t.runningBalance < 0);
    },
    negativeBalanceTransactions() {
      const symbols = [...new Set(this.transactions
        .filter(t => t.runningBalance < 0)
        .map(t => t.symbol))];
      
      return symbols.map(symbol => {
        const transactions = this.getTransactionsForSymbol(symbol);
        const lastTransaction = transactions[transactions.length - 1];
        return {
          symbol,
          runningBalance: lastTransaction.runningBalance,
          transactions
        };
      });
    }
  },
  methods: {
    beforeUpload(file) {
      const isCSVOrXLSX = file.type.includes('csv') || file.type.includes('sheet');
      if (!isCSVOrXLSX) {
        ElMessage.error('Chỉ hỗ trợ file CSV/XLSX');
        return false;
      }
      this.currentFile = file;
      return true;
    },
    handleFileSuccess(response, file) {
      this.currentFile = file;
      this.transactions = response.map((transaction, index) => {
        const totalAmount = transaction.price * transaction.volume;
        const feeRate = transaction.fee / totalAmount;
        const taxRate = transaction.type === 'SELL' ? (transaction.tax / totalAmount) : 0;

        return {
          ...transaction,
          rowIndex: index + 1,
          feeRate,
          taxRate
        };
      });
      this.ignoreNegativeBalances = false;
    },
    handleFileError(error) {
      console.error('Upload error:', error);
      const errorMessage = error.response?.data?.error || 'Có lỗi xảy ra khi xử lý file.';
      ElMessage.error(errorMessage);
      this.currentFile = null;
    },
    handleFileRemove() {
      this.currentFile = null;
      this.transactions = [];
      this.ignoreNegativeBalances = false;
      ElMessage.success('Đã xóa file');
    },
    formatFileSize(bytes) {
      if (bytes === 0) return '0 B';
      const k = 1024;
      const sizes = ['B', 'KB', 'MB', 'GB'];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },
    async importTransactions() {
      try {
        console.log('Starting import with data:', {
          transactionCount: this.transactions.length,
          ignoreNegativeBalances: this.ignoreNegativeBalances,
          userId: this.userId,
          sampleTransaction: this.transactions[0]
        });

        const { data } = await axios.post('/api/transactions/import', {
          transactions: this.transactions,
          userId: this.userId,
          ignoreNegativeBalances: this.ignoreNegativeBalances
        }, {
          timeout: 30000, // 30 seconds timeout
          headers: {
            'Content-Type': 'application/json'
          }
        });
        
        console.log('Import response:', data);
        
        if (data.errors.length === 0) {
          ElMessage.success(`✅ Import thành công ${data.success} giao dịch.`);
          this.transactions = []; // Clear the table after successful import
          this.currentFile = null; // Clear the current file
        } else {
          console.error('Import errors:', data.errors);
          data.errors.forEach((error) => {
            const transaction = this.transactions[error.index];
            ElMessage.error(
              `❌ Lỗi ở dòng ${error.index + 1} (${transaction.symbol}): ${error.error}`
            );
          });
        }
      } catch (error) {
        console.error('Import error details:', {
          message: error.message,
          response: error.response?.data,
          status: error.response?.status,
          code: error.code
        });
        
        let errorMessage = 'Không thể kết nối đến máy chủ. ';
        
        if (error.code === 'ECONNABORTED') {
          errorMessage += 'Yêu cầu đã hết thời gian chờ. Vui lòng thử lại.';
        } else if (!error.response) {
          errorMessage += 'Vui lòng kiểm tra kết nối mạng và thử lại.';
        } else if (error.response.status === 404) {
          errorMessage += 'Không tìm thấy API endpoint. Vui lòng liên hệ admin.';
        } else if (error.response.status === 500) {
          errorMessage += 'Lỗi máy chủ. Vui lòng thử lại sau.';
        } else {
          errorMessage += error.response?.data?.error || 
                         error.response?.data?.details || 
                         error.message || 
                         'Đã xảy ra lỗi không xác định.';
        }
        
        ElMessage.error(`❌ Lỗi import: ${errorMessage}`);
      }
    },
    getBalanceClass({ row }) {
      return row.runningBalance < 0 ? 'negative-balance' : '';
    },
    getTransactionsForSymbol(symbol) {
      return this.transactions
        .filter(t => t.symbol === symbol)
        .sort((a, b) => new Date(a.tradeDate) - new Date(b.tradeDate));
    },
    formatPrice(price) {
      return (price / 1000).toLocaleString('vi-VN', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      });
    },
    formatPercentage(value) {
      if (value === null || value === undefined || value === 0) return '-';
      return `${(value * 100).toLocaleString('vi-VN', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      })}%`;
    }
  }
};
</script>

<style scoped>
.transaction-uploader {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.upload-section {
  margin-bottom: 30px;
}

.upload-area {
  border: 2px dashed #dcdfe6;
  border-radius: 8px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  transition: all 0.3s;
  background-color: #fafafa;
  padding: 20px;
}

.upload-area:hover {
  border-color: #409eff;
  background-color: #f5f7fa;
}

.upload-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px 0;
}

.upload-icon {
  font-size: 48px;
  color: #c0c4cc;
  margin-bottom: 16px;
}

.upload-text {
  text-align: center;
  margin-bottom: 16px;
}

.main-text {
  font-size: 18px;
  color: #303133;
  margin-bottom: 8px;
  font-weight: 500;
}

.sub-text {
  font-size: 14px;
  color: #909399;
  margin-bottom: 12px;
}

.select-button {
  padding: 12px 24px;
  font-size: 14px;
  border-radius: 4px;
}

.upload-tip {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #909399;
  font-size: 13px;
  margin-top: 12px;
}

.upload-tip i {
  font-size: 14px;
  color: #909399;
}

.template-link {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 8px;
  font-size: 13px;
}

.template-link i {
  color: #409eff;
  font-size: 14px;
}

.template-link a {
  color: #409eff;
  text-decoration: none;
  transition: color 0.3s;
}

.template-link a:hover {
  color: #66b1ff;
  text-decoration: underline;
}

:deep(.el-upload) {
  width: 100%;
}

:deep(.el-upload-dragger) {
  width: 100%;
  height: auto;
  border: none;
  background: transparent;
}

:deep(.el-upload-dragger:hover) {
  background: transparent;
}

.file-info {
  margin-top: 15px;
  border-radius: 8px;
  overflow: hidden;
}

.file-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
  padding: 0 4px;
}

.file-size {
  color: #606266;
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.file-size::before {
  content: '';
  display: inline-block;
  width: 4px;
  height: 4px;
  background-color: #909399;
  border-radius: 50%;
}

.transactions-section {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 12px 0 rgba(0,0,0,0.1);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #ebeef5;
}

.section-header h3 {
  margin: 0;
  color: #303133;
  font-size: 18px;
}

.negative-balance {
  background-color: #fff2f0;
  color: #f56c6c;
}

.negative-balance-warning {
  margin: 20px 0;
  padding: 15px;
  border: 1px solid #e6a23c;
  border-radius: 4px;
  background-color: #fdf6ec;
}

/* Responsive styles */
@media (max-width: 768px) {
  .section-header {
    flex-direction: column;
    gap: 10px;
  }
  
  .section-header .el-button {
    width: 100%;
  }
}
</style> 