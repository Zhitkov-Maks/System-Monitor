from typing import List
import os

from util import error_decorate
from table import format_table, create_separator


@error_decorate((FileNotFoundError, PermissionError, ValueError, OSError))
def get_cpu_info() -> List[str]:
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


@error_decorate((FileNotFoundError, PermissionError, ValueError, OSError))
def get_core_temperatures() -> List[List[str]]:
    temps: List[List[str]] = []
    hwmon_dir = '/sys/class/hwmon'
    cpu_keywords = ('core', 'cpu', 'package', 'tdie', 'tctl')

    try:
        hwmon_devices = [
            d for d in os.listdir(hwmon_dir)
            if os.path.isdir(os.path.join(hwmon_dir, d))
        ]
    except Exception:
        return [["Температура CPU", "N/A"]]

    for device in hwmon_devices:
        device_path = os.path.join(hwmon_dir, device)
        try:
            files = os.listdir(device_path)
        except Exception:
            continue

        temp_inputs = [f for f in files if f.startswith('temp') and f.endswith('_input')]
        for temp_file in temp_inputs:
            base = temp_file.split('_')[0]
            label_path = os.path.join(device_path, f"{base}_label")
            label = base
            if os.path.exists(label_path):
                try:
                    with open(label_path) as f:
                        label = f.read().strip()
                except Exception:
                    pass

            temp_path = os.path.join(device_path, temp_file)
            try:
                with open(temp_path) as f:
                    temp_str = f.read().strip()
                    if not temp_str:
                        continue
                    temp_val = float(temp_str) / 1000
                    if temp_val < 0:
                        continue
            except Exception:
                continue

            if any(kw in label.lower() for kw in cpu_keywords):
                temps.append([label, f"{temp_val:.1f}°C"])

    if not temps:
        return [["Температура CPU", "N/A"]]

    temps.sort(key=lambda x: x[0])
    return temps
