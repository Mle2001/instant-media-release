# 📊 Hướng Dẫn Chi Tiết: Chuẩn Bị Dữ Liệu & Sử Dụng Dashboard Doanh Nghiệp

## 🎯 Mục Đích Tài Liệu

Tài liệu này hướng dẫn chi tiết cách doanh nghiệp chuẩn bị dữ liệu chất lượng cao và sử dụng hiệu quả các dashboard để hệ thống AI học tập tối ưu. Mỗi bước đều có ví dụ cụ thể và checklist để đảm bảo thành công.

---

## 📋 Phần 1: Chuẩn Bị Dữ Liệu Chất Lượng

### 🗂️ Loại Dữ Liệu Cần Thiết

#### 1.1 Thông Tin Chiến Dịch (Campaign Data)

**Dữ liệu bắt buộc:**
- **Tên chiến dịch**: Tên mô tả rõ ràng, dễ nhận biết
- **Ngày bắt đầu**: Ngày bắt đầu thực hiện chiến dịch
- **Ngày kết thúc**: Ngày kết thúc đo lường kết quả
- **Mô tả chiến dịch**: Nội dung, mục tiêu, đối tượng

**Ví dụ tốt:**
```
Tên: "Ra mắt ứng dụng EduTech cho học sinh THPT - Q3/2025"
Bắt đầu: 2025-03-01
Kết thúc: 2025-03-31
Mô tả: "Giới thiệu ứng dụng học tập EduTech mới, 
       tập trung vào học sinh THPT, 
       tính năng AI cá nhân hóa học tập"
```

**Ví dụ không tốt:**
```
Tên: "Campaign ABC"
Mô tả: "Quảng cáo sản phẩm"
```

#### 1.2 Kết Quả Báo Chí (Media Results)

**Cho mỗi báo chí được liên hệ:**

| Trường Dữ Liệu | Bắt Buộc | Ví Dụ | Ghi Chú |
|----------------|----------|-------|---------|
| **Tên báo** | ✅ | \"VnExpress\", \"Tuoi Tre\" | Tên chính xác |
| **Đã đăng bài** | ✅ | True/False | Có đăng hay không |
| **Loại bài** | ✅ | \"Tin tức\", \"Phỏng vấn\" | Từ dropdown |
| **Ngày đăng** | ✅ | 2025-03-15 | Định dạng YYYY-MM-DD |
| **URL bài viết** | ⚠️ | https://vnexpress.net/... | Nếu có |
| **Lượt xem** | ⚠️ | 25000 | Số nguyên |
| **Tương tác** | ⚠️ | 150 | Like + Comment + Share |

**✅ Checklist chất lượng dữ liệu báo chí:**
- [ ] Tên báo chính xác (không viết tắt)
- [ ] Ngày đăng phải nằm trong khoảng thời gian chiến dịch
- [ ] URL có thể truy cập được (nếu cung cấp)
- [ ] Số liệu lượt xem, tương tác hợp lý (không quá phóng đại)

#### 1.3 Chỉ Số Kinh Doanh (Business Metrics)

**Dữ liệu quan trọng:**

| Chỉ Số | Đơn Vị | Ví Dụ | Cách Tính |
|--------|--------|-------|-----------|
| **Doanh thu** | VNĐ | 500,000,000 | Doanh thu trực tiếp từ chiến dịch |
| **Chi phí** | VNĐ | 50,000,000 | Tổng chi phí (media + production) |
| **Khách hàng mới** | Người | 1,250 | Khách hàng mới trong thời gian chiến dịch |
| **Tỷ lệ chuyển đổi** | % | 3.5 | (Khách mua / Người xem) × 100 |

**🎯 Tips tính toán chính xác:**
- **Doanh thu**: Chỉ tính doanh thu có thể attribute được từ media
- **Chi phí**: Bao gồm cả chi phí PR, content creation, media buying
- **Attribution window**: Thường 7-30 ngày sau khi báo đăng
- **Conversion tracking**: Sử dụng UTM codes hoặc promo codes riêng

### 🔍 Phần 2: Quy Trình Chuẩn Bị Dữ Liệu

#### 2.1 Trước Chiến Dịch (Pre-Campaign)

**Setup tracking:**
```
1. Tạo tracking links riêng cho mỗi báo chí
   VD: https://yoursite.com?utm_source=vnexpress&utm_campaign=edutech_q3
   
2. Setup promo codes riêng biệt
   VD: VNEXPRESS10, TUOITRE15
   
3. Chuẩn bị spreadsheet tracking
   Columns: Media_Name | Contact_Date | Response | Publish_Date | URL | Views | Conversions
```

**📋 Checklist pre-campaign:**
- [ ] Tracking system đã setup
- [ ] Attribution method đã định nghĩa
- [ ] Measurement window đã quyết định (7/14/30 ngày)
- [ ] Team đã hiểu cách collect data

#### 2.2 Trong Chiến Dịch (During Campaign)

**Daily monitoring:**
- Kiểm tra các báo đã đăng bài
- Record URL và basic metrics
- Monitor social media mentions
- Track website traffic từ media

**📊 Template tracking hàng ngày:**
```
Date: 2025-03-15
New Publications:
- VnExpress: Published, URL: [link], Early views: 5,000
- Tuoi Tre: Response received, waiting for publication
- Thanh Nien: No response yet

Traffic Impact:
- Website visitors: +120% vs yesterday
- Promo code usage: 15 redemptions
```

#### 2.3 Sau Chiến Dịch (Post-Campaign)

**Final data collection (7-30 ngày sau):**
- Final view counts từ các báo
- Complete conversion data
- Customer lifetime value (nếu có)
- Brand awareness metrics (nếu đo được)

**📈 Data validation checklist:**
- [ ] Tất cả báo đã đăng đều có data đầy đủ
- [ ] Conversion attribution đã kiểm tra chéo
- [ ] Outliers đã được investigate
- [ ] ROI calculations đã double-check

---

## 🖥️ Phần 3: Hướng Dẫn Sử Dụng Dashboard Chi Tiết

### 📊 Dashboard 1: Enterprise Data Upload (Port 8501)

#### Tab 1: \"📝 Tải Lên Chiến Dịch Đơn\"

**Bước 1: Thông Tin Chiến Dịch**

```
📋 Campaign Information Section:
┌─────────────────────────────────────────┐
│ Campaign Name: [                      ] │
│ Start Date:    [📅 DD/MM/YYYY         ] │ 
│ End Date:      [📅 DD/MM/YYYY         ] │
│ Description:   [                      ] │
│                [                      ] │
│                [                      ] │
└─────────────────────────────────────────┘
```

**🎯 Best practices:**
- **Campaign Name**: Sử dụng format nhất quán
  ```
  Good: "Product Launch - EduTech App - Q3 2025"
  Bad:  "campaign 1"
  ```
- **Dates**: Chọn chính xác thời gian đo lường
- **Description**: Bao gồm context quan trọng cho AI

**Bước 2: Media Results Input**

```
📰 Media Results Section:
┌─────────────────────────────────────────┐
│ Media Name:    [VnExpress             ] │
│ Published:     [☑ Yes] [☐ No]          │
│ Article Type:  [News Article ▼        ] │
│ Publish Date:  [📅 DD/MM/YYYY         ] │
│ Article URL:   [https://...           ] │
│ Views:         [25000                 ] │
│ Interactions:  [150                   ] │
│                                         │
│ [+ Add Another Media] [🗑 Remove]      │
└─────────────────────────────────────────┘
```

**📝 Cách điền từng trường:**

1. **Media Name**: 
   - Tìm trong dropdown list
   - Nếu không có, liên hệ admin để thêm

2. **Published**: 
   - ✅ Yes: Báo đã đăng bài
   - ❌ No: Báo từ chối hoặc không phản hồi

3. **Article Type**: Chọn từ dropdown
   ```
   - News Article (Tin tức thường)
   - Interview (Phỏng vấn) 
   - Feature Story (Bài viết chuyên sâu)
   - Press Release (Thông cáo báo chí)
   - Opinion Piece (Bài bình luận)
   - Product Review (Đánh giá sản phẩm)
   ```

4. **Publish Date**: 
   - Ngày báo thực sự đăng bài
   - Format: DD/MM/YYYY

5. **Article URL**:
   - Copy full URL từ browser
   - Đảm bảo link còn hoạt động

6. **Views & Interactions**:
   - Views: Số lượt xem/đọc bài viết
   - Interactions: Tổng like + comment + share

**Bước 3: Business Metrics**

```
💼 Business Impact Section:
┌─────────────────────────────────────────┐
│ Revenue (VNĐ):     [500,000,000      ] │
│ Cost (VNĐ):        [50,000,000       ] │
│ New Customers:     [1,250             ] │
│ Conversion Rate:   [3.5               ] │
│                                         │
│ Notes:             [Attribution       ] │
│                    [method used...    ] │
└─────────────────────────────────────────┘
```

**💡 Tips nhập business metrics:**
- **Revenue**: Chỉ tính phần có thể attribute trực tiếp
- **Cost**: Bao gồm tất cả chi phí liên quan
- **Conversion Rate**: Nhập dạng số thập phân (3.5 thay vì 3.5%)
- **Notes**: Ghi rõ phương pháp tính toán

**Bước 4: Submit & Validation**

```
✅ Validation Results:
┌─────────────────────────────────────────┐
│ ✓ Campaign dates valid                  │
│ ✓ All required fields completed         │
│ ✓ Business metrics reasonable           │
│ ⚠ Warning: URL for VnExpress not      │
│   accessible (will retry later)        │
│                                         │
│ [📤 Upload Data] [📋 Save Draft]       │
└─────────────────────────────────────────┘
```

#### Tab 2: \"📁 Tải Lên Hàng Loạt (CSV)\"

**Chuẩn bị file CSV:**

**Template CSV structure:**
```csv
campaign_name,start_date,end_date,description,media_name,published,article_type,publish_date,url,views,interactions,revenue,cost,new_customers,conversion_rate
EduTech Launch Q3,2025-03-01,2025-03-31,AI-powered learning app for high school students,VnExpress,true,News Article,2025-03-15,https://vnexpress.net/sample,25000,150,500000000,50000000,1250,3.5
EduTech Launch Q3,2025-03-01,2025-03-31,AI-powered learning app for high school students,Tuoi Tre,true,Interview,2025-03-16,https://tuoitre.vn/sample,18000,85,500000000,50000000,1250,3.5
```

**🔧 Tạo CSV bằng Excel:**

1. **Mở Excel, tạo headers:**
   ```
   A1: campaign_name
   B1: start_date  
   C1: end_date
   D1: description
   E1: media_name
   F1: published
   G1: article_type
   H1: publish_date
   I1: url
   J1: views
   K1: interactions
   L1: revenue
   M1: cost
   N1: new_customers
   O1: conversion_rate
   ```

2. **Điền dữ liệu:**
   - Mỗi row = 1 media outlet cho 1 campaign
   - Dates format: YYYY-MM-DD
   - Published: true/false (không phải Yes/No)
   - Numbers: Không có dấu phẩy (50000000 chứ không phải 50,000,000)

3. **Save as CSV:**
   - File → Save As → CSV (Comma delimited)
   - Đặt tên: company_campaign_date.csv

**📤 Upload process:**

```
📁 Bulk Upload Section:
┌─────────────────────────────────────────┐
│ Select CSV File:                        │
│ [📎 Choose File] [campaign_data.csv ✓] │
│                                         │
│ File Preview (first 5 rows):           │
│ ┌─────────────────────────────────────┐ │
│ │campaign_name │media_name│published │ │
│ │EduTech Q3   │VnExpress │true     │ │
│ │EduTech Q3   │Tuoi Tre  │true     │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ Validation Status:                      │
│ ✓ 25 rows valid                        │
│ ⚠ 2 warnings (see below)              │
│ ❌ 0 errors                            │
│                                         │
│ [📤 Upload CSV Data]                   │
└─────────────────────────────────────────┘
```

#### Tab 3: \"📊 Phân Tích Dữ Liệu\"

**Overview Dashboard:**

```
📈 Data Analytics Overview:
┌─────────────────────────────────────────┐
│ Total Campaigns: 12                     │
│ Total Media Contacts: 156               │
│ Average Success Rate: 74%               │
│ Total Revenue Tracked: 2.5B VNĐ         │
└─────────────────────────────────────────┘

📊 Top Performing Media:
┌─────────────────────────────────────────┐
│ 1. VnExpress    - 89% success rate     │
│ 2. Tuoi Tre     - 78% success rate     │  
│ 3. Dantri       - 72% success rate     │
│ 4. Thanh Nien   - 65% success rate     │
│ 5. VietnamNet   - 61% success rate     │
└─────────────────────────────────────────┘

📋 Article Type Performance:
┌─────────────────────────────────────────┐
│ Interview       - 85% avg success      │
│ Feature Story   - 79% avg success      │
│ News Article    - 71% avg success      │
│ Press Release   - 58% avg success      │
└─────────────────────────────────────────┘
```

**🔍 Cách đọc insights:**
- **Success Rate**: % báo đồng ý đăng bài
- **Performance Trends**: Xu hướng theo thời gian
- **ROI Analysis**: Hiệu quả đầu tư cho từng báo

---

### 🔍 Dashboard 2: ML Monitoring (Port 8502)

#### Tab 1: \"🎯 Tổng Quan Hiệu Suất\"

```
🤖 AI Performance Overview:
┌─────────────────────────────────────────┐
│ Current Model Accuracy: 87.3%           │
│ ↗ +2.1% from last month               │
│                                         │
│ Predictions Made: 1,247                 │
│ Feedback Collected: 856                 │
│ Learning Data Quality: 94.2%            │
│                                         │
│ Last Model Update: 2 days ago           │
│ Next Scheduled Update: 5 days           │
└─────────────────────────────────────────┘

📊 Accuracy Trend (Last 30 days):
   100%│                                    
    90%│     ●●●●                          
    80%│ ●●●●    ●●●●●●●●●                 
    70%│                                   
       └────────────────────────────────→
       Jan 1    Jan 15    Jan 30
```

**🎯 Cách hiểu các chỉ số:**

1. **Model Accuracy**: 
   - 70-80%: Đang học, cần thêm data
   - 80-90%: Tốt, có thể tin tưởng
   - 90%+: Rất tốt, gần như chuyên gia

2. **Feedback Ratio**:
   - Predictions Made / Feedback Collected
   - Tỷ lệ cao = system học nhanh hơn

3. **Data Quality Score**:
   - Đánh giá chất lượng data được input
   - <80%: Cần cải thiện data quality

#### Tab 2: \"🚀 Tiến Trình Huấn Luyện\"

```
🔄 Training Job Status:
┌─────────────────────────────────────────┐
│ Current Job: model_v2.3_incremental     │
│ Status: ✅ Completed                    │
│ Started: 2025-01-15 09:30               │
│ Duration: 45 minutes                    │
│                                         │
│ Training Progress:                      │
│ ████████████████████████████ 100%      │
│                                         │
│ Metrics:                                │
│ • Training Accuracy: 91.2%             │
│ • Validation Accuracy: 87.3%           │
│ • Training Loss: 0.23                  │
│ • Validation Loss: 0.31                │
└─────────────────────────────────────────┘

📋 Training History:
┌─────────────────────────────────────────┐
│ v2.3 - Completed ✅ - Accuracy: 87.3%  │
│ v2.2 - Completed ✅ - Accuracy: 85.1%  │  
│ v2.1 - Failed ❌    - Data insufficient │
│ v2.0 - Completed ✅ - Accuracy: 82.8%  │
└─────────────────────────────────────────┘
```

**📊 Understanding training metrics:**
- **Training vs Validation Accuracy**: Không nên chênh lệch >5%
- **Loss values**: Càng thấp càng tốt
- **Training Duration**: Thường 30-60 phút cho incremental update

#### Tab 3: \"🎨 Tầm Quan Trọng Của Yếu Tố\"

```
🔍 Feature Importance Analysis:
┌─────────────────────────────────────────┐
│ What AI considers most important:       │
│                                         │
│ Content Relevance     ████████████ 28% │
│ Target Audience Match ████████     22% │
│ Media Outlet Category ██████       18% │
│ Timing Factors       █████        15% │
│ Company Industry     ████         12% │
│ Geographic Focus     ██           5%  │
│                                         │
│ 📈 Changes from last month:            │
│ • Content relevance ↗ +3%             │
│ • Timing factors ↗ +2%                │
│ • Audience match ↘ -1%                │
└─────────────────────────────────────────┘

🎯 Actionable Insights:
┌─────────────────────────────────────────┐
│ • Focus on content relevance in briefs │
│ • Timing is becoming more important     │
│ • Audience targeting remains critical   │
│ • Consider seasonal/trending topics     │
└─────────────────────────────────────────┘
```

**💡 Cách áp dụng insights:**
1. **Content Relevance cao**: Viết brief chi tiết hơn về nội dung
2. **Timing quan trọng**: Chú ý thời điểm gửi media
3. **Audience match**: Làm rõ target audience trong yêu cầu

---

## ⚠️ Phần 4: Troubleshooting & Quality Control

### 🔧 Xử Lý Lỗi Thường Gặp

#### Lỗi Upload Dữ Liệu

**Problem**: \"File upload failed\"
```
Possible causes:
1. File size > 50MB
2. Wrong CSV format  
3. Invalid characters in data
4. Network connection issue

Solutions:
✓ Split large files into smaller chunks
✓ Check CSV headers match template exactly
✓ Remove special characters (except comma)
✓ Try uploading again with stable connection
```

**Problem**: \"Data validation failed\"
```
Common validation errors:
1. Date format wrong (use YYYY-MM-DD)
2. Numbers with commas (use 50000 not 50,000)
3. Boolean values wrong (use true/false not yes/no)
4. Missing required fields

Solutions:
✓ Download and use official CSV template
✓ Double-check date formats
✓ Remove formatting from numbers
✓ Fill all required fields
```

#### Lỗi Dashboard Không Hoạt Động

**Problem**: \"Dashboard not loading\"
```
Check these steps:
1. Verify dashboard is running
   → Open terminal: python run_dashboards.py
   
2. Check correct ports
   → Data Upload: http://localhost:8501
   → ML Monitoring: http://localhost:8502
   
3. Clear browser cache
   → Ctrl+F5 or Ctrl+Shift+R
   
4. Try different browser
   → Chrome, Firefox, Edge
```

### 📊 Data Quality Checklist

#### Trước Khi Upload

**✅ Campaign Data Quality:**
- [ ] Campaign name descriptive và unique
- [ ] Start/end dates logical (end > start)
- [ ] Description contains enough context
- [ ] All campaigns have different names

**✅ Media Results Quality:**
- [ ] Media names match exactly with database
- [ ] Publish dates within campaign period
- [ ] URLs accessible and correct
- [ ] View/interaction numbers reasonable
- [ ] At least 3 media outlets per campaign

**✅ Business Metrics Quality:**
- [ ] Revenue and cost numbers realistic
- [ ] Conversion rates between 0-20%
- [ ] Attribution method documented
- [ ] Numbers consistent across campaigns

#### Sau Khi Upload

**✅ Verification Steps:**
- [ ] Check data appears correctly in analytics tab
- [ ] Verify calculations make sense
- [ ] Look for obvious outliers
- [ ] Cross-check with internal records

---

## 📈 Phần 5: Best Practices Cho Kết Quả Tốt Nhất

### 🎯 Data Collection Strategy

#### Phase 1: Foundation (Tháng 1-2)
**Mục tiêu**: Tạo foundation data cho AI

**Action items:**
```
Week 1-2: Setup tracking systems
- Implement UTM tracking
- Setup conversion tracking
- Train team on data collection

Week 3-4: Historical data upload
- Collect 20-30 past campaigns
- Focus on diverse industries/types
- Include both successes and failures

Week 5-8: Real-time data collection
- Upload new campaigns weekly
- Monitor data quality closely
- Adjust collection process based on learnings
```

#### Phase 2: Optimization (Tháng 3-4)
**Mục tiêu**: Improve data quality và AI performance

**Focus areas:**
- Increase data granularity
- Add more detailed business metrics
- Track longer-term customer value
- A/B test AI recommendations

#### Phase 3: Scaling (Tháng 5+)
**Mục tiêu**: Scale system và maximize ROI

**Advanced strategies:**
- Implement automated data pipelines
- Add predictive analytics
- Integrate with CRM systems
- Train team on advanced features

### 💡 Pro Tips for Success

#### Data Collection
1. **Consistency is key**: Sử dụng same format và process mỗi lần
2. **Quality over quantity**: 10 campaigns với data đầy đủ tốt hơn 50 campaigns thiếu data
3. **Track everything**: Bao gồm cả failed attempts và negative results
4. **Regular reviews**: Weekly data quality checks

#### Dashboard Usage
1. **Daily monitoring**: Check ML dashboard mỗi ngày cho alerts
2. **Weekly analysis**: Review performance trends và insights
3. **Monthly optimization**: Adjust strategy based on learnings
4. **Quarterly reviews**: Deep dive vào ROI và system improvements

#### Team Training
1. **Standard procedures**: Document và train team on data collection
2. **Quality control**: Assign người review data trước khi upload
3. **Feedback loop**: Regular meetings để discuss insights và improvements
4. **Continuous learning**: Stay updated with new features và best practices

---

## 📞 Support & Resources

### 🆘 When to Contact Support

**Technical Issues:**
- Dashboard không start sau 5 phút
- Data upload fails repeatedly
- AI performance suddenly drops >10%
- Missing features hoặc data

**Data Issues:**
- Không chắc về data format
- Cần custom fields cho industry
- Attribution method advice
- ROI calculation support

**Strategy Questions:**
- How to interpret AI insights
- Optimization recommendations
- Integration với existing systems
- Custom dashboard requirements

### 📚 Additional Resources

**Documentation:**
- RANKING_SYSTEM_THEORY.md - Lý thuyết và scientific foundation
- TECHNICAL_ARCHITECTURE.md - Technical details cho IT team
- ENTERPRISE_USER_GUIDE.md - Basic user guide

**Video Tutorials:**
- Dashboard walkthrough (coming soon)
- Data preparation best practices (coming soon)
- Advanced analytics features (coming soon)

---

*Tài liệu này được cập nhật thường xuyên dựa trên feedback từ users và improvements của system. Phiên bản hiện tại: v1.0 - January 2025*