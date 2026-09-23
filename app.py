import streamlit as st
import io
import os
import base64
from fpdf import FPDF

# 1. Page Config
st.set_page_config(page_title="Financial Tiered Calculator", page_icon="📊", layout="centered")

# --- پیدا کردن هوشمند آدرس دسکتاپ در ویندوز یا سرور ---
desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
FONT_PATH = os.path.join(desktop_path, "Vazirmatn-Regular.ttf")

if not os.path.exists(FONT_PATH):
    FONT_PATH = "Vazirmatn-Regular.ttf"

# 2. Main Logic Function
def calculate_all_values(b20: float) -> dict:
    c20 = 0
    tier_name = "خارج از محدوده محاسبات"
    
    if 0 < b20 <= 50_000_000_000_000:
        if b20 >= 50_000_000_000_000:
            c20 = 0
            tier_name = "بیشتر یا برابر ۵۰ تریلیون"
        elif 4_318_333_330_000 < b20 < 50_000_000_000_000:
            c20 = 1_350_000_000
            tier_name = "سقف ثابت بازه آخر"
        else:
            brackets = [
                {"upper": 500_000_000,         "rate": 0,          "base": 20_000_000,    "lower": 0, "name": "پله یک - زیر پانصد میلیون"},
                {"upper": 1_000_000_000,       "rate": 0.0045,     "base": 20_000_000,    "lower": 500_000_000, "name": "پله دو - پانصد میلیون تا یک میلیارد"},
                {"upper": 5_000_000_000,       "rate": 0.0040,     "base": 22_250_000,    "lower": 1_000_000_000, "name": "پله سه - یک تا پنج میلیارد"},
                {"upper": 30_000_000_000,      "rate": 0.0020,     "base": 38_250_000,    "lower": 5_000_000_000, "name": "پله چهار - پنج تا سی میلیارد"},
                {"upper": 150_000_000_000,     "rate": 0.0012,     "base": 88_250_000,    "lower": 30_000_000_000, "name": "پله پنج - سی تا صد و پنجاه میلیارد"},
                {"upper": 500_000_000_000,     "rate": 0.0009,     "base": 232_250_000,   "lower": 150_000_000_000, "name": "پله شش - صد و پنجاه تا پانصد میلیارد"},
                {"upper": 1_000_000_000_000,   "rate": 0.00031,    "base": 547_250_000,   "lower": 500_000_000_000, "name": "پله هفت - پانصد میلیارد تا یک تریلیون"},
                {"upper": 2_000_000_000_000,   "rate": 0.00023,    "base": 702_250_000,   "lower": 1_000_000_000_000, "name": "پله هشت - یک تا دو تریلیون"},
                {"upper": 4_000_000_000_000,   "rate": 0.000185,   "base": 932_250_000,   "lower": 2_000_000_000_000, "name": "پله نه - دو تا چهار تریلیون"},
                {"upper": 4_318_333_330_000,   "rate": 0.00015,    "base": 1_302_250_000, "lower": 4_000_000_000_000, "name": "پله ده - چهار تا چهار ممیز سی و یک تریلیون"},
            ]
            for bracket in brackets:
                if b20 <= bracket["upper"]:
                    c20 = (b20 - bracket["lower"]) * bracket["rate"] + bracket["base"]
                    tier_name = bracket["name"]
                    break

    c21 = c20 * 0.50
    c22 = c20 + c21
    return {"c20": c20, "c21": c21, "c22": c22, "tier": tier_name}

# 3. PDF Generator Helper
def generate_pdf_report(b20, res):
    pdf = FPDF()
    pdf.add_page()
    
    if os.path.exists(FONT_PATH):
        pdf.add_font("Vazir", style="", fname=FONT_PATH)
        pdf.set_font("Vazir", size=13)
        pdf.set_text_shaping(use_shaping_engine=True, direction="rtl")
    else:
        pdf.set_font("Helvetica", size=12)
    
    pdf.set_text_color(31, 78, 120)
    pdf.cell(180, 10, txt="گزارش رسمی محاسبات مالی دستمزد", ln=True, align="R")
    pdf.ln(2)
    
    pdf.set_text_color(89, 89, 89)
    pdf.cell(180, 8, txt="تنظیم کننده: محمد هادی حجتی", ln=True, align="R")
    pdf.cell(180, 8, txt=f"بازه محاسباتی شناسایی شده: {res['tier']}", ln=True, align="R")
    pdf.ln(5)
    
    pdf.set_draw_color(31, 78, 120)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(8)
    
    pdf.set_text_color(38, 38, 38)
    pdf.cell(180, 10, txt=f"• مقدار ورودی مبنا (B20): {b20:,.0f} ریال", ln=True, align="R")
    pdf.cell(180, 10, txt=f"• دستمزد طبق ماده ۱۱ (C20): {res['c20']:,.0f} ریال", ln=True, align="R")
    pdf.cell(180, 10, txt=f"• مبنای ماده ۲۵ (C21): {res['c21']:,.0f} ریال (پنجاه درصد از ماده ۱۱)", ln=True, align="R")
    pdf.ln(5)
    
    pdf.set_draw_color(191, 191, 191)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(6)
    
    pdf.set_text_color(46, 91, 24)
    pdf.cell(180, 12, txt=f"◄ جمع کل دستمزد حسابرسی (C22): {res['c22']:,.0f} ریال", ln=True, align="R")
    
    pdf_output = pdf.output()
    return bytes(pdf_output)

# 4. Streamlit UI Layout
st.title("📊 داشبورد محاسبات پلکانی دستمزد")
st.caption("🔒 محیط کاملاً خصوصی و محلی | تنظیم‌کننده: *محمد هادی حجتی*")
st.write("---")

# باکس دریافت ورودی از کاربر
raw_b20 = st.text_input("مقدار ورودی مبنا (B20) را به ریال وارد کنید:", value="1,000,000,000")

# 🌟 هوشمندسازی: فرمت‌دهی خودکار و جدا کردن سه رقم سه رقم به محض تایپ کاربر
clean_str = raw_b20.replace(",", "").replace(" ", "")
b20_input = 0.0

if clean_str.isdigit():
    b20_input = float(clean_str)
    formatted_str = f"{int(b20_input):,}"
    # در صورتی که کاربر ویرگول‌ها را جا انداخته باشد، متن راهنما زیر باکس تغییر می‌کند
    st.info(f"💵 مبلغ پردازش شده سیستم: {formatted_str} ریال")

if b20_input > 0:
    results = calculate_all_values(b20_input)
    
    st.success(f"بازه شناسایی‌شده: {results['tier']}")
    col1, col2, col3 = st.columns(3)
    col1.metric("دستمزد ماده ۱۱ (C20)", f"{results['c20']:,.0f}")
    col2.metric("ماده ۲۵ (C21)", f"{results['c21']:,.0f}")
    col3.metric("جمع کل دستمزد (C22)", f"{results['c22']:,.0f}")
    
    try:
        pdf_data = generate_pdf_report(b20_input, results)
        
        # 🌟 متد دانلود انقلابی و ۱۰۰٪ سازگار با تمام نسخه‌های موبایل
        b64 = base64.b64encode(pdf_data).decode()
        
        # طراحی دکمه بومی HTML که قفل دانلود تمام مرورگرهای گوشی را می‌شکند
        mobile_download_btn = f'''
            <a href="data:application/pdf;base64,{b64}" download="financial_report.pdf" target="_blank" style="
                display: block;
                width: 100%;
                text-align: center;
                background-color: #ff4b4b;
                color: white;
                padding: 12px 20px;
                margin: 10px 0;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
                text-decoration: none;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            ">📥 پرینت و دانلود نهایی فایل PDF (ویژه گوشی و کامپیوتر)</a>
        '''
        st.markdown(mobile_download_btn, unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"خطا در تولید فایل PDF: {e}")
