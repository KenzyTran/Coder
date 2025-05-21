# Hệ Thống Import Giao Dịch Chứng Khoán

Hệ thống cho phép import và quản lý các giao dịch chứng khoán từ file Excel/CSV, với các tính năng như kiểm tra số dư âm, tính toán phí và thuế, và hiển thị báo cáo chi tiết.

## Tính Năng Chính

- Upload file Excel/CSV chứa thông tin giao dịch
- Tự động parse và validate dữ liệu
- Tính toán số dư (running balance) cho từng mã chứng khoán
- Cảnh báo số dư âm và cho phép bỏ qua cảnh báo
- Tính toán tự động phí giao dịch và thuế
- Hiển thị báo cáo chi tiết với định dạng số tiền và tỷ lệ phần trăm
- Template file mẫu để người dùng điền thông tin

## Yêu Cầu Hệ Thống

- Node.js >= 14.x
- npm >= 6.x
- Vue.js 3.x
- Express.js
- Modern web browser (Chrome, Firefox, Edge)

## Cài Đặt

### 1. Clone Repository

```bash
git clone <repository-url>
cd engineering_team
```

### 2. Cài Đặt Backend

```bash
cd backend
npm install
```

Tạo file `.env` trong thư mục backend với nội dung:
```
PORT=4000
```

### 3. Cài Đặt Frontend

```bash
cd frontend
npm install
```

## Chạy Ứng Dụng

### 1. Khởi Động Backend

```bash
cd backend
npm run dev
```

Server sẽ chạy tại `http://localhost:4000`

### 2. Khởi Động Frontend

```bash
cd frontend
npm run serve
```

Ứng dụng sẽ chạy tại `http://localhost:8080`

## Cấu Trúc Dự Án

```
engineering_team/
├── backend/                   # Backend Node.js/Express
│   ├── server.js             # Entry point server
│   ├── transactions.js       # Xử lý logic giao dịch
│   ├── models/              
│   │   └── Transaction.js    # Model giao dịch
│   └── utils/
│       └── parser.js         # Xử lý parse file
├── frontend/                  # Frontend Vue.js
│   ├── src/
│   │   ├── App.vue           # Root component
│   │   ├── main.js           # Entry point Vue
│   │   └── components/
│   │       └── TransactionUploader.vue  # Component upload
│   └── vue.config.js         # Cấu hình Vue
└── tests/                     # Unit tests
```

## Hướng Dẫn Sử Dụng

### 1. Chuẩn Bị File

- Tải file mẫu từ link trong giao diện upload
- Điền thông tin giao dịch theo mẫu:
  - Mã CK: Mã chứng khoán
  - Ngày giao dịch: Định dạng DD/MM/YYYY
  - Loại giao dịch: MUA hoặc BÁN
  - Giá thực hiện: Giá giao dịch
  - Khối lượng: Số lượng cổ phiếu
  - Phí thực hiện: Phí giao dịch
  - Thuế bán: Thuế (chỉ cho giao dịch BÁN)

### 2. Upload File

- Kéo thả file vào vùng upload hoặc click để chọn file
- Hệ thống sẽ tự động parse và hiển thị preview
- Kiểm tra thông tin và số dư

### 3. Import Giao Dịch

- Nếu có số dư âm, hệ thống sẽ hiển thị cảnh báo
- Chọn "Bỏ qua cảnh báo số dư âm" nếu muốn tiếp tục
- Click "Import Giao Dịch" để lưu vào hệ thống

## Xử Lý Lỗi

### Lỗi Thường Gặp

1. "Lỗi parsing/giá/khối lượng <= 0"
   - Kiểm tra lại giá và khối lượng trong file
   - Đảm bảo không có giá trị âm hoặc bằng 0

2. "Lỗi network"
   - Kiểm tra kết nối mạng
   - Đảm bảo backend đang chạy
   - Thử refresh trang

3. "Lỗi định dạng file"
   - Chỉ hỗ trợ file .xlsx và .csv
   - Tải và sử dụng file mẫu

## Đóng Góp

1. Fork repository
2. Tạo branch mới (`git checkout -b feature/AmazingFeature`)
3. Commit thay đổi (`git commit -m 'Add some AmazingFeature'`)
4. Push lên branch (`git push origin feature/AmazingFeature`)
5. Tạo Pull Request

## License

MIT License - Xem file [LICENSE](LICENSE) để biết thêm chi tiết.

## Liên Hệ

Nếu có bất kỳ câu hỏi hoặc góp ý nào, vui lòng tạo issue trong repository.
