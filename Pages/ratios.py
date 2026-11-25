import streamlit as st

st.set_page_config(page_title="حاسبة نسب المخاطر الأربعة", page_icon="📐", layout="centered")

st.title("📐 حاسبة نسب المخاطر المصرفية الأربعة")
st.caption("أدخل المعطيات الأولية لحساب النسبة المئوية لكل مخاطرة بدقة")

# 1. مخاطر الائتمان
st.subheader("1️⃣ مخاطر الائتمان (Risque de crédit)")
c1, c2 = st.columns(2)
with c1:
    pd_pct = st.number_input("احتمالية التعثر PD (%):", min_value=0.0, value=3.0, step=0.5)
with c2:
    lgd_pct = st.number_input("الخسارة عند التعثر LGD (%):", min_value=0.0, max_value=100.0, value=25.0, step=5.0)
risque_credit = (pd_pct * lgd_pct) / 100.0

# 2. مخاطر السوق
st.subheader("2️⃣ مخاطر السوق (Risque de marché)")
c3, c4 = st.columns(2)
with c3:
    duration = st.number_input("المدة المعدلة (سنوات):", min_value=0.1, value=4.0, step=0.5)
with c4:
    delta_r = st.number_input("تغير سعر الفائدة المتوقع (%):", min_value=0.0, value=0.10, step=0.05)
risque_marche = duration * delta_r

# 3. مخاطر السيولة
st.subheader("3️⃣ مخاطر السيولة (Risque de liquidité)")
c5, c6 = st.columns(2)
with c5:
    duree_ans = st.number_input("مدة القرض (سنوات):", min_value=1, value=10, step=1)
with c6:
    cout_liq = st.number_input("معامل تكلفة السيولة السنوي (%):", min_value=0.0, value=0.05, step=0.01)
risque_liquidite = duree_ans * cout_liq

# 4. مخاطر البلد
st.subheader("4️⃣ مخاطر البلد (Risque de pays)")
c7, c8 = st.columns(2)
with c7:
    prime_pays = st.number_input("علاوة مخاطر الدولة (%):", min_value=0.0, value=3.0, step=0.5)
with c8:
    sensibilite = st.number_input("حساسية القطاع (0.1 إلى 1.0):", min_value=0.05, max_value=1.0, value=0.10, step=0.05)
risque_pays = prime_pays * sensibilite

# المجموع الكلي وعرض النتائج
risque_total = risque_credit + risque_marche + risque_liquidite + risque_pays

st.divider()
st.subheader("📊 النسب المحسوبة الجاهزة للاستخدام")

r1, r2 = st.columns(2)
r1.metric("1. مخاطر الائتمان", f"{risque_credit:.2f}%")
r2.metric("2. مخاطر السوق", f"{risque_marche:.2f}%")

r3, r4 = st.columns(2)
r3.metric("3. مخاطر السيولة", f"{risque_liquidite:.2f}%")
r4.metric("4. مخاطر البلد", f"{risque_pays:.2f}%")

st.success(f"**إجمالي نسبة المخاطر الكلية (Total Risques) = {risque_total:.2f}%**")
