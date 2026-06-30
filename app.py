import streamlit as st
import requests

st.set_page_config(page_title="BMB 매수 경로 비교 계산기", layout="centered")

st.title("📊 BMB 실시간 최적 매수 경로 계산기")
st.write("실시간 시세와 직접 입력한 시세를 비교하여 가장 유리한 BMB 매수 경로를 찾습니다.")

# -------------------------------------------------------------
# [안정적인 실시간 시세 데이터 수집 함수]
# -------------------------------------------------------------
@st.cache_data(ttl=15)
def get_live_prices():
    try:
        upbit_url = "https://api.upbit.com/v1/ticker?markets=KRW-USDT"
        upbit_res = requests.get(upbit_url, headers={"accept": "application/json"}).json()
        live_usdt_krw = float(upbit_res[0]['trade_price'])
    except Exception:
        live_usdt_krw = 1550.0

    try:
        lbank_url = "https://api.lbkex.com/v1/ticker.do?symbol=bmb_usdt"
        lbank_res = requests.get(lbank_url).json()
        live_bmb_usdt = float(lbank_res['ticker']['latest'])
    except Exception:
        live_bmb_usdt = 129.6
        
    try:
        network = "bsc"
        movn_contract_address = "0x200b63AA750c901892d4DCf82439860F9C270274"
        uniswap_url = f"https://api.geckoterminal.com/api/v2/networks/{network}/tokens/{movn_contract_address}"
        uniswap_res = requests.get(uniswap_url).json()
        live_movn_usdt = float(uniswap_res['data']['attributes']['price_usd'])
    except Exception:
        live_movn_usdt = 0.979

    return live_usdt_krw, live_bmb_usdt, live_movn_usdt

current_usdt_krw, current_bmb_usdt, current_movn_usdt = get_live_prices()
# -------------------------------------------------------------

# 천 단위 쉼표를 붙여주는 변환 함수
def format_with_commas(val_str):
    clean = "".join(filter(str.isdigit, val_str))
    if not clean:
        return ""
    return f"{int(clean):,}"

st.divider()

st.header("1. 투자 금액 및 현재 시세")
col1, col2 = st.columns(2)

with col1:
    # 1. 투자 원화 금액 처리 (기존 텍스트가 있으면 쉼표를 붙여서 기억)
    if 'krw_raw' not in st.session_state:
        st.session_state.krw_raw = "1,000,000"
        
    krw_text = st.text_input("🚨 :red[**투자할 원화(KRW) 금액 [직접 입력]**]", value=st.session_state.krw_raw)
    formatted_krw = format_with_commas(krw_text)
    
    # 실시간으로 입력창 값을 쉼표 포맷으로 강제 변환
    if formatted_krw != krw_text:
        st.session_state.krw_raw = formatted_krw
        st.rerun()
        
    # 실제 계산용 숫자 변환
    krw_input = int(formatted_krw.replace(",", "")) if formatted_krw else 0

    usdt_krw = st.number_input("현재 원화 마켓 테더(USDT) 가격", min_value=1.0, value=current_usdt_krw, step=1.0)

with col2:
    bmb_usdt_input = st.number_input("1 BMB 당 USDT 가격 (엘뱅크)", min_value=0.1, value=current_bmb_usdt, step=0.1)
    
    # 2. 모빅매니아 원화 가격 처리
    if 'bmb_krw_raw' not in st.session_state:
        st.session_state.bmb_krw_raw = "200,000"
        
    bmb_krw_text = st.text_input("🚨 :red[**1 BMB 당 원화 가격 (모빅매니아 시세) [직접 입력]**]", value=st.session_state.bmb_krw_raw, help="현재 원화 직거래 가격을 직접 적어주세요.")
    formatted_bmb_krw = format_with_commas(bmb_krw_text)
    
    if formatted_bmb_krw != bmb_krw_text:
        st.session_state.bmb_krw_raw = formatted_bmb_krw
        st.rerun()
        
    bmb_krw_input = int(formatted_bmb_krw.replace(",", "")) if formatted_bmb_krw else 1000
    
    movn_usdt = st.number_input("1 Movn 당 USDT 가격 (BSC 기반)", min_value=0.001, value=current_movn_usdt, format="%.4f", step=0.001)
    bmb_movn_ratio = st.number_input("1 BMB 당 필요한 Movn 개수", min_value=0.1, value=132.2, step=0.1)

info_text = f"테더: {current_usdt_krw}원 / 엘뱅크 BMB: {current_bmb_usdt} USDT / Movn: {current_movn_usdt:.4f} USDT"
st.caption(f"🔄 **실시간 연동** | {info_text}")

st.divider()

# -------------------------------------------------------------
# [3대 경로 계산 로직]
# -------------------------------------------------------------
bmb_price_krw_via_usdt = bmb_usdt_input * usdt_krw
bmb_price_usdt_via_movn = movn_usdt * bmb_movn_ratio
bmb_price_krw_via_movn = bmb_price_usdt_via_movn * usdt_krw
bmb_price_krw_direct = bmb_krw_input

routes = {
    "USDT 직구매": bmb_price_krw_via_usdt,
    "Movn 경유 스왑": bmb_price_krw_via_movn,
    "원화 직구매 (모빅매니아)": bmb_price_krw_direct
}
best_route_name = min(routes, key=routes.get)
# -------------------------------------------------------------

st.header("2. 경로별 비교 결과")
st.success(f"💡 현재는 **[{best_route_name}]** 경로가 BMB 1개당 가장 저렴하고 유리합니다!")

st.subheader("💰 BMB 1개당 실질 구매 비용 (원화)")
st.metric(label="🟢 USDT 직구매 가격 (엘뱅크)", value=f"{int(bmb_price_krw_via_usdt):,} 원", delta=f"{bmb_usdt_input:.2f} USDT")
st.metric(label="🔵 Movn 스왑시 가격 (유니스왑)", value=f"{int(bmb_price_krw_via_movn):,} 원", delta=f"{bmb_price_usdt_via_movn:.2f} USDT")
st.metric(label="🟠 원화 직구매 가격 (모빅매니아 직접 입력)", value=f"{int(bmb_price_krw_direct):,} 원", delta=f"{(bmb_price_krw_direct/usdt_krw):.2f} USDT 환산")

st.divider()

st.subheader("📋 내 자금 기준 예상 획득 수량")
res_col1, res_col2, res_col3 = st.columns(3)
with res_col1:
    val1 = (krw_input / bmb_price_krw_via_usdt) if bmb_price_krw_via_usdt > 0 else 0
    st.info(f"**USDT 직구매 시**\n\n**{val1:.4f} BMB**")
with res_col2:
    val2 = (krw_input / bmb_price_krw_via_movn) if bmb_price_krw_via_movn > 0 else 0
    st.info(f"**Movn 스왑 시**\n\n**{val2:.4f} BMB**")
with res_col3:
    val3 = (krw_input / bmb_price_krw_direct) if bmb_price_krw_direct > 0 else 0
    st.info(f"**원화 직구매 시**\n\n**{val3:.4f} BMB**")