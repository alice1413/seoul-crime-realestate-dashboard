import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from scipy.stats import pearsonr

st.set_page_config(page_title="서울시 범죄율 × 아파트 가격", page_icon="🏙️", layout="wide")
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"

st.markdown("""
<style>
.stApp { background: #f7f8fa; }
.block-container { max-width: 1400px; padding-top: 2rem; padding-bottom: 3rem; }
h1, h2, h3 { letter-spacing: -0.03em; }
.subtitle { color:#737b8c; font-size:.95rem; margin-top:-.6rem; margin-bottom:1.4rem; }
.section-title { font-size:1.15rem; font-weight:700; color:#202634; margin-top:1.3rem; margin-bottom:.8rem; }
.subsection-title { font-size:1.02rem; font-weight:700; color:#303746; margin-top:.9rem; margin-bottom:.65rem; }
div[data-testid="stMetric"] { background:white; border:1px solid #e7e9ee; border-radius:16px; padding:18px 20px; box-shadow:0 2px 10px rgba(25,35,50,.04); }
div[data-testid="stMetricLabel"] { color:#7a8291; }
div[data-testid="stMetricValue"] { color:#222837; }
.note-box { background:white; border:1px solid #e7e9ee; border-radius:14px; padding:14px 16px; color:#5d6574; font-size:.92rem; line-height:1.65; }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    df = pd.read_csv(DATA_DIR / "seoul_crime_realestate_2024.csv")
    with open(DATA_DIR / "seoul_gu.geojson", "r", encoding="utf-8") as f:
        geojson = json.load(f)
    return df, geojson

df, geojson = load_data()

crime_options = {
    "전체 범죄": ("전체범죄", "전체범죄율"),
    "살인": ("살인", "살인율"),
    "강도": ("강도", "강도율"),
    "강간·강제추행": ("강간강제추행", "강간강제추행율"),
    "절도": ("절도", "절도율"),
    "폭력": ("폭력", "폭력율"),
}

st.title("서울시 범죄 발생률과 아파트 매매가격")
st.markdown('<div class="subtitle">2024년 · 서울시 25개 자치구 · 범죄 발생 수준과 주택가격의 관계</div>', unsafe_allow_html=True)

c1, c2 = st.columns(2, gap="large")
with c1:
    selected_crime = st.selectbox("범죄 유형", list(crime_options.keys()))
with c2:
    gu_list = sorted(df["자치구"].tolist())
    selected_gu = st.selectbox("상세 자치구", gu_list, index=gu_list.index("강남구") if "강남구" in gu_list else 0)

count_col, rate_col = crime_options[selected_crime]
r, p_value = pearsonr(df[rate_col], df["제곱미터당가격중앙값"])
mean_crime_rate = df[rate_col].mean()
mean_price = df["제곱미터당가격중앙값"].mean()

if abs(r) < .2:
    corr_label = "매우 약한 관계"
elif abs(r) < .4:
    corr_label = "약한 관계"
elif abs(r) < .6:
    corr_label = "중간 정도 관계"
else:
    corr_label = "강한 관계"
if r > 0:
    corr_label += " · 양(+)의 방향"
elif r < 0:
    corr_label += " · 음(-)의 방향"

st.markdown(f'<div class="subsection-title">{selected_gu} 상세 비교</div>', unsafe_allow_html=True)
gu = df[df["자치구"] == selected_gu].iloc[0]
price_mean = df["제곱미터당가격중앙값"].mean()
crime_mean = df[rate_col].mean()
price_delta = (gu["제곱미터당가격중앙값"] / price_mean - 1) * 100
crime_delta = (gu[rate_col] / crime_mean - 1) * 100

d1, d2, d3, d4 = st.columns(4, gap="large")
with d1:
    st.metric(f"{selected_crime} 발생건수", f"{gu[count_col]:,.0f}건")
with d2:
    st.metric("인구 1만 명당 발생", f"{gu[rate_col]:,.1f}건", delta=f"{crime_delta:+.1f}% vs 서울 평균")
with d3:
    st.metric("㎡당 매매가격", f"{gu['제곱미터당가격중앙값']:,.1f}만원", delta=f"{price_delta:+.1f}% vs 서울 평균")
with d4:
    st.metric("2024 아파트 거래", f"{gu['거래건수']:,.0f}건")

st.markdown('<div class="section-title">전체 요약</div>', unsafe_allow_html=True)
m1, m2, m3 = st.columns(3, gap="large")
with m1:
    st.metric("Pearson 상관계수 r", f"{r:+.3f}", help=f"{corr_label} / p-value = {p_value:.4f}")
with m2:
    st.metric(f"평균 {selected_crime} 발생률", f"{mean_crime_rate:.1f}건", help="주민등록인구 1만 명당 발생건수의 자치구 평균")
with m3:
    st.metric("평균 ㎡당 아파트 가격", f"{mean_price:,.0f}만원", help="25개 자치구의 ㎡당 아파트 매매가격 중앙값의 평균")

st.markdown('<div class="section-title">지역별 공간 분포</div>', unsafe_allow_html=True)
map1, map2 = st.columns(2, gap="large")

# 지도 색은 선택한 범죄 유형 기준이지만, Hover에서는 모든 범죄 유형별 발생률을 함께 보여준다.
crime_map = px.choropleth_map(
    df,
    geojson=geojson,
    locations="자치구",
    featureidkey="properties.SIG_KOR_NM",
    color=rate_col,
    custom_data=[
        "자치구", count_col, rate_col,
        "전체범죄율", "살인율", "강도율", "강간강제추행율", "절도율", "폭력율"
    ],
    color_continuous_scale=[[0,"#fff7f7"],[.25,"#fbd7d7"],[.5,"#f4a6a6"],[.75,"#e56565"],[1,"#c92f2f"]],
    center={"lat":37.5665,"lon":126.9780},
    zoom=9.25,
    opacity=.9,
    map_style="carto-positron",
)
crime_map.update_traces(
    marker_line_width=.7,
    marker_line_color="white",
    hovertemplate=(
        "<b>%{customdata[0]}</b><br>"
        + f"<b>{selected_crime}</b> 발생: " + "%{customdata[1]:,.0f}건<br>"
        + f"<b>{selected_crime}</b> 발생률: " + "%{customdata[2]:.2f}건<br>"
        + "<br><b>범죄 유형별 발생률 (인구 1만 명당)</b><br>"
        + "전체 범죄: %{customdata[3]:.2f}건<br>"
        + "살인: %{customdata[4]:.2f}건<br>"
        + "강도: %{customdata[5]:.2f}건<br>"
        + "강간·강제추행: %{customdata[6]:.2f}건<br>"
        + "절도: %{customdata[7]:.2f}건<br>"
        + "폭력: %{customdata[8]:.2f}건"
        + "<extra></extra>"
    ),
)
crime_map.update_layout(
    title=dict(text=f"{selected_crime} 발생률", x=.02, xanchor="left", font=dict(size=17)),
    height=470,
    margin=dict(l=0,r=0,t=45,b=0),
    paper_bgcolor="white",
    plot_bgcolor="white",
    coloraxis_colorbar=dict(title="1만 명당", thickness=10, len=.7, outlinewidth=0),
)

price_map = px.choropleth_map(
    df,
    geojson=geojson,
    locations="자치구",
    featureidkey="properties.SIG_KOR_NM",
    color="제곱미터당가격중앙값",
    custom_data=["자치구","제곱미터당가격중앙값","매매가격중앙값","거래건수"],
    color_continuous_scale=[[0,"#fff8ef"],[.25,"#fde1bd"],[.5,"#f7bd78"],[.75,"#ec8d37"],[1,"#c95d12"]],
    center={"lat":37.5665,"lon":126.9780},
    zoom=9.25,
    opacity=.9,
    map_style="carto-positron",
)
price_map.update_traces(
    marker_line_width=.7,
    marker_line_color="white",
    hovertemplate=(
        "<b>%{customdata[0]}</b><br>"
        "㎡당 매매가격 중앙값: %{customdata[1]:,.1f}만원<br>"
        "매매가격 중앙값: %{customdata[2]:,.0f}만원<br>"
        "거래건수: %{customdata[3]:,.0f}건<extra></extra>"
    ),
)
price_map.update_layout(
    title=dict(text="아파트 ㎡당 매매가격 중앙값", x=.02, xanchor="left", font=dict(size=17)),
    height=470,
    margin=dict(l=0,r=0,t=45,b=0),
    paper_bgcolor="white",
    plot_bgcolor="white",
    coloraxis_colorbar=dict(title="만원/㎡", thickness=10, len=.7, outlinewidth=0),
)

with map1:
    st.plotly_chart(crime_map, use_container_width=True, config={"displayModeBar":False})
with map2:
    st.plotly_chart(price_map, use_container_width=True, config={"displayModeBar":False})

st.markdown('<div class="section-title">범죄 발생률과 아파트 가격의 관계</div>', unsafe_allow_html=True)
scatter = px.scatter(
    df,
    x=rate_col,
    y="제곱미터당가격중앙값",
    hover_name="자치구",
    custom_data=["자치구",count_col,"거래건수"],
    trendline="ols",
    labels={rate_col:f"인구 1만 명당 {selected_crime} 발생건수", "제곱미터당가격중앙값":"㎡당 매매가격 중앙값 (만원)"},
)
for trace in scatter.data:
    if trace.mode == "markers":
        trace.update(
            marker=dict(size=11,color="#5b6b8c",opacity=.85,line=dict(width=1,color="white")),
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                + f"{selected_crime} 발생률: " + "%{x:.1f}건<br>"
                + "㎡당 가격: %{y:,.1f}만원<br>"
                + f"{selected_crime} 발생건수: " + "%{customdata[1]:,.0f}건<br>"
                + "아파트 거래건수: %{customdata[2]:,.0f}건<extra></extra>"
            ),
        )
    else:
        trace.update(line=dict(width=2.2,dash="dash",color="#d04a4a"))

selected_row = df.loc[df["자치구"] == selected_gu].iloc[0]
scatter.add_trace(go.Scatter(
    x=[selected_row[rate_col]],
    y=[selected_row["제곱미터당가격중앙값"]],
    mode="markers+text",
    text=[selected_gu],
    textposition="top center",
    marker=dict(size=17,color="#1d3557",line=dict(width=2,color="white")),
    name=selected_gu,
    hoverinfo="skip",
))
scatter.update_layout(
    height=520,
    margin=dict(l=10,r=10,t=20,b=10),
    paper_bgcolor="white",
    plot_bgcolor="white",
    showlegend=False,
    xaxis=dict(gridcolor="#edf0f4",zeroline=False,title=f"인구 1만 명당 {selected_crime} 발생건수"),
    yaxis=dict(gridcolor="#edf0f4",zeroline=False,title="㎡당 매매가격 중앙값 (만원)"),
    annotations=[dict(
        x=.99,y=.98,xref="paper",yref="paper",xanchor="right",yanchor="top",
        text=f"<b>r = {r:+.3f}</b><br>p = {p_value:.4f}",
        showarrow=False,bgcolor="rgba(255,255,255,.92)",bordercolor="#e4e7ec",borderwidth=1,borderpad=8,
        font=dict(size=13,color="#3c4350"),
    )],
)
st.plotly_chart(scatter, use_container_width=True, config={"displayModeBar":False})

st.markdown("""
<div class="note-box"><b>해석 시 유의사항</b><br>
범죄율은 주민등록인구 1만 명당 발생건수로 계산했습니다. 따라서 유동인구가 많은 도심·상업지역의 특성을 완전히 반영하지 못할 수 있습니다.
또한 상관관계는 인과관계를 의미하지 않습니다.</div>
""", unsafe_allow_html=True)
