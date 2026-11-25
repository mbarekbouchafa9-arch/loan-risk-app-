import streamlit as st
import pandas as pd
import numpy as np
from scipy.optimize import linprog

st.set_page_config(page_title="نظام إدارة المخاطر المصرفية", page_icon="🏦", layout="centered")

st.title("🏦 نظام التحسين وإدارة المخاطر الشاملة")
st.caption("جداول مستقلة لمخاطر الائتمان، السوق، السيولة، والبلد مع التحسين الرياضي")

main_tab1, main_tab2 = st.tabs(["📊 1. تحسين المحفظة (جداول مستقلة)", "🧮 2. حاسبة المخاطر لقرض فردي"])

# ==============================================================================
# التبويب الأول: تحسين المحفظة بجداول مستقلة لكل مخاطرة
# ==============================================================================
with main_tab1:
    with st.expander("⚙️ إعدادات السيولة وأوزان الأهداف", expanded=True):
        total_budget = st.number_input("إجمالي السيولة المتاحة (مليون):", min_value=10.0, value=100.0, step=10.0)
        col_w1, col_w2 = st.columns(2)
        with col_w1:
            w_return = st.slider("أهمية تعظيم العائد:", 1, 50, 10)
        with col_w2:
            w_risk = st.slider("أهمية تقليل المخاطر الكلية:", 1, 50, 25)

    st.subheader("📋 إدخال بيانات كل مخاطرة في جدول مستقل")
    r_tab1, r_tab2, r_tab3, r_tab4 = st.tabs([
        "1️⃣ مخاطر الائتمان",
        "2️⃣ مخاطر السوق",
        "3️⃣ مخاطر السيولة",
        "4️⃣ مخاطر البلد"
    ])

    # الجدول 1: الأساسي + مخاطر الائتمان
    with r_tab1:
        st.caption("أدخل الفائدة، حدود التمويل، ومخاطر الائتمان (PD × LGD) لكل فئة:")
        df_credit = st.data_editor(pd.DataFrame([
            {"الفئة": "قرض استهلاكي", "الفائدة %": 7.5, "مخاطر الائتمان %": 0.75, "الحد الأدنى": 0.0, "الحد الأقصى": 40.0},
            {"الفئة": "قرض عقاري", "الفائدة %": 6.5, "مخاطر الائتمان %": 0.25, "الحد الأدنى": 20.0, "الحد الأقصى": 60.0},
            {"الفئة": "مؤسسات (SME)", "الفائدة %": 10.0, "مخاطر الائتمان %": 2.70, "الحد الأدنى": 0.0, "الحد الأقصى": 50.0},
        ]), use_container_width=True, key="t_credit")

    # الجدول 2: مخاطر السوق مستقلة
    with r_tab2:
        st.caption("تقلب أسعار الفائدة والتضخم (Risque de marché):")
        df_market = st.data_editor(pd.DataFrame({
            "الفئة": df_credit["الفئة"],
            "مخاطر السوق %": [0.40, 0.80, 0.90]
        }), disabled=["الفئة"], use_container_width=True, key="t_market")

    # الجدول 3: مخاطر السيولة مستقلة
    with r_tab3:
        st.caption("صعوبة تسييل القرض وطول المدة (Risque de liquidité):")
        df_liquidity = st.data_editor(pd.DataFrame({
            "الفئة": df_credit["الفئة"],
            "مخاطر السيولة %": [0.50, 1.20, 0.60]
        }), disabled=["الفئة"], use_container_width=True, key="t_liquidity")

    # الجدول 4: مخاطر البلد مستقلة
    with r_tab4:
        st.caption("المخاطر الاقتصادية والتشريعية (Risque de pays):")
        df_country = st.data_editor(pd.DataFrame({
            "الفئة": df_credit["الفئة"],
            "مخاطر البلد %": [0.30, 0.30, 0.70]
        }), disabled=["الفئة"], use_container_width=True, key="t_country")

    # دمج المخاطر الأربعة حسابياً لتشغيل النموذج
    total_risk_pct_series = (
        df_credit["مخاطر الائتمان %"] +
        df_market["مخاطر السوق %"] +
        df_liquidity["مخاطر السيولة %"] +
        df_country["مخاطر البلد %"]
    )

    with st.expander("🎯 المستهدفات المالية للمحفظة", expanded=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            max_risk_lp = st.number_input("سقف المخاطر الكلية للخطية (م):", value=3.0, step=0.2)
        with c2:
            target_ret_gp = st.number_input("العائد المستهدف (م):", value=8.5, step=0.5)
        with c3:
            target_risk_gp = st.number_input("المخاطر الكلية المستهدفة (م):", value=2.5, step=0.2)

    if st.button("🚀 احسب التوزيع الأمثل الشامل", type="primary", use_container_width=True):
        n = len(df_credit)
        rates = df_credit["الفائدة %"].values / 100.0
        total_risks = total_risk_pct_series.values / 100.0
        bounds_base = [(df_credit["الحد الأدنى"].iloc[i], df_credit["الحد الأقصى"].iloc[i]) for i in range(n)]

        # 1. البرمجة الخطية (LP)
        res_lp = linprog(
            c=-rates,
            A_ub=[[1.0]*n, list(total_risks)],
            b_ub=[total_budget, max_risk_lp],
            bounds=bounds_base,
            method="highs"
        )

        # 2. البرمجة بالأهداف (GP)
        c_gp = [0.0]*n + [w_return, 0.0, 0.0, w_risk]
        A_eq_gp = [
            list(rates) + [1.0, -1.0, 0.0, 0.0],
            list(total_risks) + [0.0, 0.0, 1.0, -1.0]
        ]
        res_gp = linprog(
            c=c_gp,
            A_ub=[[1.0]*n + [0.0]*4],
            b_ub=[total_budget],
            A_eq=A_eq_gp,
            b_eq=[target_ret_gp, target_risk_gp],
            bounds=bounds_base + [(0, None)]*4,
            method="highs"
        )

        if res_lp.success and res_gp.success:
            alloc_lp = res_lp.x
            alloc_gp = res_gp.x[:n]

            st.divider()
            st.subheader("📈 توزيع السيولة المقترح")

            res_t1, res_t2 = st.tabs(["⚖️ البرمجة بالأهداف (المتوازن)", "💰 البرمجة الخطية (أعلى عائد)"])
            with res_t1:
                m1, m2 = st.columns(2)
                m1.metric("العائد المتوقع", f"{np.sum(alloc_gp * rates):.2f} م")
                m2.metric("المخاطر الكلية", f"{np.sum(alloc_gp * total_risks):.2f} م")
                st.bar_chart(pd.DataFrame({"المبلغ (مليون)": alloc_gp}, index=df_credit["الفئة"]))

            with res_t2:
                m3, m4 = st.columns(2)
                m3.metric("العائد الأقصى", f"{np.sum(alloc_lp * rates):.2f} م")
                m4.metric("المخاطر الكلية", f"{np.sum(alloc_lp * total_risks):.2f} م")
                st.bar_chart(pd.DataFrame({"المبلغ (مليون)": alloc_lp}, index=df_credit["الفئة"]))

            st.subheader("📑 جداول الخسائر المتوقعة لكل مخاطرة على حدة")

            # 4 جداول مستقلة للنتائج
            st.markdown("**1️⃣ جدول مخاطر الائتمان (Risque de crédit):**")
            st.dataframe(pd.DataFrame({
                "الفئة": df_credit["الفئة"],
                "النسبة %": df_credit["مخاطر الائتمان %"],
                "خسارة الخطية (م)": np.round(alloc_lp * (df_credit["مخاطر الائتمان %"]/100), 3),
                "خسارة الأهداف (م)": np.round(alloc_gp * (df_credit["مخاطر الائتمان %"]/100), 3),
            }), use_container_width=True)

            st.markdown("**2️⃣ جدول مخاطر السوق (Risque de marché):**")
            st.dataframe(pd.DataFrame({
                "الفئة": df_credit["الفئة"],
                "النسبة %": df_market["مخاطر السوق %"],
                "خسارة الخطية (م)": np.round(alloc_lp * (df_market["مخاطر السوق %"]/100), 3),
                "خسارة الأهداف (م)": np.round(alloc_gp * (df_market["مخاطر السوق %"]/100), 3),
            }), use_container_width=True)

            st.markdown("**3️⃣ جدول مخاطر السيولة (Risque de liquidité):**")
            st.dataframe(pd.DataFrame({
                "الفئة": df_credit["الفئة"],
                "النسبة %": df_liquidity["مخاطر السيولة %"],
                "خسارة الخطية (م)": np.round(alloc_lp * (df_liquidity["مخاطر السيولة %"]/100), 3),
                "خسارة الأهداف (م)": np.round(alloc_gp * (df_liquidity["مخاطر السيولة %"]/100), 3),
            }), use_container_width=True)

            st.markdown("**4️⃣ جدول مخاطر البلد (Risque de pays):**")
            st.dataframe(pd.DataFrame({
                "الفئة": df_credit["الفئة"],
                "النسبة %": df_country["مخاطر البلد %"],
                "خسارة الخطية (م)": np.round(alloc_lp * (df_country["مخاطر البلد %"]/100), 3),
                "خسارة الأهداف (م)": np.round(alloc_gp * (df_country["مخاطر البلد %"]/100), 3),
            }), use_container_width=True)
        else:
            st.error("⚠️ تعذر إيجاد حل! يرجى رفع سقف المخاطر الكلية المسموح به.")

# ==============================================================================
# التبويب الثاني: حاسبة المخاطر الفردية (كل مخاطرة بجدولها المستقل + المؤشر البصري)
# ==============================================================================
with main_tab2:
    st.subheader("🔍 تقييم قرض محدد")
    
    c_a, c_b = st.columns(2)
    with c_a:
        salary = st.number_input("الراتب الشهري (مليون):", min_value=1.0, value=7.4, step=0.1)
        loan_amount = st.number_input("مبلغ القرض EAD (مليون):", min_value=1.0, value=200.0, step=10.0)
        years = st.number_input("مدة القرض (سنوات):", min_value=1, max_value=30, value=10, step=1)
        interest_rate = st.number_input("معدل الفائدة (%):", min_value=0.0, value=7.5, step=0.5)
    with c_b:
        insurance_tax = st.number_input("التأمين والضرائب (مليون):", min_value=0.0, value=0.186, step=0.01, format="%.3f")
        lgd_ind = st.slider("نسبة الخسارة LGD (%):", 5, 100, 25)
        market_r = st.slider("مخاطر السوق (%):", 0.0, 5.0, 0.4, step=0.1)
        country_r = st.slider("مخاطر البلد (%):", 0.0, 5.0, 0.3, step=0.1)

    # الحسابات
    months = years * 12
    m_rate = (interest_rate / 100.0) / 12.0
    base_inst = loan_amount * (m_rate * (1 + m_rate)**months) / ((1 + m_rate)**months - 1) if m_rate > 0 else loan_amount / months
    total_inst = base_inst + insurance_tax
    dti = (total_inst / salary) * 100.0

    pd_est = 1.5 if dti <= 30 else (3.0 if dti <= 36 else (6.0 if dti <= 45 else 10.0))
    liquidity_r = round(years * 0.05, 2)

    credit_loss = loan_amount * (pd_est / 100.0) * (lgd_ind / 100.0)
    market_loss = loan_amount * (market_r / 100.0)
    liquidity_loss = loan_amount * (liquidity_r / 100.0)
    country_loss = loan_amount * (country_r / 100.0)
    total_el = credit_loss + market_loss + liquidity_loss + country_loss
    total_risk_pct = (total_el / loan_amount) * 100.0

    st.divider()

    # المؤشر البصري التفاعلي (أخضر / أصفر / أحمر)
    if dti <= 33.0 and total_risk_pct <= 2.0:
        st.markdown(
            f"""
            <div style="background-color:#d4edda; border-left:8px solid #28a745; padding:15px; border-radius:8px; color:#155724; direction:rtl;">
                <h3 style="margin:0;">🟢 مؤشر الأمان: منخفض المخاطر (مقبول فوراً)</h3>
