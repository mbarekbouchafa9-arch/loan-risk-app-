import streamlit as st
import pandas as pd
import numpy as np
import requests
from scipy.optimize import linprog

st.set_page_config(page_title="نظام إدارة المخاطر والعملات", page_icon="🏦", layout="centered")

st.title("🏦 نظام التحسين وإدارة المخاطر والعملات")
st.caption("منصة متكاملة لتحسين المحافظ، دراسة القروض، حساب المخاطر، وأسعار الصرف مقابل الدينار الجزائري")

# ==============================================================================
# التبويبات الأربعة الرئيسية
# ==============================================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 1. المحفظة",
    "🧮 2. القروض",
    "📐 3. المخاطر",
    "💱 4. العملات DZD"
])

# ==============================================================================
# التبويب الأول: تحسين محفظة البنك
# ==============================================================================
with tab1:
    st.subheader("📊 تحسين توزيع محفظة القروض")
    total_budget = st.number_input("إجمالي السيولة المتاحة (مليون):", min_value=10.0, value=100.0, step=10.0)
    col_w1, col_w2 = st.columns(2)
    with col_w1:
        w_return = st.slider("أهمية تعظيم العائد:", 1, 50, 10)
    with col_w2:
        w_risk = st.slider("أهمية تقليل المخاطر الكلية:", 1, 50, 25)

    df_loans = st.data_editor(pd.DataFrame([
        {"الفئة": "فردي استهلاكي", "الفائدة %": 7.5, "ائتمان %": 0.75, "سوق %": 0.40, "سيولة %": 0.54, "بلد %": 0.30, "الحد الأدنى": 0.0, "الحد الأقصى": 40.0},
        {"الفئة": "فردي برهن", "الفائدة %": 6.5, "ائتمان %": 0.25, "سوق %": 0.80, "سيولة %": 1.20, "بلد %": 0.30, "الحد الأدنى": 20.0, "الحد الأقصى": 60.0},
        {"الفئة": "مؤسسات استهلاكي", "الفائدة %": 10.0, "ائتمان %": 2.70, "سوق %": 0.90, "سيولة %": 0.60, "بلد %": 0.70, "الحد الأدنى": 0.0, "الحد الأقصى": 40.0},
        {"الفئة": "مؤسسات برهن", "الفائدة %": 8.5, "ائتمان %": 1.10, "سوق %": 0.70, "سيولة %": 0.90, "بلد %": 0.50, "الحد الأدنى": 10.0, "الحد الأقصى": 50.0},
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
# التبويب الثاني: دراسة أنواع القروض الأربعة + حساب أقصى قرض للزبون
# ==============================================================================
with tab2:
    st.subheader("🧮 دراسة القروض وحساب أقصى تمويل للزبون")

    loan_type = st.selectbox(
        "اختر نوع القرض المطلوب دراسته:",
        [
            "1️⃣ قرض فردي استهلاكي",
            "2️⃣ قرض فردي برهن (عقاري)",
            "3️⃣ قرض استهلاكي للمؤسسات (تشغيلي)",
            "4️⃣ قرض برهن للمؤسسات (استثماري)"
        ]
    )

    if loan_type == "1️⃣ قرض فردي استهلاكي":
        income_label = "الراتب الشهري للزبون (مليون):"
        def_income, def_rate, def_yrs, def_lgd, max_dti_limit = 7.4, 7.5, 10, 35, 33.0
    elif loan_type == "2️⃣ قرض فردي برهن (عقاري)":
        income_label = "الراتب الشهري للزبون (مليون):"
        def_income, def_rate, def_yrs, def_lgd, max_dti_limit = 10.0, 6.5, 15, 15, 35.0
    elif loan_type == "3️⃣ قرض استهلاكي للمؤسسات (تشغيلي)":
        income_label = "صافي التدفق النقدي الشهري للمؤسسة (مليون):"
        def_income, def_rate, def_yrs, def_lgd, max_dti_limit = 50.0, 10.0, 5, 45, 40.0
    else:
        income_label = "صافي التدفق النقدي الشهري للمؤسسة (مليون):"
        def_income, def_rate, def_yrs, def_lgd, max_dti_limit = 80.0, 8.5, 12, 20, 45.0

    st.divider()

    with st.expander("💰 أولاً: احسب أقصى مبلغ قرض يمكن منحه للزبون", expanded=True):
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            client_income = st.number_input(income_label, min_value=1.0, value=def_income, step=0.5, key="cap_inc")
            cap_years = st.number_input("المدة المطلوبة (سنوات):", min_value=1, max_value=30, value=def_yrs, step=1, key="cap_yrs")
        with col_c2:
            cap_rate = st.number_input("معدل الفائدة السنوي (%):", min_value=0.1, value=def_rate, step=0.5, key="cap_rate")
            allowed_dti = st.slider("نسبة الاقتطاع القصوى المسموحة (%):", 20.0, 60.0, max_dti_limit, step=1.0, key="cap_dti")

        max_monthly_payment = client_income * (allowed_dti / 100.0)
        cap_months = cap_years * 12
        cap_m_rate = (cap_rate / 100.0) / 12.0

        if cap_m_rate > 0:
            max_loan_eligible = max_monthly_payment * (1 - (1 + cap_m_rate)**(-cap_months)) / cap_m_rate
        else:
            max_loan_eligible = max_monthly_payment * cap_months

        st.success(f"**أقصى قرض يمكن منحه:** **{max_loan_eligible:.2f} مليون** (بقسط شهري أقصى قدره **{max_monthly_payment:.2f} مليون**)")

    st.subheader(f"🔍 ثانياً: تقييم مخاطر ({loan_type})")
    c_a, c_b = st.columns(2)
    with c_a:
        loan_amount = st.number_input("مبلغ القرض المطلوب فعلياً (مليون):", min_value=1.0, value=round(float(max_loan_eligible), 1), step=10.0)
        insurance_tax = st.number_input("التأمين والضرائب الشهرية (مليون):", min_value=0.0, value=0.186, step=0.01, format="%.3f")
    with c_b:
        lgd_ind = st.slider("نسبة الخسارة عند التعثر LGD (%):", 5, 100, def_lgd)
        market_r = st.slider("مخاطر السوق (%):", 0.0, 5.0, 0.4, step=0.1)
        country_r = st.slider("مخاطر البلد (%):", 0.0, 5.0, 0.3, step=0.1)

    base_inst = loan_amount * (cap_m_rate * (1 + cap_m_rate)**cap_months) / ((1 + cap_m_rate)**cap_months - 1) if cap_m_rate > 0 else loan_amount / cap_months
    total_inst = base_inst + insurance_tax
    dti = (total_inst / client_income) * 100.0

    is_corporate = "للمؤسسات" in loan_type
    if not is_corporate:
        pd_est = 1.5 if dti <= 30 else (3.0 if dti <= 36 else (6.0 if dti <= 45 else 10.0))
    else:
        pd_est = 2.5 if dti <= 35 else (5.0 if dti <= 45 else (8.5 if dti <= 55 else 13.0))

    liquidity_r = round(cap_years * 0.054, 2)
    total_el = loan_amount * (((pd_est * lgd_ind)/100.0 + market_r + liquidity_r + country_r) / 100.0)
    total_risk_pct = (total_el / loan_amount) * 100.0

    st.divider()
    if dti <= allowed_dti and total_risk_pct <= 2.5:
        st.markdown(f"""<div style="background-color:#d4edda; border-left:8px solid #28a745; padding:15px; border-radius:8px; color:#155724; direction:rtl;"><h3 style="margin:0;">🟢 مؤشر الأمان: مقبول فوراً ({loan_type})</h3><p style="margin:5px 0 0 0;">القرض المطلوب ({loan_amount} م) ضمن القدرة الائتمانية للزبون، والمخاطر الكلية ({total_risk_pct:.2f}%) منخفضة.</p></div>""", unsafe_allow_html=True)
    elif dti <= (allowed_dti + 5.0) and total_risk_pct <= 4.5:
        st.markdown(f"""<div style="background-color:#fff3cd; border-left:8px solid #ffc107; padding:15px; border-radius:8px; color:#856404; direction:rtl;"><h3 style="margin:0;">🟡 مؤشر الأمان: مقبول بضمانات إضافية</h3><p style="margin:5px 0 0 0;">نسبة الاقتطاع ({dti:.1f}%) تقترب من السقف الأقصى ({allowed_dti}%)، يُنصح بتعزيز الضمانات أو التأمين.</p></div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"""<div style="background-color:#f8d7da; border-left:8px solid #dc3545; padding:15px; border-radius:8px; color:#721c24; direction:rtl;"><h3 style="margin:0;">🔴 مؤشر الأمان: مرفوض (يتجاوز قدرة الزبون)</h3><p style="margin:5px 0 0 0;">المبلغ المطلوب يتجاوز الحد الأقصى المسموح به ({max_loan_eligible:.2f} مليون) أو المخاطر ({total_risk_pct:.2f}%) مرتفعة جداً.</p></div>""", unsafe_allow_html=True)

    st.write("")
    r1, r2, r3 = st.columns(3)
    r1.metric("القسط الشهري الفعلي", f"{total_inst:.2f} م")
    r2.metric("نسبة الاقتطاع (DTI)", f"{dti:.1f}%")
    r3.metric("الخسارة المتوقعة (EL)", f"{total_el:.2f} م")

# ==============================================================================
# التبويب الثالث: حاسبة المخاطر المطوّرة
# ==============================================================================
with tab3:
    st.subheader("📐 استخراج نسب المخاطر من المعطيات الأولية")
    
    risk_choice = st.selectbox(
        "اختر المخاطرة لحساب معاملها ونسبتها تلقائياً:",
        [
            "1️⃣ مخاطر الائتمان (من نسبة الضمانات)",
            "2️⃣ مخاطر السوق (من المدة وتغير الفائدة)",
            "3️⃣ مخاطر السيولة (من فائدة القرض وإعادة التمويل)",
            "4️⃣ مخاطر البلد (من عوائد السندات وحساسية القطاع)"
        ]
    )

    st.divider()

    if risk_choice == "1️⃣ مخاطر الائتمان (من نسبة الضمانات)":
        st.markdown("### 1️⃣ مخاطر الائتمان (Risque de crédit)")
        pd_val = st.number_input("احتمالية التعثر PD (%):", min_value=0.0, value=3.0, step=0.5)
