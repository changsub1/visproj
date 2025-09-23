
from dash.dependencies import Input, Output, State
from dash import html, dcc
import dash_bootstrap_components as dbc
import pandas as pd
import sqlite3
import glob
import os

# 프로젝트의 다른 파일에서 함수들을 가져옵니다.
from data_collector import collect_and_save_data
from visualizations import create_matplotlib_figure, fig_to_base64, create_brand_rank_chart

def register_callbacks(app):
    # 1. 데이터 수집 콜백 (단순 동기 방식)
    @app.callback(
        Output('collection-status-output', 'children'),
        Input('start-collection-button', 'n_clicks'),
        State('api-url-input', 'value'),
        State('db-name-input', 'value'),
        State('start-year-input', 'value'),
        State('end-year-input', 'value'),
        prevent_initial_call=True
    )
    def handle_data_collection(n_clicks, api_url, db_name, start_year, end_year):
        if not all([api_url, db_name, start_year, end_year]):
            return "API URL, DB 파일 이름, 시작 연도, 종료 연도를 모두 입력해주세요."
        
        # 데이터 수집 함수를 호출하고 로그를 반환받음
        log_output = collect_and_save_data(api_url, db_name, start_year, end_year)
        
        # 줄바꿈이 유지되도록 html.Pre 사용
        return html.Pre(log_output)

    # 2. 데이터셋 드롭다운 메뉴 업데이트 콜백
    @app.callback(
        Output('dataset-dropdown', 'options'),
        Input('main-tabs', 'active_tab')
    )
    def update_dataset_dropdown(tab_id):
        if tab_id == 'tab-visualize':
            db_files = glob.glob('*.db')
            return [{'label': os.path.basename(f), 'value': f} for f in db_files]
        return []

    # 3. 동적 필터 옵션 업데이트 (오류 방지 기능 강화)
    @app.callback(
        Output('year-filter-dropdown', 'options'),
        Output('industry-filter-dropdown', 'options'),
        Input('dataset-dropdown', 'value'),
        prevent_initial_call=True
    )
    def update_filter_options(db_file):
        if not db_file:
            return [], []
        
        try:
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            # 테이블이 아직 생성되지 않았거나, 비어있을 경우 오류 방지
            if not tables:
                conn.close()
                return [], []
                
            table_name = tables[0][0]
            
            # 필요한 컬럼이 있는지 확인
            df_cols = pd.read_sql(f'SELECT * FROM "{table_name}" LIMIT 1', conn)
            conn.close()

            year_options = []
            industry_options = []

            if 'yr' in df_cols.columns:
                years = pd.unique(df_cols['yr'])
                year_options = [{'label': y, 'value': y} for y in sorted(years, reverse=True)]
            
            if 'indutyMlsfcNm' in df_cols.columns:
                industries = pd.unique(df_cols['indutyMlsfcNm'])
                industry_options = [{'label': i, 'value': i} for i in sorted(industries)]
            
            return year_options, industry_options
        except Exception as e:
            print(f"필터 옵션 생성 오류: {e}")
            return [], []

    # 4. 시각화 그래프 업데이트 콜백 (필터링 기능 추가)
    @app.callback(
        Output('visualization-graph', 'src'),
        Input('dataset-dropdown', 'value'),
        Input('chart-type-dropdown', 'value'),
        Input('year-filter-dropdown', 'value'),
        Input('industry-filter-dropdown', 'value'),
        prevent_initial_call=True
    )
    def update_graph(db_file, chart_type, selected_years, selected_industries):
        if not all([db_file, chart_type]):
            return ""

        try:
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            table_name = cursor.fetchall()[0][0]
            df = pd.read_sql_query(f'SELECT * FROM "{table_name}"', conn)
            conn.close()

            # 필터링 적용
            filtered_df = df.copy()
            if selected_years:
                filtered_df = filtered_df[filtered_df['yr'].isin(selected_years)]
            if selected_industries:
                filtered_df = filtered_df[filtered_df['indutyMlsfcNm'].isin(selected_industries)]

            if filtered_df.empty:
                return ""

            # 선택된 차트 종류에 따라 적절한 시각화 함수를 호출
            if chart_type == 'rank_brand':
                fig = create_brand_rank_chart(filtered_df)
            else:
                fig = create_matplotlib_figure(filtered_df)
            
            return fig_to_base64(fig)
        
        except Exception as e:
            print(f"그래프 생성 오류: {e}")
            return ""
