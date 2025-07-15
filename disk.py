import shutil
from typing import List

from table import format_table


def get_disk_info() -> List[str]:
    """Информация о диске в виде горизонтальной таблицы."""
    disk_usage = shutil.disk_usage('/')
    total_gb: float = disk_usage.total / (1024 ** 3)
    used_gb: float = disk_usage.used / (1024 ** 3)
    free_gb: float = disk_usage.free / (1024 ** 3)
    used_percent: float = (disk_usage.used / disk_usage.total) * 100
    reserved_gb: float = total_gb - (used_gb + free_gb)

    keys = ["Всего", "Использовано", "Свободно", "Зарезервировано", "Занято"]
    values = [
        f"{total_gb:.2f} ГБ",
        f"{used_gb:.2f} ГБ",
        f"{free_gb:.2f} ГБ",
        f"{reserved_gb:.2f} ГБ",
        f"{used_percent:.2f}%"
    ]

    data = [keys, values]

    return format_table("ДИСКОВОЕ ПРОСТРАНСТВО", data)
