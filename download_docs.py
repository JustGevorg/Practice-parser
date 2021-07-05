import os
import requests
from bs4 import BeautifulSoup


URL = 'https://zakupki.gov.ru/223/purchase/public/purchase/info/documents.html'     # Пока работаю только с законом №223
HEADERS = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                         '(KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
           'accept': '*/*'}


def get_html(url, params=None):
    r = requests.get(url, headers = HEADERS, params = params)
    return r


def get_content(html):
    soup = BeautifulSoup(html, 'html.parser')
    items = soup.find_all('a', class_='epz_aware')
    result = []
    for item in items:
        result.append({
            'name': item.get_text().replace('\r\n', '').replace('\n', '').replace('  ', ''),
            'link': f"https://zakupki.gov.ru{item.get('href')}"
        })
    return result


def save_docs(dir_names, files):
    try:
        os.mkdir(dir_names)
    except:
        print("Такая папка уже существует!")
    for file in files:
        document = get_html(file['link'])
        with open(f"{dir_names}\{file['name']}", 'wb') as f:
            f.write(document.content)


def parse():
    user_numbers = input("Введите номера закупок для скачивания документов через пробел и нажмите Enter: ").split(' ')    # Пока работаю только с законом №223
    for number in user_numbers:
        html = get_html(URL, params = {'regNumber': f'{number}'})
        if html.status_code == 200:
            files = get_content(html.text)
            save_docs(number, files)
            print(f"Скачаны документы по закупке №{number}")
        else:
            print("Error")
    input("Для выхода нажмите Enter ")


parse()
