import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="دایرةالمعارف توابع اکسل",
    layout="wide"
)

st.markdown("""
<style>
    [data-testid="stAppViewContainer"], [data-testid="stSidebar"] { direction: rtl; }
    div[data-baseweb="select"] { direction: rtl; }
    h1 { text-align: center; }

    /* ظرف جدول */
    .table-wrapper {
        direction: rtl;
        overflow-x: auto;
        overflow-y: auto;
        max-height: 650px;
        border: 1px solid #ddd;
        border-radius: 8px;
    }
    .table-wrapper table {
        width: 100%;
        min-width: 100%;
        table-layout: auto;
        border-collapse: collapse;
    }
    .table-wrapper th {
        text-align: center;
        background-color: #f0f2f6;
        color: #111;
        padding: 10px;
        border-bottom: 2px solid #ccc;
        position: sticky;
        top: 0;
        z-index: 1;
        white-space: nowrap;
    }
    .table-wrapper td {
        text-align: center;
        padding: 8px;
        border-bottom: 1px solid #eee;
        vertical-align: middle;
        word-break: break-word;
        overflow-wrap: anywhere;
        font-size: 14px;
    }

    /* ستون‌های انگلیسی/فرمولی (فرمت و مثال): جهت LTR */
    .table-wrapper td:nth-child(5),
    .table-wrapper td:nth-child(7) {
        direction: ltr;
        font-family: Consolas, monospace;
        font-size: 13px;
    }

    /* ستون‌های باریک: ردیف و دسته‌بندی */
    .table-wrapper th:nth-child(1),
    .table-wrapper td:nth-child(1) { width: 50px; }
    .table-wrapper th:nth-child(3),
    .table-wrapper td:nth-child(3) { width: 90px; }
</style>
""", unsafe_allow_html=True)

# ستونی که جستجو فقط در آن انجام می‌شود
NAME_COL = "نام تابع"

# ترتیب ستون‌ها از راست به چپ (نام‌ها را مطابق فایل خودتان تغییر دهید)
# 1=ردیف، 2=نام تابع، 3=دسته بندی، 4=توضیحات، 5=فرمت، 6=ورودی‌ها، 7=مثال
ORDER_RTL = ["ردیف", "نام تابع", "دسته بندی", "توضیحات", "فرمت", "ورودی‌ها", "مثال"]


def normalize(text: str) -> str:
    """یکسان‌سازی ی/ک عربی و فارسی، نیم‌فاصله و حروف بزرگ و کوچک"""
    return (
        str(text)
        .replace("ي", "ی")
        .replace("ك", "ک")
        .replace("\u200c", " ")
        .strip()
        .lower()
    )


@st.cache_data
def load_data():
    df = pd.read_excel("database.xlsx")
    df.columns = [str(col).strip() for col in df.columns]

    # یکسان‌سازی نام ستون «دسته بندی»
    rename_dict = {
        col: "دسته بندی"
        for col in df.columns
        if normalize(col) in ("دسته بندی", "دسته  بندی", "category")
    }
    df.rename(columns=rename_dict, inplace=True)

    # حذف ستون «ردیف» قدیمی در صورت وجود
    if "ردیف" in df.columns:
        df = df.drop(columns=["ردیف"])

    # ستون جستجو: فقط از ستون «نام تابع» ساخته می‌شود
    if NAME_COL in df.columns:
        df["_search"] = df[NAME_COL].fillna("").map(normalize)
    else:
        df["_search"] = ""

    return df


def main():
    st.title("📚 دایرةالمعارف توابع اکسل")

    try:
        df = load_data()
    except FileNotFoundError:
        st.error("فایل database.xlsx پیدا نشد. آن را کنار فایل برنامه قرار دهید.")
        return
    except Exception as e:
        st.error(f"خطا در خواندن فایل: {e}")
        return

    if NAME_COL not in df.columns:
        st.error(f"ستون «{NAME_COL}» در فایل اکسل پیدا نشد. جستجو کار نخواهد کرد.")

    st.sidebar.header("🔍 تنظیمات جستجو")

    if "دسته بندی" in df.columns:
        cat_col = "دسته بندی"
        categories = sorted(df[cat_col].dropna().astype(str).unique().tolist())
        selected_categories = st.sidebar.multiselect("انتخاب دسته‌بندی‌ها:", categories)
    else:
        cat_col = None
        selected_categories = []
        st.sidebar.info("ستون «دسته بندی» در فایل پیدا نشد.")

    search_query = st.sidebar.text_input("جستجو در نام توابع:")

    # --- منطق فیلتر ---
    filtered_df = df

    if cat_col and selected_categories:
        filtered_df = filtered_df[filtered_df[cat_col].astype(str).isin(selected_categories)]

    if search_query.strip():
        q = normalize(search_query)
        filtered_df = filtered_df[
            filtered_df["_search"].str.contains(q, regex=False, na=False)
        ]

    # حذف ستون کمکی و شماره‌گذاری مجدد
    filtered_df = filtered_df.drop(columns=["_search"]).reset_index(drop=True)
    filtered_df["ردیف"] = filtered_df.index + 1

    # --- ترتیب ستون‌ها (جدول HTML با direction: rtl است، پس برعکس نمی‌کنیم) ---
    ordered = [c for c in ORDER_RTL if c in filtered_df.columns]
    rest = [c for c in filtered_df.columns if c not in ordered]
    filtered_df = filtered_df[ordered + rest]

    st.write(f"تعداد توابع یافت‌شده: **{len(filtered_df)}**")

    if not filtered_df.empty:
        table_html = filtered_df.to_html(
            index=False,
            escape=True,
            na_rep="",
            border=0,
        )
        st.markdown(
            f'<div class="table-wrapper">{table_html}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.warning("موردی یافت نشد.")


if __name__ == "__main__":
    main()