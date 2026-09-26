import streamlit as st
import io
import os
import base64
from fpdf import FPDF

# 1. Page Config (عنوان رسمی در تب مرورگر)
st.set_page_config(page_title="محاسبه دستمزد کارشناسی ۱۴۰۵", page_icon="📊", layout="centered")

# --- تزریق کدهای CSS برای زرد کردن کادر و راست‌چین کردن کل اپلیکیشن ---
st.markdown("""
    <style>
    @import url('https://jsdelivr.net');
    
    /* اعمال فونت وزیر و راست‌چین کردن کامل اپلیکیشن */
    html, body, [data-testid="stAppViewContainer"], .stApp {
        font-family: 'Vazirmatn', sans-serif !important;
        direction: RTL !important;
        text-align: right !important;
        background-color: #f8f9fa !important;
    }
    
    /* زرد کردن قطعی کادر ورودی پایتون */
    div[data-testid="stTextInput"] input {
        direction: LTR !important;
        text-align: center !important;
        font-size: 20px !important;
        font-weight: bold !important;
        border-radius: 12px !important;
        border: 2px solid #f1c40f !important; /* حاشیه طلایی/زرد */
        background-color: #fef9e7 !important; /* پس‌زمینه زرد ملایم مالی */
        color: #2c3e50 !important;
        padding: 14px !important;
    }
    
    /* استایل کادرهای مالی خروجی نتایج (زیر هم) */
    .result-card {
        background-color: #ffffff !important;
        border-right: 6px solid #1f4e78 !important;
        border-radius: 10px !important;
        padding: 18px !important;
        margin: 15px 0 !important; /* فاصله عمودی مناسب برای چیدمان زیر هم */
        box-shadow: 0 4px 12px rgba(0,0,0,0.06) !important;
    }
    .result-card.surcharge {
        border-right: 6px solid #b33939 !important;
    }
    .result-card.total {
        border-right: 6px solid #2e5b18 !important;
        background-color: #f4faf0 !important;
    }
    .card-title {
        font-size: 14px !important;
        color: #6c757d !important;
        margin-bottom: 6px !important;
        font-weight: bold !important;
    }
    .card-value {
        font-size: 24px !important;
        font-weight: bold !important;
        color: #212529 !important;
    }
    
    /* نمایش بزرگ مبالغ پردازش شده بالای کادر */
    .processed-amount {
        background-color: #ebf5fb;
        border-left: 5px solid #2980b9;
        padding: 12px;
        border-radius: 8px;
        font-size: 18px;
        font-weight: bold;
        color: #1b4f72;
        margin-bottom: 15px;
        text-align: center;
        direction: LTR;
    }
    
    h1, h2, h3, p, span, label {
        font-family: 'Vazirmatn', sans-serif !important;
        text-align: right !important;
    }
    </style>
""", unsafe_allow_html=True)

# آدرس‌دهی فونت و لوگو برای سازگاری ابری
FONT_PATH = "Vazirmatn-Regular.ttf"
LOGO_PATH = "logo.png"

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
                {"upper": 30_000_000_000,      "rate": 0.0020,     "base": 38_250_000,    "lower": 5_000_000_000, "name": "پله ۴ (۵ تا سی میلیارد ریال)"},
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

    c20_val = c20
    c21_val = c20 * 0.50
    c22_val = c20 + c21_val
    return {"c20": c20_val, "c21": c21_val, "c22": c22_val, "tier": tier_name}

# 3. PDF Generator Helper (تولید فایل چاپی مجهز به لوگوی رسمی کانون)
def generate_pdf_report(b20, res):
    pdf = FPDF()
    pdf.add_page()
    
    # 🌟 قرار دادن هوشمند لوگو در بالای سمت چپ صفحه در صورت وجود فایل تصویر
    if os.path.exists(LOGO_PATH):
        pdf.image(LOGO_PATH, x=15, y=10, w=22) # عرض ۲۲ میلی‌متر استاندارد اداری
    
    if os.path.exists(FONT_PATH):
        pdf.add_font("Vazir", style="", fname=FONT_PATH)
        pdf.set_font("Vazir", size=13)
        pdf.set_text_shaping(use_shaping_engine=True, direction="rtl")
    else:
        pdf.set_font("Helvetica", size=12)
    
    # تیتر اصلی گزارش رسمی (راست‌چین)
    pdf.set_text_color(31, 78, 120)
    pdf.cell(180, 12, txt="گزارش رسمی محاسبات مالی دستمزد کارشناسی", ln=True, align="R")
    pdf.ln(2)
    
    pdf.set_text_color(89, 89, 89)
    pdf.cell(180, 8, txt="تنظیم کننده: محمد هادی حجتـی", ln=True, align="R")
    pdf.cell(180, 8, txt=f"محدوده محاسبه: {res['tier']}", ln=True, align="R")
    pdf.ln(5)
    
    # خط جداکننده افقی سرمه‌ای
    pdf.set_draw_color(31, 78, 120)
    pdf.line(15, pdf.get_y() + 5, 195, pdf.get_y() + 5)
    pdf.ln(12)
    
    # جزییات ارقام محاسباتی
    pdf.set_text_color(38, 38, 38)
    pdf.cell(180, 10, txt=f"• مقدار ورودی مبنا: {b20:,.0f} ریال", ln=True, align="R")
    pdf.cell(180, 10, txt=f"• دستمزد پایه (طبق تعرفه): {res['c20']:,.0f} ریال", ln=True, align="R")
    pdf.cell(180, 10, txt=f"• افزایش حسابرسی (پنجاه درصد): {res['c21']:,.0f} ریال", ln=True, align="R")
    pdf.ln(5)
    
    # خط جداکننده طوسی کم‌رنگ
    pdf.set_draw_color(191, 191, 191)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(6)
    
    # جمع کل نهایی به رنگ سبز تیره
    pdf.set_text_color(46, 91, 24)
    pdf.cell(180, 12, txt=f"◄ جمع کل حق‌الزحمه قابل پرداخت: {res['c22']:,.0f} ریال", ln=True, align="R")
    
    return bytes(pdf.output())

# 4. Streamlit UI Layout
st.title("📊 محاسبه دستمزد کارشناسی ۱۴۰۵")
st.markdown("<p style='color: #6c757d; font-size: 14px;'>🔒 محیط کاملاً محلی و ایمن مالی | تنظیم‌کننده: <b>محمد هادی حجتی</b></p>", unsafe_allow_html=True)
st.write("---")

initial_val = "1000000000"
b20_str = st.text_input("مقدار ورودی مبنا را به ریال وارد کنید (اعداد را بدون فاصله وارد کنید):", value=initial_val)

b20_input = 0.0
if b20_str:
    clean_str = b20_str.replace(",", "").replace(" ", "")
    if clean_str.isdigit():
        b20_input = float(clean_str)

if b20_input > 0:
    formatted_preview = f"{int(b20_input):,}"
    st.markdown(f'<div class="processed-amount">🔹 مبلغ پردازش شده: {formatted_preview} ریال</div>', unsafe_allow_html=True)

    results = calculate_all_values(b20_input)
    st.info(f"🔍 **محدوده شناسایی‌شده:** {results['tier']}")
    
    # چیدمان ستونی و زیر هم خروجی‌ها طبق آخرین درخواست شما
    st.markdown(f"""
        <div class="result-card">
            <div class="card-title">دستمزد پایه (طبق تعرفه)</div>
            <div class="card-value">{results['c20']:,.0f} <span style="font-size:14px; font-weight:normal;">ریال</span></div>
        </div>
    """, unsafe_allow_html=True)
        
    st.markdown(f"""
        <div class="result-card surcharge">
            <div class="card-title" style="color: #b33939;">افزایش ۵۰ درصدی (حسابرسی)</div>
            <div class="card-value" style="color: #b33939;">{results['c21']:,.0f} <span style="font-size:14px; font-weight:normal;">ریال</span></div>
        </div>
    """, unsafe_allow_html=True)
        
    st.markdown(f"""
        <div class="result-card total">
            <div class="card-title" style="color: #2e5b18; font-weight: bold;">◄ جمع کل حق‌الزحمه قابل پرداخت</div>
            <div class="card-value" style="color: #2e5b18; font-size: 30px;">{results['c22']:,.0f} <span style="font-size:16px; font-weight:normal;">ریال</span></div>
        </div>
    """, unsafe_allow_html=True)
    
    st.write("")
    try:
        pdf_data = generate_pdf_report(b20_input, results)
        st.download_button(label="📥 دانلود مستقیم فایل PDF گزارش رسمی", data=pdf_data, file_name="financial_report.pdf", mime="application/pdf", use_container_width=True)
        
        b64 = base64.b64encode(pdf_data).decode()
        href = f'<a href="data:application/pdf;base64,{b64}" download="financial_report.pdf" style="display: inline-block; padding: 12px; color: white; background-color: #1f4e78; text-decoration: none; border-radius: 8px; font-weight: bold; text-align: center; margin-top: 10px; width: 100%;">🔗 لینک کمکی دانلود PDF (مخصوص مرورگر گوشی)</a>'
        st.markdown(href, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"خطا در تولید فایل PDF: {e}")