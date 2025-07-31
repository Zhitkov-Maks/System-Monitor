import os
from typing import List


from util import error_decorate
from core import get_hwmon_devices
from table import format_table


def get_hwmon_data(path: str) -> str | None:
    """
    Чтение данных из файла.

    :param path: Путь к файлу.
    """
    result = 0
    if os.path.isdir(path):
        return result
    with open(path) as file:
        return file.read()


def append_data(
    name: str, val: str, mark: str, lst: list[list]
) -> None:
    """
    Формирование списка для отображения.

    :param name: Название параметра.
    :param val: Значение параметра.
    :param mark: Метка о норме.
    :param lst: Список для формирования.
    """
    lst[0].append(name)
    lst[1].append(val)
    lst[2].append(mark)


def mark_voltage(val: float) -> str:
    """
    Получаем метку о напряжении.
    :param val:
    """
    if 12.8 >= val >= 12.6:
        return "Заряжена"
    elif 10.6 < val < 12.6:
        return "В норме"
    elif val < 10.6:
        return "Критический"
    else:
        return "Неисправность"


def get_mark_fan(val: float) -> str:
    """
    Определяем нагрузку вентилятора.
    :param val: Значение нагрузки.
    """
    if val < 2500:
        return "Нет нагрузки"
    elif val < 4000:
        return "Средняя нагрузка"
    elif val < 6000:
        return "Высокая нагрузка"
    else:
        return "Максимальная нагрузка"


def get_mark_power(val: int) -> str:
    """
    Получаем информацию о мощности.
    :param val: Значение мощности.
    """
    if 10 >= val:
        return "Простая нагузка(4-8ч)"
    elif 25 >= val > 10:
        return "Средняя(2-3ч)"
    elif 35 >= val > 25:
        return "Высокая(1-1,5ч)"
    else:
        "Максимальная(<1ч)"


def find_path_for_writing(device_path, files: list[str], lst: list[list]):
    """
    Находим нужные пути для чтения файлов с нужными данными.
    :param device_path: Базовый буть.
    :param files: Список с файлами.
    :param lst: Список для отображения на дисплее.
    """
    for f in files:
        full_path = os.path.join(device_path, f)
        if f == 'in0_input':
            result = get_hwmon_data(full_path)
            append_data(
                name="Напряжение(бат)",
                val=f"{round(int(result)/1000, 2)} В",
                mark=mark_voltage(round(int(result)/1000, 2)),
                lst=lst
            )

        if f == 'fan1_input':
            result = get_hwmon_data(full_path)
            append_data(
                name="Скорость вентилятора",
                val=f"{result.rstrip("\n")} Об/мин",
                mark=get_mark_fan(int(result.rstrip("\n"))),
                lst=lst
            )

        if 'power1_input' in f:
            result = int(get_hwmon_data(full_path))
            result
            result = round(result / 1000000, 3)
            append_data(
                name="Мощность(разряд/бат)",
                val=result,
                mark=get_mark_power(result),
                lst=lst
            )


@error_decorate((FileNotFoundError, PermissionError, ValueError, OSError))
def get_fan_and_in() -> List[List[str]]:
    """Нахождение температуры для каждого ядра."""
    hwmon_dir = '/sys/class/hwmon'
    data = [[], [], []]

    hwmon_devices = get_hwmon_devices(hwmon_dir)
    for device in hwmon_devices:
        device_path = os.path.join(hwmon_dir, device)
        files_path = os.listdir(device_path)
        find_path_for_writing(device_path, files_path, data)
    return format_table("ПРОЧИЕ ДАТЧИКИ", data)
