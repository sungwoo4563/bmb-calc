import streamlit as st
import requests

st.set_page_config(page_title="BMB 매수 경로 비교 계산기", layout="centered")

st.title("📊 BMB 실시간 최적 매수 경로 계산기")
st.write("실시간 시세를 반영하여 가장 돈이 덜 드는(저렴한) BMB 매수 경로를 찾습니다.")

# -------------------------------------------------------------
# [모든 플랫폼 실시간 시세 데이터 수집 함수]
# -------------------------------------------------------------
@st.cache_data(ttl=15)  # 15초마다 시세를 새로고침합니다.
def get_all_live_prices():
    # 1. 업비트 테더(USDT/KRW) 가격
    try:
        upbit_url = "https://api.upbit.com/v1/ticker?markets=KRW-USDT"
        upbit_res = requests.get(upbit_url, headers={"accept": "application/json"}).json()
        live_usdt_krw = float(upbit_res[0]['trade_price'])
    except Exception:
        live_usdt_krw = 1550.0
        
    # 2. 엘뱅크 BMB/USDT 가격
    try:
        lbank_url = "https://api.lbkex.com/v1/ticker.do?symbol=bmb_usdt"
        lbank_res = requests.get(lbank_url).json()
        live_bmb_usdt = float(lbank_res['ticker']['latest'])
    except Exception:
        live_bmb_usdt = 125.1

    # 3. 유니스왑 Movn/USDT 가격 (GeckoTerminal API 활용 - BSC 네트워크)
    try:
        network = "bsc"
        movn_contract_address = "0x200b63AA750c901892d4DCf82439860F9C270274"
        
        uniswap_url = f"https://api.geckoterminal.com/api/v2/networks/{network}/tokens/{movn_contract_address}"
        uniswap_res = requests.get(uniswap_url).json()
        
        # BSC 체인의 풀에 형성된 실시간 달러(USDT) 가격 추출
        live_movn_usdt = float(uniswap_res['data']['attributes']['price_usd'])
    except Exception:
        live_movn_usdt = 0.979

    return live_usdt_krw, live_bmb_usdt, live_movn_usdt

# 실시간 시세 일괄 로드
current_usdt_krw, current_bmb_usdt, current_movn_usdt = get_all_live_prices()
# -------------------------------------------------------------

st.divider()

st.header("1. 투자 금액 및 현재 시세")
col1, col2 = st.columns(2)

with col1:
    krw_input = st.number_input("투자할 원화(KRW) 금액", min_value=0, value=1000000, step=100000)
    usdt_krw = st.number_input("현재 원화 마켓 테더(USDT) 가격", min_value=1.0, value=current_usdt_krw, step=1.0)

with col2:
    bmb_usdt = st.number_input("1 BMB 당 USDT 가격 (엘뱅크)", min_value=0.1, value=current_bmb_usdt, step=0.1)
    movn_usdt = st.number_input("1 Movn 당 USDT 가격 (BSC 기반)", min_value=0.001, value=current_movn_usdt, format="%.4f", step=0.001)
    bmb_movn_ratio = st.number_input("1 BMB 당 필요한 Movn 개수", min_value=0.1, value=132.2, step=0.1)

st.caption(f"🔄 **실시간 시세** | 테더: {current_usdt_krw}원 / BMB: {current_bmb_usdt} USDT / Movn: {current_movn_usdt:.4f} USDT")

st.divider()

# 계산 로직
user_usdt = krw_input / usdt_krw

# 경로 A: USDT 직구매
bmb_via_usdt = user_usdt / bmb_usdt
bmb_price_krw_via_usdt = bmb_usdt * usdt_krw

# 경로 B: Movn 스왑
user_movn = user_usdt / movn_usdt
bmb_via_movn = user_movn / bmb_movn_ratio
bmb_price_usdt_via_movn = movn_usdt * bmb_movn_ratio
bmb_price_krw_via_movn = bmb_price_usdt_via_movn * usdt_krw

st.header("2. 경로별 비교 결과")

# [업그레이드된 알림창 로직] 얼마나 더 저렴한지 차액 계산
if bmb_via_usdt > bmb_via_movn:
    # USDT 직구매가 더 저렴한 경우 (BMB 1개당 비용이 더 낮음)
    diff_krw = bmb_price_krw_via_movn - bmb_price_krw_via_usdt
    diff_usdt = bmb_price_usdt_via_movn - bmb_usdt
    st.success(f"💡 현재는 **[USDT 직구매]** 경로가 BMB 1개당 **약 {int(diff_krw):,}원 ({diff_usdt:.2f} USDT) 더 저렴하고 유리합니다!**")

elif bmb_via_usdt < bmb_via_movn:
    # Movn 스왑이 더 저렴한 경우 (BMB 1개당 비용이 더 낮음)
    diff_krw = bmb_price_krw_via_usdt - bmb_price_krw_via_movn
    diff_usdt = bmb_usdt - bmb_price_usdt_via_movn
    st.success(f"💡 현재는 **[Movn 경유 스왑]** 경로가 BMB 1개당 **약 {int(diff_krw):,}원 ({diff_usdt:.2f} USDT) 더 저렴하고 유리합니다!**")

else:
    st.info("두 경로의 효율이 동일합니다.")

# BMB 1개당 실질 구매 비용 (원화) 전광판
st.subheader("💰 BMB 1개당 실질 구매 비용 (원화)")
st.metric(label="🟢 USDT 직구매 시 가격", value=f"{int(bmb_price_krw_via_usdt):,} 원", delta=f"{bmb_usdt:.2f} USDT")
st.metric(label="🔵 Movn 스왑 시 가격", value=f"{int(bmb_price_krw_via_movn):,} 원", delta=f"{bmb_price_usdt_via_movn:.2f} USDT")

st.divider()

st.subheader("📋 내 자금 기준 예상 획득 수량")
col_res1, col_res2 = st.columns(2)
with col_res1:
    st.info(f"**USDT 직구매 시**\n\n총 **{bmb_via_usdt:.4f} BMB** 확보")
with col_res2:
    st.info(f"**Movn 스왑 시**\n\n총 **{bmb_via_movn:.4f} BMB** 확보")