"""
Data Loader with Caching
Загрузка и кэширование данных для дашборда
"""

import pandas as pd
import numpy as np
import re
import pickle
import os
from datetime import datetime


CACHE_DIR = os.path.join(os.path.dirname(__file__), 'cache')
CACHE_FILE = os.path.join(CACHE_DIR, 'processed_data.pkl')

# Пути к исходному файлу — проверяем несколько вариантов (для Railway и локально)
_BASE = os.path.dirname(os.path.abspath(__file__))
_SOURCE_CANDIDATES = [
    os.path.join(_BASE, 'data', 'Дашборд_исходные данные.xlsx'),   # внутри dashboard_app/data/
    os.path.join(_BASE, '..', 'Дашборд_исходные данные.xlsx'),     # на уровень выше (Railway root)
    os.path.join(_BASE, '..', '..', 'Дашборд_исходные данные.xlsx'),  # оригинальный путь
]

def _find_source_file():
    for p in _SOURCE_CANDIDATES:
        if os.path.exists(p):
            return p
    return _SOURCE_CANDIDATES[0]  # fallback

SOURCE_FILE = _find_source_file()


def parse_salary(salary_str):
    if pd.isna(salary_str):
        return np.nan
    salary_str = str(salary_str)
    numbers = re.findall(r'\$([\d,]+)', salary_str)
    if numbers:
        avg_salary = np.mean([float(n.replace(',', '')) for n in numbers])
        if 'hour' in salary_str.lower():
            avg_salary *= 2080
        elif 'week' in salary_str.lower():
            avg_salary *= 52
        return avg_salary
    return np.nan


def categorize_title(title):
    if pd.isna(title):
        return 'Other'
    title = str(title).lower()
    if any(x in title for x in ['senior', 'sr.', 'lead', 'principal', 'staff']):
        return 'Senior/Lead'
    elif any(x in title for x in ['junior', 'entry', 'associate']):
        return 'Junior/Entry'
    elif any(x in title for x in ['devops', 'sre', 'infrastructure']):
        return 'DevOps/SRE'
    elif any(x in title for x in ['data', 'ml', 'ai', 'machine learning']):
        return 'Data/AI/ML'
    elif any(x in title for x in ['frontend', 'front-end', 'ui', 'ux']):
        return 'Frontend'
    elif any(x in title for x in ['backend', 'back-end']):
        return 'Backend'
    elif any(x in title for x in ['full stack', 'full-stack']):
        return 'Full Stack'
    elif any(x in title for x in ['manager', 'director', 'vp']):
        return 'Management'
    elif any(x in title for x in ['architect']):
        return 'Architect'
    else:
        return 'Software Engineer'


def load_and_process_data(force_reload=False):
    """
    Загрузка данных с кэшированием.
    Если кэш существует и force_reload=False, загружает из кэша.
    """
    # Проверяем кэш
    if not force_reload and os.path.exists(CACHE_FILE):
        print("Загрузка из кэша...")
        try:
            with open(CACHE_FILE, 'rb') as f:
                data = pickle.load(f)
            print(f"Загружено из кэша: {len(data)} записей")
            return data
        except Exception as e:
            print(f"Ошибка кэша: {e}. Загружаю из источника...")
    
    # Загрузка из Excel
    print("Загрузка из Excel...")
    if not os.path.exists(SOURCE_FILE):
        raise FileNotFoundError(f"Файл не найден: {SOURCE_FILE}")
    
    df = pd.read_excel(SOURCE_FILE, sheet_name='Свои_данные')
    
    # Обработка данных
    df['Salary'] = df['salary'].apply(parse_salary)
    df['Category'] = df['title'].apply(categorize_title)
    df['Is_Remote'] = df['location'].str.lower().str.contains('remote', na=False)
    df['Remote_Label'] = df['Is_Remote'].map({True: 'Remote', False: 'On-site'})
    
    def extract_city(loc):
        if pd.isna(loc):
            return 'Unknown'
        loc = str(loc)
        if 'remote' in loc.lower():
            return 'Remote'
        return loc.split(',')[0].strip() if ',' in loc else loc.strip()
    
    df['City'] = df['location'].apply(extract_city)
    
    df['Salary_Range'] = pd.cut(df['Salary'],
                                 bins=[0, 60000, 90000, 120000, 150000, 200000, np.inf],
                                 labels=['<$60K', '$60-90K', '$90-120K', '$120-150K', '$150-200K', '>$200K'])
    
    # Days ago
    def parse_days(relative_time):
        if pd.isna(relative_time):
            return np.nan
        relative_time = str(relative_time)
        if '30+' in relative_time:
            return 30
        import re
        match = re.search(r'(\d+)', relative_time)
        return int(match.group(1)) if match else np.nan
    
    df['Days_Ago'] = df['relative_time'].apply(parse_days)
    
    # Сохранение в кэш
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(CACHE_FILE, 'wb') as f:
        pickle.dump(df, f)
    
    print(f"Данные обработаны и сохранены в кэш: {len(df)} записей")
    return df


def get_aggregated_data(df):
    """Получение агрегированных данных для графиков"""
    
    # Тренд по времени
    days_bins = [0, 1, 3, 7, 14, 30, 100]
    days_labels = ['Сегодня', '1-3 дня', '4-7 дней', '8-14 дней', '15-30 дней', '>30 дней']
    df['days_bin'] = pd.cut(df['Days_Ago'], bins=days_bins, labels=days_labels, include_lowest=True)
    trend_data = df['days_bin'].value_counts().sort_index().reset_index()
    trend_data.columns = ['Period', 'Count']
    
    return {
        'category_counts': df.groupby('Category').size().reset_index(name='Count').sort_values('Count', ascending=False),
        'city_counts': df.groupby('City').size().reset_index(name='Count').sort_values('Count', ascending=False).head(20),
        'company_counts': df.groupby('company').size().reset_index(name='Count').sort_values('Count', ascending=False).head(20),
        'salary_range_counts': df['Salary_Range'].value_counts().sort_index().reset_index().rename(columns={'Salary_Range': 'Range', 'count': 'Count'}),
        'remote_counts': df['Remote_Label'].value_counts().reset_index(),
        'trend_data': trend_data,
        'kpis': {
            'Всего вакансий': f"{len(df):,}",
            'Компаний': f"{df['company'].nunique():,}",
            'Средняя ЗП': f"${df['Salary'].mean():,.0f}" if df['Salary'].notna().any() else "N/A",
            'Медианная ЗП': f"${df['Salary'].median():,.0f}" if df['Salary'].notna().any() else "N/A",
            'Удаленная работа %': f"{df['Is_Remote'].mean()*100:.1f}%",
            'Срочный найм': f"{df['urgently_hiring'].sum():,}",
        }
    }


if __name__ == '__main__':
    # Тест
    df = load_and_process_data(force_reload=True)
    print(f"\nDataFrame shape: {df.shape}")
    print(f"Columns: {df.columns.tolist()}")
