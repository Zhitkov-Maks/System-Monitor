#!/usr/bin/env python3
import time
import curses
import asyncio
import sys
from asyncio import AbstractEventLoop
from concurrent.futures import ThreadPoolExecutor
from asyncio.exceptions import CancelledError

import ssd_info
from util import error_decorate
from cpu_used import get_cpu_usage
from disk import get_disk_info
from core import get_cpu_info
from memory import get_memory_info


def safe_addstr(
    win: curses.window,
    y: int,
    x: int,
    text: str,
    color=None
) -> None:
    """Безопасный вывод текста с цветом"""
    try:
        if color:
            win.addstr(y, x, text, color)
        else:
            win.addstr(y, x, text)
    except curses.error:
        pass


def time_sleep(seconds=1):
    """
    Функция для синхронизации времени обновления данных.
    Все остальные функции уже должны будут собрать необходимые
    данные.
    """
    time.sleep(seconds)
    return []


@error_decorate((KeyboardInterrupt, CancelledError))
def display_app(lst_info: list, stdscr, start_time) -> None:
    """
    Отображение собранных данных для мониторинга.

    :param lst_info: Двумерный список с собранными данными.
    :param stdsrc: Отображение на дисплее данных.
    :param start time: Начальное время старта.
    """
    stdscr.nodelay(1)  # type: ignore
    stdscr.clear()
    height, width = stdscr.getmaxyx()
    y = 0  # Высота
    for section in lst_info:
        for line in section:
            if y >= height - 1:
                safe_addstr(stdscr, y, 0, line[:width-1])
            else:
                safe_addstr(stdscr, y, 0, line[:width-1])
            y += 1

    elapsed = time.time() - start_time
    time_str = (f"Обновлено: {time.strftime('%H:%M:%S')} "
                f"| Q-выход | Задержка: {elapsed:.1f}с | D-ssd info |")
    safe_addstr(stdscr, height - 1, 0, time_str[:width - 1])
    stdscr.refresh()

    ch = stdscr.getch()

    if ch in (ord('q'), ord('Q')):
        sys.exit(0)

    elif ch in (ord('d'), ord('D')):
        stdscr.clear()
        curses.endwin()
        try:
            ssd_info.main()
        except Exception as e:
            print(f"Ошибка в ssd_info: {e}")
        input("Нажмите Enter для возврата в мониторинг...")
        stdscr.clear()
        curses.doupdate()


@error_decorate((KeyboardInterrupt, curses.error, CancelledError))
async def run_main(stdscr: curses.window) -> None:
    """Основная функция, принимающая curses-окно.

    :param stdscr (curses.window): Главное окно curses,
                                    используемое для вывода
    """
    curses.curs_set(0)
    while True:
        start_time: float = time.time()
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
            display_app(results, stdscr, start_time)


@error_decorate((KeyboardInterrupt,))
def main(stdscr) -> None:
    """Запуск асинхронной функции."""
    asyncio.run(run_main(stdscr))


if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except Exception as e:
        print(f"Ошибка: {e}")
    print("Мониторинг остановлен")
