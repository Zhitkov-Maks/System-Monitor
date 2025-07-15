from typing import List


def format_table(title: str, data: list[list[str]]) -> list[str]:
    """
    Форматирует данные в виде таблицы с выравниванием.
    Поддерживает произвольное количество столбцов.

    :param title: Название раздела
    :param data: Список строк, каждая строка — список значений столбцов.
    """
    if not data:
        return [title, "─" * 40, "Нет данных", "─" * 40, ""]

    num_cols: int = max(len(row) for row in data)
    # Находим максимальную ширину колонки по каждому столбцу
    col_widths = [0] * num_cols
    for row in data:
        for i, col in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(col)))

    # Общая ширина таблицы
    # (с ограждениями + 3 символа на каждую колонку: пробел+|+пробел)
    total_width: int = sum(col_widths) + 3 * num_cols + 1

    lines = []
    lines.append(f"{title}".center(total_width))
    lines.append("─" * total_width)

    for row in data:
        line = "│"
        for i in range(num_cols):
            val = row[i] if i < len(row) else ""
            line += " " + str(val).ljust(col_widths[i]) + " │"
        lines.append(line)

    lines.append("─" * total_width)
    lines.append("")
    return lines


def create_separator(headers: List[str]) -> List[str]:
    """
    Добавляет разделитель если строк несколько в таблице.
    """
    return ['─' * len(h) for h in headers]
