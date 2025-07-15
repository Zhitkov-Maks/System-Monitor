import subprocess
import re
import json


def print_table(stats: dict) -> None:
    """
    Вывод информации о диске.

    :param stats: Информация о диске в виде словаря.
    """
    print("\n" + "="*45)
    print("💾 АНАЛИЗ СОСТОЯНИЯ ДИСКА".center(45))
    print("="*45, end="")
    print("\n| {:<21} | {:<17} |".format('Параметр', 'Значение'))
    print("-" * 45)
    for param, value in stats.items():
        print("| {:<21} | {:<17} |".format(param, value))
    print("-" * 45)


def parse_nvme_stats(json_data: str) -> dict:
    """
    Парсинг полученной информации о ssd/
    
    :param json_data: Строка с данными.
    """

    stats = json.loads(json_data)

    # Конвертируем температуру из Кельвинов в Цельсии
    temp_c = stats['temperature'] - 273

    # Рассчитываем записанные данные
    # (1 unit = 1000 sectors, sector = 512 bytes -> ~0.5MB)
    written_tb = round(stats['data_units_written'] * 1000 * 512 / (1024**4), 2)

    return {
        "Износ SSD": f"{stats['percent_used']}%",
        "Температура": f"{temp_c}°C",
        "Остаточный ресурс": f"{stats['avail_spare']}%",
        "Записано данных": f"{written_tb} TB",
        "Часы работы": f"{
            stats['power_on_hours']
            }(ч)/{int(stats['power_on_hours']) // 24}(дн)",
        "Циклов включения": stats['power_cycles'],
        "Аварийные выключения": stats['unsafe_shutdowns'],
        "Ошибки носителя": stats['media_errors']
    }


def get_root_disk() -> str:
    """
    Получение информации о диске на котором
    установлена система.
    """
    root_disk = subprocess.run(
            "df --output=source /",
            shell=True,
            capture_output=True,
            text=True
        ).stdout.splitlines()[1]
    return re.sub(r"n\d+p\d+$", "", root_disk)


def main():
    """
    Получение непосредственно информации о ssd. Пока только
    диски nvme.
    """
    try:
        disk = get_root_disk()
        print(f"Анализ SSD: {disk}")

        result = subprocess.run(
            f"sudo nvme smart-log {disk} --output-format=json",
            shell=True,
            text=True,
            capture_output=True
        )

        if result.returncode != 0:
            raise Exception(f"Ошибка выполнения команды: {result.stderr}")

        stats = parse_nvme_stats(result.stdout)

        print_table(stats=stats)

    except json.JSONDecodeError:
        print("Ошибка: Не удалось разобрать JSON-данные")
    except Exception as e:
        print(f"Ошибка: {e}")
