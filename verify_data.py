
import pandas as pd
import sqlite3

# 데이터베이스 파일 경로
DB_FILE = 'franchise.db'
TABLE_NAME = 'brands'

# 표시할 컬럼 선택 (10개)
COLUMNS_TO_DISPLAY = [
    'corpNm',           # 회사명
    'brandNm',          # 브랜드명
    'yr',               # 연도
    'indutyMlsfcNm',    # 산업(중분류)
    'avrgSlsAmt',       # 평균매출액
    'arUnitAvrgSlsAmt', # 면적당 평균매출액
    'frcsCnt',          # 가맹점수
    'newFrcsRgsCnt',    # 신규개점수
    'ctrtEndCnt',       # 계약종료수
    'ctrtCncltnCnt'     # 계약해지수
]

def verify_data():
    """
    DB에 저장된 데이터를 읽어와 일부를 출력합니다.
    """
    try:
        # DB에 연결
        conn = sqlite3.connect(DB_FILE)
        
        # 컬럼 목록을 SQL 쿼리용 문자열로 변환
        columns_str = ", ".join([f'"{col}"' for col in COLUMNS_TO_DISPLAY])
        
        # 데이터 조회를 위한 SQL 쿼리
        query = f"SELECT {columns_str} FROM {TABLE_NAME}"
        
        # pandas를 사용하여 쿼리 실행 및 데이터프레임으로 로드
        df = pd.read_sql_query(query, conn)
        
        print(f"'{DB_FILE}'의 '{TABLE_NAME}' 테이블 데이터 확인 (상위 5개):")
        
        # pandas 출력 옵션 설정 (컬럼이 잘리지 않게)
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', 1000)
        
        if df.empty:
            print("테이블에 데이터가 없습니다.")
        else:
            print(df.head())

    except sqlite3.Error as e:
        print(f"데이터베이스 오류: {e}")
    except Exception as e:
        print(f"오류 발생: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == "__main__":
    verify_data()
