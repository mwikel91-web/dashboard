"""
Job Market Intelligence Dashboard
Главный файл приложения
"""

import os
from dash import Dash
import dash_bootstrap_components as dbc
from data_loader import load_and_process_data, get_aggregated_data
from layouts import create_layout
from callbacks import register_callbacks


def main():
    print("="*60)
    print("Job Market Intelligence Dashboard")
    print("="*60)
    
    # Загрузка данных (с кэшированием)
    df = load_and_process_data(force_reload=False)
    agg_data = get_aggregated_data(df)
    
    print(f"\nДанные загружены: {len(df)} записей")
    print(f"Компаний: {df['company'].nunique()}")
    print(f"Городов: {df['City'].nunique()}")
    
    # Инициализация Dash
    app = Dash(__name__, 
               external_stylesheets=[dbc.themes.FLATLY],
               suppress_callback_exceptions=True)
    app.title = "Job Market Intelligence Dashboard"
    
    # Получение данных для фильтров
    categories = agg_data['category_counts']['Category'].unique()
    cities = agg_data['city_counts']['City'].unique()
    salary_ranges = agg_data['salary_range_counts']['Range'].unique()
    
    # Создание layout
    app.layout = create_layout(
        kpis=agg_data['kpis'],
        categories=categories,
        cities=cities,
        salary_ranges=salary_ranges
    )
    
    # Регистрация callbacks
    register_callbacks(app, df)
    
    # Порт из переменной окружения (для Railway) или 8050 локально
    port = int(os.environ.get('PORT', 8050))
    
    # Запуск сервера
    print("\n" + "="*60)
    print("Dashboard запущен!")
    print(f"Порт: {port}")
    print("="*60 + "\n")
    
    app.run(debug=False, host='0.0.0.0', port=port)


if __name__ == '__main__':
    main()

