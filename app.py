
import dash
import dash_bootstrap_components as dbc
from layouts import create_visualize_tab, create_config_tab
from dash import dcc, html
from dash.dependencies import Input, Output
from callbacks import register_callbacks

# Dash 앱 초기화 및 Bootstrap 테마 적용
app = dash.Dash(
    __name__, 
    suppress_callback_exceptions=True, 
    external_stylesheets=[dbc.themes.BOOTSTRAP]
)

# 앱의 제목 설정
app.title = "가맹사업 정보 대시보드"

# 앱의 전체 레이아웃 정의
app.layout = dbc.Container([
    html.H1("예비 창업자를 위한 가맹사업 정보 대시보드", style={'textAlign': 'center', 'margin': '20px'}),
    dbc.Tabs(id='main-tabs', active_tab='tab-visualize', children=[
        dbc.Tab(label='시각화', tab_id='tab-visualize'),
        dbc.Tab(label='DB 구성', tab_id='tab-config'),
    ]),
    html.Div(id='tabs-content', style={'padding': '20px'})
], fluid=True)

# 탭 선택에 따라 내용을 렌더링하는 콜백
@app.callback(Output('tabs-content', 'children'),
              Input('main-tabs', 'active_tab'))
def render_tab_content(tab_id):
    if tab_id == 'tab-visualize':
        return create_visualize_tab()
    elif tab_id == 'tab-config':
        return create_config_tab()

# 콜백 등록
register_callbacks(app)

# 서버 실행
if __name__ == '__main__':
    app.run(debug=True)
