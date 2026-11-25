import streamlit as st
import pandas as pd
import numpy as np
from scipy.optimize import linprog

st.set_page_config(page_title="نظام إدارة المخاطر المصرفية الشامل", page_icon="🏦", layout="centered")

st.title("🏦 نظام التحسين وإدارة المخاطر الشاملة")
st.caption("دمج مخاطر الائتمان، السوق، السيولة، والبلد في نماذج البرمجة الخطية وبالأهداف")

main_tab1, main_tab2 = st.tabs(["📊 1. تحسين المحفظة (4 مخاطر)", "🧮 2. حاسبة المخاطر الشاملة لقرض"])

# ==============================================================================
# التبويب الأول: تحسين المحفظة بدمج المخاطر الأربعة
# ==============================================================================
with main_tab1:
    with st.expander("⚙️ إعدادات السيولة وأوزان الأهداف", expanded=True):
        total_budget = st.number_input("إجمالي السيولة المتاحة (مليون):", min_value=10.0, value=100.0, step=10.0)
        col_w1, col_w2 = st.columns(2)
        with col_w1:
            w_return = st.slider("أهمية تعظيم العائد:", 1, 50, 10)
        with col_w2:
            w_risk = st.slider("أهمية تقليل المخاطر الكلية:", 1, 50, 25)

    st.subheader("📋 جدول القروض والمخاطر الأربعة (%)")
    default_loans = pd.DataFrame([
        {
            "الفئة": "قرض استهلاكي", "الفائدة %": 7.5,
            "ائتمان (PD×LGD)%": 0.75, "سوق %": 0.40, "سيولة %": 0.50, "بلد %": 0.30,
            "الحد الأدنى": 0.0, "الحد الأقصى": 40.0
        },
        {
            "الفئة": "قرض عقاري", "الفائدة %": 6.5,
            "ائتمان (PD×LGD)%": 0.25, "سوق %": 0.80, "سيولة %": 1.20, "بلد %": 0.30,
            "الحد الأدنى": 20.0, "الحد الأقصى": 60.0
        },
        {
            "الفئة": "مؤسسات (SME)", "الفائدة %": 10.0,
            "ائتمان (PD×LGD)%": 2.70, "سوق %": 0.90, "سيولة %": 0.60, "بلد %": 0.70,
            "الحد الأدنى": 0.0, "الحد الأقصى": 50.0
        },
    ])
    df_loans = st.data_editor(default_loans, num_rows="dynamic", use_container_width=True)

    df_loans["إجمالي المخاطرة %"] = (
        df_loans["ائتمان (PD×LGD)%"] +
        df_loans["سوق %"] +
        df_loans["سيولة %"] +
        df_loans["بلد %"]
    )
    st.dataframe(df_loans[["الفئة", "الفائدة %", "إجمالي المخاطرة %"]], use_container_width=True)

    with st.expander("🎯 المستهدفات المالية للمحفظة", expanded=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            max_risk_lp = st.number_input("سقف المخاطر الكلية للخطية (م):", value=3.0, step=0.2)
        with c2:
            target_ret_gp = st.number_input("العائد المستهدف (م):", value=8.5, step=0.5)
        with c3:
            target_risk_gp = st.number_input("المخاطر الكلية المستهدفة (م):", value=2.5, step=0.2)

    if st.button("🚀 احسب التوزيع الأمثل الشامل", type="primary", use_container_width=True):
        n = len(df_loans)
        rates = df_loans["الفائدة %"].values / 100.0
        total_risks = df_loans["إجمالي المخاطرة %"].values / 100.0
        bounds_base = [(df_loans["الحد الأدنى"].iloc[i], df_loans["الحد الأقصى"].iloc[i]) for i in range(n)]

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
            st.subheader("📈 النتائج بعد دمج المخاطر الأربعة")

            t1, t2 = st.tabs(["⚖️ البرمجة بالأهداف (المتوازن)", "💰 البرمجة الخطية (أعلى عائد)"])
            with t1:
                m1, m2 = st.columns(2)
                m1.metric("العائد المتوقع", f"{np.sum(alloc_gp * rates):.2f} م")
                m2.metric("المخاطر الكلية", f"{np.sum(alloc_gp * total_risks):.2f} م")
                st.bar_chart(pd.DataFrame({"المبلغ (مليون)": alloc_gp}, index=df_loans["الفئة"]))

            with t2:
                m3, m4 = st.columns(2)
                m3.metric("العائد الأقصى", f"{np.sum(alloc_lp * rates):.2f} م")
                m4.metric("المخاطر الكلية", f"{np.sum(alloc_lp * total_risks):.2f} م")
                st.bar_chart(pd.DataFrame({"المبلغ (مليون)": alloc_lp}, index=df_loans["الفئة"]))

            breakdown_df = pd.DataFrame({
                "نوع المخاطرة": ["مخاطر الائتمان", "مخاطر السوق", "مخاطر السيولة", "مخاطر البلد"],
                "بالبرمجة الخطية (م)": [
                    round(np.sum(alloc_lp * (df_loans["ائتمان (PD×LGD)%"]/100)), 3),
                    round(np.sum(alloc_lp * (df_loans["سوق %"]/100)), 3),
                    round(np.sum(alloc_lp * (df_loans["سيولة %"]/100)), 3),
                    round(np.sum(alloc_lp * (df_loans["بلد %"]/100)), 3),
                ],
                "بالبرمجة بالأهداف (م)": [
                    round(np.sum(alloc_gp * (df_loans["ائتمان (PD×LGD)%"]/100)), 3),
                    round(np.sum(alloc_gp * (df_loans["سوق %"]/100)), 3),
                    round(np.sum(alloc_gp * (df_loans["سيولة %"]/100)), 3),
                    round(np.sum(alloc_gp * (df_loans["بلد %"]/100)), 3),
                ]
            })
            st.write("**تفصيل الخسائر المتوقعة حسب نوع المخاطرة:**")
            st.dataframe(breakdown_df, use_container_width=True)
        else:
            st.error("⚠️ تعذر إيجاد حل! يرجى رفع سقف المخاطر الكلية المسموح به.")

# ==============================================================================
# التبويب الثاني: حاسبة المخاطر الشاملة لقرض فردي + المؤشر البصري
# ==============================================================================
with main_tab2:
    st.subheader("🔍 تقييم المخاطر الأربعة لقرض محدد")
    
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

    # حساب القسط ونسبة الاقتطاع
    months = years * 12
    m_rate = (interest_rate / 100.0) / 12.0
    base_inst = loan_amount * (m_rate * (1 + m_rate)**months) / ((1 + m_rate)**months - 1) if m_rate > 0 else loan_amount / months
    total_inst = base_inst + insurance_tax
    dti = (total_inst / salary) * 100.0

    # تقدير PD ومخاطر السيولة تلقائياً
    pd_est = 1.5 if dti <= 30 else (3.0 if dti <= 36 else (6.0 if dti <= 45 else 10.0))
    liquidity_r = round(years * 0.05, 2)

    credit_loss = loan_amount * (pd_est / 100.0) * (lgd_ind / 100.0)
    market_loss = loan_amount * (market_r / 100.0)
    liquidity_loss = loan_amount * (liquidity_r / 100.0)
    country_loss = loan_amount * (country_r / 100.0)
    total_el = credit_loss + market_loss + liquidity_loss + country_loss
    total_risk_pct = (total_el / loan_amount) * 100.0

    st.divider()

    # ==========================================================================
    # المؤشر البصري التفاعلي (أخضر / أصفر / أحمر)
    # ==========================================================================
    if dti <= 33.0 and total_risk_pct <= 2.0:
        st.markdown(
            f"""
            <div style="background-color:#d4edda; border-left:8px solid #28a745; padding:15px; border-radius:8px; color:#155724; direction:rtl;">
                <h3 style="margin:0;">🟢 مؤشر الأمان: منخفض المخاطر (مقبول فوراً)</h3>
                <p style="margin:5px 0 0 0;">نسبة الاقتطاع ({dti:.1f}%) مثالية، وإجمالي المخاطر ({total_risk_pct:.2f}%) في المنطقة الآمنة تماماً.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    elif dti <= 38.0 and total_risk_pct <= 4.0:
        st.markdown(
            f"""
            <div style="background-color:#fff3cd; border-left:8px solid #ffc107; padding:15px; border-radius:8px; color:#856404; direction:rtl;">
                <h3 style="margin:0;">🟡 مؤشر الأمان: مخاطر متوسطة (مقبول بضمانات)</h3>
                <p style="margin:5px 0 0 0;">نسبة الاقتطاع ({dti:.1f}%) تقترب من السقف البنكي، يُنصح بالقبول مع توطين الراتب والتأمين الشامل.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f"""
            <div style="background-color:#f8d7da; border-left:8px solid #dc3545; padding:15px; border-radius:8px; color:#721c24; direction:rtl;">
                <h3 style="margin:0;">🔴 مؤشر الأمان: مخاطر مرتفعة (يُنصح بالرفض أو التعديل)</h3>
                <p style="margin:5px 0 0 0;">نسبة الاقتطاع ({dti:.1f}%) أو المخاطر الكلية ({total_risk_pct:.2f}%) تتجاوز الحدود الآمنة. يُنصح بتمديد المدة أو تقليل المبلغ.</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.write("")
    r1, r2, r3 = st.columns(3)
    r1.metric("القسط الشهري", f"{total_inst:.2f} م")
    r2.metric("نسبة الاقتطاع", f"{dti:.1f}%")
    r3.metric("إجمالي الخسارة المتوقعة", f"{total_el:.2f} م ({total_risk_pct:.2f}%)")

    st.write(f"**تفصيل المخاطر على قرض {loan_amount} مليون:**")
