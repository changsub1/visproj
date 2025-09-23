
import matplotlib.pyplot as plt
import io
import base64
import pandas as pd

# 한글 폰트가 깨지지 않도록 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

def create_brand_rank_chart(df):
    """평균 매출액 기준 상위 15개 브랜드 순위 차트(가로 막대그래프)를 생성합니다."""
    
    # 데이터 타입 변환 (오류 발생 시 0으로 처리)
    df['avrgSlsAmt'] = pd.to_numeric(df['avrgSlsAmt'], errors='coerce').fillna(0)
    
    # 평균 매출액으로 정렬하여 상위 15개 선택
    top_brands = df.sort_values(by='avrgSlsAmt', ascending=False).head(15)
    
    # 그래프 생성
    fig, ax = plt.subplots(figsize=(10, 8))
    
    ax.barh(top_brands['brandNm'], top_brands['avrgSlsAmt'])
    ax.invert_yaxis()  # 상위 브랜드가 위로 오도록 y축 순서 뒤집기
    ax.set_xlabel('평균 매출액 (단위: 천원)')
    ax.set_title('브랜드별 평균 매출액 순위 (상위 15)')
    
    # 레이아웃을 타이트하게 조정
    fig.tight_layout()
    
    return fig

def create_matplotlib_figure(data):
    """matplotlib Figure 객체를 생성합니다. (기존 예시 함수)"""
    fig, ax = plt.subplots()
    sample_labels = ['A', 'B', 'C', 'D']
    sample_values = [10, 20, 15, 25]
    ax.bar(sample_labels, sample_values)
    ax.set_title("Sample Bar Chart")
    ax.set_xlabel("Category")
    ax.set_ylabel("Value")
    return fig

def fig_to_base64(fig):
    """matplotlib Figure를 base64 인코딩된 이미지 문자열로 변환합니다."""
    img_buf = io.BytesIO()
    fig.savefig(img_buf, format='png')
    img_buf.seek(0)
    base64_string = base64.b64encode(img_buf.read()).decode('utf-8')
    return f'data:image/png;base64,{base64_string}'
