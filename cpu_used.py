import time
from typing import List

from util import error_decorate
from table import format_table, create_separator


def read_cpu_stats() -> List[str]:
    """Читает текущие значения из /proc/stat."""
    with open('/proc/stat') as file:
        return [line for line in file if line.startswith('cpu')]


def parse_cpu_stats(cpu_lines) -> List[List[int]]:
    """Разбирает строки из /proc/stat и возвращает список значений"""
    stats: List[List[int]] = []
    for line in cpu_lines:
        parts = line.split()
        stats.append([int(x) for x in parts[1:]])
    return stats


@error_decorate((FileNotFoundError, PermissionError, ValueError, OSError))
def get_cpu_frequencies() -> List[float]:
    """Получение частот по каждому ядру."""
    freqs: list[float] = []
    with open('/proc/cpuinfo', 'r', encoding='utf-8') as file:
        cpuinfo = file.read()
    for processor_section in cpuinfo.strip().split('\n\n'):
        for line in processor_section.split('\n'):
            if line.startswith('cpu MHz'):
                mhz = float(line.split(':')[1].strip())
                freqs.append(mhz)
                break
    return freqs


def aggreagate_data_core(data: list) -> float:
    """
    Высчитываем процент загрузки для каждого ядра.

    :param data: Список с данными по ядру.
    """
    user, nice, system, idle, iowait, irq, softirq, steal = data[:8]
    core_total: int = (
        user + nice + system + idle + iowait + irq + softirq + steal
    )
    core_used: int = core_total - idle - iowait
    return 100 * (core_used / core_total) if core_total > 0 else 0


def get_frequency(freques: list, ind: int) -> str:
    """
    Получение частоты ядра и возвращение в виде строки.
    """
    freq = ""
    if freques and ind - 1 < len(freques):
        freq_ghz = freques[ind-1] / 1000
        freq = f"{freq_ghz:.2f}GHz"
    return freq


def get_general_statistic(
    diffs: list,
    freqs: List[float],
    cores_per_row=10
) -> list[str]:
    """
    Обработка данных и формирования списка для отображения
    на дисплее в виде таблицы.
    """
    cpu_data: list[list[str]] = []
    core_names: list[str] = []
    core_percents: list[str] = []
    core_freq: list[str] = []

    for i, diff in enumerate(diffs[1:], start=1):
        if len(diff) < 8:
            continue
        core_percent: float = aggreagate_data_core(diff)
        freq_str: str = get_frequency(freqs, i)

        core_names.append(f"Core {i}")
        core_percents.append(f"{core_percent:.0f}%")
        core_freq.append(freq_str)

        if len(core_names) == cores_per_row or i == len(diffs) - 1:

            cpu_data.append(core_names)
            cpu_data.append(core_percents)
            cpu_data.append(core_freq)

            if i < len(diffs) - 1:
                separator = create_separator(core_names)
                cpu_data.append(separator)

            core_names, core_percents, core_freq = [], [], []

    return format_table("ЗАГРУЗКА CPU", cpu_data)


@error_decorate((FileNotFoundError, PermissionError, ValueError, OSError))
def get_cpu_usage(interval=1) -> List[str]:
    """
    Запрашивает данные для замера использования CPU и
    отправляет на группировку и обработку.
    :param interval: По умолчанию 1 секунда.
    """
    cpu_lines1 = read_cpu_stats()
    stats1 = parse_cpu_stats(cpu_lines1)

    time.sleep(interval)

    cpu_lines2 = read_cpu_stats()
    stats2 = parse_cpu_stats(cpu_lines2)

    diffs: list[list[int]] = []
    for i in range(len(stats1)):
        diff = [stats2[i][j] - stats1[i][j] for j in range(len(stats1[i]))]
        diffs.append(diff)

    freqs: list[float] = get_cpu_frequencies()
    return get_general_statistic(diffs, freqs)
