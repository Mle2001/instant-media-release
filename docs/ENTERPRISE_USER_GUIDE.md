# 🏢 Hướng Dẫn Sử Dụng Dashboard Doanh Nghiệp 
## Hệ Thống ML-Enhanced Ranking cho Instant Media Release

### 📋 Tổng Quan
Hệ thống Instant Media Release đã được nâng cấp với trí tuệ nhân tạo (AI) để học hỏi từ dữ liệu thực tế của các chiến dịch truyền thông. Hướng dẫn này sẽ giúp bạn sử dụng các dashboard (bảng điều khiển) dành cho doanh nghiệp một cách dễ dàng, ngay cả khi bạn không có kiến thức kỹ thuật.

---

## 🚀 Bước 1: Khởi Động Hệ Thống

### Cách chạy dashboard:
1. Mở Command Prompt hoặc Terminal
2. Di chuyển đến thư mục dự án: `cd D:\pythonlearn\instant-media-release`
3. Chạy lệnh: `python run_dashboards.py`
4. Hệ thống sẽ khởi động 2 dashboard:
   - **Dashboard Tải Dữ Liệu**: http://localhost:8501 
   - **Dashboard Giám Sát ML**: http://localhost:8502

### Nếu gặp lỗi:
- Đảm bảo đã cài đặt Python và các thư viện cần thiết
- Kiểm tra không có ứng dụng khác đang sử dụng port 8501, 8502

---

## 📊 Dashboard 1: Tải Dữ Liệu Chiến Dịch

**Truy cập tại**: http://localhost:8501

### Mục đích:
Dashboard này cho phép bạn tải lên kết quả thực tế từ các chiến dịch truyền thông để hệ thống AI có thể học hỏi và cải thiện độ chính xác của việc đề xuất báo chí.

### Cách sử dụng:

#### 📝 Tab 1: "Tải Lên Chiến Dịch Đơn"
**Khi nào sử dụng**: Khi bạn muốn nhập dữ liệu của 1 chiến dịch cụ thể.

**Các bước thực hiện**:

1. **Thông Tin Chiến Dịch**:
   - Nhập tên chiến dịch (VD: "Ra mắt sản phẩm ABC tháng 8/2025")
   - Chọn ngày bắt đầu và kết thúc chiến dịch
   - Nhập mô tả ngắn về chiến dịch

2. **Kết Quả Báo Chí**:
   - **Tên báo**: Nhập tên báo đã đăng bài (VD: "VnExpress", "Tuoi Tre")
   - **Loại bài**: Chọn từ dropdown (Tin tức, Phỏng vấn, Bài viết chuyên sâu, v.v.)
   - **Ngày đăng**: Chọn ngày báo đăng bài
   - **URL bài viết**: Dán link bài viết (nếu có)
   - **Số lượt xem**: Nhập số lượt xem/đọc (nếu biết)
   - **Tương tác**: Nhập số like, comment, share (nếu có)

3. **Chỉ Số Kinh Doanh**:
   - **Doanh thu**: Nhập doanh thu tạo ra từ chiến dịch (VNĐ)
   - **Chi phí**: Nhập tổng chi phí chiến dịch (VNĐ) 
   - **Khách hàng mới**: Số khách hàng mới có được
   - **Chuyển đổi**: Tỷ lệ % khách hàng tiềm năng thành khách hàng thực

4. **Nhấn "Tải Lên Dữ Liệu"**

#### 📁 Tab 2: "Tải Lên Hàng Loạt (CSV)"
**Khi nào sử dụng**: Khi bạn có nhiều chiến dịch và muốn tải lên cùng lúc.

**Cách tạo file CSV**:
1. Mở Excel hoặc Google Sheets
2. Tạo các cột theo mẫu:
   ```
   campaign_name | start_date | end_date | description | media_name | article_type | publish_date | url | views | interactions | revenue | cost | new_customers | conversion_rate
   ```
3. Điền dữ liệu vào từng hàng
4. Lưu file dạng CSV

**Upload file**:
1. Nhấn "Browse files" và chọn file CSV
2. Xem trước dữ liệu trong bảng hiển thị
3. Nhấn "Tải Lên Dữ Liệu CSV"

#### 📈 Tab 3: "Phân Tích Dữ Liệu"
**Mục đích**: Xem tổng quan về dữ liệu đã tải lên

**Thông tin hiển thị**:
- Số chiến dịch đã tải lên
- Top báo chí hiệu quả nhất
- Thống kê theo loại bài viết
- Biểu đồ xu hướng theo thời gian

---

## 🔍 Dashboard 2: Giám Sát Hệ Thống ML

**Truy cập tại**: http://localhost:8502

### Mục đích:
Dashboard này giúp bạn theo dõi hiệu suất của hệ thống AI và đảm bảo nó đang học hỏi hiệu quả từ dữ liệu bạn cung cấp.

### Các Tab chính:

#### 🎯 Tab 1: "Tổng Quan Hiệu Suất"
**Hiển thị**:
- **Độ chính xác hiện tại**: % dự đoán đúng của hệ thống
- **Số mô hình**: Có bao nhiêu phiên bản AI đang chạy
- **Dữ liệu huấn luyện**: Số lượng chiến dịch AI đã học từ
- **Cải thiện gần đây**: Mức độ cải thiện so với tháng trước

#### 🚀 Tab 2: "Tiến Trình Huấn Luyện"
**Thông tin theo dõi**:
- Trạng thái huấn luyện: Đang học/Hoàn thành/Lỗi
- Thời gian còn lại để hoàn thành việc học
- Biểu đồ tiến độ học tập

#### 🎨 Tab 3: "Tầm Quan Trọng Của Yếu Tố"
**Giải thích**:
Cho biết AI đang chú trọng yếu tố nào khi đề xuất báo chí:
- Nội dung bài viết (40%)
- Đối tượng mục tiêu (25%)
- Thời điểm phát hành (20%)
- Ngành nghề (15%)

---

## 💡 Lời Khuyên Sử Dụng Hiệu Quả

### ✅ Nên làm:

1. **Cập nhật dữ liệu thường xuyên**:
   - Tải lên kết quả sau mỗi chiến dịch (trong vòng 1 tuần)
   - Càng nhiều dữ liệu, AI càng thông minh

2. **Cung cấp thông tin đầy đủ**:
   - Điền đầy đủ các trường thông tin
   - Số liệu càng chính xác, AI học càng tốt

3. **Theo dõi Dashboard Giám Sát**:
   - Kiểm tra 1 lần/tuần để đảm bảo hệ thống hoạt động tốt
   - Chú ý thông báo lỗi (nếu có)

### ❌ Tránh làm:

1. **Không nhập dữ liệu sai lệch**:
   - Không nhập số liệu ảo hoặc quá phóng đại
   - AI sẽ học sai và cho kết quả không chính xác

2. **Không bỏ sót thông tin quan trọng**:
   - Luôn nhập đầy đủ thông tin báo chí và kết quả
   - Thông tin thiếu sót làm giảm khả năng học của AI

---

## 🆘 Xử Lý Sự Cố

### Lỗi thường gặp và cách khắc phục:

#### 1. "Cannot connect to dashboard"
**Nguyên nhân**: Dashboard chưa được khởi động
**Khắc phục**: 
- Chạy lại lệnh `python run_dashboards.py`
- Đợi 30 giây rồi refresh trình duyệt

#### 2. "File upload failed"
**Nguyên nhân**: File CSV không đúng định dạng
**Khắc phục**:
- Kiểm tra file CSV có đúng các cột yêu cầu không
- Đảm bảo ngày tháng theo định dạng YYYY-MM-DD
- File không quá 50MB

#### 3. "Training error"
**Nguyên nhân**: Dữ liệu không đủ để AI học
**Khắc phục**:
- Cần ít nhất 10 chiến dịch để AI bắt đầu học
- Mỗi chiến dịch cần có ít nhất 2 báo chí khác nhau

#### 4. "Model accuracy too low" 
**Nguyên nhân**: AI chưa học đủ hoặc dữ liệu chất lượng kém
**Khắc phục**:
- Tải thêm dữ liệu chiến dịch thành công
- Kiểm tra lại độ chính xác của số liệu đã nhập

---

## 📞 Hỗ Trợ Kỹ Thuật

### Khi nào cần liên hệ hỗ trợ:
- Dashboard không khởi động được sau nhiều lần thử
- Dữ liệu bị mất hoặc hiển thị sai
- AI không cải thiện sau 1 tháng sử dụng
- Cần tùy chỉnh dashboard theo nhu cầu riêng

### Thông tin cần chuẩn bị khi liên hệ:
1. Mô tả chi tiết lỗi gặp phải
2. Screenshots màn hình lỗi
3. Thời điểm xảy ra lỗi
4. Các bước đã thực hiện trước khi gặp lỗi

---

## 🏆 Tối Ưu Hóa Kết Quả

### Để có kết quả tốt nhất:

1. **Giai đoạn đầu (Tháng 1-2)**:
   - Tải lên ít nhất 20-30 chiến dịch cũ
   - Bao gồm cả chiến dịch thành công và thất bại
   - Đảm bảo dữ liệu đa dạng về ngành nghề và quy mô

2. **Giai đoạn phát triển (Tháng 3-6)**:
   - Tiếp tục cập nhật kết quả chiến dịch mới
   - Theo dõi độ chính xác AI qua Dashboard Giám Sát
   - Điều chỉnh chiến lược dựa trên gợi ý của AI

3. **Giai đoạn tối ưu (Tháng 6+)**:
   - AI đã đủ thông minh để đưa ra gợi ý chính xác
   - Sử dụng tính năng dự đoán tự động trong hệ thống chính
   - Tận dụng insights từ tab "Tầm Quan Trọng Của Yếu Tố"

---

## 📈 Hiểu Biết Kết Quả AI

### Cách đọc các chỉ số:

**Độ chính xác (Accuracy)**:
- 70-80%: Tốt cho giai đoạn đầu
- 80-90%: Rất tốt, có thể tin cậy gợi ý
- 90%+: Xuất sắc, AI rất thông minh

**Điểm tin cậy (Confidence Score)**:
- 0.5-0.7: Gợi ý cần xem xét thêm
- 0.7-0.9: Gợi ý đáng tin cậy
- 0.9+: Gợi ý rất chắc chắn

**Xu hướng học tập**:
- Đường cong đi lên: AI đang học tốt
- Đường cong phẳng: Cần thêm dữ liệu đa dạng
- Đường cong đi xuống: Cần kiểm tra chất lượng dữ liệu

---

*Hướng dẫn này được thiết kế để giúp người dùng không chuyên kỹ thuật có thể sử dụng hiệu quả hệ thống ML-Enhanced Ranking. Nếu cần hỗ trợ thêm, vui lòng liên hệ bộ phận kỹ thuật.*