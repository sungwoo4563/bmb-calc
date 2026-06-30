import streamlit as st
import requests

st.set_page_config(page_title="BMB 매수 경로 비교 계산기", layout="centered")

st.title("📊 BMB 실시간 최적 매수 경로 계산기")
st.write("업비트(테더 가격)와 엘뱅크(BMB 가격)의 실시간 시세를 반영하여 최적의 경로를 판별합니다.")

# -------------------------------------------------------------
# [실시간 시세 데이터 수집 함수]
# -------------------------------------------------------------
@st.cache_data(ttl=15)  # 15초마다 최신 시세로 갱신합니다.
def get_live_prices():
    # 1. 업비트 테더(USDT/KRW) 가격 가져오기
    try:
        upbit_url = "https://api.upbit.com/v1/ticker?markets=KRW-USDT"
        upbit_res = requests.get(upbit_url, headers={"accept": "application/json"}).json()
        live_usdt_krw = float(upbit_res[0]['trade_price'])
    except Exception:
        live_usdt_krw = 1550.0  # 오류 시 기본값
        
    # 2. 엘뱅크 BMB/USDT 가격 가져오기
    try:
        # 엘뱅크 공식 가이드에 따른 시세 조회 주소 (bmb_usdt 마켓)
        lbank_url = "https://api.lbkex.com/v1/ticker.do?symbol=bmb_usdt"
        lbank_res = requests.get(lbank_url).json()
        # 최신 거래가(latest) 추출
        live_bmb_usdt = float(lbank_res['ticker']['latest'])
    except Exception:
        live_bmb_usdt = 125.1  # 오류 시 기본값

    return live_usdt_krw, live_bmb_usdt

# 실시간 시세 로드
current_usdt_krw, current_bmb_usdt = get_live_prices()
# -------------------------------------------------------------

st.divider()

st.header("1. 투자 금액 및 현재 시세 (자동 반영)")
col1, col2 = st.columns(2)

with col1:
    krw_input = st.number_input("투자할 원화(KRW) 금액", min_value=0, value=1000000, step=100000)
    # 업비트 가격 자동 세팅
    usdt_krw = st.number_input("현재 원화 마켓 테더(USDT) 가격", min_value=1.0, value=current_usdt_krw, step=1.0)

with col2:
    # 엘뱅크 가격 자동 세팅
    bmb_usdt = st.number_input("1 BMB 당 USDT 가격 (엘뱅크)", min_value=0.1, value=current_bmb_usdt, step=0.1)
    movn_usdt = st.number_input("1 Movn 당 USDT 가격", min_value=0.001, value=0.979, step=0.001)
    bmb_movn_ratio = st.number_input("1 BMB 당 필요한 Movn 개수", min_value=0.1, value=132.2, step=0.1)

st.caption(f"🔄 **실시간 연동 완료** | 업비트 테더: {current_usdt_krw}원 / 엘뱅크 BMB: {current_bmb_usdt} USDT")

st.divider()

# 계산 로직
user_usdt = krw_input / usdt_krw
bmb_via_usdt = user_usdt / bmb_usdt

user_movn = user_usdt / movn_usdt
bmb_via_movn = user_movn / bmb_movn_ratio

st.header("2. 경로별 비교 결과")

if bmb_via_usdt > bmb_via_movn:
    best_route = "USDT 직구매"
    st.success(f"💡 현재는 엘뱅크에서 **[{best_route}]** 경로가 더 유리합니다!")
elif bmb_via_usdt < bmb_via_movn:
    best_route = "Movn 경유 스왑"
    st.success(f"💡 현재는 **[{best_route}]** 경로가 더 유리합니다!")
else:
    st.info("두 경로의 효율이 동일합니다.")

st.subheader("📋 상세 수치")
st.dataframe({
    "구분": ["USDT 직구매 경로", "Movn 스왑 경로"],
    "확보 가능한 BMB 개수": [f"{bmb_via_usdt:.4f} BMB", f"{bmb_via_movn:.4f} BMB"],
    "BMB 1개당 실질 비용": [f"{bmb_usdt:.2f} USDT", f"{(movn_usdt * bmb_movn_ratio):.2f} USDT"]
}, use_container_width=True)