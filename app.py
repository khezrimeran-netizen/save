import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime
import threading

# تنظیم صفحه
st.set_page_config(
    layout="wide", 
    page_title="سیستم مقایسه محصولات",
    page_icon="🔄"
)

# ذخیره اطلاعات
if 'df' not in st.session_state:
    st.session_state.df = None
if 'results' not in st.session_state:
    st.session_state.results = []
if 'notes_data' not in st.session_state:
    st.session_state.notes_data = {}
if 'current_row' not in st.session_state:
    st.session_state.current_row = 0
if 'file_uploaded' not in st.session_state:
    st.session_state.file_uploaded = False
if 'user_name' not in st.session_state:
    st.session_state.user_name = ""
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

# تنظیمات
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbxKqWYYGLqDj6NgMxpUKrLrNvqVNandjoZ3ON4i3vnjmcfwh3ExLMV_pFJiu4iaCn06EQ/exec"

# اطلاعات کاربران
USERS = {
    "ali": "1234",
    "maryam": "1234", 
    "reza": "1234",
    "sara": "1234"
}

def create_new_sheet_for_user(user):
    """ایجاد تب جدید برای کاربر در گوگل شیت"""
    try:
        data = {
            'user': user,
            'row': 1,
            'result': 'NEW_SHEET',
            'notes': 'Sheet created automatically',
            'link1': 'https://www.digikala.com/',
            'link2': 'https://www.digikala.com/'
        }
        response = requests.post(WEB_APP_URL, json=data, timeout=10)
        if response.status_code == 200:
            result_data = response.json()
            return result_data.get('status') == 'success'
        return False
    except Exception as e:
        print(f"❌ Error creating sheet: {e}")
        return False

def save_to_sheets_async(user, row_num, result, notes, link1, link2):
    """ذخیره غیرهمزمان در گوگل شیت"""
    def send_data():
        try:
            data = {
                'user': user,
                'row': row_num,
                'result': result,
                'notes': notes,
                'link1': link1,
                'link2': link2
            }
            response = requests.post(WEB_APP_URL, json=data, timeout=10)
            if response.status_code == 200:
                result_data = response.json()
                if result_data.get('status') == 'success':
                    print(f"✅ Saved: User={user}, Row={row_num}, Result={result}")
                else:
                    print(f"❌ Save failed: {result_data.get('message')}")
            else:
                print(f"❌ HTTP Error: {response.status_code}")
        except Exception as e:
            print(f"❌ Save error: {e}")
    
    thread = threading.Thread(target=send_data)
    thread.daemon = True
    thread.start()

def load_user_data_from_sheets(user):
    """بارگذاری داده‌های کاربر از گوگل شیت"""
    try:
        print(f"🔍 Loading data for user: {user}")
        response = requests.get(f"{WEB_APP_URL}?user={user}", timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            print(f"📡 API Response status: {result.get('status')}")
            
            if result.get('status') == 'success' and result.get('data'):
                headers = result.get('headers', [])
                data_rows = result['data']
                
                print(f"🏷️ Headers: {headers}")
                print(f"📋 Data rows received: {len(data_rows)}")
                
                # ایجاد DataFrame
                df = pd.DataFrame(data_rows, columns=headers)
                print(f"🎯 DataFrame created: {len(df)} rows")
                
                if len(df) > 0:
                    # آماده‌سازی نتایج و یادداشت‌ها
                    results = []
                    notes_data = {}
                    
                    for idx in range(len(df)):
                        row_data = df.iloc[idx]
                        
                        # خواندن Result
                        result_val = None
                        if len(headers) > 5:  # ستون Result
                            result_cell = row_data[headers[5]]
                            if pd.notna(result_cell) and str(result_cell).strip() not in ['', 'nan', 'None']:
                                result_val = str(result_cell).strip()
                        
                        # خواندن Notes
                        note_val = ""
                        if len(headers) > 6:  # ستون Notes
                            note_cell = row_data[headers[6]]
                            if pd.notna(note_cell) and str(note_cell).strip() not in ['', 'nan', 'None']:
                                note_val = str(note_cell).strip()
                        
                        results.append(result_val)
                        notes_data[idx] = note_val
                    
                    print(f"✅ Final - Rows: {len(df)}, Results: {len(results)}, Notes: {len(notes_data)}")
                    return df, results, notes_data
            
            elif result.get('status') == 'no_data':
                print("ℹ️ No data found in sheet")
                return pd.DataFrame(), [], {}
        
        print("⚠️ Using empty data")
        return pd.DataFrame(), [], {}
        
    except Exception as e:
        print(f"❌ Load error: {e}")
        return pd.DataFrame(), [], {}

def jump_to_row(row_number):
    """پرش به ردیف خاص"""
    try:
        row_num = int(row_number) - 1
        if 0 <= row_num < len(st.session_state.df):
            st.session_state.current_row = row_num
            st.rerun()
        else:
            st.error(f"❌ ردیف {row_number} معتبر نیست")
    except ValueError:
        st.error("❌ لطفاً عدد وارد کنید")

# استایل‌ها
st.markdown("""
<style>
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    .stButton>button {
        border-radius: 8px;
        font-weight: bold;
        height: 2.8em;
        margin: 0.1rem;
    }
    iframe {
        border: 1px solid #ddd;
        border-radius: 10px;
        width: 100%;
        height: 600px;
    }
    .status-success {
        padding: 8px;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        color: #155724;
        margin: 5px 0;
    }
    .status-error {
        padding: 8px;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 5px;
        color: #721c24;
        margin: 5px 0;
    }
    .status-warning {
        padding: 8px;
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 5px;
        color: #856404;
        margin: 5px 0;
    }
    .header-container {
        display: flex;
        align-items: center;
        gap: 15px;
        margin-bottom: 1rem;
    }
    .digikala-logo {
        width: 40px;
        height: 40px;
    }
</style>
""", unsafe_allow_html=True)

# هدر با لوگوی واقعی دیجی کالا
col_logo, col_title = st.columns([0.1, 0.9])
with col_logo:
    st.image("https://www.digikala.com/statics/img/png/footerlogo2.webp", width=40)
with col_title:
    st.markdown("<h1 style='color: #A62626; margin:0;'>سیستم مقایسه محصولات</h1>", unsafe_allow_html=True)

st.markdown("---")

# اگر کاربر لاگین نکرده
if not st.session_state.authenticated:
    st.header("👥 انتخاب کاربر")
    
    cols = st.columns(4)
    selected_user = None
    
    for i, (username, password) in enumerate(USERS.items()):
        with cols[i % 4]:
            if st.button(f"👤 {username}", key=f"user_{username}", use_container_width=True):
                selected_user = username
    
    if selected_user:
        st.session_state.selected_user = selected_user
        st.session_state.auth_step = "password"
        st.rerun()

# اگر کاربر انتخاب شده اما پسورد وارد نکرده
if hasattr(st.session_state, 'auth_step') and st.session_state.auth_step == "password":
    st.header(f"🔐 وارد کردن رمز برای {st.session_state.selected_user}")
    
    password = st.text_input("رمز عبور:", type="password", key="password_input")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("✅ تأیید رمز", type="primary", use_container_width=True):
            if password == USERS.get(st.session_state.selected_user, ""):
                st.session_state.user_name = st.session_state.selected_user
                st.session_state.authenticated = True
                st.session_state.auth_step = None
                
                with st.spinner("📥 در حال بارگذاری داده‌ها..."):
                    df, results, notes_data = load_user_data_from_sheets(st.session_state.user_name)
                    st.session_state.df = df
                    st.session_state.results = results
                    st.session_state.notes_data = notes_data
                    st.session_state.file_uploaded = len(df) > 0
                    st.session_state.current_row = 0
                st.rerun()
            else:
                st.error("❌ رمز عبور اشتباه است")
    
    with col2:
        if st.button("🔙 بازگشت", use_container_width=True):
            st.session_state.auth_step = None
            st.rerun()

# اگر کاربر لاگین کرده و داده دارد
elif st.session_state.authenticated and st.session_state.file_uploaded:
    df = st.session_state.df
    current_row = st.session_state.current_row
    results = st.session_state.results
    notes_data = st.session_state.notes_data
    
    if current_row >= len(df):
        st.session_state.current_row = 0
        current_row = 0
        st.rerun()
    
    row = df.iloc[current_row]
    link1 = str(row['Link1']).strip()
    link2 = str(row['Link2']).strip()
    
    # نوار کنترل فشرده - همه در یک ردیف
    st.header(f"👤 {st.session_state.user_name} - ردیف {current_row + 1} از {len(df)}")
    
    # ردیف اول: کنترل‌های اصلی
    col1, col2, col3, col4, col5, col6, col7, col8, col9 = st.columns([0.8, 0.8, 1.2, 1.2, 2, 1, 1, 1, 1])
    
    with col1:
        if st.button("⏮", use_container_width=True, disabled=current_row == 0):
            st.session_state.current_row -= 1
            st.rerun()
    
    with col2:
        if st.button("⏭", use_container_width=True, disabled=current_row >= len(df) - 1):
            st.session_state.current_row += 1
            st.rerun()
    
    with col3:
        if st.button("✅ مشابه", type="primary", use_container_width=True):
            st.session_state.results[current_row] = 'Yes'
            save_to_sheets_async(
                st.session_state.user_name,
                current_row + 1,
                'Yes',
                notes_data.get(current_row, ''),
                link1,
                link2
            )
            if current_row < len(df) - 1:
                st.session_state.current_row += 1
            st.rerun()
    
    with col4:
        if st.button("❌ متفاوت", type="secondary", use_container_width=True):
            st.session_state.results[current_row] = 'No'
            save_to_sheets_async(
                st.session_state.user_name,
                current_row + 1,
                'No',
                notes_data.get(current_row, ''),
                link1,
                link2
            )
            if current_row < len(df) - 1:
                st.session_state.current_row += 1
            st.rerun()
    
    with col5:
        current_note = notes_data.get(current_row, "")
        new_note = st.text_input("", value=current_note, placeholder="یادداشت...", key=f"note_{current_row}", label_visibility="collapsed")
        if new_note != current_note:
            st.session_state.notes_data[current_row] = new_note
    
    with col6:
        if st.button("💾", use_container_width=True):
            if current_row in st.session_state.notes_data:
                save_to_sheets_async(
                    st.session_state.user_name,
                    current_row + 1,
                    st.session_state.results[current_row] or '',
                    st.session_state.notes_data[current_row],
                    link1,
                    link2
                )
                st.success("✅")
    
    with col7:
        jump_num = st.number_input("", min_value=1, max_value=len(df), value=current_row + 1, 
                                 key="jump_input", label_visibility="collapsed")
    
    with col8:
        if st.button("🎯", use_container_width=True):
            jump_to_row(jump_num)
    
    with col9:
        st.metric("", f"{current_row + 1}/{len(df)}")

    # وضعیت فعلی
    current_result = results[current_row] if current_row < len(results) else None
    if current_result == 'Yes':
        st.markdown('<div class="status-success">✅ <b>مشابه</b></div>', unsafe_allow_html=True)
    elif current_result == 'No':
        st.markdown('<div class="status-error">❌ <b>متفاوت</b></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-warning">⏳ <b>تصمیم گرفته نشده</b></div>', unsafe_allow_html=True)
    
    # نمایش محصولات
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🛒 محصول اول")
        if link1.startswith('http'):
            st.components.v1.iframe(link1, height=600, scrolling=True)
        else:
            st.error("❌ لینک معتبر نیست")
    
    with col2:
        st.subheader("🛒 محصول دوم")
        if link2.startswith('http'):
            st.components.v1.iframe(link2, height=600, scrolling=True)
        else:
            st.error("❌ لینک معتبر نیست")
    
    # پیشرفت
    completed = len([r for r in results if r is not None])
    total = len(results)
    progress = completed / total if total > 0 else 0
    
    st.progress(progress)
    st.write(f"**پیشرفت: {completed} از {total} ردیف ({progress:.0%})**")

# اگر کاربر لاگین کرده اما داده‌ای ندارد
elif st.session_state.authenticated and not st.session_state.file_uploaded:
    st.warning("⚠️ هیچ داده‌ای برای این کاربر پیدا نشد")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("🔄 بارگذاری مجدد داده‌ها", use_container_width=True):
            with st.spinner("📥 در حال بارگذاری داده‌ها..."):
                df, results, notes_data = load_user_data_from_sheets(st.session_state.user_name)
                st.session_state.df = df
                st.session_state.results = results
                st.session_state.notes_data = notes_data
                st.session_state.file_uploaded = len(df) > 0
                st.rerun()
    
    with col2:
        if st.button("➕ ایجاد تب جدید", type="primary", use_container_width=True):
            with st.spinner("🔄 در حال ایجاد تب جدید..."):
                if create_new_sheet_for_user(st.session_state.user_name):
                    st.success("✅ تب جدید با موفقیت ایجاد شد!")
                    # حالا داده‌ها رو بارگذاری کن
                    df, results, notes_data = load_user_data_from_sheets(st.session_state.user_name)
                    st.session_state.df = df
                    st.session_state.results = results
                    st.session_state.notes_data = notes_data
                    st.session_state.file_uploaded = len(df) > 0
                    st.rerun()
                else:
                    st.error("❌ خطا در ایجاد تب جدید")

# سایدبار
with st.sidebar:
    st.header("👤 اطلاعات کاربر")
    if st.session_state.authenticated:
        st.success(f"**کاربر:** {st.session_state.user_name}")
        
        if st.session_state.file_uploaded:
            completed = len([r for r in st.session_state.results if r is not None])
            total = len(st.session_state.results)
            if total > 0:
                st.metric("تکمیل شده", f"{completed}/{total}")
                st.metric("پیشرفت", f"{completed/total*100:.0f}%")
                
                # نمایش خلاصه وضعیت
                st.markdown("---")
                st.subheader("📈 خلاصه وضعیت")
                yes_count = len([r for r in st.session_state.results if r == 'Yes'])
                no_count = len([r for r in st.session_state.results if r == 'No'])
                pending_count = total - completed
                
                col_s1, col_s2, col_s3 = st.columns(3)
                with col_s1:
                    st.metric("✅", yes_count)
                with col_s2:
                    st.metric("❌", no_count)
                with col_s3:
                    st.metric("⏳", pending_count)
        
        if st.button("🚪 خروج", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()