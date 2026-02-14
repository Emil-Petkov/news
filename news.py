import sys
import time
import re
import webbrowser
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from colorama import init, Fore, Style
init(autoreset=True)

DW_HOME = "https://www.dw.com/bg"

# DW секции (shortcuts)
DW_IRAN = "https://www.dw.com/bg/%D0%B8%D1%80%D0%B0%D0%BD/t-43804039"
DW_UKRAINE = "https://www.dw.com/bg/vojnata-v-ukrajna/t-63617932"
DW_MIDEAST = "https://www.dw.com/bg/vojnata-v-blizkia-iztok/t-67110584"
DW_LATEST_VIDEOS = "https://www.dw.com/bg/%D0%BF%D0%BE%D1%81%D0%BB%D0%B5%D0%B4%D0%BD%D0%B8-%D0%B2%D0%B8%D0%B4%D0%B5%D0%B0/s-64173289"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/122.0 Safari/537.36"
}

ARTICLE_RE = re.compile(r"/a-\d+")
BAD_PATH_RE = re.compile(r"^/bg/(?:начало|посledni-videa|posledni-videa|видео|теми|тема|медия-център|контакт|карта-на-сайта|информация)\b")

# ============ UI HELPERS ============

def clear_screen():
    import os
    os.system("cls" if os.name == "nt" else "clear")

def banner_main():
    print(Fore.GREEN + r"""
 ███╗   ██╗███████╗██╗    ██╗███████╗
 ████╗  ██║██╔════╝██║    ██║██╔════╝
 ██╔██╗ ██║█████╗  ██║ █╗ ██║███████╗
 ██║╚██╗██║██╔══╝  ██║███╗██║╚════██║
 ██║ ╚████║███████╗╚███╔███╔╝███████║
 ╚═╝  ╚═══╝╚══════╝ ╚══╝╚══╝ ╚══════╝
""" + Style.RESET_ALL)

def banner_dw():
    print(Fore.GREEN + r"""
 ██████╗ ██╗    ██╗    ██████╗  ██████╗
 ██╔══██╗██║    ██║    ██╔══██╗██╔════╝
 ██║  ██║██║ █╗ ██║    ██████╔╝██║  ███╗
 ██║  ██║██║███╗██║    ██╔══██╗██║   ██║
 ██████╔╝╚███╔███╔╝    ██████╔╝╚██████╔╝
 ╚═════╝  ╚══╝╚══╝     ╚═════╝  ╚═════╝
""" + Style.RESET_ALL)

# ============ DW PARSER (TOP 10) ============

def is_good_dw_article_href(href: str) -> bool:
    if not href:
        return False
    href = href.strip()

    if not href.startswith("/bg/"):
        return False
    if BAD_PATH_RE.match(href):
        return False
    if not ARTICLE_RE.search(href):
        return False
    return True

def extract_title_from_article_tag(article_tag) -> str:
    for h in ["h1", "h2", "h3", "h4"]:
        ht = article_tag.find(h)
        if ht:
            t = " ".join(ht.get_text(" ", strip=True).split())
            if t:
                return t
    a = article_tag.find("a", href=True)
    if a:
        t = " ".join(a.get_text(" ", strip=True).split())
        return t
    return ""

def fetch_dw_top_homepage(count=10):
    try:
        r = requests.get(DW_HOME, headers=HEADERS, timeout=15)
        r.raise_for_status()
    except Exception as e:
        return [], f"Грешка при достъп до DW: {e}"

    soup = BeautifulSoup(r.text, "html.parser")
    main = soup.find("main") or soup

    items = []
    seen = set()

    for art in main.find_all("article"):
        chosen_href = None
        chosen_a = None

        for a in art.find_all("a", href=True):
            href = a["href"].strip()
            if is_good_dw_article_href(href):
                chosen_href = href
                chosen_a = a
                break

        if not chosen_href:
            continue

        full_url = urljoin("https://www.dw.com", chosen_href)
        if full_url in seen:
            continue
        seen.add(full_url)

        title = extract_title_from_article_tag(art)
        if not title or len(title) < 8:
            title = " ".join(chosen_a.get_text(" ", strip=True).split())

        if not title or len(title) < 8:
            continue

        items.append({"title": title, "url": full_url})

        if len(items) >= count:
            break

    if len(items) < 6:
        items = []
        seen = set()
        for a in main.find_all("a", href=True):
            href = a["href"].strip()
            if not is_good_dw_article_href(href):
                continue
            title = " ".join(a.get_text(" ", strip=True).split())
            if not title or len(title) < 12:
                continue
            full_url = urljoin("https://www.dw.com", href)
            if full_url in seen:
                continue
            seen.add(full_url)
            items.append({"title": title, "url": full_url})
            if len(items) >= count:
                break

    if not items:
        return [], "Не успях да извадя TOP новините от началната (DW може да е сменил структурата или да рендърва с JavaScript)."

    return items, None

def show_dw_top(items):
    for i, it in enumerate(items, start=1):
        print(f"{Fore.YELLOW}{i}){Style.RESET_ALL} {it['title']}")

# ============ TOP SESSION ============

def dw_top_session():
    """
    Показва TOP списъка и остава в него, докато не излезеш.
    - номер -> отваря новината, остава в списъка
    - M -> обратно към DW менюто
    - R -> презареди TOP (само ако поискаш)
    - Q -> изход
    """
    items, err = fetch_dw_top_homepage(count=10)
    clear_screen()
    banner_dw()

    if err:
        print(Fore.RED + f"\n{err}\n" + Style.RESET_ALL)
        input("Enter за назад...")
        return

    show_dw_top(items)
    print("\n| R презареди | M меню | Q изход\n")

    while True:
        sub = input("Избор: ").strip().upper()

        if sub == "Q":
            sys.exit(0)

        if sub == "M":
            return  # назад към DW менюто

        if sub == "R":
            items, err = fetch_dw_top_homepage(count=10)
            clear_screen()
            banner_dw()
            if err:
                print(Fore.RED + f"\n{err}\n" + Style.RESET_ALL)
                print("Команди: R презареди | M меню | Q изход\n")
                continue
            show_dw_top(items)
            print("\n| R презареди | M меню | Q изход\n")
            continue

        if sub.isdigit():
            idx = int(sub)
            if 1 <= idx <= len(items):
                webbrowser.open(items[idx - 1]["url"], new=2)
                # НЕ чистим екрана, НЕ ресваме списъка — стоим тук
                continue
            else:
                print(Fore.RED + "Невалиден номер." + Style.RESET_ALL)
                continue

        print(Fore.RED + "Невалиден избор." + Style.RESET_ALL)

# ============ MODULES ============

def dw_module():
    while True:
        clear_screen()
        banner_dw()
        print("\n1 - ТОП новини")
        print("2 - Отвори DW България")
        print("3 - Иран")
        print("4 - Войната в Украйна")
        print("5 - Войната в Близкия изток")
        print("6 - Последни видеа")
        print("\n| B - Назад към главното меню | Q изход\n")

        choice = input("Избор: ").strip().upper()

        if choice == "Q":
            sys.exit(0)

        if choice == "B":
            return

        if choice == "2":
            webbrowser.open(DW_HOME, new=2)
            continue

        if choice == "3":
            webbrowser.open(DW_IRAN, new=2)
            continue

        if choice == "4":
            webbrowser.open(DW_UKRAINE, new=2)
            continue

        if choice == "5":
            webbrowser.open(DW_MIDEAST, new=2)
            continue

        if choice == "6":
            webbrowser.open(DW_LATEST_VIDEOS, new=2)
            continue

        if choice == "1":
            dw_top_session()
            continue

        print(Fore.RED + "Невалиден избор." + Style.RESET_ALL)
        time.sleep(0.7)

def placeholder_module(name):
    clear_screen()
    print(Fore.YELLOW + f"[{name}] Модулът е шаблон (още не е реализиран)." + Style.RESET_ALL)
    input("\nEnter за назад...")

def investigative_media_module():
    while True:
        clear_screen()

        print("\n1 - BIRD")
        print("2 - Bivol\n")
        print("\n| B - Назад към главното меню | Q изход\n")


        choice = input("Избор: ").strip().upper()

        if choice == "Q":
            sys.exit(0)

        if choice == "B":
            return

        if choice == "1":
            webbrowser.open("https://bird.bg/", new=2)
            continue

        if choice == "2":
            webbrowser.open("https://bivol.bg/", new=2)
            continue

        print(Fore.RED + "Невалиден избор." + Style.RESET_ALL)
        time.sleep(0.7)


def podcasts_module():
    while True:
        clear_screen()

        print("\n1 - Любен Жечев")
        print("2 - Капитал")
        print("\n| B - Назад към главното меню | Q изход\n")


        choice = input("Избор: ").strip().upper()

        if choice == "Q":
            sys.exit(0)

        if choice == "B":
            return

        if choice == "1":
            webbrowser.open(
                "https://www.youtube.com/@lyubo_zhechev/videos",
                new=2
            )
            continue

        if choice == "2":
            webbrowser.open(
                "https://www.youtube.com/@Capital-bg",
                new=2
            )
            continue

        print(Fore.RED + "Невалиден избор." + Style.RESET_ALL)
        time.sleep(0.7)


# ============ MAIN MENU ============

def main_menu():
    while True:
        clear_screen()
        banner_main()

        print("1 - Deutsche Welle BG")
        print("2 - Свободна Европа")
        print("3 - Дневен ред")
        print("4 - Разследващи медии")
        print("5 - Подкасти\n")
        print("Q - Изход\n")

        choice = input("Избор: ").strip().upper()

        if choice == "1":
            dw_module()
        elif choice == "2":
            webbrowser.open(
        "https://www.youtube.com/@svobodna-evropa/videos",
        new=2
        )
        elif choice == "3":
            webbrowser.open(
        "https://www.youtube.com/@DnevenRed/videos",
        new=3
        )
        elif choice == "4":
            investigative_media_module()

        elif choice == "5":
            podcasts_module()

        elif choice == "Q":
            sys.exit(0)
        else:
            print(Fore.RED + "Невалиден избор." + Style.RESET_ALL)
            time.sleep(0.7)

if __name__ == "__main__":
    main_menu()
