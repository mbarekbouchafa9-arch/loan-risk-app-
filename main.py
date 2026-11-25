import streamlit as st
import pandas as pd
import numpy as np
from scipy.optimize import linprog

# إعدادات الصفحة لتناسب شاشة الهاتف وتطبيق الأندرويد
st.set_page_config(page_title="نظام إدارة وتحسين القروض", page_icon="🏦", layout="centered")

st.title("🏦 نظام تحليل المخاطر وتحسين القروض")
st.caption("منصة متكاملة لحساب الخسارة المتوقعة (EL) وتحسين المحافظ بالبرمجة الخطية وبالأهداف")

# تقسيم التطبيق إلى تبويبين رئيسيين
main_tab1, main_tab2 = st.tabs(["📊 1. تحسين محفظة البنك", "🧮 2. حاسبة مخاطر قرض فردي"])

# ==============================================================================
# التبويب الأول: تحسين المحفظة وحساب المخاطر تلقائياً (PD × LGD)
# ==============================================================================
with main_tab1:
    with st.expander("⚙️ إعدادات السيولة وأوزان المفاضلة", expanded=True):
        total_budget = st.number_input("إجمالي السيولة المتاحة (مليون):", min_value=10.0, value=100.0, step=10.0)
        col_w1, col_w2 = st.columns(2)
        with col_w1:
            w_return = st.slider("أهمية تعظيم العائد:", 1, 50, 10)
        with col_w2:
            w_risk = st.slider("أهمية تقليل المخاطر:", 1, 50, 20)

    st.subheader("📋 فئات القروض (أدخل PD و LGD)")
    default_loans = pd.DataFrame([
        {"الفئة": "قرض استهلاكي (بالتأمين)", "الفائدة %": 7.5, "PD %": 3.0, "LGD %": 25.0, "الحد الأدنى": 0.0, "الحد الأقصى": 40.0},
        {"الفئة": "قرض عقاري (برهن)", "الفائدة %": 6.5, "PD %": 1.5, "LGD %": 15.0, "الحد الأدنى": 20.0, "الحد الأقصى": 60.0},
        {"الفئة": "مؤسسات صغيرة (SME)", "الفائدة %": 10.0, "PD %": 6.0, "LGD %": 45.0, "الحد الأدنى": 0.0, "الحد الأقصى": 50.0},
    ])
    df_loans = st.data_editor(default_loans, num_rows="dynamic", use_container_width=True)

    # حساب معامل المخاطرة الصافي تلقائياً لكل فئة (PD * LGD)
    df_loans["المخاطرة الصافية %"] = (df_loans["PD %"] * df_loans["LGD %"]) / 100.0
    st.info("💡 معامل المخاطرة الصافي = PD × LGD (يُحسب تلقائياً لكل فئة)")
    st.dataframe(df_loans[["الفئة", "الفائدة %", "PD %", "LGD %", "المخاطرة الصافية %"]], use_container_width=True)

    with st.expander("🎯 تحديد المستهدفات المالية للمحفظة", expanded=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            max_risk_lp = st.number_input("سقف الخسارة للخطية (م):", value=1.5, step=0.1)
        with c2:
            target_ret_gp = st.number_input("العائد المستهدف (م):", value=8.0, step=0.5)
        with c3:
            target_risk_gp = st.number_input("الخسارة المستهدفة (م):", value=1.0, step=0.1)

    if st.button("🚀 احسب التوزيع الأمثل والمخاطر", type="primary", use_container_width=True):
        n = len(df_loans)
        rates = df_loans["الفائدة %"].values / 100.0
        net_risks = df_loans["المخاطرة الصافية %"].values / 100.0
        bounds_base = [(df_loans["الحد الأدنى"].iloc[i], df_loans["الحد الأقصى"].iloc[i]) for i in range(n)]

        # 1. البرمجة الخطية (LP)
        res_lp = linprog(
            c=-rates,
            A_ub=[[1.0]*n, list(net_risks)],
            b_ub=[total_budget, max_risk_lp],
            bounds=bounds_base,
            method="highs"
        )

        # 2. البرمجة بالأهداف (GP)
        c_gp = [0.0]*n + [w_return, 0.0, 0.0, w_risk]
        A_eq_gp = [
            list(rates) + [1.0, -1.0, 0.0, 0.0],
            list(net_risks) + [0.0, 0.0, 1.0, -1.0]
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
            st.subheader("📈 نتائج المقارنة وتوزيع السيولة")

            res_t1, res_t2 = st.tabs(["⚖️ البرمجة بالأهداف (المتوازن)", "💰 البرمجة الخطية (أعلى عائد)"])

            with res_t1:
                m1, m2 = st.columns(2)
                m1.metric("العائد المتوقع", f"{np.sum(alloc_gp * rates):.2f} م")
                m2.metric("الخسارة المتوقعة (EL)", f"{np.sum(alloc_gp * net_risks):.2f} م")
                st.bar_chart(pd.DataFrame({"المبلغ المخصص (مليون)": alloc_gp}, index=df_loans["الفئة"]))

            with res_t2:
                m3, m4 = st.columns(2)
                m3.metric("العائد الأقصى", f"{np.sum(alloc_lp * rates):.2f} م")
                m4.metric("الخسارة المتوقعة (EL)", f"{np.sum(alloc_lp * net_risks):.2f} م")
                st.bar_chart(pd.DataFrame({"المبلغ المخصص (مليون)": alloc_lp}, index=df_loans["الفئة"]))

            comp_df = pd.DataFrame({
                "فئة القرض": df_loans["الفئة"],
                "الخطية (مليون)": np.round(alloc_lp, 2),
                "بالأهداف (مليون)": np.round(alloc_gp, 2),
                "الخسارة بالخطية (م)": np.round(alloc_lp * net_risks, 3),
                "الخسارة بالأهداف (م)": np.round(alloc_gp * net_risks, 3)
            })
            st.dataframe(comp_df, use_container_width=True)
        else:
            st.error("⚠️ تعذر إيجاد حل! يرجى مراجعة الحدود الدنيا أو رفع سقف الخسارة المسموح.")

# ==============================================================================
# التبويب الثاني: حاسبة مخاطر القرض الفردي (DTI & EL = PD × LGD × EAD)
# ==============================================================================
with main_tab2:
    st.subheader("🔍 تقييم ملف مقترض فردي")
    
    col_i1, col_i2 = st.columns(2)
    with col_i1:
        salary = st.number_input("الراتب الشهري (مليون سنتيم):", min_value=1.0, value=7.4, step=0.1)
        loan_amount = st.number_input("مبلغ القرض EAD (مليون سنتيم):", min_value=1.0, value=200.0, step=10.0)
        years = st.number_input("مدة القرض (سنوات):", min_value=1, max_value=30, value=10, step=1)
    with col_i2:
        interest_rate = st.number_input("معدل الفائدة السنوي (%):", min_value=0.0, value=7.5, step=0.5)
        insurance_tax = st.number_input("التأمين والضرائب الشهرية (مليون):", min_value=0.0, value=0.186, step=0.01, format="%.3f")
        lgd_ind = st.slider("نسبة الخسارة عند التعثر LGD (%):", 5, 100, 25)

    # حساب القسط الشهري الأساسي
    months = years * 12
    monthly_rate = (interest_rate / 100.0) / 12.0
    if monthly_rate > 0:
        base_installment = loan_amount * (monthly_rate * (1 + monthly_rate)**months) / ((1 + monthly_rate)**months - 1)
    else:
        base_installment = loan_amount / months

    total_installment = base_installment + insurance_tax
    dti_ratio = (total_installment / salary) * 100.0

    # تقدير احتمالية التعثر PD تلقائياً بناءً على نسبة الاقتطاع من الراتب (DTI)
    if dti_ratio <= 30.0:
        pd_est = 1.5
        risk_status = "منخفضة (آمن مصرفياً)"
    elif dti_ratio <= 36.0:
        pd_est = 3.0
        risk_status = "مقبولة (ضمن هامش المرونة والتأمين)"
    elif dti_ratio <= 45.0:
        pd_est = 6.0
        risk_status = "متوسطة إلى مرتفعة (تحتاج ضمانات إضافية)"
    else:
        pd_est = 10.0
        risk_status = "مرتفعة جداً (تتجاوز قدرة السداد)"

    # حساب الخسارة المتوقعة EL
    expected_loss = loan_amount * (pd_est / 100.0) * (lgd_ind / 100.0)
    net_risk_pct = (pd_est * lgd_ind) / 100.0

    st.divider()
    st.subheader("📊 نتيجة التقييم الائتماني")

    r1, r2, r3 = st.columns(3)
    r1.metric("القسط الشهري الفعلي", f"{total_installment:.2f} م")
    r2.metric("نسبة الاقتطاع (DTI)", f"{dti_ratio:.1f}%")
    r3.metric("الخسارة المتوقعة (EL)", f"{expected_loss:.2f} م")

    st.write(f"**احتمالية التعثر المقدرة (PD):** {pd_est}% — **تصنيف المخاطرة:** {risk_status}")
    st.write(f"**معامل المخاطرة الصافي (PD × LGD):** **{net_risk_pct:.2f}%** (يمكنك نقل هذا الرقم إلى جدول المحفظة في التبويب الأول).")
