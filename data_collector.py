
import requests
import pandas as pd
import sqlite3
import time
import math
import os
from urllib.parse import urlparse, parse_qs

def collect_and_save_data(api_url, db_name, start_year, end_year, delay=1.0):
    """
    지정된 기간 동안 API 데이터를 수집하여 사용자가 지정한 이름의 SQLite DB에 저장합니다.
    진행 로그를 문자열로 반환합니다.
    """
    all_data = []
    log_messages = []
    
    # 사용자가 입력한 DB 이름에 .db 확장자가 없으면 추가합니다.
    if not db_name.endswith('.db'):
        db_name += '.db'

    # 테이블 이름은 파일명에서 확장자를 제외한 부분으로 사용합니다.
    table_name = os.path.splitext(db_name)[0]

    # .env 파일에서 서비스 키를 가져옵니다.
    from dotenv import load_dotenv
    load_dotenv()
    service_key = os.getenv("SERVICE_KEY")

    if not service_key or service_key == "YOUR_API_KEY_HERE":
        return f"오류: .env 파일에 유효한 SERVICE_KEY가 설정되지 않았습니다."

    years_to_collect = list(range(start_year, end_year + 1))

    for year in years_to_collect:
        log_messages.append(f"--- {year}년 데이터 수집 시작 ---")
        page_no = 1
        num_of_rows = 100

        while True:
            params = {
                'serviceKey': service_key,
                'resultType': 'json',
                'numOfRows': num_of_rows,
                'pageNo': page_no
            }
            params['yr'] = year

            try:
                response = requests.get(api_url, params=params)
                response.raise_for_status()
                data = response.json()

                body = data.get('response', {}).get('body', {})
                if not body:
                    body = data

                items = body.get('items', [])
                total_count = int(body.get('totalCount', 0))

                if page_no == 1 and total_count == 0:
                    log_messages.append(f"{year}년 데이터 없음 (totalCount: 0). 서버 응답: {body}")
                    break

                if isinstance(items, dict) and 'item' in items:
                    items = items.get('item', [])
                
                if isinstance(items, dict):
                    items = [items]

                if not items:
                    log_messages.append(f"{year}년 데이터 수집 완료.")
                    break

                all_data.extend(items)
                log_messages.append(f"{year}년: {page_no} 페이지 수집... (현재까지 총 {len(all_data)}건)")
                
                page_no += 1
                time.sleep(delay)
            
            except requests.exceptions.JSONDecodeError:
                log_messages.append(f"JSON 디코딩 오류. 서버 원본 응답: {response.text}")
                break # 해당 연도는 중단
            except requests.exceptions.RequestException as e:
                log_messages.append(f"요청 오류 발생: {e}")
                break # 해당 연도는 중단

    final_log = "\n".join(log_messages)

    if not all_data:
        return f"수집된 데이터가 없습니다.\n\n--- 로그 ---\n{final_log}"

    try:
        df = pd.DataFrame(all_data)
        # 데이터 타입 자동 변환: 숫자 칼럼은 숫자로, 나머지는 문자로 처리
        for col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='ignore')
        
        # 1. DB에 저장
        conn = sqlite3.connect(db_name)
        df.to_sql(table_name, conn, if_exists='replace', index=False)
        conn.close()

        # 2. 엑셀 파일로 저장
        excel_path = os.path.splitext(db_name)[0] + '.xlsx'
        df.to_excel(excel_path, index=False)
        
        return f"성공! 총 {len(all_data)}건의 데이터를 '{db_name}' 및 '{excel_path}' 파일에 저장했습니다.\n\n--- 로그 ---\n{final_log}"
    except Exception as e:
        return f"DB 또는 엑셀 저장 중 오류 발생: {e}\n\n--- 로그 ---\n{final_log}"
