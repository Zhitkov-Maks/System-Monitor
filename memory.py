from util import error_decorate
from table import format_table


@error_decorate((FileNotFoundError, PermissionError, ValueError, OSError))
def get_memory_info():
    """Информация о памяти через /proc/meminfo"""
    with open('/proc/meminfo') as file:
        meminfo: dict[str, str] = {}
        for line in file:
            key, value = line.split(':', 1)
            meminfo[key] = value.strip().split()[0]

    total: int = int(meminfo['MemTotal'])
    available: int = int(meminfo.get(
        'MemAvailable', meminfo.get('MemFree', 0))
    )
    used: int = total - available
    used_percent: float = (used / total) * 100
    swap_total: float = round(int(meminfo.get('SwapTotal')) / 1048576, 2)
    swap_free: float = round(int(meminfo.get('SwapFree')) / 1048576, 2)
    swap_used: float = round(int(meminfo.get('SwapCached')) / 1048576, 2)
    cashed: float = round(int(meminfo.get('Cached')) / 1048576, 2)

    # Создаем шкалу
    bar_length = 20
    filled = int(round(bar_length * used_percent / 100))
    bar = f"[{'='*filled}{' '*(bar_length-filled)}]"

    return format_table("ОПЕРАТИВНАЯ ПАМЯТЬ", [
        ["Всего", f"{round(total / 1048576, 2)} ГБ"],
        ["Доступно", f"{round(available / 1048576, 2)} ГБ"],
        ["Использовано", f"{round(used / 1048576, 2)} ГБ"],
        ['Кэш', f"{cashed} ГБ"],
        ["SWAP", f"{swap_total} ГБ"],
        ["SWAP используеться", f"{swap_used} ГБ"],
        ["SWAP свободно", f"{swap_free} ГБ"],
        ["Использовано %", f"{round(used_percent, 2)}%"],
        ["Шкала", bar]
    ])
