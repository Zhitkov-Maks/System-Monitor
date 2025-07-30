from typing import List
import os

from table import format_table, create_separator

from util import error_decorate


@error_decorate((FileNotFoundError, PermissionError, ValueError, OSError))
def get_cpu_info() -> List[str]:
    """Обработка информации о загрузке ядер."""
    cpu_pairs: List[List[str]] = get_core_temperatures()

    # Если нет данных, просто выводим как есть
    if not cpu_pairs or cpu_pairs == [["Температура CPU", "N/A"]]:
        data = cpu_pairs
    else:
        half = (len(cpu_pairs) + 1) // 2  # разбиваем на две части

        data = []
        # Первая половина
        headers1 = [pair[0] for pair in cpu_pairs[:half]]
        values1 = [pair[1] for pair in cpu_pairs[:half]]
        data.append(headers1)
        data.append(values1)
        data.append(create_separator(headers1))

        # Вторая половина (если есть)
        if len(cpu_pairs) > half:
            headers2 = [pair[0] for pair in cpu_pairs[half:]]
            values2 = [pair[1] for pair in cpu_pairs[half:]]
            data.append(headers2)
            data.append(values2)

    return format_table("ТЕМПЕРАТУРА ЯДЕР", data)


def get_hwmon_devices(hwmon_dir: str) -> list[str]:
    """Получаем необходимое датчики для порлучения температуры."""
    return [
        d for d in os.listdir(hwmon_dir)
        if os.path.isdir(os.path.join(hwmon_dir, d))
    ]


def get_core_label(temp_file: str, device_path: str) -> str:
    """Получаем метку ядра."""
    base: str = temp_file.split('_')[0]
    label_path: str = os.path.join(device_path, f"{base}_label")
    label = base
    if os.path.exists(label_path):
        with open(label_path) as f:
            label = f.read().strip()
    return label


@error_decorate((FileNotFoundError, OSError, PermissionError))
def get_temperature(temp_path: str) -> float:
    """
    Получаем температуру для ядра.

    :param temp_path: Путь для чтения.
    """
    with open(temp_path) as f:
        temp_str: str = f.read().strip()
        temp_val: float = float(temp_str) / 1000
        if temp_val and temp_val > 0:
            return temp_val


@error_decorate((FileNotFoundError, PermissionError, ValueError, OSError))
def get_core_temperatures() -> List[List[str]]:
    """Нахождение температуры для каждого ядра."""
    hwmon_dir = '/sys/class/hwmon'
    cpu_keywords = ('core', 'cpu', 'package', 'tdie', 'tctl')
    temps: List[List[str]] = []

    hwmon_devices = get_hwmon_devices(hwmon_dir)
    for device in hwmon_devices:
        device_path = os.path.join(hwmon_dir, device)
        files = os.listdir(device_path)
        temp_inputs = [
            f for f in files if f.startswith('temp') and f.endswith('_input')
        ]
        for temp_file in temp_inputs:
            label: str = get_core_label(temp_file, device_path)

            temp_path = os.path.join(device_path, temp_file)
            temp_val = get_temperature(temp_path)

            if any(kw in label.lower() for kw in cpu_keywords):
                temps.append([label, f"{temp_val:.1f}°C"])

    if not temps:
        return [["Температура CPU", "N/A"]]
    temps.sort(key=lambda x: x[0])
    return temps
