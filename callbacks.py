
from dash.dependencies import Input, Output, State, ALL
from dash import html, dcc, dash
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
import plotly.express as px
import sqlite3
import glob
import os

# 프로젝트의 다른 파일에서 함수들을 가져옵니다.
from data_collector import collect_and_save_data
from visualizations import create_matplotlib_figure, fig_to_base64, create_brand_rank_chart

def register_callbacks(app):
    # 1. 데이터 수집 및 스키마 표시 콜백
    @app.callback(
        Output('collection-status-output', 'children'),
        Input('start-collection-button', 'n_clicks'),
        State('api-url-input', 'value'),
        State('db-name-input', 'value'),
        State('start-year-input', 'value'),
        State('end-year-input', 'value'),
        State('delay-input', 'value'),
        prevent_initial_call=True
    )
    def handle_data_collection(n_clicks, api_url, db_name, start_year, end_year, delay):
        if not all([api_url, db_name, start_year, end_year, delay is not None]):
            return "API URL, DB 파일 이름, 시작/종료 연도, 지연 시간을 모두 입력해주세요."

        # 데이터 수집 함수 호출
        log_output = collect_and_save_data(api_url, db_name, start_year, end_year, delay)

        # 성공적으로 수집되었는지 확인
        if "성공!" in log_output:
            try:
                if not db_name.endswith('.db'):
                    db_name += '.db'
                table_name = os.path.splitext(db_name)[0]

                conn = sqlite3.connect(db_name)
                
                # 1. 스키마 정보 가져오기
                schema_df = pd.read_sql_query(f'PRAGMA table_info("{table_name}")', conn)
                schema_table = dbc.Table.from_dataframe(
                    schema_df[['name', 'type']], 
                    striped=True, bordered=True, hover=True,
                    header=['칼럼명', '데이터 타입']
                )

                # 2. 샘플 데이터 가져오기
                sample_df = pd.read_sql_query(f'SELECT * FROM "{table_name}" LIMIT 5', conn)
                sample_table = dbc.Table.from_dataframe(
                    sample_df, striped=True, bordered=True, hover=True, responsive=True
                )
                
                conn.close()

                # 최종 결과물 조합
                return html.Div([
                    html.Pre(log_output),
                    html.Hr(),
                    html.H4("📋 DB 스키마 정보"),
                    schema_table,
                    html.Hr(),
                    html.H4("📊 샘플 데이터 (상위 5개)"),
                    sample_table
                ])

            except Exception as e:
                return html.Div([
                    html.Pre(log_output),
                    html.Hr(),
                    dbc.Alert(f"DB 정보 조회 중 오류 발생: {e}", color="danger")
                ])
        
        # 실패 시 로그만 반환
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

    # 3. 엑셀 다운로드 버튼 활성화/비활성화
    @app.callback(
        Output('download-excel-button', 'disabled'),
        Input('dataset-dropdown', 'value')
    )
    def toggle_download_button(db_file):
        return db_file is None

    # 4. 엑셀 파일 다운로드
    @app.callback(
        Output('download-excel', 'data'),
        Input('download-excel-button', 'n_clicks'),
        State('dataset-dropdown', 'value'),
        prevent_initial_call=True
    )
    def download_excel_file(n_clicks, db_file):
        if not db_file:
            return None
        
        excel_path = os.path.splitext(db_file)[0] + '.xlsx'
        if not os.path.exists(excel_path):
            return None 
            
        return dcc.send_file(excel_path)

    # 5. 계층 필터 레이아웃 생성 (직접 연결 방식)
    @app.callback(
        Output('h-filter-container-0', 'children'),
        Output('h-filter-container-1', 'children'),
        Output('h-filter-container-2', 'children'),
        Output('h-filter-container-3', 'children'),
        Output('h-filter-container-4', 'children'),
        Output('h-filter-cols', 'data'),
        Input('dataset-dropdown', 'value'),
        prevent_initial_call=True
    )
    def generate_filters_layout(db_file):
        if not db_file:
            return [None] * 5 + [None]

        try:
            conn = sqlite3.connect(db_file)
            table_name = os.path.splitext(os.path.basename(db_file))[0]
            df_schema = pd.read_sql_query(f'SELECT * FROM "{table_name}" LIMIT 1', conn)

            h_cols = []
            for col in df_schema.columns:
                is_numeric = pd.api.types.is_numeric_dtype(df_schema[col].dtype)
                if is_numeric and col != 'yr':
                    break
                h_cols.append(col)
                if len(h_cols) >= 5:
                    break
            
            filters = [None] * 5
            for i, col in enumerate(h_cols):
                options = []
                if i == 0:
                    query = f'SELECT DISTINCT "{col}" FROM "{table_name}" ORDER BY "{col}" DESC' if col == 'yr' else f'SELECT DISTINCT "{col}" FROM "{table_name}" ORDER BY "{col}" ASC'
                    options_df = pd.read_sql_query(query, conn)
                    options = [{'label': opt, 'value': opt} for opt in options_df[col].dropna()]

                filters[i] = html.Div([
                    dbc.Label(col),
                    dcc.Dropdown(id=f'h-filter-{i}', options=options, multi=True, placeholder=f'{col} 선택...'),
                    html.Br()
                ])
            
            conn.close()
            return filters[0], filters[1], filters[2], filters[3], filters[4], h_cols
        except Exception as e:
            print(f"필터 레이아웃 생성 오류: {e}")
            return [None] * 5 + [None]

    # 6. 연계 필터 콜백 체인 (최대 5단계)
    def create_cascading_callback(level):
        @app.callback(
            Output(f'h-filter-{level}', 'options'),
            Output(f'h-filter-{level}', 'value'),
            Input(f'h-filter-{level-1}', 'value'),
            [State(f'h-filter-{j}', 'value') for j in range(level-1)],
            State('dataset-dropdown', 'value'),
            State('h-filter-cols', 'data'),
            prevent_initial_call=True
        )
        def update_options(parent_value, *args):
            # *args를 사용하여 모든 State 인자를 튜플로 받음
            # 마지막 두 인자는 db_file, h_cols로 고정됨
            db_file = args[-2]
            h_cols = args[-1]
            grandparent_values = args[:-2]

            if not parent_value or not db_file or not h_cols or level >= len(h_cols):
                return [], None

            conn = sqlite3.connect(db_file)
            table_name = os.path.splitext(os.path.basename(db_file))[0]
            current_col = h_cols[level]

            all_parent_vals = list(grandparent_values) + [parent_value]
            
            where_clauses = []
            params = []
            for i, val_list in enumerate(all_parent_vals):
                if val_list:
                    col_name = h_cols[i]
                    placeholders = ', '.join('?' for _ in val_list)
                    where_clauses.append(f'"{col_name}" IN ({placeholders})')
                    params.extend(val_list)

            query = f'SELECT DISTINCT "{current_col}" FROM "{table_name}"'
            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)
            query += f' ORDER BY "{current_col}" ASC'

            try:
                df = pd.read_sql_query(query, conn, params=params)
                options = [{'label': i, 'value': i} for i in df[current_col].dropna()]
                return options, None
            finally:
                conn.close()
        return update_options

    for i in range(1, 5):
        create_cascading_callback(i)

    # 7. 차트 빌더 옵션 업데이트
    @app.callback(
        Output('chart-builder-xaxis', 'options'),
        Output('chart-builder-yaxis', 'options'),
        Output('chart-builder-group', 'options'),
        Input('dataset-dropdown', 'value'),
        prevent_initial_call=True
    )
    def update_chart_builder_options(db_file):
        if not db_file:
            return [], [], []
        
        conn = sqlite3.connect(db_file)
        table_name = os.path.splitext(os.path.basename(db_file))[0]
        df = pd.read_sql_query(f'SELECT * FROM "{table_name}" LIMIT 5', conn)
        conn.close()

        numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
        categorical_cols = df.select_dtypes(exclude=np.number).columns.tolist()

        cat_options = [{'label': col, 'value': col} for col in categorical_cols]
        num_options = [{'label': col, 'value': col} for col in numeric_cols]
        
        return cat_options, num_options, cat_options

    # 8. 최종 그래프 생성 콜백
    @app.callback(
        Output('visualization-graph', 'figure'),
        Input('update-graph-button', 'n_clicks'),
        State('dataset-dropdown', 'value'),
        # Chart builder states
        State('chart-builder-chart-type', 'value'),
        State('chart-builder-xaxis', 'value'),
        State('chart-builder-yaxis', 'value'),
        State('chart-builder-agg', 'value'),
        State('chart-builder-group', 'value'),
        State('chart-builder-top-n', 'value'), # Top N 추가
        # Filter states
        State('h-filter-cols', 'data'),
        [State(f'h-filter-{i}', 'value') for i in range(5)],
        prevent_initial_call=True
    )
    def update_graph_final(n_clicks, db_file, chart_type, xaxis, yaxis, agg, group, top_n, h_cols, filter_values):
        if not all([db_file, chart_type, xaxis, agg]):
            return px.bar(title="차트 빌더의 모든 필수 항목(차트 종류, X축, Y축 집계 방식)을 선택해주세요.")
        
        if agg != 'count' and not yaxis:
            return px.bar(title="'개수(Count)'가 아닌 집계 방식에는 Y축을 반드시 선택해야 합니다.")

        # 1. 데이터 로드 및 필터링
        conn = sqlite3.connect(db_file)
        table_name = os.path.splitext(os.path.basename(db_file))[0]
        df = pd.read_sql_query(f'SELECT * FROM "{table_name}"', conn)
        conn.close()

        if h_cols:
            for i, vals in enumerate(filter_values):
                if vals and i < len(h_cols):
                    col_name = h_cols[i]
                    df = df[df[col_name].isin(vals)]
        
        if df.empty:
            return px.bar(title="필터 결과에 해당하는 데이터가 없습니다.")

        # 2. 데이터 집계
        group_by_cols = [xaxis]
        if group and group != xaxis:
            group_by_cols.append(group)
        
        try:
            if agg == 'count':
                agg_df = df.groupby(group_by_cols).size().reset_index(name='count')
                yaxis = 'count'
            else:
                agg_df = df.groupby(group_by_cols)[yaxis].agg(agg).reset_index()
        except Exception as e:
            return px.bar(title=f"데이터 집계 중 오류 발생: {e}")

        # 3. 정렬 및 상위 N개 선택
        # 파이 차트가 아닐 경우에만 정렬 적용
        if chart_type != 'pie':
            agg_df = agg_df.sort_values(by=yaxis, ascending=False)
            if top_n and top_n > 0:
                agg_df = agg_df.head(top_n)

        # 4. 차트 생성
        try:
            title = f'{xaxis} 별 {yaxis} {agg} 분석'
            if top_n and top_n > 0:
                title += f' (상위 {top_n}개)'

            if chart_type == 'bar':
                fig = px.bar(agg_df, x=xaxis, y=yaxis, color=group, barmode='group', title=title)
            elif chart_type == 'line':
                fig = px.line(agg_df, x=xaxis, y=yaxis, color=group, title=title)
            elif chart_type == 'pie':
                if group: # 파이차트는 그룹화 미지원
                    return px.bar(title="파이 차트는 그룹화(색상) 기능을 지원하지 않습니다.")
                # 파이차트는 상위 N개 로직을 다르게 적용해야 할 수 있음 (여기서는 집계 후 전체 비율 표시)
                pie_df = df.groupby(xaxis)[yaxis].agg(agg).reset_index()
                if top_n and top_n > 0:
                    pie_df = pie_df.sort_values(by=yaxis, ascending=False).head(top_n)
                fig = px.pie(pie_df, names=xaxis, values=yaxis, title=title)
            else:
                fig = px.bar(title="알 수 없는 차트 종류")
        except Exception as e:
            return px.bar(title=f"차트 생성 중 오류 발생: {e}")

        return fig
