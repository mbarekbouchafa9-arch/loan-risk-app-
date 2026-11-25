import streamlit as st
import pandas as pd
import numpy as np
from scipy.optimize import linprog

st.set_page_config(page_title="حاسبة المخاطر المصرفية المستقلة", page_icon="🏦", layout="centered")

st.title("🏦 نظام إدارة وتحسين القروض")

# قائمة تنقل رئيسية تفتح كل قسم في شاشة مستقلة تماماً
section = st.radio(
    "اختر القسم الذي تريد العمل عليه الآن:",
    [
        "1️⃣ مخاطر الائتمان (وحدها)",
        "2️⃣ مخاطر السوق (وحدها)",
        "3️⃣ مخاطر السيولة (وحدها)",
        "4️⃣ مخاطر البلد (وحدها)",
        "📊 تحسين محفظة البنك",
        "🧮 تقييم قرض فردي (المؤشر البصري)"
    ],
    horizontal=True
)

st.divider()

# ==============================================================================
# 1. شاشة مخاطر الائتمان وحدها فقط
# ==============================================================================
if section == "1️⃣ مخاطر الائتمان (وحدها)":
    st.header("1️⃣ حاسبة مخاطر الائتمان (Risque de crédit)")
    st.caption("هذه الشاشة مخصصة لحساب مخاطر الائتمان فقط بشكل مستقل.")

    loan_val = st.number_input("مبلغ القرض EAD (مليون):", min_value=1.0, value=200.0, step=10.0)
    pd_pct = st.number_input("احتمالية التعثر PD (%):", min_value=0.0, value=3.0, step=0.5)
    lgd_pct = st.number_input("نسبة الخسارة عند التعثر LGD (%):", min_value=0.0, max_value=100.0, value=25.0, step=5.0)

    ratio_credit = (pd_pct * lgd_pct) / 100.0
    loss_credit = loan_val * (ratio_credit / 100.0)

    st.divider()
    c1, c2 = st.columns(2)
    c1.metric("نسبة مخاطر الائتمان", f"{ratio_credit:.2f}%")
    c2.metric("قيمة الخسارة المتوقعة", f"{loss_credit:.2f} مليون")

# ==============================================================================
# 2. شاشة مخاطر السوق وحدها فقط
# ==============================================================================
elif section == "2️⃣ مخاطر السوق (وحدها)":
    st.header("2️⃣ حاسبة مخاطر السوق (Risque de marché)")
    st.caption("هذه الشاشة مخصصة لحساب مخاطر تقلب الفائدة والتضخم فقط.")

    loan_val = st.number_input("مبلغ القرض (مليون):", min_value=1.0, value=200.0, step=10.0)
    duration = st.number_input("المدة المعدلة للقرض (سنوات):", min_value=0.1, value=4.0, step=0.5)
    delta_r = st.number_input("التغير المتوقع في سعر الفائدة (%):", min_value=0.0, value=0.10, step=0.05)

    ratio_market = duration * delta_r
    loss_market = loan_val * (ratio_market / 100.0)

    st.divider()
    c1, c2 = st.columns(2)
    c1.metric("نسبة مخاطر السوق", f"{ratio_market:.2f}%")
    c2.metric("قيمة الخسارة المتوقعة", f"{loss_market:.2f} مليون")

# ==============================================================================
# 3. شاشة مخاطر السيولة وحدها فقط
# ==============================================================================
elif section == "3️⃣ مخاطر السيولة (وحدها)":
    st.header("3️⃣ حاسبة مخاطر السيولة (Risque de liquidité)")
    st.caption("هذه الشاشة مخصصة لحساب مخاطر تجميد السيولة حسب مدة القرض فقط.")

    loan_val = st.number_input("مبلغ القرض (مليون):", min_value=1.0, value=200.0, step=10.0)
    duree_ans = st.number_input("مدة القرض (سنوات):", min_value=1, value=10, step=1)
    cout_liq = st.number_input("معامل تكلفة السيولة السنوي (%):", min_value=0.0, value=0.05, step=0.01)

    ratio_liq = duree_ans * cout_liq
    loss_liq = loan_val * (ratio_liq / 100.0)

    st.divider()
    c1, c2 = st.columns(2)
    c1.metric("نسبة مخاطر السيولة", f"{ratio_liq:.2f}%")
    c2.metric("قيمة الخسارة المتوقعة", f"{loss_liq:.2f} مليون")

# ==============================================================================
# 4. شاشة مخاطر البلد وحدها فقط
# ==============================================================================
elif section == "4️⃣ مخاطر البلد (وحدها)":
    st.header("4️⃣ حاسبة مخاطر البلد (Risque de pays)")
    st.caption("هذه الشاشة مخصصة لحساب المخاطر الاقتصادية والتشريعية للدولة فقط.")

    loan_val = st.number_input("مبلغ القرض (مليون):", min_value=1.0, value=200.0, step=10.0)
    prime_pays = st.number_input("علاوة مخاطر الدولة CRP (%):", min_value=0.0, value=3.0, step=0.5)
    sensibilite = st.number_input("معامل حساسية القطاع (0.1 إلى 1.0):", min_value=0.05, max_value=1.0, value=0.10, step=0.05)

    ratio_pays = prime_pays * sensibilite
    loss_pays = loan_val * (ratio_pays / 100.0)

    st.divider()
    c1, c2 = st.columns(2)
    c1.metric("نسبة مخاطر البلد", f"{ratio_pays:.2f}%")
    c2.metric("قيمة الخسارة المتوقعة", f"{loss_pays:.2f} مليون")

# ==============================================================================
# 5. شاشة تحسين محفظة البنك
# ==============================================================================
elif section == "📊 تحسين محفظة البنك":
    st.header("📊 تحسين توزيع محفظة القروض")
    total_budget = st.number_input("إجمالي السيولة المتاحة (مليون):", min_value=10.0, value=100.0, step=10.0)
    col_w1, col_w2 = st.columns(2)
    with col_w1:
        w_return = st.slider("أهمية تعظيم العائد:", 1, 50, 10)
    with col_w2:
        w_risk = st.slider("أهمية تقليل المخاطر الكلية:", 1, 50, 25)

    df_loans = st.data_editor(pd.DataFrame([
        {"الفئة": "قرض استهلاكي", "الفائدة %": 7.5, "ائتمان %": 0.75, "سوق %": 0.40, "سيولة %": 0.50, "بلد %": 0.30, "الحد الأدنى": 0.0, "الحد الأقصى": 40.0},
        {"الفئة": "قرض عقاري", "الفائدة %": 6.5, "ائتمان %": 0.25, "سوق %": 0.80, "سيولة %": 1.20, "بلد %": 0.30, "الحد الأدنى": 20.0, "الحد الأقصى": 60.0},
        {"الفئة": "مؤسسات (SME)", "الفائدة %": 10.0, "ائتمان %": 2.70, "سوق %": 0.90, "سيولة %": 0.60, "بلد %": 0.70, "الحد الأدنى": 0.0, "الحد الأقصى": 50.0},
    ]), use_container_width=True)

    total_risks = (df_loans["ائتمان %"] + df_loans["سوق %"] + df_loans["سيولة %"] + df_loans["بلد %"]).values / 100.0
    c1, c2, c3 = st.columns(3)
    with c1:
        max_risk_lp = st.number_input("سقف المخاطر (خطية):", value=3.0, step=0.2)
    with c2:
        target_ret_gp = st.number_input("العائد المستهدف:", value=8.5, step=0.5)
    with c3:
        target_risk_gp = st.number_input("المخاطر المستهدفة:", value=2.5, step=0.2)

    if st.button("🚀 احسب التوزيع الأمثل", type="primary", use_container_width=True):
        n = len(df_loans)
        rates = df_loans["الفائدة %"].values / 100.0
        bounds_base = [(df_loans["الحد الأدنى"].iloc[i], df_loans["الحد الأقصى"].iloc[i]) for i in range(n)]

        res_lp = linprog(c=-rates, A_ub=[[1.0]*n, list(total_risks)], b_ub=[total_budget, max_risk_lp], bounds=bounds_base, method="highs")
        c_gp = [0.0]*n + [w_return, 0.0, 0.0, w_risk]
        A_eq_gp = [list(rates) + [1.0, -1.0, 0.0, 0.0], list(total_risks) + [0.0, 0.0, 1.0, -1.0]]
        res_gp = linprog(c=c_gp, A_ub=[[1.0]*n + [0.0]*4], b_ub=[total_budget], A_eq=A_eq_gp, b_eq=[target_ret_gp, target_risk_gp], bounds=bounds_base + [(0, None)]*4, method="highs")

        if res_lp.success and res_gp.success:
            st.success("تم الحساب بنجاح!")
            st.dataframe(pd.DataFrame({
                "الفئة": df_loans["الفئة"],
                "البرمجة الخطية (م)": np.round(res_lp.x, 2),
                "البرمجة بالأهداف (م)": np.round(res_gp.x[:n], 2)
            }), use_container_width=True)
        else:
            st.error("⚠️ تعذر إيجاد حل ضمن هذه القيود.")

# ==============================================================================
# 6. شاشة تقييم قرض فردي مع المؤشر البصري
# ==============================================================================
elif section == "🧮 تقييم قرض فردي (المؤشر البصري)":
    st.header("🧮 تقييم شامل لقرض فردي")
    c_a, c_b = st.columns(2)
    with c_a:
        salary = st.number_input("الراتب الشهري (مليون):", min_value=1.0, value=7.4, step=0.1)
        loan_amount = st.number_input("مبلغ القرض (مليون):", min_value=1.0, value=200.0, step=10.0)
        years = st.number_input("مدة القرض (سنوات):", min_value=1, max_value=30, value=10, step=1)
        interest_rate = st.number_input("معدل الفائدة (%):", min_value=0.0, value=7.5, step=0.5)
    with c_b:
        insurance_tax = st.number_input("التأمين والضرائب (مليون):", min_value=0.0, value=0.186, step=0.01, format="%.3f")
        lgd_ind = st.slider("نسبة الخسارة LGD (%):", 5, 100, 25)
        market_r = st.slider("مخاطر السوق (%):", 0.0, 5.0, 0.4, step=0.1)
        country_r = st.slider("مخاطر البلد (%):", 0.0, 5.0, 0.3, step=0.1)

    months = years * 12
    m_rate = (interest_rate / 100.0) / 12.0
    base_inst = loan_amount * (m_rate * (1 + m_rate)**months) / ((1 + m_rate)**months - 1) if m_rate > 0 else loan_amount / months
    total_inst = base_inst + insurance_tax
    dti = (total_inst / salary) * 100.0

    pd_est = 1.5 if dti <= 30 else (3.0 if dti <= 36 else (6.0 if dti <= 45 else 10.0))
    liquidity_r = round(years * 0.05, 2)
    total_el = loan_amount * (((pd_est * lgd_ind)/100.0 + market_r + liquidity_r + country_r) / 100.0)
    total_risk_pct = (total_el / loan_amount) * 100.0

    st.divider()
    if dti <= 33.0 and total_risk_pct <= 2.0:
        st.markdown(f"""<div style="background-color:#d4edda; border-left:8px solid #28a745; padding:15px; border-radius:8px; color:#155724; direction:rtl;"><h3 style="margin:0;">🟢 مؤشر الأمان: منخفض المخاطر (مقبول فوراً)</h3><p style="margin:5px 0 0 0;">نسبة الاقتطاع ({dti:.1f}%) مثالية، وإجمالي المخاطر ({total_risk_pct:.2f}%) في المنطقة الآمنة.</p></div>""", unsafe_allow_html=True)
    elif dti <= 38.0 and total_risk_pct <= 4.0:
        st.markdown(f"""<div style="background-color:#fff3cd; border-left:8px solid #ffc107; padding:15px; border-radius:8px; color:#856404; direction:rtl;"><h3 style="margin:0;">🟡 مؤشر الأمان: مخاطر متوسطة (مقبول بضمانات)</h3><p style="margin:5px 0 0 0;">نسبة الاقتطاع ({dti:.1f}%) تقترب من السقف البنكي، يُنصح بالقبول مع توطين الراتب والتأمين.</p></div>""", unsafe_allow_html=True)
    else:
