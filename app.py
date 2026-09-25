import streamlit as st
import io
import os
import base64
from fpdf import FPDF

# 1. Page Config
st.set_page_config(page_title="داشبورد محاسبات دستمزد ۱۴۰۵", page_icon="📊", layout="centered")

# --- تزریق کدهای CSS برای زیباسازی پیشرفته محیط Streamlit ---
st.markdown("""
    <style>
    @import url('https://jsdelivr.net');
    
    /* اعمال فونت وزیر و راست‌چین کردن کل صفحه */
    html, body, [data-testid="stAppViewContainer"], .stApp {
        font-family: 'Vazirmatn', sans-serif !important;
        direction: RTL !important;
        text-align: right !important;
        background-color: #f8f9fa;
    }
    
    /* زیباسازی کادر ورودی متن */
    div[data-testid="stTextInput"] input {
        direction: LTR !important;
        text-align: center !important;
        font-size: 18px !important;
        font-weight: bold !important;
        border-radius: 10px !important;
        border: 2px solid #dfe4ea !important;
        padding: 12px !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05) !important;
    }
    div[data-testid="stTextInput"] input:focus {
        border-color: #1f4e78 !important;
        box-shadow: 0 0 8px rgba(31, 78, 120, 0.2) !important;
    }
    
    /* ساخت کادرهای سایه‌دار مالی (Cards) برای نمایش نتایج */
    .result-card {
        background-color: #ffffff;
        border-right: 5px solid #1f4e78;
        border-radius: 8px;
        padding: 20px;
        margin: 15px 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
    }
    .result-card.total {
        border-right: 5px solid #2e5b18;
        background-color: #f4faf0;
    }
    .card-title {
        font-size: 14px;
        color: #6c757d;
        margin-bottom: 5px;
    }
    .card-value {
        font-size: 24px;
        font-weight: bold;
        color: #212529;
    }
    
    /* زیباسازی متون راهنما */
    label, p, span, h1 {
        font-family: 'Vazirmatn', sans-serif !important;
    }
    </style>
""", unsafe_allow_html=True)

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
                {"upper": 500_000_000,         "rate": 0,          "base": 20_000_000,    "lower": 0, "name": "پله ۱ (زیر ۵۰۰ میلیون ریال)"},
                {"upper": 1_000_000_000,       "rate": 0.0045,     "base": 20_000_000,    "lower": 500_000_000, "name": "پله ۲ (۵۰۰ میلیون تا ۱ میلیارد ریال)"},
                {"upper": 5_000_000_000,       "rate": 0.0040,     "base": 22_250_000,    "lower": 1_000_000_000, "name": "پله ۳ (۱ تا ۵ میلیارد ریال)"},
                {"upper": 30_000_000_000,      "rate": 0.0020,     "base": 38_250_000,    "lower": 5_000_000_000, "name": "پله ۴ (۵ تا ۳۰ میلیارد ریال)"},
                {"upper": 150_000_000_000,     "rate": 0.0012,     "base": 88_250_000,    "lower": 30_000_000_000, "name": "پله ۵ (۳۰ تا ۱۵۰ میلیارد ریال)"},
                {"upper": 500_000_000_000,     "rate": 0.0009,     "base": 232_250_000,   "lower": 150_000_000_000, "name": "پله ۶ (۱۵۰ تا ۵۰۰ میلیارد ریال)"},
                {"upper": 1_000_000_000_000,   "rate": 0.00031,    "base": 547_250_000,   "lower": 500_000_000_000, "name": "پله ۷ (۵۰۰ میلیارد تا ۱ تریلیون ریال)"},
                {"upper": 2_000_000_000_000,   "rate": 0.00023,    "base": 702_250_000,   "lower": 1_000_000_000_000, "name": "پله ۸ (۱ تا ۲ تریلیون ریال)"},
                {"upper": 4_000_000_000_000,   "rate": 0.000185,   "base": 932_250_000,   "lower": 2_000_000_000_000, "name": "پله ۹ (۲ تا ۴ تریلیون ریال)"},
                {"upper": 4_318_333_330_000,   "rate": 0.00015,    "base": 1_302_250_000, "lower": 4_000_000_000_000, "name": "پله ۱۰ (۴ تا ۴.۳۱ تریلیون ریال)"},
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
st.title("📊 سیستم هوشمند محاسبه دستمزد حسابرسی")
st.markdown("<p style='color: #6c757d; font-size: 14px;'>🔒 محیط کاملاً محلی و ایمن مالی | تنظیم‌کننده: <b>محمد هادی حجتی</b></p>", unsafe_allow_html=True)
st.write("---")

# کادر متنی تمیز و مرتب
b20_str = st.text_input("مقدار ورودی مبنا (B20) را به ریال وارد کنید:", value="1,000,000,000")

b20_input = 0.0
if b20_str:
    clean_str = b20_str.replace(",", "").replace(" ", "")
    if clean_str.isdigit():
        b20_input = float(clean_str)

if b20_input > 0:
    results = calculate_all_values(b20_input)
    
    # نمایش بازه به صورت شکیل
    st.info(f"🔍 **محدوده شناسایی‌شده:** {results['tier']}")
    
    # ساخت ستون‌ها با طراحی اختصاصی کادرهای مالی (Card Layout)
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
            <div class="result-card">
                <div class="card-title">دستمزد پایه (ماده ۱۱)</div>
                <div class="card-value">{results['c20']:,.0f} <span style="font-size:14px; font-weight:normal;">ریال</span></div>
            </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown(f"""
            <div class="result-card">
                <div class="card-title">افزایش حسابرسی (۵۰٪ ماده ۲۵)</div>
                <div class="card-value" style="color: #b33939;">{results['c21']:,.0f} <span style="font-size:14px; font-weight:normal;">ریال</span></div>
            </div>
        """, unsafe_allow_html=True)
        
    # کادر مجزا برای جمع کل نهایی
    st.markdown(f"""
        <div class="result-card total">
            <div class="card-title" style="color: #2e5b18; font-weight: bold;">◄ جمع کل حق‌الزحمه قابل پرداخت (C22)</div>
            <div class="card-value" style="color: #2e5b18; font-size: 30px;">{results['c22']:,.0f} <span style="font-size:16px; font-weight:normal;">ریال</span></div>
        </div>
    """, unsafe_allow_html=True)
    
    st.write("")
    
    try:
        pdf_data = generate_pdf_report(b20_input, results)
        
        # دکمه اصلی دانلود
        st.download_button(
            label="📥 دانلود مستقیم فایل PDF گزارش رسمی",
            data=pdf_data,
            file_name="financial_report.pdf",
            mime="application/pdf",
            use_container_width=True
        )
        
        # لینک کمکی موبایل
        b64 = base64.b64encode(pdf_data).decode()
        href = f'<a href="data:application/pdf;base64,{b64}" download="financial_report.pdf" style="display: inline-block; padding: 12px; color: white; background-color: #1f4e78; text-decoration: none; border-radius: 8px; font-weight: bold; text-align: center; margin-top: 10px; width: 100%;">🔗 لینک کمکی دانلود PDF (مخصوص مرورگر گوشی و آیفون)</a>'
        st.markdown(href, unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"خطا در تولید فایل PDF: {e}")