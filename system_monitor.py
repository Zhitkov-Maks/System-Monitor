#!/usr/bin/env python3
import time
import curses
import shutil
import os
from asyncio import AbstractEventLoop
from concurrent.futures import ThreadPoolExecutor
import asyncio
from typing import List


def safe_addstr(win: curses.window, y: int, x: int, text: str) -> None:
    """
    Безопасный вывод текста с обработкой переполнения.
    """
    try:
        win.addstr(y, x, text)
    except curses.error:
        pass


def format_table(title: str, data: list[list[str]]) -> list[str]:
    """
    Форматирует данные в виде таблицы с выравниванием.

    :param title: Название раздела
    :param data: Список с данными.
    """
    max_key_len: int = max(len(str(item[0])) for item in data) + 2
    formatted: list[str] = [title, "─" * (max_key_len + 20)]

    for item in data:
        key = f"│ {item[0]}"
        value = str(item[1])
        formatted.append(f"{key:<{max_key_len}} │ {value:>15} │")

    formatted.append("─" * (max_key_len + 20))
    formatted.append("")
    return formatted


def get_cpu_info() -> List[str]:
    """
    Получает информацию о процессоре через системные файлы.

    Returns:
        List[str]: Отформатированные строки с информацией о процессоре

    Raises:
        FileNotFoundError: если отсутствуют системные файлы
        PermissionError: если нет прав на чтение файлов
        ValueError: при ошибках парсинга числовых значений
        RuntimeError: при других ошибках получения данных
    """
    cpuinfo_path = '/proc/cpuinfo'
    loadavg_path = '/proc/loadavg'
    cpu_data: List[List[str]] = []

    try:
        # Чтение и парсинг cpuinfo один раз
        try:
            with open(cpuinfo_path, 'r', encoding='utf-8') as file:
                cpuinfo = file.read()

                # Количество ядер/потоков
                cores = cpuinfo.count('processor\t:')
                cpu_data.append(["Ядер/потоков", str(cores)])

                # Частота процессора
                freq = "N/A"
                for line in cpuinfo.split('\n'):
                    if line.startswith('cpu MHz'):
                        try:
                            freq_val = float(line.split(':')[1].strip()) / 1000
                            freq = f"{freq_val:.2f} GHz"
                        except (ValueError, IndexError):
                            pass
                        break
                cpu_data.append(["Частота", freq])

        except (FileNotFoundError, PermissionError) as err:
            raise RuntimeError(f"Ошибка чтения {cpuinfo_path}: {err}") from err

        # Чтение нагрузки
        try:
            with open(loadavg_path, 'r', encoding='utf-8') as file:
                load_parts = file.read().strip().split()
                if len(load_parts) >= 3:
                    try:
                        load = (f"{float(load_parts[0]):.2f}"
                                f"/{float(load_parts[1]):.2f}"
                                f"/{float(load_parts[2]):.2f}")

                    except ValueError:
                        load = "/".join(load_parts[:3])
                    cpu_data.append(["Нагрузка (1/5/15)", load])

        except (FileNotFoundError, PermissionError):
            cpu_data.append(["Нагрузка", "N/A"])

        # Получение температур
        try:
            temps: List[List[str]] = get_core_temperatures()
            if temps and temps != [["Температура CPU", "N/A"]]:
                cpu_data.extend(temps)
        except (
                PermissionError, FileNotFoundError, ValueError, OSError
        ) as err:
            cpu_data.append(["Температура", f"Ошибка: {err}"])

        return format_table("ПРОЦЕССОР", cpu_data)

    except Exception as err:
        return format_table("ПРОЦЕССОР", [["Ошибка", str(err)]])


def get_core_temperatures() -> List[List[str]]:
    """
    Получает температуры ядер CPU через интерфейс /sys/class/hwmon.

    Returns:
        List[List[str]]: Список списков формата [["Лейбл", "Температура"], ...]

    Raises:
        PermissionError: Если нет прав доступа к файлам
        FileNotFoundError: Если отсутствуют необходимые файлы
        ValueError: Если данные в файлах некорректны
        OSError: Для других ошибок ввода-вывода
    """
    temps: List[List[str]] = []
    hwmon_dir: str = '/sys/class/hwmon'
    cpu_keywords: tuple = ('core', 'cpu', 'package', 'tdie', 'tctl')

    try:
        hwmon_devices: List[str] = [
            dir_ for dir_ in os.listdir(hwmon_dir)
            if os.path.isdir(os.path.join(hwmon_dir, dir_))
        ]

    except (PermissionError, FileNotFoundError, OSError) as err:
        raise type(e)(f"Ошибка доступа к {hwmon_dir}: {err}")

    for device in hwmon_devices:
        device_path: str = os.path.join(hwmon_dir, device)
        try:
            device_files: List[dir] = os.listdir(device_path)
        except OSError:
            continue

        temp_inputs: List[str] = [
            file for file in device_files
            if file.startswith('temp') and file.endswith('_input')
        ]

        for temp_file in temp_inputs:
            try:
                # Получаем базовое имя (temp1, temp2 и т.д.)
                base_name: str = temp_file.split('_')[0]

                # Чтение метки
                label_file: str = f"{base_name}_label"
                label_path: str = os.path.join(device_path, label_file)
                label: str = base_name

                if os.path.exists(label_path):
                    try:
                        with open(label_path, 'r') as file:
                            label = file.read().strip()
                    except (OSError, UnicodeDecodeError):
                        pass

                # Чтение температуры
                temp_path: str = os.path.join(device_path, temp_file)
                try:
                    with open(temp_path, 'r') as file:
                        temp_str = file.read().strip()
                        if not temp_str:
                            continue

                        temp: float = float(temp_str) / 1000
                        if temp < 0:  # Проверка на корректность
                            continue
                except (ValueError, OSError):
                    continue

                # Фильтрация CPU температур
                if any(kw in label.lower() for kw in cpu_keywords):
                    temps.append([label, f"{temp:.1f}°C"])

            except OSError:
                continue

    if not temps:
        return [["Температура CPU", "N/A"]]

    temps.sort(key=lambda x: x[0])
    return temps


def get_disk_info() -> List[str]:
    """Информация о диске, используя утилиту shutil."""
    disk_usage = shutil.disk_usage('/')
    total_gb: float = disk_usage.total / (1024 ** 3)
    used_gb: float = disk_usage.used / (1024 ** 3)
    free_gb: float = disk_usage.free / (1024 ** 3)
    used_percent: float = (disk_usage.used / disk_usage.total) * 100
    reserved_gb: float = total_gb - (used_gb + free_gb)

    return format_table("ДИСКОВОЕ ПРОСТРАНСТВО", [
        ["Всего", f"{total_gb:.2f} ГБ"],
        ["Использовано", f"{used_gb:.2f} ГБ"],
        ["Свободно", f"{free_gb:.2f} ГБ"],
        ["Зарезервировано", f"{reserved_gb:.2f} ГБ"],
        ["Занято", f"{used_percent:.2f}%"]
    ])


def get_memory_info() -> List[str]:
    """Информация о памяти через /proc/meminfo"""
    try:
        with open('/proc/meminfo') as f:
            meminfo: dict[str, str] = {}
            for line in f:
                key, value = line.split(':', 1)
                meminfo[key] = value.strip().split()[0]

        total: int = int(meminfo['MemTotal'])
        available: int = int(meminfo.get(
            'MemAvailable', meminfo.get('MemFree', 0))
        )
        used: int = total - available
        used_percent: float = (used / total) * 100

        return format_table("ОПЕРАТИВНАЯ ПАМЯТЬ", [
            ["Всего", f"{round(total / 1048576, 2)} ГБ"],
            ["Доступно", f"{round(available / 1048576, 2)} ГБ"],
            ["Использовано", f"{round(used / 1048576, 2)} ГБ"],
            ["Использовано %", f"{round(used_percent, 2)}%"]
        ])
    except FileNotFoundError as err:
        return format_table(
            "ОПЕРАТИВНАЯ ПАМЯТЬ",
            [["Ошибка", f"Файл не найден: {err}"]]
        )
    except PermissionError as err:
        return format_table(
            "ОПЕРАТИВНАЯ ПАМЯТЬ",
            [["Ошибка", f"Нет прав доступа: {err}"]]
        )
    except (IOError, OSError) as err:
        return format_table(
            "ОПЕРАТИВНАЯ ПАМЯТЬ",
            [["Ошибка", f"Ошибка ввода-вывода: {err}"]]
        )
    except (ValueError, KeyError) as err:
        return format_table(
            "ОПЕРАТИВНАЯ ПАМЯТЬ",
            [["Ошибка", f"Некорректные данные: {err}"]]
        )


def get_cpu_usage(interval=1) -> List[str]:
    """
    Возвращает информацию о загрузке CPU.

    :param interval: Number seconds.
    """
    def read_cpu_stats() -> List[str]:
        """Читает текущие значения из /proc/stat"""
        with open('/proc/stat') as file:
            cpu_lines = [line for line in file if line.startswith('cpu')]
        return cpu_lines

    def parse_cpu_stats(cpu_lines) -> List[List[int]]:
        """Разбирает строки из /proc/stat и возвращает список значений"""
        stats: List[List[int]] = []
        for line in cpu_lines:
            parts = line.split()
            stats.append([int(x) for x in parts[1:]])
        return stats

    try:
        # Первое чтение данных
        cpu_lines1: List[str] = read_cpu_stats()
        stats1: List[List[int]] = parse_cpu_stats(cpu_lines1)

        # Ждём указанный интервал, по умолчанию 1с.
        time.sleep(interval)

        # Второе чтение данных
        cpu_lines2: List[str] = read_cpu_stats()
        stats2: List[List[int]] = parse_cpu_stats(cpu_lines2)

        # Рассчитываем разницу между двумя временными точками
        diffs: List[List[int]] = []
        for i in range(len(stats1)):
            diff = [stats2[i][j] - stats1[i][j] for j in range(len(stats1[i]))]
            diffs.append(diff)

        # Обрабатываем общую статистику CPU
        total_diff: List[int] = diffs[0]
        user, nice, system, idle, iowait, irq, softirq, steal = total_diff[:8]
        total: int = (user + nice + system +
                      idle + iowait + irq + softirq + steal)
        used: int = total - idle - iowait

        # Рассчитываем проценты
        usage_percent: float = 100 * (used / total) if total > 0 else 0
        user_percent: float = 100 * (user + nice) / total if total > 0 else 0
        system_percent: float = (100 * (system + irq + softirq)
                                 / total) if total > 0 else 0
        io_percent: float = 100 * iowait / total if total > 0 else 0

        # Формируем базовую информацию
        cpu_data = [
            ["Средняя загрузка", f"{usage_percent:.1f}%"],
            ["Пользовательские процессы", f"{user_percent:.1f}%"],
            ["Системные процессы", f"{system_percent:.1f}%"],
            ["Ожидание I/O", f"{io_percent:.1f}%"],
        ]
        return format_table("ЗАГРУЗКА CPU", cpu_data)

    except FileNotFoundError as err:
        return format_table(
            "ЗАГРУЗКА CPU",
            [["Ошибка", f"Файл не найден: {err}"]]
        )
    except PermissionError as err:
        return format_table(
            "ЗАГРУЗКА CPU",
            [["Ошибка", f"Нет прав доступа: {err}"]]
        )
    except (IOError, OSError) as err:
        return format_table(
            "ЗАГРУЗКА CPU",
            [["Ошибка", f"Ошибка ввода-вывода: {err}"]]
        )
    except ValueError as err:
        return format_table(
            "ЗАГРУЗКА CPU",
            [["Ошибка", f"Некорректные данные: {err}"]]
        )
    except IndexError as err:
        return format_table(
            "ЗАГРУЗКА CPU",
            [["Ошибка", f"Некорректная структура данных: {err}"]]
        )


def time_sleep(seconds=1):
    """
    Функция для синхронизации времени обновления данных.
    Все остальные функции уже должны будут собрать необходимые
    данные.
    """
    time.sleep(seconds)
    return []


async def run_main(stdscr: curses.window) -> None:
    """Основная функция, принимающая curses-окно.

    Args:
        stdscr (curses.window): Главное окно curses, используемое для вывода
    """
    try:
        curses.curs_set(0)
        stdscr.nodelay(1)

        while True:
            start_time: time = time.time()
            try:
                stdscr.clear()
                height, width = stdscr.getmaxyx()
                y = 0  # Высота

                # Получаем динамические данные асинхронно
                with ThreadPoolExecutor(max_workers=4) as pool:
                    loop: AbstractEventLoop = asyncio.get_running_loop()
                    tasks: list = [
                        loop.run_in_executor(pool, get_disk_info),
                        loop.run_in_executor(pool, get_cpu_usage),
                        loop.run_in_executor(pool, get_memory_info),
                        loop.run_in_executor(pool, get_cpu_info),
                        loop.run_in_executor(pool, time_sleep)
                    ]
                    results = await asyncio.gather(*tasks)

                    # Выводим динамические данные
                    for section in results:
                        for line in section:
                            if y >= height - 1:
                                break
                            safe_addstr(stdscr, y, 0, line[:width - 1])
                            y += 1

                # Статусная строка
                elapsed: float = time.time() - start_time
                time_str = (f"Обновлено: {time.strftime('%H:%M:%S')} "
                            f"| Q-выход | Задержка: {elapsed:.1f}с")
                safe_addstr(stdscr, height - 1, 0, time_str[:width - 1])
                stdscr.refresh()

                if stdscr.getch() in (ord('q'), ord('Q')):
                    break

            except curses.error:
                pass
    except KeyboardInterrupt:
        pass

    finally:
        try:
            curses.endwin()
        except curses.error:
            pass


def main(stdscr) -> None:
    """Запуск асинхронной функции."""
    asyncio.run(run_main(stdscr))


if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except Exception as e:
        print(f"Ошибка: {e}")
    print("Мониторинг остановлен")
