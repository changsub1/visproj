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
    return dbc.Row([
        # 1. 컨트롤 패널 영역
        dbc.Col(
            dbc.Card(
                dbc.CardBody([
                    html.H4("시각화 제어판", className="card-title"),
                    html.Hr(),
                    dbc.Label("1. 분석할 데이터베이스 선택"),
                    dcc.Dropdown(id='dataset-dropdown', placeholder='DB 파일 선택...'),
                    html.Br(),
                    
                    dbc.Label("2. 데이터 필터링 (선택 사항)"),
                    dcc.Dropdown(id='year-filter-dropdown', placeholder='연도 선택...', multi=True),
                    html.Br(),
                    dcc.Dropdown(id='industry-filter-dropdown', placeholder='업종 선택...', multi=True),
                    html.Br(),

                    dbc.Label("3. 시각화 차트 종류 선택"),
                    dcc.Dropdown(
                        id='chart-type-dropdown',
                        options=[
                            {'label': '업종별 개/폐점 수 비교 (막대그래프)', 'value': 'bar_open_close'},
                            {'label': '업종별 수익성/투자비용 분석 (산점도)', 'value': 'scatter_profit_cost'},
                            {'label': '브랜드별 순위 (순위 차트)', 'value': 'rank_brand'},
                        ],
                        placeholder='차트 종류 선택...'
                    ),
                ])
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
                        children=html.Img(id='visualization-graph', style={'width': '100%'})
                    )
                ])
            ),
            width=9 # 전체 12칸 중 9칸을 차지
        )
    ])