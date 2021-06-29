import requests
from bs4 import BeautifulSoup
import csv

# Сделать ссылку по пользовательскому вводу
FILE = 'parsing_results.csv'
URL = 'https://zakupki.gov.ru/epz/order/extendedsearch/results.html'    # далее может быть задана пользователем,
# хотя пока нет нужды, парсятся-то только страницы закупок
HEADERS = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                         '(KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
           'accept': '*/*'}


def get_html(url, params=None):
    r = requests.get(url, headers = HEADERS, params = params)
    return r


def get_content(html):
    soup = BeautifulSoup(html, 'html.parser')
    items = soup.find_all('div', class_='row no-gutters registry-entry__form mr-0')
    positions = []
    for item in items:  # Тут могут быть любе критерии для выбора записей(номера, объекты закупки, заказчики и т.д.)
        positions.append({
            'number': item.find('div', class_='registry-entry__header-mid__number').get_text().replace('\r\n', '').replace('\n', '').replace(' ', ''),
            'status': item.find('div', class_='registry-entry__header-mid__title').get_text().replace('\r\n', '').replace('\n', '').replace('  ', ''),
            'start_price': item.find('div', class_='price-block__value').get_text().replace('\r\n', '').replace('\n', '').replace('  ', '').replace('₽', 'руб'),
            'customer': item.find('div', class_='registry-entry__body-href').get_text().replace('\r\n', '').replace('\n', '').replace('  ', ''),
            'procurement_object': item.find('div', class_='registry-entry__body-value').get_text().replace('\r\n', '').replace('\n', '').replace('  ', ''),
            'last_update': item.find('div', class_='data-block__value').get_text()
        })
    return positions


def save_file(items, path):
    """Сохранение результатов парсинга в файл"""
    with open(path, 'w', newline = '') as file:
        writer = csv.writer(file, delimiter=';')
        writer.writerow(['Номер', 'Статус', 'Стартовая цена', 'Заказчик', 'Объект закупки', 'Обновлено'])
        for item in items:
            writer.writerow([item['number'], item['status'], item['start_price'], item['customer'],
                             item['procurement_object'], item['last_update']])


def parse():
    html = get_html(URL)
    result = []
    if html.status_code == 200:
        user_req_page = int(input("Введите количество страниц для парсинга: "))
        page_number = 1
        while page_number <= user_req_page:
            html = get_html(URL, params = {'pageNumber': page_number})
            result.extend(get_content(html.text))
            print(f"Парсинг страницы {page_number}")
            page_number += 1
        get_content(html.text)
    else:
        print("Error")

    print(result)
    save_file(result, FILE)
    print(f'Найдено закупок: {len(result)}')


parse()
