from dash import dcc, html
import dash_bootstrap_components as dbc

def create_config_tab():
    """'DB 구성' 탭의 레이아웃을 생성합니다."""
    return dbc.Card(
        dbc.CardBody([
            html.H3('데이터 수집 설정', className="card-title"),
            dbc.Row([
                dbc.Col(dbc.Input(id='api-url-input', type='text', placeholder='API URL을 입력하세요...'), width=12),
            ], className="mb-3"),
            dbc.Row([
                dbc.Col(dbc.Input(id='db-name-input', type='text', placeholder='저장할 DB 파일 이름 (예: 창업비용)'), width=12),
            ], className="mb-3"),
            dbc.Row([
                dbc.Col(dbc.Input(id='start-year-input', type='number', placeholder='시작 연도 (예: 2017)'), width=6),
                dbc.Col(dbc.Input(id='end-year-input', type='number', placeholder='종료 연도 (예: 2024)'), width=6),
            ], className="mb-3"),
            dbc.Row([
                dbc.Col([
                    dbc.Label("호출 지연 시간(초):", html_for="delay-input"),
                    dbc.Input(
                        id='delay-input', 
                        type='number', 
                        value=1.0, 
                        min=0, 
                        step=0.1
                    )
                ])
            ], className="mb-3"),
            dbc.Button('데이터 수집 시작', id='start-collection-button', n_clicks=0, color="primary"),
            html.Hr(),
            # 진행률 표시 바 (이제 사용하지 않음)
            # dbc.Progress(id="collection-progress", style={"height": "20px", "marginTop": "10px"}),
            html.Hr(),
            # 데이터 수집 상태 메시지 표시 영역
            dcc.Loading(
                id="loading-collection",
                type="default",
                children=html.Div(id='collection-status-output')
            )
        ])
    )

def create_visualize_tab():
    """'시각화' 탭의 레이아웃을 생성합니다."""
    return html.Div([ # 모든 요소를 하나의 Div로 감싸서 반환
        dbc.Row([
            # 1. 컨트롤 패널 영역
            dbc.Col(
                dbc.Card(
                    dbc.CardBody([
                        html.H4("시각화 제어판", className="card-title"),
                        html.Hr(),
                        dbc.Label("1. 분석할 데이터베이스 선택"),
                        dcc.Dropdown(id='dataset-dropdown', placeholder='DB 파일 선택...'),
                        dbc.Button(
                            "엑셀 파일 다운로드", 
                            id="download-excel-button", 
                            color="success", 
                            className="mt-2 w-100",
                            disabled=True
                        ),
                        dcc.Download(id="download-excel"),
                        html.Br(),
                        
                                            dbc.Label("2. 데이터 필터링 (선택 사항)"),
                                            dcc.Store(id='h-filter-cols'),
                                            html.Div(id='h-filter-container-0'),
                                            html.Div(id='h-filter-container-1'),
                                            html.Div(id='h-filter-container-2'),
                                            html.Div(id='h-filter-container-3'),
                                            html.Div(id='h-filter-container-4'),
                                            html.Br(),
                                            dbc.Label("3. 차트 빌더"),
                                            dbc.Card([
                                                dbc.CardBody([
                                                    dbc.Label("차트 종류"),
                                                    dcc.Dropdown(id='chart-builder-chart-type', options=[
                                                        {'label': '선 그래프 (Line Chart)', 'value': 'line'},
                                                        {'label': '막대 그래프 (Bar Chart)', 'value': 'bar'},
                                                        {'label': '파이 차트 (Pie Chart)', 'value': 'pie'},
                                                    ], placeholder='차트 종류 선택...'),
                                                    html.Br(),
                                                    dbc.Label("X축 / 항목"),
                                                    dcc.Dropdown(id='chart-builder-xaxis', placeholder='X축으로 사용할 칼럼...'),
                                                    html.Br(),
                                                    dbc.Label("Y축 / 값"),
                                                    dcc.Dropdown(id='chart-builder-yaxis', placeholder='Y축으로 사용할 칼럼...'),
                                                    html.Br(),
                                                    dbc.Label("Y축 집계 방식"),
                                                    dcc.Dropdown(id='chart-builder-agg', options=[
                                                        {'label': '합계 (Sum)', 'value': 'sum'},
                                                        {'label': '평균 (Mean)', 'value': 'mean'},
                                                        {'label': '개수 (Count)', 'value': 'count'},
                                                    ], placeholder='집계 방식 선택...'),
                                                    html.Br(),
                                                    dbc.Label("그룹화 기준 (색상)"),
                                                    dcc.Dropdown(id='chart-builder-group', placeholder='그룹화할 칼럼...'),
                            html.Br(),
                            dbc.Label("상위 N개만 보기 (선택 사항)"),
                            dcc.Input(id='chart-builder-top-n', type='number', placeholder='예: 10', min=1, step=1, className="w-100"),
                                                ])
                                            ], className="mb-3"),
                        
                                            html.Hr(),
                                            dbc.Button("그래프 업데이트", id="update-graph-button", color="primary", className="w-100"),                    ])
                ),
                width=3 # 전체 12칸 중 3칸을 차지
            ),
            
            # 2. 그래프 표시 영역
            dbc.Col(
                dbc.Card(
                    dbc.CardBody([
                        # 그래프가 여기에 표시됩니다.
                        dcc.Loading(
                            id="loading-graph",
                            type="default",
                            children=dcc.Graph(id='visualization-graph')
                        )
                    ])
                ),
                width=9 # 전체 12칸 중 9칸을 차지
            )
        ]),
        html.Hr(),
        html.H4("[디버그 정보]"),
        html.Pre(id='debug-output', style={'border': '1px solid grey', 'padding': '10px', 'backgroundColor': '#f0f0f0'})
    ])