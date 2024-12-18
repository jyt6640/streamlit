import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime
import json

# JSON 파일 읽기
with open('air_quality.json', 'r', encoding='utf-8') as file:
    json_data = json.load(file)

# JSON 데이터를 데이터프레임으로 변환
df_json = pd.DataFrame(json_data)

# 지역데이터터
additional_data = {
    "region": ["광주", "대구", "대전", "부산", "서울", "울산", "인천"],
    "lat": [35.1595, 35.8722, 36.3504, 35.1796, 37.5665, 35.5384, 37.4563],
    "lng": [126.9780, 128.6014, 127.3845, 129.0756, 126.7052, 129.3114, 126.8526],
}
df_additional = pd.DataFrame(additional_data)

# 데이터 결합
df = pd.merge(df_json, df_additional, left_on="sidoName", right_on="region", how="left")

# Streamlit 설정
st.set_page_config(
    page_title="대기질 시각화 시스템 🌟",
    page_icon="🌬️",
    layout="wide",
)

# 색상 기준 함수
def get_color(pm10):
    if pm10 <= 30:
        return "#00ff88"  # 녹색
    elif pm10 <= 80:
        return "#ffff00"  # 노란색
    elif pm10 <= 150:
        return "#ff9900"  # 주황색
    else:
        return "#ff0000"  # 빨간색

# 지도 생성 함수
def create_map_html(df, selected_region=None):
    polygons_data = []
    for _, row in df.iterrows():
        color = get_color(row["pm10Value"])
        polygons_data.append({
            'lat': row["lat"],
            'lng': row["lng"],
            'color': color,
            'opacity': 0.7,
            'region': row["region"],
            'pm10': row["pm10Value"],
            'pm25': row["pm25Value"],
        })

    if selected_region:
        center_lat = df[df["region"] == selected_region]["lat"].iloc[0]
        center_lng = df[df["region"] == selected_region]["lng"].iloc[0]
    else:
        center_lat = df["lat"].mean()
        center_lng = df["lng"].mean()

    html = f"""
    <div id="map" style="width:100%;height:600px;"></div>
    <script type="text/javascript" src="https://dapi.kakao.com/v2/maps/sdk.js?appkey=bdf86abb0427674d9d321fc6401555db"></script>
    <script>
        var mapContainer = document.getElementById('map');
        var options = {{
            center: new kakao.maps.LatLng({center_lat}, {center_lng}),
            level: 12
        }};
        var map = new kakao.maps.Map(mapContainer, options);

        var polygons = {str(polygons_data)};
        polygons.forEach(function(data) {{
            var circle = new kakao.maps.Circle({{
                center: new kakao.maps.LatLng(data.lat, data.lng),
                radius: 30000,
                strokeWeight: 2,
                strokeColor: data.color,
                strokeOpacity: 0.8,
                strokeStyle: 'solid',
                fillColor: data.color,
                fillOpacity: data.opacity
            }});
            
            var content = '<div style="padding:15px;background:rgba(45,45,45,0.9);color:white;border-radius:10px;min-width:200px;box-shadow:0 4px 6px rgba(0,0,0,0.3);border:1px solid rgba(255,255,255,0.2)">' +
                          '<h3 style="color:#00ff88;margin:0 0 10px 0;">' + data.region + '</h3>' +
                          '<div style="margin:5px 0;"><span style="color:#aaa;">미세먼지(PM10):</span> <span style="color:white;font-weight:bold;">' + data.pm10 + ' µg/m³</span></div>' +
                          '<div style="margin:5px 0;"><span style="color:#aaa;">초미세먼지(PM2.5):</span> <span style="color:white;font-weight:bold;">' + data.pm25 + ' µg/m³</span></div>' +
                          '</div>';
            
            var overlay = new kakao.maps.CustomOverlay({{
                content: content,
                position: new kakao.maps.LatLng(data.lat, data.lng),
                yAnchor: 1.5,
                zIndex: 3
            }});
            
            kakao.maps.event.addListener(circle, 'click', function() {{
                overlay.setMap(map);
                setTimeout(function() {{
                    overlay.setMap(null);
                }}, 3000);
            }});
            
            circle.setMap(map);
        }});
    </script>
    """
    return html

# 앱 제목
st.title("🌟 실시간 대기질 모니터링 시스템")

# 데이터셋 표시
st.subheader("📋 대기질 데이터")
st.dataframe(df)

# 선택 옵션
with st.sidebar:
    st.header("⚙️ 설정")
    selected_region = st.selectbox("지역 선택:", df["region"].dropna().unique())
    st.write(f"마지막 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

# 선택된 지역 데이터
region_data = df[df["region"] == selected_region].iloc[0]
current_pm10 = region_data["pm10Value"]
current_pm25 = region_data["pm25Value"]

# 지역별 데이터 요약 및 지도 표시
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📍 대기질 지도")
    st.caption("지도에서 지역을 클릭하면 상세 정보를 확인할 수 있습니다.")
    components.html(create_map_html(df, selected_region), height=600)

with col2:
    st.subheader(f"{selected_region} 대기질 정보")
    st.metric("미세먼지(PM10)", f"{current_pm10} µg/m³")
    st.metric("초미세먼지(PM2.5)", f"{current_pm25} µg/m³")

    # 대기질 상태 메시지
    if current_pm10 > 150:
        st.error("⚠️ 매우 나쁨: 실외 활동을 자제하세요.")
    elif current_pm10 > 80:
        st.warning("⚠️ 나쁨: 민감군은 실외 활동을 자제하세요.")
    elif current_pm10 > 30:
        st.info("ℹ️ 보통: 평소와 같은 실외 활동이 가능합니다.")
    else:
        st.success("✅ 좋음: 대기질이 좋습니다!")
        
st.subheader("🏥 건강 정보")
if current_pm10 > 150:
    st.markdown("""
    - 외출을 삼가세요.
    - KF94 이상의 마스크를 착용하세요.
    """)
elif current_pm10 > 80:
    st.markdown("""
    - 장시간 실외 활동을 줄이세요.
    - 민감군은 외출 시 주의하세요.
    """)
else:
    st.markdown("""
    - 대기질이 좋아 일상 활동이 가능합니다.
    - 환기하기 좋은 날입니다.
    """)
