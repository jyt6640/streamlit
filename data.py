import requests
import pandas as pd
import json
from dotenv import load_dotenv
import os
import numpy as np
import schedule
import time

# .env 파일에서 API_KEY 로드
load_dotenv()
api_key = os.getenv("API_KEY")

if not api_key:
    raise ValueError("'.env' 파일에 'API_KEY'가 설정되지 않았습니다.")

# API URL 및 키 설정
api_url = "http://apis.data.go.kr/B552584/ArpltnStatsSvc/getCtprvnMesureSidoLIst"
sido_names = ["서울", "인천", "울산", "대전", "부산", "광주", "대구"]

# 대기질 평가 함수 정의
def evaluate_air_quality_with_score(row):
    scores = []
    if row["so2Value"] <= 0.02:
        scores.append(1)
    elif row["so2Value"] <= 0.05:
        scores.append(2)
    elif row["so2Value"] <= 0.15:
        scores.append(3)
    else:
        scores.append(4)
    
    if row["coValue"] <= 2.0:
        scores.append(1)
    elif row["coValue"] <= 9.0:
        scores.append(2)
    elif row["coValue"] <= 15.0:
        scores.append(3)
    else:
        scores.append(4)
    
    if row["o3Value"] <= 0.03:
        scores.append(1)
    elif row["o3Value"] <= 0.09:
        scores.append(2)
    elif row["o3Value"] <= 0.15:
        scores.append(3)
    else:
        scores.append(4)
    
    if row["no2Value"] <= 0.03:
        scores.append(1)
    elif row["no2Value"] <= 0.06:
        scores.append(2)
    elif row["no2Value"] <= 0.20:
        scores.append(3)
    else:
        scores.append(4)
    
    if row["pm10Value"] <= 30:
        scores.append(1)
    elif row["pm10Value"] <= 80:
        scores.append(2)
    elif row["pm10Value"] <= 150:
        scores.append(3)
    else:
        scores.append(4)
    
    if row["pm25Value"] <= 15:
        scores.append(1)
    elif row["pm25Value"] <= 35:
        scores.append(2)
    elif row["pm25Value"] <= 75:
        scores.append(3)
    else:
        scores.append(4)
    
    total_score = sum(scores) / len(scores)
    if total_score <= 1.5:
        return total_score, "매우 좋음"
    elif total_score <= 2.5:
        return total_score, "좋음"
    elif total_score <= 3.5:
        return total_score, "보통"
    elif total_score <= 4.0:
        return total_score, "나쁨"
    else:
        return total_score, "매우 나쁨"

# 데이터 수집 및 저장 함수
def save_air_quality_data():
    all_data = []
    for sido in sido_names:
        params = {
            "serviceKey": api_key,
            "returnType": "json",
            "numOfRows": 100,
            "pageNo": 1,
            "sidoName": sido,
            "searchCondition": "DAILY",
        }
        try:
            response = requests.get(api_url, params=params)
            response.raise_for_status()
            data = response.json()

            if "response" in data and "body" in data["response"]:
                items = data["response"]["body"]["items"]
                df = pd.DataFrame(items)
                df["sidoName"] = sido
                all_data.append(df)
            else:
                print(f"{sido} 지역 데이터가 없습니다.")
        except requests.exceptions.RequestException as e:
            print(f"{sido} 데이터 요청 중 오류 발생: {e}")

    final_df = pd.concat(all_data, ignore_index=True)
    columns_of_interest = [
        "dataTime", "sidoName", "cityName", "so2Value", "coValue", "o3Value",
        "no2Value", "pm10Value", "pm25Value"
    ]
    final_df = final_df[columns_of_interest]

    numeric_columns = ["so2Value", "coValue", "o3Value", "no2Value", "pm10Value", "pm25Value"]
    for col in numeric_columns:
        final_df[col] = pd.to_numeric(final_df[col], errors="coerce")

    mean_values = final_df.groupby(["sidoName", "dataTime"])[numeric_columns].mean().reset_index()
    mean_values[["통합스코어", "대기질평가"]] = mean_values.apply(
        lambda row: pd.Series(evaluate_air_quality_with_score(row)), axis=1
    )

    final_data = mean_values[["sidoName", "dataTime", "통합스코어", "대기질평가", "pm10Value", "pm25Value"]]
    final_data_last_time = final_data.loc[final_data.groupby("sidoName")["dataTime"].idxmax()]

    file_name = f"air_quality.json"
    final_data_last_time.to_json(file_name, orient="records", force_ascii=False)
    print(f"데이터 저장 완료: {file_name}")

# 프로그램 실행 시 최초 데이터 저장
print("프로그램 실행 중... 초기 데이터를 저장합니다.")
save_air_quality_data()

# 스케줄 설정
schedule.every(1).hour.do(save_air_quality_data)

print("스케줄러 시작... 한 시간마다 데이터를 저장합니다.")
while True:
    schedule.run_pending()
    time.sleep(1)
