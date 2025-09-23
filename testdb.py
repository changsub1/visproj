import requests
import pandas as pd
import time
import math
import sqlite3
import json
import os
from dotenv import load_dotenv

# .env 파일에서 환경 변수를 로드합니다.
load_dotenv()

# --- 1. 데이터 수집 ---

# 🔑 .env 파일에서 서비스 키를 가져옵니다.
service_key = os.getenv("SERVICE_KEY")
all_data = []

# 예시: 2015년부터 2024년까지 데이터 수집
for year in range(2015, 2025):
    page_no = 1
    num_of_rows = 100
    total_pages = 1 # 우선 1페이지로 초기화
    
    print(f"--- {year}년 데이터 수집 시작 ---")

    while page_no <= total_pages:
        url = "http://apis.data.go.kr/1130000/FftcBrandFrcsStatsService/getBrandFrcsStats"
        params = {
            "serviceKey": service_key,
            "yr": year, # 파라미터를 'year'에서 'yr'로 다시 변경
            "resultType": "json",
            "numOfRows": num_of_rows,
            "pageNo": page_no
        }
        
        try:
            response = requests.get(url, params=params)
            # HTTP 상태 코드가 200 (OK)이 아니면 에러를 발생시킴
            response.raise_for_status()
            
            # 서버 응답을 JSON으로 변환
            data = response.json()
            
            items = data.get('items', [])
            total_count = data.get('totalCount', 0)

            if not items and page_no == 1:
                print(f"{year}년 데이터 없음.")
                break # 해당 연도에 데이터가 없으면 중단하고 다음 연도로

            if items:
                all_data.extend(items)
                
                # 첫 페이지를 요청했을 때만 전체 페이지 수를 다시 계산
                if page_no == 1:
                    total_pages = math.ceil(total_count / num_of_rows)
                
                print(f"{year}년: {page_no} / {total_pages} 페이지 수집 완료 (현재까지 총 {len(all_data)}건)")
            
            page_no += 1 # 다음 페이지로
            
            # 마지막 페이지가 아니면 API 서버에 부담을 주지 않기 위해 1초 대기
            if page_no <= total_pages:
                time.sleep(1)

        # JSON 디코딩 오류 발생 시 서버의 원본 응답을 출력
        except json.JSONDecodeError:
            print(f"{year}년, {page_no}페이지: JSON 디코딩 오류 발생! 서버가 JSON이 아닌 다른 응답을 보냈습니다.")
            print("▼ 서버 원본 응답 ▼")
            print(response.text)
            print("▲----------------▲")
            break # 해당 연도는 더 이상 진행하지 않고 중단
            
        # 요청 관련 오류 발생 시
        except requests.exceptions.RequestException as e:
            print(f"{year}년, {page_no}페이지 데이터 수집 중 요청 오류 발생: {e}")
            break # 해당 연도는 더 이상 진행하지 않고 중단

print(f"\n--- 총 {len(all_data)}건의 데이터 수집 완료! ---")


# --- 2. 데이터 가공 및 DB 저장 ---

if all_data: # 수집된 데이터가 있을 경우에만 진행
    full_df = pd.DataFrame(all_data)

    # 숫자 컬럼 변환
    numeric_cols = ['frcsCnt', 'newFrcsRgsCnt', 'ctrtEndCnt', 'ctrtCncltnCnt', 'nmChgCnt', 'avrgSlsAmt', 'arUnitAvrgSlsAmt']
    for col in numeric_cols:
        full_df[col] = pd.to_numeric(full_df[col], errors='coerce').fillna(0) # 빈 값은 0으로 채움

    # 'franchise.db'라는 이름의 데이터베이스 파일에 연결
    conn = sqlite3.connect('franchise.db')

    # DataFrame을 'brands'라는 이름의 테이블에 저장
    full_df.to_sql('brands', conn, if_exists='replace', index=False)

    print("\n데이터프레임을 'franchise.db' 파일의 'brands' 테이블에 성공적으로 저장했습니다.")

    # --- 3. DB에서 데이터 읽어오기 테스트 ---
    query = "SELECT COUNT(*) FROM brands"
    count_result = pd.read_sql(query, conn)
    print(f"\n[DB 저장 확인] DB에 저장된 총 데이터 수: {count_result.iloc[0,0]}건")

    conn.close()
else:
    print("\n수집된 데이터가 없어 DB 작업을 진행하지 않았습니다.")