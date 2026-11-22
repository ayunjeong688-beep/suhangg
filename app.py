import os
from datetime import date, datetime
from io import BytesIO

import qrcode
import streamlit as st
from openai import OpenAI

st.set_page_config(
    page_title="우리 가족 건강 도우미",
    page_icon="💙",
    layout="centered",
)

# ---------- 디자인 ----------
st.markdown(
    """
    <style>
    .stApp { background: #f5f8fc; }
    .block-container { max-width: 850px; padding-top: 1.8rem; padding-bottom: 3rem; }
    .main-title { font-size: 2rem; font-weight: 800; color: #183b56; margin-bottom: .2rem; }
    .sub-title { color: #62788a; margin-bottom: 1.2rem; }
    div[data-testid="stMetric"] {
        background: white; border: 1px solid #e3ebf2;
        padding: 14px; border-radius: 14px;
    }
    div.stButton > button {
        border-radius: 10px; border: 0; font-weight: 650;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="main-title">💙 우리 가족 건강 도우미</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">약 복용부터 식사와 생활 습관까지, 매일의 건강 관리를 한곳에서</div>',
    unsafe_allow_html=True,
)

# ---------- 세션 데이터 ----------
if "medicines" not in st.session_state:
    st.session_state.medicines = []
if "meals" not in st.session_state:
    st.session_state.meals = []
if "habits" not in st.session_state:
    st.session_state.habits = {
        "규칙적인 식사하기": False,
        "가벼운 신체 활동하기": False,
        "충분히 휴식하기": False,
        "개인별 식사 주의사항 확인하기": False,
    }
if "chat" not in st.session_state:
    st.session_state.chat = []

today = date.today().isoformat()

# ---------- 오늘의 요약 ----------
taken_count = sum(
    1 for med in st.session_state.medicines
    if med["date"] == today and med["taken"]
)
today_meds = sum(1 for med in st.session_state.medicines if med["date"] == today)
done_habits = sum(st.session_state.habits.values())

m1, m2, m3 = st.columns(3)
m1.metric("오늘 등록한 약", f"{today_meds}개")
m2.metric("복용 확인", f"{taken_count}/{today_meds}")
m3.metric("생활 습관", f"{done_habits}/{len(st.session_state.habits)}")

st.divider()

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["💊 약 복용", "🥗 식사 관리", "🌿 생활 습관", "🤖 AI 도우미", "📱 QR 공유"]
)

# ---------- 약 복용 관리 ----------
with tab1:
    st.subheader("약 복용 관리")
    st.caption("복용할 약과 시간을 등록하고, 복용 후 체크해 보세요.")
    with st.form("medicine_form", clear_on_submit=True):
        med_name = st.text_input("약 이름", placeholder="예: 처방받은 약")
        med_time = st.time_input("복용 예정 시간", value=datetime.now().replace(second=0, microsecond=0).time())
        med_note = st.text_input("메모 (선택)", placeholder="예: 식후 복용 등")
        add_med = st.form_submit_button("약 등록", use_container_width=True)
        if add_med:
            if med_name.strip():
                st.session_state.medicines.append({
                    "name": med_name.strip(),
                    "time": med_time.strftime("%H:%M"),
                    "note": med_note.strip(),
                    "date": today,
                    "taken": False,
                })
                st.success("약이 등록되었어요.")
            else:
                st.warning("약 이름을 입력해 주세요.")

    todays_meds = [
        (idx, med) for idx, med in enumerate(st.session_state.medicines)
        if med["date"] == today
    ]
    if todays_meds:
        st.markdown("**오늘의 복용 목록**")
        for idx, med in todays_meds:
            c1, c2 = st.columns([4, 1])
            with c1:
                status = "✅ 복용 확인" if med["taken"] else "⏰ 복용 전"
                st.write(f"**{med['time']} · {med['name']}**")
                st.caption(f"{status}" + (f" · {med['note']}" if med["note"] else ""))
            with c2:
                new_value = st.checkbox(
                    "복용 완료",
                    value=med["taken"],
                    key=f"taken_{idx}",
                )
                st.session_state.medicines[idx]["taken"] = new_value
            st.divider()
    else:
        st.info("등록된 약이 없어요. 위에서 약을 등록해 보세요.")

# ---------- 식사 관리 ----------
with tab2:
    st.subheader("식사 관리")
    st.caption("먹은 음식과 식사 시간을 기록해 보세요.")
    with st.form("meal_form", clear_on_submit=True):
        meal_type = st.selectbox("식사 구분", ["아침", "점심", "저녁", "간식"])
        meal_content = st.text_input("먹은 음식", placeholder="예: 밥, 생선, 채소")
        meal_caution = st.text_input("확인할 주의사항 (선택)", placeholder="예: 안내받은 식사 주의사항")
        save_meal = st.form_submit_button("식사 기록 저장", use_container_width=True)
        if save_meal:
            if meal_content.strip():
                st.session_state.meals.append({
                    "date": today,
                    "type": meal_type,
                    "content": meal_content.strip(),
                    "caution": meal_caution.strip(),
                })
                st.success("식사 기록을 저장했어요.")
            else:
                st.warning("먹은 음식을 입력해 주세요.")

    todays_meals = [m for m in st.session_state.meals if m["date"] == today]
    if todays_meals:
        st.markdown("**오늘의 식사 기록**")
        for meal in todays_meals:
            st.write(f"**{meal['type']}** · {meal['content']}")
            if meal["caution"]:
                st.caption(f"확인 사항: {meal['caution']}")
    else:
        st.info("아직 오늘의 식사 기록이 없어요.")

# ---------- 생활 습관 ----------
with tab3:
    st.subheader("생활 습관 관리")
    st.caption("오늘 실천한 항목을 체크해 보세요.")
    for habit in list(st.session_state.habits.keys()):
        st.session_state.habits[habit] = st.checkbox(
            habit,
            value=st.session_state.habits[habit],
            key=f"habit_{habit}",
        )
    st.progress(done_habits / len(st.session_state.habits))
    st.caption(f"오늘 {done_habits}개 항목을 실천했어요.")

# ---------- AI 도우미 ----------
with tab4:
    st.subheader("AI 건강 관리 도우미")
    st.caption("건강 관리에 관한 일반적인 정보를 질문할 수 있어요.")
    st.info(
        "AI 답변은 일반 정보이며 의사의 진단이나 약사의 복약 지도를 대신하지 않아요. "
        "약의 용량·복용 시간 변경, 복용 중단 여부는 반드시 의료진 또는 약사에게 확인하세요."
    )

    api_key = st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY", ""))
    if not api_key:
        st.warning(
            "AI 기능을 사용하려면 Streamlit Cloud의 앱 설정 → Secrets에 "
            "OPENAI_API_KEY를 등록해야 해요."
        )
        st.code('OPENAI_API_KEY = "여기에_발급받은_API_키"', language="toml")
    else:
        question = st.text_area(
            "무엇이 궁금한가요?",
            placeholder="예: 건강한 식사 습관을 유지하려면 어떤 점을 신경 쓰면 좋을까요?",
            height=100,
        )
        if st.button("AI에게 질문하기", type="primary", use_container_width=True):
            if not question.strip():
                st.warning("질문을 입력해 주세요.")
            else:
                try:
                    client = OpenAI(api_key=api_key)
                    with st.spinner("답변을 준비하고 있어요..."):
                        response = client.responses.create(
                            model="gpt-4o-mini",
                            instructions=(
                                "너는 청소년과 가족을 위한 안전한 일반 건강정보 안내 도우미다. "
                                "한국어로 쉽고 차분하게 답한다. 질병을 진단하거나 치료를 처방하지 않는다. "
                                "약의 용량, 복용 시간, 복용 중단을 지시하지 않는다. "
                                "개인별 의료 판단이 필요한 질문은 의사나 약사에게 확인하도록 안내한다. "
                                "응급 증상이 의심되면 즉시 보호자와 의료진에게 도움을 요청하라고 안내한다. "
                                "개인정보나 불필요한 민감정보를 입력하지 말라고 상기시킨다."
                            ),
                            input=question.strip(),
                        )
                    answer = response.output_text
                    st.session_state.chat.append((question.strip(), answer))
                    st.markdown("**AI 답변**")
                    st.write(answer)
                except Exception as e:
                    st.error("AI 답변을 가져오지 못했어요. API 키와 사용량 설정을 확인해 주세요.")
                    st.caption(f"오류 종류: {type(e).__name__}")

    if st.session_state.chat:
        st.markdown("**이전 질문과 답변**")
        for q, a in reversed(st.session_state.chat):
            with st.expander(q):
                st.write(a)
        if st.button("대화 기록 지우기"):
            st.session_state.chat = []
            st.rerun()

# ---------- QR 공유 ----------
with tab5:
    st.subheader("QR코드로 앱 공유하기")
    st.caption("앱을 Streamlit Community Cloud에 배포한 뒤 공개 주소를 입력하세요.")
    app_url = st.text_input("배포된 앱 주소", placeholder="https://your-app-name.streamlit.app")
    if st.button("QR코드 만들기", use_container_width=True):
        if app_url.startswith("https://") or app_url.startswith("http://"):
            qr = qrcode.QRCode(box_size=8, border=3)
            qr.add_data(app_url.strip())
            qr.make(fit=True)
            qr_img = qr.make_image(fill_color="#183b56", back_color="white")
            buffer = BytesIO()
            qr_img.save(buffer, format="PNG")
            st.image(buffer.getvalue(), caption="휴대폰 카메라로 QR코드를 스캔하세요.", width=230)
            st.download_button(
                "QR코드 이미지 다운로드",
                data=buffer.getvalue(),
                file_name="family_health_app_qr.png",
                mime="image/png",
                use_container_width=True,
            )
        else:
            st.warning("https://로 시작하는 배포 주소를 입력해 주세요.")

st.divider()
st.caption(
    "※ 이 앱은 건강 관리 기록을 돕는 교육용 예시입니다. "
    "기록은 현재 접속 세션에 임시 저장되며, 새로 접속하거나 앱이 다시 시작되면 사라질 수 있어요. "
    "실제 약 복용 여부는 사용자가 직접 확인해 주세요."
)
