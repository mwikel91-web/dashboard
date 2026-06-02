"""
Запуск дашборда с публичным доступом через интернет

Два метода:
1. cloudflared (Cloudflare Tunnel) - БЕЗ регистрации, рекомендуется
2. pyngrok (ngrok) - требует регистрацию на ngrok.com

Использование:
1. Скачать cloudflared: https://github.com/cloudflare/cloudflared/releases
   - Windows: cloudflared-windows-amd64.exe -> переименовать в cloudflared.exe
   - Положить в PATH или в папку dashboard_app

2. Запустить:
   python run_public.py

3. После запуска появится ссылка вида https://xxxx.trycloudflare.com
   Эту ссылку можно отправить кому угодно для доступа к дашборду.

Остановка: Ctrl+C

Альтернатива (ngrok):
   python run_public.py --ngrok
"""

import sys
import os
import subprocess
import threading
import time
import signal

# Добавляем текущую директорию в путь для импортов
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def find_cloudflared():
    """Ищет cloudflared в PATH и текущей директории"""
    # Проверяем в PATH
    try:
        result = subprocess.run(['cloudflared', '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            return 'cloudflared'
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Проверяем в текущей директории
    script_dir = os.path.dirname(os.path.abspath(__file__))
    for name in ['cloudflared.exe', 'cloudflared-windows-amd64.exe', 'cloudflared']:
        path = os.path.join(script_dir, name)
        if os.path.exists(path):
            return path

    return None


def run_with_cloudflared():
    """Запуск с Cloudflare Tunnel (без регистрации)"""
    cloudflared = find_cloudflared()

    if not cloudflared:
        print("=" * 60)
        print("ОШИБКА: cloudflared не найден!")
        print("=" * 60)
        print("\nСкачайте cloudflared:")
        print("  https://github.com/cloudflare/cloudflared/releases")
        print("\nДля Windows: cloudflared-windows-amd64.exe")
        print("Переименуйте в cloudflared.exe и положите в эту папку")
        print("\nИли используйте ngrok: python run_public.py --ngrok")
        sys.exit(1)

    from dash import Dash
    import dash_bootstrap_components as dbc
    from data_loader import load_and_process_data, get_aggregated_data
    from layouts import create_layout
    from callbacks import register_callbacks

    print("=" * 60)
    print("Job Market Dashboard - ПУБЛИЧНЫЙ ДОСТУП (Cloudflare)")
    print("=" * 60)

    print("\nЗагрузка данных...")
    df = load_and_process_data(force_reload=False)
    agg_data = get_aggregated_data(df)
    print(f"Загружено: {len(df)} записей")

    app = Dash(__name__,
               external_stylesheets=[dbc.themes.FLATLY],
               suppress_callback_exceptions=True)
    app.title = "Job Market Intelligence Dashboard"

    categories = agg_data['category_counts']['Category'].unique()
    cities = agg_data['city_counts']['City'].unique()
    salary_ranges = agg_data['salary_range_counts']['Range'].unique()

    app.layout = create_layout(
        kpis=agg_data['kpis'],
        categories=categories,
        cities=cities,
        salary_ranges=salary_ranges
    )

    register_callbacks(app, df)

    port = 8050
    tunnel_process = None

    def start_tunnel():
        nonlocal tunnel_process
        time.sleep(5)  # Ждём пока сервер полностью запустится
        print("\nСоздание туннеля Cloudflare...")
        print("(Если ссылка не работает, подождите 30-60 секунд)")
        tunnel_process = subprocess.Popen(
            [cloudflared, 'tunnel', '--url', f'http://127.0.0.1:{port}',
             '--no-tls-verify', '--retries', '5'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Читаем вывод чтобы найти URL
        url_found = False
        for line in tunnel_process.stderr:
            print(f"[tunnel] {line.strip()}")
            if 'trycloudflare.com' in line or '.trycloudflare.com' in line:
                # Извлекаем URL
                import re
                match = re.search(r'https://[a-z0-9-]+\.trycloudflare\.com', line)
                if match:
                    url = match.group(0)
                    print("\n" + "=" * 60)
                    print("ДАШБОРД ЗАПУЩЕН И ДОСТУПЕН ЧЕРЕЗ ИНТЕРНЕТ!")
                    print("=" * 60)
                    print(f"\nПубличная ссылка: {url}")
                    print(f"Локальный адрес:  http://127.0.0.1:{port}")
                    print("\nВАЖНО: Подождите 30-60 секунд перед открытием ссылки!")
                    print("Cloudflare нужно время для установки соединения.")
                    print("\nОтправьте публичную ссылку кому угодно.")
                    print("Для остановки нажмите Ctrl+C")
                    print("=" * 60 + "\n")
                    url_found = True
                    break

    # Запускаем туннель в отдельном потоке
    tunnel_thread = threading.Thread(target=start_tunnel, daemon=True)
    tunnel_thread.start()

    # Запуск сервера
    try:
        app.run(debug=False, host='0.0.0.0', port=port)
    except KeyboardInterrupt:
        print("\n\nОстановка сервера...")
        if tunnel_process:
            tunnel_process.terminate()
        print("Сервер остановлен.")


def run_with_ngrok():
    """Запуск с ngrok (требует регистрацию на ngrok.com)"""
    try:
        from pyngrok import ngrok
    except ImportError:
        print("=" * 60)
        print("ОШИБКА: pyngrok не установлен!")
        print("=" * 60)
        print("\nУстановите pyngrok:")
        print("  pip install pyngrok")
        print("\nИли используйте cloudflared: python run_public.py")
        sys.exit(1)

    from dash import Dash
    import dash_bootstrap_components as dbc
    from data_loader import load_and_process_data, get_aggregated_data
    from layouts import create_layout
    from callbacks import register_callbacks

    print("=" * 60)
    print("Job Market Dashboard - ПУБЛИЧНЫЙ ДОСТУП (ngrok)")
    print("=" * 60)

    print("\nЗагрузка данных...")
    df = load_and_process_data(force_reload=False)
    agg_data = get_aggregated_data(df)
    print(f"Загружено: {len(df)} записей")

    app = Dash(__name__,
               external_stylesheets=[dbc.themes.FLATLY],
               suppress_callback_exceptions=True)
    app.title = "Job Market Intelligence Dashboard"

    categories = agg_data['category_counts']['Category'].unique()
    cities = agg_data['city_counts']['City'].unique()
    salary_ranges = agg_data['salary_range_counts']['Range'].unique()

    app.layout = create_layout(
        kpis=agg_data['kpis'],
        categories=categories,
        cities=cities,
        salary_ranges=salary_ranges
    )

    register_callbacks(app, df)

    port = 8050

    print(f"\nЗапуск сервера на порту {port}...")
    print("Создание ngrok туннеля...")

    try:
        public_url = ngrok.connect(port, "http")
        print("\n" + "=" * 60)
        print("ДАШБОРД ЗАПУЩЕН И ДОСТУПЕН ЧЕРЕЗ ИНТЕРНЕТ!")
        print("=" * 60)
        print(f"\nПубличная ссылка: {public_url}")
        print(f"Локальный адрес:  http://127.0.0.1:{port}")
        print("\nОтправьте публичную ссылку кому угодно.")
        print("Для остановки нажмите Ctrl+C")
        print("=" * 60 + "\n")
    except Exception as e:
        print(f"\nОШИБКА: {e}")
        print("\nВозможные решения:")
        print("1. Зарегистрируйтесь на https://ngrok.com (новый аккаунт)")
        print("2. Получите authtoken и выполните: ngrok authtoken ВАШ_ТОКЕН")
        print("3. Или используйте cloudflared: python run_public.py")
        sys.exit(1)

    try:
        app.run(debug=False, host='0.0.0.0', port=port)
    except KeyboardInterrupt:
        print("\n\nОстановка сервера...")
        ngrok.disconnect(public_url)
        ngrok.kill()
        print("Сервер остановлен.")


def run_local_only():
    """Запуск только для локальной сети"""
    from dash import Dash
    import dash_bootstrap_components as dbc
    from data_loader import load_and_process_data, get_aggregated_data
    from layouts import create_layout
    from callbacks import register_callbacks

    print("=" * 60)
    print("Job Market Dashboard - ЛОКАЛЬНАЯ СЕТЬ")
    print("=" * 60)

    df = load_and_process_data(force_reload=False)
    agg_data = get_aggregated_data(df)
    print(f"Загружено: {len(df)} записей")

    app = Dash(__name__,
               external_stylesheets=[dbc.themes.FLATLY],
               suppress_callback_exceptions=True)
    app.title = "Job Market Intelligence Dashboard"

    categories = agg_data['category_counts']['Category'].unique()
    cities = agg_data['city_counts']['City'].unique()
    salary_ranges = agg_data['salary_range_counts']['Range'].unique()

    app.layout = create_layout(
        kpis=agg_data['kpis'],
        categories=categories,
        cities=cities,
        salary_ranges=salary_ranges
    )

    register_callbacks(app, df)

    import socket
    try:
        local_ip = socket.gethostbyname(socket.gethostname())
    except Exception:
        local_ip = "127.0.0.1"

    port = 8050

    print("\n" + "=" * 60)
    print("ДАШБОРД ЗАПУЩЕН!")
    print("=" * 60)
    print(f"\nЛокально:          http://127.0.0.1:{port}")
    print(f"В локальной сети:  http://{local_ip}:{port}")
    print("\nДля доступа из интернета: python run_public.py")
    print("Для остановки нажмите Ctrl+C")
    print("=" * 60 + "\n")

    app.run(debug=False, host='0.0.0.0', port=port)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == '--local':
            run_local_only()
        elif sys.argv[1] == '--ngrok':
            run_with_ngrok()
        else:
            run_with_cloudflared()
    else:
        # По умолчанию используем cloudflared (без регистрации)
        run_with_cloudflared()
