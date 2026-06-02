"""
Layout Components
UI компоненты дашборда с поддержкой тёмной/светлой темы
"""

from dash import html, dcc
import dash_bootstrap_components as dbc


def create_kpi_card(kpi_name, kpi_value, color, index):
    """Создание KPI карточки"""
    return dbc.Col(
        dbc.Card([
            dbc.CardBody([
                html.H4(kpi_name, className='kpi-label'),
                html.H2(kpi_value, className='kpi-value', style={'color': color}, id=f'kpi-value-{index}')
            ])
        ], className='kpi-card', id=f'kpi-{index}'),
        md=2, sm=6
    )


def create_filters(categories, cities, salary_ranges):
    """Создание блока фильтров"""
    return dbc.Card([
        dbc.CardHeader([
            html.Span("Фильтры", style={'fontWeight': 'bold'}),
            dbc.Button("Сбросить фильтры", id='reset-filters', color='secondary', size='sm', 
                      style={'marginLeft': '10px'})
        ], className='filter-header'),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Label("Категория:", className='filter-label'),
                    dcc.Dropdown(
                        id='category-filter',
                        options=[{'label': 'Все', 'value': 'all'}] + 
                                [{'label': cat, 'value': cat} for cat in categories],
                        value='all',
                        multi=True,
                        className='filter-dropdown',
                        placeholder='Выберите категории...'
                    )
                ], md=3),
                dbc.Col([
                    html.Label("Remote/On-site:", className='filter-label'),
                    dcc.Dropdown(
                        id='remote-filter',
                        options=[
                            {'label': 'Все', 'value': 'all'},
                            {'label': 'Remote', 'value': 'Remote'},
                            {'label': 'On-site', 'value': 'On-site'}
                        ],
                        value='all',
                        className='filter-dropdown'
                    )
                ], md=3),
                dbc.Col([
                    html.Label("Диапазон ЗП:", className='filter-label'),
                    dcc.Dropdown(
                        id='salary-filter',
                        options=[{'label': 'Все', 'value': 'all'}] + 
                                [{'label': str(r), 'value': str(r)} for r in salary_ranges],
                        value='all',
                        multi=True,
                        className='filter-dropdown',
                        placeholder='Выберите диапазон...'
                    )
                ], md=3),
                dbc.Col([
                    html.Label("Город:", className='filter-label'),
                    dcc.Dropdown(
                        id='city-filter',
                        options=[{'label': 'Все', 'value': 'all'}] + 
                                [{'label': city, 'value': city} for city in cities[:15]],
                        value='all',
                        multi=True,
                        className='filter-dropdown',
                        placeholder='Выберите город...'
                    )
                ], md=3)
            ])
        ])
    ], className='filter-card')


def create_chart_card(title, chart_id, height='400px'):
    """Создание карточки с графиком"""
    return dbc.Card([
        dbc.CardHeader(title, className='chart-header'),
        dbc.CardBody([
            dcc.Graph(
                id=chart_id,
                config={'displayModeBar': True, 'scrollZoom': True},
                style={'height': height}
            )
        ])
    ], className='chart-card')


def create_about_tab():
    """Создание вкладки 'О проекте' с описанием"""
    return html.Div([
        # Заголовок проекта
        dbc.Card([
            dbc.CardBody([
                html.H2([
                    html.Span("АНАЛИТИЧЕСКИЙ ДАШБОРД", style={'fontWeight': 'bold', 'color': '#1a1a2e'}),
                    html.Span(" · ", style={'color': '#999'}),
                    html.Span("АНАЛИЗ РЫНКА IT-ВАКАНСИЙ", style={'fontWeight': 'bold', 'color': '#1F4E79'})
                ], style={'textAlign': 'center', 'marginBottom': '10px'}),
                html.P([
                    html.Span("Тренды, зарплаты и требования на мировом рынке IT-вакансий", style={'fontSize': '18px', 'color': '#666'}),
                    html.Br(),
                    html.Span("Источник: Kaggle · ~58 000 вакансий", style={'fontSize': '14px', 'color': '#999', 'fontStyle': 'italic'})
                ], style={'textAlign': 'center'})
            ])
        ], className='about-header-card', style={'marginBottom': '30px', 'border': 'none', 'boxShadow': '0 4px 6px rgba(0,0,0,0.1)'}),

        # Цель проекта
        dbc.Card([
            dbc.CardBody([
                html.H4([html.Span("", style={'marginRight': '10px'}), "ЦЕЛЬ ПРОЕКТА"], 
                       style={'fontWeight': 'bold', 'color': '#1F4E79', 'marginBottom': '15px'}),
                html.P(
                    "Проанализировать данные о мировых IT-вакансиях, чтобы выявить ключевые тренды рынка труда: "
                    "какие навыки востребованы, как различаются зарплаты по категориям и регионам, "
                    "какие компании лидируют по количеству вакансий и рейтингу, а также определить "
                    "соотношение remote и on-site позиций.",
                    style={'fontSize': '16px', 'lineHeight': '1.6'}
                )
            ])
        ], className='about-section-card', style={'marginBottom': '20px'}),

        # Основные задачи
        dbc.Card([
            dbc.CardBody([
                html.H4([html.Span("", style={'marginRight': '10px'}), "ОСНОВНЫЕ ЗАДАЧИ"], 
                       style={'fontWeight': 'bold', 'color': '#1F4E79', 'marginBottom': '15px'}),
                html.Ol([
                    html.Li([
                        html.Strong("Категоризация вакансий: "),
                        "Определить распределение по категориям (Senior/Lead, Backend, Frontend, Data/AI/ML и др.) и выявить наиболее востребованные направления."
                    ], style={'marginBottom': '10px'}),
                    html.Li([
                        html.Strong("Анализ зарплат: "),
                        "Изучить распределение зарплат, выявить медианные значения и различия по категориям и уровням позиций."
                    ], style={'marginBottom': '10px'}),
                    html.Li([
                        html.Strong("География рынка: "),
                        "Определить топ-города по количеству вакансий и проанализировать региональные различия."
                    ], style={'marginBottom': '10px'}),
                    html.Li([
                        html.Strong("Remote vs On-site: "),
                        "Проанализировать соотношение удалённых и офисных позиций, выявить тренды."
                    ], style={'marginBottom': '10px'}),
                    html.Li([
                        html.Strong("Рейтинг компаний: "),
                        "Выявить топ-компании по количеству вакансий и среднему рейтингу, оценить концентрацию рынка."
                    ])
                ], style={'fontSize': '15px', 'lineHeight': '1.6'})
            ])
        ], className='about-section-card', style={'marginBottom': '20px'}),

        # Описание данных
        dbc.Card([
            dbc.CardBody([
                html.H4([html.Span("", style={'marginRight': '10px'}), "КРАТКОЕ ОПИСАНИЕ ДАННЫХ"], 
                       style={'fontWeight': 'bold', 'color': '#1F4E79', 'marginBottom': '15px'}),
                dbc.Table([
                    html.Tbody([
                        html.Tr([html.Td("Источник", style={'fontWeight': 'bold', 'width': '30%'}), 
                                html.Td("Kaggle — Job Market Data")]),
                        html.Tr([html.Td("Объём", style={'fontWeight': 'bold'}), 
                                html.Td("~58 000 записей о вакансиях")]),
                        html.Tr([html.Td("Единица", style={'fontWeight': 'bold'}), 
                                html.Td("Вакансия (job posting)")]),
                        html.Tr([html.Td("Ключевые поля", style={'fontWeight': 'bold'}), 
                                html.Td("title, company, location, salary, rating, review_count, relative_time")]),
                        html.Tr([html.Td("Производные поля", style={'fontWeight': 'bold'}), 
                                html.Td("Category (категория должности), City, Salary_Range, Is_Remote, Days_Ago")]),
                        html.Tr([html.Td("Ограничения", style={'fontWeight': 'bold'}), 
                                html.Td("Не все вакансии содержат информацию о зарплате; данные могут не отражать текущий момент")])
                    ])
                ], bordered=True, hover=True, style={'fontSize': '14px'})
            ])
        ], className='about-section-card', style={'marginBottom': '20px'}),

        # Основные выводы
        dbc.Card([
            dbc.CardBody([
                html.H4([html.Span("", style={'marginRight': '10px'}), "ОСНОВНЫЕ ВЫВОДЫ"], 
                       style={'fontWeight': 'bold', 'color': '#1F4E79', 'marginBottom': '20px'}),
                
                dbc.Row([
                    dbc.Col([
                        html.Div([
                            html.Div("01", className='conclusion-number'),
                            html.H5("Senior/Lead позиции доминируют", style={'fontWeight': 'bold', 'marginTop': '10px'}),
                            html.P("Категория Senior/Lead занимает наибольшую долю вакансий, что указывает на высокий спрос на опытных специалистов. Junior позиции составляют меньшую часть рынка.",
                                  style={'fontSize': '14px', 'color': '#666'})
                        ], className='conclusion-card')
                    ], md=4),
                    
                    dbc.Col([
                        html.Div([
                            html.Div("02", className='conclusion-number'),
                            html.H5("Значительный разброс зарплат", style={'fontWeight': 'bold', 'marginTop': '10px'}),
                            html.P("Зарплаты варьируются от $40K до $250K+ в зависимости от категории, локации и уровня. Средняя зарплата существенно выше медианы, что указывает на наличие высокооплачиваемых позиций.",
                                  style={'fontSize': '14px', 'color': '#666'})
                        ], className='conclusion-card')
                    ], md=4),
                    
                    dbc.Col([
                        html.Div([
                            html.Div("03", className='conclusion-number'),
                            html.H5("Remote позиции широко распространены", style={'fontWeight': 'bold', 'marginTop': '10px'}),
                            html.P("Значительная доля вакансий предлагает удалённую работу, особенно в IT-секторе. Это глобальный тренд,появившийся после 2020 года.",
                                  style={'fontSize': '14px', 'color': '#666'})
                        ], className='conclusion-card')
                    ], md=4)
                ], style={'marginBottom': '20px'}),

                dbc.Row([
                    dbc.Col([
                        html.Div([
                            html.Div("04", className='conclusion-number'),
                            html.H5("Концентрация в крупных городах", style={'fontWeight': 'bold', 'marginTop': '10px'}),
                            html.P("Топ-города концентрируют большинство вакансий, но remote позиции позволяют специалистам из регионов конкурировать на равных.",
                                  style={'fontSize': '14px', 'color': '#666'})
                        ], className='conclusion-card')
                    ], md=4),
                    
                    dbc.Col([
                        html.Div([
                            html.Div("05", className='conclusion-number'),
                            html.H5("Рейтинг компаний коррелирует с количеством вакансий", style={'fontWeight': 'bold', 'marginTop': '10px'}),
                            html.P("Крупные компании с высоким рейтингом активно нанимают, создавая высокую конкуренцию за таланты. Малые компании предлагают niche-позиции.",
                                  style={'fontSize': '14px', 'color': '#666'})
                        ], className='conclusion-card')
                    ], md=4),
                    
                    dbc.Col([
                        html.Div([
                            html.Div("06", className='conclusion-number'),
                            html.H5("Data/AI/ML — быстрорастущий сегмент", style={'fontWeight': 'bold', 'marginTop': '10px'}),
                            html.P("Категория Data/AI/ML показывает высокий рост, отражая глобальный тренд на внедрение машинного обучения и аналитики данных во все отрасли.",
                                  style={'fontSize': '14px', 'color': '#666'})
                        ], className='conclusion-card')
                    ], md=4)
                ])
            ])
        ], className='about-section-card', style={'marginBottom': '30px'}),

        # Footer
        html.Div([
            html.P("Итоговый проект · Данные: Kaggle · Job Market Analysis", 
                  style={'textAlign': 'center', 'color': '#999', 'fontStyle': 'italic', 'fontSize': '14px'})
        ])
    ], style={'padding': '20px', 'maxWidth': '1400px', 'margin': '0 auto'})


def create_layout(kpis, categories, cities, salary_ranges):
    """Создание полного layout с табами"""
    
    colors = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#44BBA4', '#3B1F2B']
    
    # Создаём контент вкладки "О проекте" заранее (статический)
    about_content = create_about_tab()
    
    return html.Div([
        # Заголовок
        html.Div([
            html.H1("Job Market Intelligence Dashboard", className='main-title'),
            html.P("Анализ рынка IT-вакансий / Executive Analytics", className='subtitle')
        ], className='header'),
        
        # KPI карточки
        html.Div([
            dbc.Row([
                create_kpi_card(name, value, colors[i % len(colors)], i)
                for i, (name, value) in enumerate(kpis.items())
            ])
        ], className='kpi-section'),
        
        # Фильтры
        html.Div([
            create_filters(categories, cities, salary_ranges)
        ], className='filters-section'),
        
        # Tabs навигация — ВЫНЕсена из Loading чтобы не перекрывалась спиннером
        dbc.Tabs([
            dbc.Tab(label="Основная аналитика", tab_id="tab-main", label_class_name="tab-label"),
            dbc.Tab(label="Детальный анализ", tab_id="tab-detailed", label_class_name="tab-label"),
            dbc.Tab(label="Сравнение компаний", tab_id="tab-compare", label_class_name="tab-label"),
            dbc.Tab(label="Прогнозы", tab_id="tab-forecast", label_class_name="tab-label"),
            dbc.Tab(label="Аналитическая записка", tab_id="tab-about", label_class_name="tab-label"),
            dbc.Tab(label="Excel", tab_id="tab-excel", label_class_name="tab-label"),
        ], id="tabs", active_tab="tab-main", className="custom-tabs"),

        # Dummy store для clientside callback
        dcc.Store(id='tab-switch-dummy'),

        # Лоадер — оборачивает только КОНТЕНТ вкладок, не навигацию
        dcc.Loading(
            id="loading-spinner",
            type="circle",
            children=[
                # Контейнеры для каждой вкладки (контент сохраняется при переключении)
                html.Div(id='tab-content-main', style={'display': 'block'}),
                html.Div(id='tab-content-detailed', style={'display': 'none'}),
                html.Div([
                    html.Div(id='compare-dropdown-container'),
                    html.Div(id='compare-charts-container')
                ], id='tab-content-compare', style={'display': 'none'}),
                html.Div(id='tab-content-forecast', style={'display': 'none'}),
                # Вкладка "О проекте" — статический контент
                html.Div(about_content, id='tab-content-about', style={'display': 'none'}),
                # Вкладка "Excel" — загрузка/скачивание
                html.Div(id='tab-content-excel', style={'display': 'none'}),
            ]
        ),
        
        # Footer
        html.Div([
            html.P("Проект по анализу рынка IT-вакансий",
                  className='footer')
        ])
    ], id='main-container', className='dashboard-container')
