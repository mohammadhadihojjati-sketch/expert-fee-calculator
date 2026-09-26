import streamlit as st
import io
import os
import streamlit.components.v1 as components

# 1. Page Config
st.set_page_config(page_title="محاسبه دستمزد کارشناسی ۱۴۰۵", page_icon="📊", layout="centered")

# --- تزریق کدهای CSS پیشرفته برای موبایل و زرد کردن کادر ورودی ---
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
    
    /* زرد کردن قطعی کادر ورودی عدد حسابداری */
    div[data-testid="stTextInput"] input {
        direction: LTR !important;
        text-align: center !important;
        font-size: 20px !important;
        font-weight: bold !important;
        border-radius: 12px !important;
        border: 2px solid #f1c40f !important;
        background-color: #fef9e7 !important;
        color: #2c3e50 !important;
        padding: 14px !important;
    }
    
    /* استایل کادرهای مالی خروجی نتایج (به صورت ستونی و زیر هم) */
    .result-card {
        background-color: #ffffff !important;
        border-right: 6px solid #1f4e78 !important;
        border-radius: 10px !important;
        padding: 18px !important;
        margin: 15px 0 !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.06) !important;
        display: block !important; /* تضمین نمایش کادرها در حالت وب */
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
    
    /* کادر تفکیک مبالغ پردازش شده */
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
    
    /* 🖨️ تنظیمات اختصاصی زمان پرینت (مخفی کردن بخش‌های اضافی فقط روی برگه کاغذ) */
    @media print {
        div[data-testid="stTextInput"], .processed-amount, iframe, header, footer, [data-testid="stHeader"] {
            display: none !important;
        }
        .result-card {
            box-shadow: none !important;
            border: 1px solid #ccc !important;
            margin: 10px 0 !important;
            background-color: white !important;
        }
    }
    </style>
""", unsafe_allow_html=True)

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

# 4. Streamlit UI Layout
st.title("📊 محاسبه دستمزد کارشناسی ۱۴۰۵")
st.markdown("<p style='color: #6c757d; font-size: 14px;'>🔒 محیط کاملاً محلی و ایمن مالی | تنظیم‌کننده: <b>محمد هادی حجتی</b></p>", unsafe_allow_html=True)
st.write("---")

b20_str = st.text_input("مقدار ورودی مبنا را به ریال وارد کنید (اعداد را بدون فاصله وارد کنید):", value="0")

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
    
    # کادرهای مالی شکیل به صورت ردیف‌های ستونی زیر هم (کاملاً اصلاح‌شده برای نمایش قطعی در وب)
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
    
    st.write("---")
    
    # دکمه سبز رنگ پرینت مستقیم (سازگار با وب و موبایل)
    print_button_html = """
    <style>
    .native-print-btn {
        width: 100%;
        background-color: #2e5b18;
        color: white;
        text-align: center;
        padding: 14px;
        font-size: 18px;
        font-weight: bold;
        border-radius: 10px;
        border: none;
        cursor: pointer;
        box-shadow: 0 4px 10px rgba(46, 91, 24, 0.2);
    }
    .native-print-btn:hover {
        background-color: #234713;
    }
    </style>
    <button class="native-print-btn" onclick="parent.window.print()">🖨️ پرینت مستقیم گزارش رسمی</button>
    """
    components.html(print_button_html, height=60)
else:
    st.write("💡 *لطفاً مبلغ مورد نظر خود را در کادر زرد رنگ فوق وارد کنید تا محاسبات بلافاصله انجام شود.*")
