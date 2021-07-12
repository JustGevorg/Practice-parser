import os
import time
import requests
from bs4 import BeautifulSoup

URL = {'fz223': 'https://zakupki.gov.ru/223/purchase/public/purchase/info/documents.html',
       'fz44': 'https://zakupki.gov.ru/epz/order/notice/view/documents.html'}

HEADERS = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                         '(KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
           'accept': '*/*'}


def get_html(url, params=None):
    r = requests.get(url, headers = HEADERS, params = params)
    return r


def get_content(html, law_number):
    all_search_params = {'fz44': {'tag': 'span', 'class_': 'section__value'},
                         'fz223': {'tag': 'a', 'class_': 'epz_aware'}}
    current_search_params = {**all_search_params[f'{law_number}']}
    soup = BeautifulSoup(html, 'html.parser')
    items = soup.find_all(current_search_params['tag'],
                          current_search_params['class_'])
    result = []
    for item in items:
        result.append({
            'name': item.get_text().replace('\r\n', '').replace('\n', '').replace('  ', ''),
            'link': f"https://zakupki.gov.ru{item.get('href')}" if law_number == 'fz223' else item.find('a').get('href')
        })
    return result


def save_docs(dir_names, files):
    try:
        os.mkdir(dir_names)
    except:
        print("Такая папка уже существует!")
    for file in files:
        document = get_html(file['link']).content
        with open(f"{dir_names}\{file['name']}", 'wb') as f:
            f.write(document)


def law_define(purchase_number):
    law_number = None
    if len(str(purchase_number)) == 11:
        law_number = 'fz223'
    elif len(str(purchase_number)) == 19 or 18:
        law_number = 'fz44'
    return law_number


def parse():
    user_numbers = input("Введите номера закупок для скачивания документов через пробел и нажмите Enter: ").split(' ')
    start_time = time.time()
    for number in user_numbers:
        law_number = law_define(number)
        html = get_html(URL[law_number], params = {'regNumber': f'{number}'})
        if html.status_code == 200:
            files = get_content(html.text, law_number)
            save_docs(number, files)
            print(f"Скачаны документы по закупке № {number}")
        else:
            print("Error")
    print(time.time() - start_time)


parse()
input("Для выхода нажмите Enter ")
