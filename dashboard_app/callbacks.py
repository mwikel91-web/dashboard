"""
Callbacks
Обработчики событий для дашборда с табами и cross-filtering
"""

from dash import Input, Output, callback, html, State, dcc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import dash_bootstrap_components as dbc
import base64
import os


def register_callbacks(app, df):
    """Регистрация всех callbacks"""
    
    colors = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#44BBA4', '#3B1F2B', '#E94560', '#0F3460']
    
    # Callback для сброса фильтров
    @app.callback(
        [Output('category-filter', 'value'),
         Output('remote-filter', 'value'),
         Output('salary-filter', 'value'),
         Output('city-filter', 'value')],
        [Input('reset-filters', 'n_clicks')],
        prevent_initial_call=True
    )
    def reset_filters(n_clicks):
        return 'all', 'all', 'all', 'all'

    # Callback для динамических KPI - обновляются при изменении фильтров
    @app.callback(
        [Output('kpi-value-0', 'children'),
         Output('kpi-value-1', 'children'),
         Output('kpi-value-2', 'children'),
         Output('kpi-value-3', 'children'),
         Output('kpi-value-4', 'children'),
         Output('kpi-value-5', 'children')],
        [Input('category-filter', 'value'),
         Input('remote-filter', 'value'),
         Input('salary-filter', 'value'),
         Input('city-filter', 'value')]
    )
    def update_kpis(selected_categories, remote_filter, salary_filter, city_filter):
        filtered = df.copy()

        if selected_categories != 'all' and selected_categories:
            filtered = filtered[filtered['Category'].isin(selected_categories)]
        if remote_filter != 'all':
            filtered = filtered[filtered['Remote_Label'] == remote_filter]
        if salary_filter != 'all' and salary_filter:
            filtered = filtered[filtered['Salary_Range'].isin(salary_filter)]
        if city_filter != 'all' and city_filter:
            filtered = filtered[filtered['City'].isin(city_filter)]

        total_jobs = f"{len(filtered):,}"
        companies = f"{filtered['company'].nunique():,}"
        avg_salary = f"${filtered['Salary'].mean():,.0f}" if filtered['Salary'].notna().any() else "N/A"
        median_salary = f"${filtered['Salary'].median():,.0f}" if filtered['Salary'].notna().any() else "N/A"
        remote_pct = f"{filtered['Is_Remote'].mean()*100:.1f}%" if len(filtered) > 0 else "0%"
        urgent = f"{filtered['urgently_hiring'].sum():,}"

        return total_jobs, companies, avg_salary, median_salary, remote_pct, urgent
    
    # Clientside callback: переключает видимость табов БЕЗ перерисовки контента
    app.clientside_callback(
        """
        function(activeTab) {
            var tabMap = {
                'tab-main': 'tab-content-main',
                'tab-detailed': 'tab-content-detailed',
                'tab-compare': 'tab-content-compare',
                'tab-forecast': 'tab-content-forecast',
                'tab-about': 'tab-content-about',
                'tab-excel': 'tab-content-excel'
            };
            Object.keys(tabMap).forEach(function(tabId) {
                var el = document.getElementById(tabMap[tabId]);
                if (el) {
                    el.style.display = (tabId === activeTab) ? 'block' : 'none';
                }
            });
            return activeTab;
        }
        """,
        Output('tab-switch-dummy', 'data'),
        Input('tabs', 'active_tab')
    )

    # Callback для контента табов - рендерим вкладки (кроме compare) при изменении фильтров
    @app.callback(
        [Output('tab-content-main', 'children'),
         Output('tab-content-detailed', 'children'),
         Output('tab-content-forecast', 'children')],
        [Input('category-filter', 'value'),
         Input('remote-filter', 'value'),
         Input('salary-filter', 'value'),
         Input('city-filter', 'value')]
    )
    def render_main_detailed_forecast(selected_categories, remote_filter, salary_filter, city_filter):
        filtered_df = df.copy()

        if selected_categories != 'all' and selected_categories:
            filtered_df = filtered_df[filtered_df['Category'].isin(selected_categories)]
        if remote_filter != 'all':
            filtered_df = filtered_df[filtered_df['Remote_Label'] == remote_filter]
        if salary_filter != 'all' and salary_filter:
            filtered_df = filtered_df[filtered_df['Salary_Range'].isin(salary_filter)]
        if city_filter != 'all' and city_filter:
            filtered_df = filtered_df[filtered_df['City'].isin(city_filter)]

        plotly_template = 'plotly_white'

        main_content = render_main_tab(filtered_df, plotly_template, colors)
        detailed_content = render_detailed_tab(filtered_df, plotly_template, colors)
        forecast_content = render_forecast_tab(filtered_df, plotly_template, colors)

        return main_content, detailed_content, forecast_content

    # Callback для dropdown компаний - обновляет список при изменении фильтров
    @app.callback(
        Output('compare-dropdown-container', 'children'),
        [Input('category-filter', 'value'),
         Input('remote-filter', 'value'),
         Input('salary-filter', 'value'),
         Input('city-filter', 'value')]
    )
    def render_compare_dropdown(selected_categories, remote_filter, salary_filter, city_filter):
        filtered = df.copy()
        if selected_categories != 'all' and selected_categories:
            filtered = filtered[filtered['Category'].isin(selected_categories)]
        if remote_filter != 'all':
            filtered = filtered[filtered['Remote_Label'] == remote_filter]
        if salary_filter != 'all' and salary_filter:
            filtered = filtered[filtered['Salary_Range'].isin(salary_filter)]
        if city_filter != 'all' and city_filter:
            filtered = filtered[filtered['City'].isin(city_filter)]

        top_companies = filtered.groupby('company').size().nlargest(50).index.tolist()
        default_companies = filtered.groupby('company').size().nlargest(10).index.tolist()

        return dbc.Card([
            dbc.CardHeader("Выберите компании для сравнения", style={'fontWeight': 'bold'}),
            dbc.CardBody([
                dcc.Dropdown(
                    id='company-compare-dropdown',
                    options=[{'label': c, 'value': c} for c in top_companies],
                    value=default_companies,
                    multi=True,
                    placeholder='Начните вводить название компании...',
                    className='filter-dropdown'
                )
            ])
        ], className='filter-card', style={'margin': '20px'})

    # Callback для графиков сравнения - обновляется при выборе компаний и фильтров
    @app.callback(
        Output('compare-charts-container', 'children'),
        [Input('company-compare-dropdown', 'value'),
         Input('category-filter', 'value'),
         Input('remote-filter', 'value'),
         Input('salary-filter', 'value'),
         Input('city-filter', 'value')]
    )
    def render_compare_charts(selected_companies, selected_categories, remote_filter, salary_filter, city_filter):
        filtered = df.copy()
        if selected_categories != 'all' and selected_categories:
            filtered = filtered[filtered['Category'].isin(selected_categories)]
        if remote_filter != 'all':
            filtered = filtered[filtered['Remote_Label'] == remote_filter]
        if salary_filter != 'all' and salary_filter:
            filtered = filtered[filtered['Salary_Range'].isin(salary_filter)]
        if city_filter != 'all' and city_filter:
            filtered = filtered[filtered['City'].isin(city_filter)]

        if not selected_companies:
            return html.Div("Выберите компании для сравнения", style={'textAlign': 'center', 'padding': '40px'})

        return render_compare_tab(filtered, 'plotly_white', colors, selected_companies)

    # ============================================================
    # ВКЛАДКА EXCEL — загрузка/скачивание с защитой паролем
    # ============================================================
    EXCEL_DIR = os.path.join(os.path.dirname(__file__), 'data')
    EXCEL_PASSWORD = 'admin2025'
    os.makedirs(EXCEL_DIR, exist_ok=True)

    def get_uploaded_file_info():
        """Возвращает имя и размер загруженного файла, если он есть"""
        files = [f for f in os.listdir(EXCEL_DIR) if f.endswith(('.xlsx', '.xls', '.csv'))]
        if files:
            f = files[0]
            size_kb = os.path.getsize(os.path.join(EXCEL_DIR, f)) / 1024
            return f, round(size_kb, 1)
        return None, None

    # Рендер вкладки Excel
    @app.callback(
        Output('tab-content-excel', 'children'),
        [Input('tabs', 'active_tab')]
    )
    def render_excel_tab(active_tab):
        fname, fsize = get_uploaded_file_info()
        file_info = (
            html.P(f"Файл на сервере: {fname} ({fsize} KB)",
                   style={'color': '#2E86AB', 'fontWeight': 'bold', 'fontSize': '15px'})
            if fname else
            html.P("Файл ещё не загружен", style={'color': '#999', 'fontStyle': 'italic'})
        )
        return html.Div([
            # Store для временного хранения выбранного файла
            dcc.Store(id='excel-file-store', storage_type='session'),

            dbc.Card([
                dbc.CardHeader("Загрузка файла (только администратор)", style={'fontWeight': 'bold'}),
                dbc.CardBody([
                    # Шаг 1: выбрать файл
                    html.P("Шаг 1: Выберите файл (.xlsx, .xls, .csv)",
                           style={'fontWeight': 'bold', 'marginBottom': '8px', 'marginTop': '5px'}),
                    dcc.Upload(
                        id='excel-upload',
                        children=dbc.Button("Выбрать файл", color='outline-primary', id='excel-pick-btn'),
                        accept='.xlsx,.xls,.csv',
                        max_size=50 * 1024 * 1024,
                        multiple=False,
                    ),
                    html.Div(id='excel-selected-filename',
                             style={'marginTop': '8px', 'color': '#2E86AB', 'fontSize': '14px'}),

                    html.Hr(style={'margin': '20px 0'}),

                    # Шаг 2: пароль
                    html.P("Шаг 2: Введите пароль",
                           style={'fontWeight': 'bold', 'marginBottom': '8px'}),
                    dbc.Input(id='excel-password', type='password',
                              placeholder='Пароль для загрузки', style={'maxWidth': '250px'},
                              persistence=True, persistence_type='session'),

                    html.Hr(style={'margin': '20px 0'}),

                    # Шаг 3: кнопка загрузить
                    html.P("Шаг 3: Подтвердите загрузку",
                           style={'fontWeight': 'bold', 'marginBottom': '8px'}),
                    dbc.Button("Загрузить на сервер", color='primary',
                               id='excel-upload-btn', style={'marginTop': '5px'}),

                    html.Div(id='excel-upload-status', style={'marginTop': '15px'})
                ])
            ], className='filter-card', style={'margin': '20px'}),

            dbc.Card([
                dbc.CardHeader("Скачивание файла", style={'fontWeight': 'bold'}),
                dbc.CardBody([
                    file_info,
                    dbc.Button("Скачать файл", color='success', id='excel-download-btn',
                               style={'marginTop': '10px'}),
                    dcc.Download(id='excel-download')
                ])
            ], className='filter-card', style={'margin': '20px'}),
        ], style={'padding': '20px'})

    # Callback: при выборе файла — показать имя и сохранить в Store
    @app.callback(
        [Output('excel-selected-filename', 'children'),
         Output('excel-file-store', 'data')],
        [Input('excel-upload', 'contents')],
        [State('excel-upload', 'filename')],
        prevent_initial_call=True
    )
    def on_file_selected(contents, filename):
        if contents is None or filename is None:
            return "", None
        return f"Выбран: {filename}", {'contents': contents, 'filename': filename}

    # Callback: кнопка "Загрузить на сервер" — проверяет пароль и сохраняет
    @app.callback(
        Output('excel-upload-status', 'children'),
        [Input('excel-upload-btn', 'n_clicks')],
        [State('excel-password', 'value'),
         State('excel-file-store', 'data')],
        prevent_initial_call=True
    )
    def handle_upload(n_clicks, password, file_data):
        print(f"[DEBUG Excel upload] password received: '{password}', file_data: {bool(file_data)}")
        if password != EXCEL_PASSWORD:
            return dbc.Alert("Неверный пароль. Загрузка запрещена.", color='danger')
        if not file_data or not file_data.get('contents'):
            return dbc.Alert("Сначала выберите файл (Шаг 1).", color='warning')
        contents = file_data['contents']
        filename = file_data['filename']
        # Удаляем старые файлы
        for old in os.listdir(EXCEL_DIR):
            if old.endswith(('.xlsx', '.xls', '.csv')):
                os.remove(os.path.join(EXCEL_DIR, old))
        # Сохраняем новый
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        save_path = os.path.join(EXCEL_DIR, filename)
        with open(save_path, 'wb') as f:
            f.write(decoded)
        size_kb = round(len(decoded) / 1024, 1)
        return dbc.Alert(f"Файл '{filename}' ({size_kb} KB) успешно загружен!", color='success')

    # Callback: скачивание файла
    @app.callback(
        Output('excel-download', 'data'),
        [Input('excel-download-btn', 'n_clicks')],
        prevent_initial_call=True
    )
    def handle_download(n_clicks):
        files = [f for f in os.listdir(EXCEL_DIR) if f.endswith(('.xlsx', '.xls', '.csv'))]
        if not files:
            return None
        filepath = os.path.join(EXCEL_DIR, files[0])
        with open(filepath, 'rb') as f:
            encoded = base64.b64encode(f.read()).decode()
        return dict(
            content=encoded,
            filename=files[0],
            type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            base64=True
        )

def render_main_tab(filtered_df, template, colors):
    """Основная аналитика"""

    if len(filtered_df) == 0:
        return html.Div("Нет данных для отображения. Измените фильтры.",
                        style={'textAlign': 'center', 'padding': '60px', 'fontSize': '18px'})

    # 1. Category chart
    cat_counts = filtered_df.groupby('Category').size().reset_index(name='Count').sort_values('Count', ascending=True)
    if len(cat_counts) == 0:
        fig_cat = go.Figure()
        fig_cat.add_annotation(text="Нет данных по категориям", showarrow=False, xref="paper", yref="paper", x=0.5, y=0.5)
    else:
        fig_cat = px.bar(cat_counts, x='Count', y='Category', orientation='h',
                        title='',
                        color='Count', color_continuous_scale='Viridis',
                        template=template)
        fig_cat.update_layout(transition_duration=500, xaxis_title="Вакансий", yaxis_title="")
    
    # 2. Salary distribution
    salary_data = filtered_df['Salary'].dropna()
    fig_salary = go.Figure()
    if len(salary_data) > 0:
        fig_salary.add_trace(go.Histogram(
            x=salary_data, nbinsx=40, name='Количество вакансий',
            marker_color=colors[0], opacity=0.7,
            hovertemplate='Зарплата: $%{x:,.0f}<br>Вакансий: %{y}<extra></extra>'
        ))
        mean_sal = salary_data.mean()
        fig_salary.add_vline(x=mean_sal, line_dash="dot", line_color="blue",
                           annotation_text=f"Средняя: ${mean_sal:,.0f}")
    else:
        fig_salary.add_annotation(text="Нет данных по зарплатам", showarrow=False, xref="paper", yref="paper", x=0.5, y=0.5)
    fig_salary.update_layout(
        title='',
        xaxis_title='Годовая зарплата, USD (каждая вакансия)',
        yaxis_title='Количество вакансий в этом диапазоне ЗП',
        template=template,
        transition_duration=500
    )
    
    # 3. Company chart
    comp_counts = filtered_df.groupby('company').size().reset_index(name='Count').sort_values('Count', ascending=False).head(20)
    if len(comp_counts) == 0:
        fig_comp = go.Figure()
        fig_comp.add_annotation(text="Нет данных по компаниям", showarrow=False, xref="paper", yref="paper", x=0.5, y=0.5)
    else:
        fig_comp = px.bar(comp_counts, x='Count', y='company', orientation='h',
                         title='',
                         color='Count', color_continuous_scale='Plasma',
                     template=template)
    fig_comp.update_layout(transition_duration=500, yaxis={'categoryorder': 'total ascending'})
    
    # 4. City chart
    city_counts = filtered_df[filtered_df['City'] != 'Remote'].groupby('City').size().reset_index(name='Count').sort_values('Count', ascending=False).head(20)
    if len(city_counts) == 0:
        fig_city = go.Figure()
        fig_city.add_annotation(text="Нет данных по городам", showarrow=False, xref="paper", yref="paper", x=0.5, y=0.5)
    else:
        fig_city = px.bar(city_counts, x='City', y='Count',
                         title='',
                         color='Count', color_continuous_scale='Magma',
                         template=template)
        fig_city.update_layout(transition_duration=500, xaxis={'tickangle': -45})
    
    return html.Div([
        dbc.Row([
            dbc.Col(create_chart_card("Распределение по категориям", fig_cat), md=6, className='chart-col'),
            dbc.Col(create_chart_card("Распределение зарплат", fig_salary), md=6, className='chart-col')
        ], className='charts-row'),
        dbc.Row([
            dbc.Col(create_chart_card("Топ-20 компаний", fig_comp), md=6, className='chart-col'),
            dbc.Col(create_chart_card("Топ-20 городов", fig_city), md=6, className='chart-col')
        ], className='charts-row')
    ])


def render_detailed_tab(filtered_df, template, colors):
    """Детальный анализ"""

    if len(filtered_df) == 0:
        return html.Div("Нет данных для отображения. Измените фильтры.",
                        style={'textAlign': 'center', 'padding': '60px', 'fontSize': '18px'})

    # 1. Remote vs On-site
    remote_counts = filtered_df['Remote_Label'].value_counts().reset_index()
    remote_counts.columns = ['Type', 'Count']
    fig_remote = px.pie(remote_counts, values='Count', names='Type',
                       title='',
                       color_discrete_sequence=px.colors.qualitative.Set3,
                       template=template)
    fig_remote.update_traces(textposition='inside', textinfo='percent+label')
    
    # 2. Salary by category
    fig_sal_cat = px.box(filtered_df.dropna(subset=['Salary']), x='Category', y='Salary',
                        title='',
                        color='Category',
                        template=template)
    fig_sal_cat.update_layout(transition_duration=500, xaxis={'tickangle': -45}, showlegend=False)
    
    # 3. Rating chart - вертикальные столбцы как у Тренд публикации
    company_stats = filtered_df[filtered_df['rating'] > 0].groupby('company').agg({
        'rating': 'mean',
        'review_count': 'sum',
        'title': 'count'
    }).round(2).reset_index()
    company_stats.columns = ['company', 'avg_rating', 'total_reviews', 'job_count']
    company_stats = company_stats[company_stats['total_reviews'] >= 5]
    company_stats = company_stats.sort_values('avg_rating', ascending=False).head(15)
    
    fig_rating = px.bar(company_stats, x='company', y='avg_rating',
                       title='',
                       color='avg_rating', color_continuous_scale='Blues',
                       template=template,
                       hover_data={'avg_rating': ':.2f', 'total_reviews': True, 'job_count': True})
    fig_rating.update_layout(transition_duration=500, xaxis_title='Компания', yaxis_title='Рейтинг',
                             xaxis={'tickangle': -45})
    
    # 4. Trend by time
    days_bins = [0, 1, 3, 7, 14, 30, 100]
    days_labels = ['Сегодня', '1-3 дня', '4-7 дней', '8-14 дней', '15-30 дней', '>30 дней']
    filtered_df['days_bin'] = pd.cut(filtered_df['Days_Ago'], bins=days_bins, labels=days_labels, include_lowest=True)
    trend_data = filtered_df['days_bin'].value_counts().sort_index().reset_index()
    trend_data.columns = ['Period', 'Count']
    
    fig_trend = px.bar(trend_data, x='Period', y='Count',
                      title='',
                      color='Count', color_continuous_scale='Blues',
                      template=template)
    fig_trend.update_layout(transition_duration=500, xaxis_title='Период', yaxis_title='Вакансий')
    
    # 5. Heatmap correlations
    corr_df = filtered_df[['Salary', 'rating', 'Is_Remote', 'review_count']].dropna()
    if len(corr_df) > 10:
        corr_matrix = corr_df.corr()
        fig_heatmap = go.Figure(data=go.Heatmap(
            z=corr_matrix.values,
            x=corr_matrix.columns,
            y=corr_matrix.index,
            colorscale='RdBu',
            zmid=0
        ))
        fig_heatmap.update_layout(
            title='',
            template=template,
            transition_duration=500
        )
    else:
        fig_heatmap = go.Figure()
        fig_heatmap.add_annotation(text="Недостаточно данных для корреляции", showarrow=False)
    
    # 6. Treemap
    treemap_df = filtered_df.groupby(['Category', 'Remote_Label']).size().reset_index(name='Count')
    fig_treemap = px.treemap(treemap_df, path=['Category', 'Remote_Label'], values='Count',
                            title='',
                            template=template)
    fig_treemap.update_layout(transition_duration=500)
    
    # 7. Scatter plot
    # scatter_df = filtered_df[['Salary', 'rating', 'company', 'Category']].dropna()
    # if len(scatter_df) > 0:
    #     fig_scatter = px.scatter(scatter_df, x='rating', y='Salary', 
    #                             color='Category', hover_name='company',
    #                             title='Зарплата vs Рейтинг компании',
    #                             template=template,
    #                             opacity=0.6)
    #     fig_scatter.update_layout(transition_duration=500)
    # else:
    #     fig_scatter = go.Figure()
    
    return html.Div([
        dbc.Row([
            dbc.Col(create_chart_card("Remote vs On-site", fig_remote), md=6, className='chart-col'),
            dbc.Col(create_chart_card("Зарплата по категориям", fig_sal_cat), md=6, className='chart-col')
        ], className='charts-row'),
        dbc.Row([
            dbc.Col(create_chart_card("Рейтинг компаний", fig_rating), md=6, className='chart-col'),
            dbc.Col(create_chart_card("Тренд публикации", fig_trend), md=6, className='chart-col')
        ], className='charts-row'),
        dbc.Row([
            dbc.Col(create_chart_card("Корреляция", fig_heatmap), md=6, className='chart-col'),
            dbc.Col(create_chart_card("Иерархия", fig_treemap), md=6, className='chart-col')
        ], className='charts-row'),
        # dbc.Row([
        #     dbc.Col(create_chart_card("Зарплата vs Рейтинг", fig_scatter), md=6, className='chart-col')
        # ], className='charts-row')
    ])


def render_compare_tab(filtered_df, template, colors, selected_companies):
    """Сравнение компаний"""

    if not selected_companies or len(selected_companies) < 2:
        return html.Div("Выберите минимум 2 компании для сравнения",
                        style={'textAlign': 'center', 'padding': '40px'})

    # Сравнение по выбранным компаниям
    comp_data = filtered_df[filtered_df['company'].isin(selected_companies)]
    if len(comp_data) == 0:
        return html.Div("Нет данных для выбранных компаний. Измените фильтры.",
                        style={'textAlign': 'center', 'padding': '40px'})

    comp_compare = comp_data.groupby('company').agg({
        'title': 'count',
        'Salary': 'median',
        'rating': 'mean',
        'review_count': 'sum'
    }).round(2).reset_index()
    comp_compare.columns = ['Компания', 'Вакансий', 'Медианная ЗП', 'Рейтинг', 'Отзывов']
    comp_compare = comp_compare.sort_values('Вакансий', ascending=False)

    if len(comp_compare) < 2:
        return html.Div("Недостаточно данных для сравнения (нужно минимум 2 компании с данными)",
                        style={'textAlign': 'center', 'padding': '40px'})

    fig_compare_jobs = px.bar(comp_compare, x='Вакансий', y='Компания', orientation='h',
                             title='',
                             color='Вакансий', color_continuous_scale='Viridis',
                             template=template)

    fig_compare_salary = px.bar(comp_compare, x='Медианная ЗП', y='Компания', orientation='h',
                               title='',
                               color='Медианная ЗП', color_continuous_scale='Plasma',
                               template=template)

    fig_compare_rating = px.bar(comp_compare, x='Рейтинг', y='Компания', orientation='h',
                               title='',
                               color='Рейтинг', color_continuous_scale='RdYlGn',
                               range_color=[0, 5],
                               template=template)

    return html.Div([
        html.H4(f"Сравнение {len(comp_compare)} компаний", style={'textAlign': 'center', 'marginBottom': '20px'}),
        dbc.Row([
            dbc.Col(create_chart_card("Количество вакансий", fig_compare_jobs), md=12, className='chart-col')
        ], className='charts-row'),
        dbc.Row([
            dbc.Col(create_chart_card("Медианная зарплата", fig_compare_salary), md=6, className='chart-col'),
            dbc.Col(create_chart_card("Рейтинг", fig_compare_rating), md=6, className='chart-col')
        ], className='charts-row')
    ])


def render_forecast_tab(filtered_df, template, colors):
    """Прогнозы и тренды"""

    if len(filtered_df) == 0:
        return html.Div("Нет данных для отображения. Измените фильтры.",
                        style={'textAlign': 'center', 'padding': '60px', 'fontSize': '18px'})

    # Тренд зарплат по времени
    salary_trend = filtered_df.dropna(subset=['Salary', 'Days_Ago']).copy()
    if len(salary_trend) > 10:
        salary_trend['Days_Ago_Bin'] = pd.cut(salary_trend['Days_Ago'], bins=10, labels=False)
        trend_agg = salary_trend.groupby('Days_Ago_Bin')['Salary'].mean().reset_index()
        
        fig_trend_salary = px.line(trend_agg, x='Days_Ago_Bin', y='Salary',
                                  title='',
                                  template=template,
                                  markers=True)
        fig_trend_salary.update_layout(xaxis_title='Период (дни назад)', yaxis_title='Средняя ЗП')
    else:
        fig_trend_salary = go.Figure()
    
    # Прогноз (линейная регрессия)
    if len(salary_trend) > 20:
        from scipy import stats
        x = salary_trend['Days_Ago'].values
        y = salary_trend['Salary'].values
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        
        forecast_df = pd.DataFrame({
            'Days_Ago': range(0, 60),
            'Salary_Forecast': intercept + slope * range(0, 60)
        })
        
        fig_forecast = px.scatter(salary_trend.head(1000), x='Days_Ago', y='Salary',
                                 title='',
                                 template=template,
                                 opacity=0.5)
        fig_forecast.add_trace(go.Scatter(
            x=forecast_df['Days_Ago'],
            y=forecast_df['Salary_Forecast'],
            mode='lines',
            name='Прогноз',
            line=dict(color='red', width=3)
        ))
        fig_forecast.update_layout(xaxis_title='Дней назад', yaxis_title='Зарплата')
    else:
        fig_forecast = go.Figure()
        fig_forecast.add_annotation(text="Недостаточно данных для прогноза", showarrow=False)
    
    # Рекомендации
    recommendations = []
    if len(filtered_df) > 0:
        avg_salary = filtered_df['Salary'].mean()
        remote_pct = filtered_df['Is_Remote'].mean() * 100
        top_cat = filtered_df['Category'].mode().iloc[0] if len(filtered_df['Category'].mode()) > 0 else 'N/A'
        
        recommendations = [
            f"Средняя зарплата на рынке: ${avg_salary:,.0f}" if pd.notna(avg_salary) else "Данные по зарплате ограничены",
            f"Доля remote вакансий: {remote_pct:.1f}%",
            f"Наиболее востребованная категория: {top_cat}",
            f"Всего проанализировано вакансий: {len(filtered_df):,}"
        ]
    
    return html.Div([
        dbc.Row([
            dbc.Col(create_chart_card("Тренд средней зарплаты (по времени публикации)", fig_trend_salary), md=12, className='chart-col')
        ], className='charts-row'),
        dbc.Row([
            dbc.Col(create_chart_card("Прогноз зарплат (линейная регрессия)", fig_forecast), md=12, className='chart-col')
        ], className='charts-row'),
        dbc.Card([
            dbc.CardHeader("Рекомендации на основе анализа", style={'fontWeight': 'bold'}),
            dbc.CardBody([
                html.Ul([html.Li(rec) for rec in recommendations])
            ])
        ], style={'margin': '20px'})
    ])


def create_chart_card(title, figure):
    """Создание карточки с графиком"""
    return dbc.Card([
        dbc.CardHeader(title, className='chart-header'),
        dbc.CardBody([
            dcc.Graph(
                figure=figure,
                config={'displayModeBar': True, 'scrollZoom': True},
                style={'height': '400px'}
            )
        ])
    ], className='chart-card')
