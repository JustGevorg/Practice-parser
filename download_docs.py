import os
import re
import time
import requests
import PySimpleGUI as sg
from bs4 import BeautifulSoup

URL = {'fz223': 'https://zakupki.gov.ru/223/purchase/public/purchase/info/documents.html',
       'fz44': 'https://zakupki.gov.ru/epz/order/notice/view/documents.html',}
CONTRACT_URL = {'fz44': 'https://zakupki.gov.ru/epz/contract/search/results.html'}
CONTRACT_DOCS_URL = {'fz44': 'https://zakupki.gov.ru/epz/contract/contractCard/document-info.html'}

HEADERS = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                         '(KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
           'accept': '*/*'}


def get_html(url, params=None):
    r = requests.get(url, headers = HEADERS, params = params)
    return r


def get_content(html, law_number):
    soup = BeautifulSoup(html, 'html.parser')
    result = []

    if law_number == 'fz223':
        items = soup.find_all('a', class_='epz_aware')
        for item in items:
            result.append({
                'name': item.get_text().replace('\r\n', '').replace('\n', '').replace('  ', ''),
                'link': f"https://zakupki.gov.ru{item.get('href')}",
                'category': item.find_previous('h2').get_text()
            })

    elif law_number == 'fz44':
        items = soup.find_all('span', class_='section__value')
        for item in items:
            result.append({
                'name': item.find('a').get('title'),
                'category': item.find_previous('h2', class_='blockInfo__title').get_text(),
                'link': item.find('a').get('href')
            })

    return result


def law_define(purchase_number):
    """Определение ФЗ или ПП закупки, программа работает с ФЗ 44, Ф3 223, ПП 615"""
    law_number = None
    if len(str(purchase_number)) == 11:
        law_number = 'fz223'
    elif len(str(purchase_number)) == 19 or len(str(purchase_number)) == 18:
        law_number = 'fz44'
    return law_number


def contract_docs_search(purchase_number, law_number):
    contract_list = []
    res = []
    page_number = 1
    if law_number == 'fz44':
        while True:  # На случай, если по закупке заключено несколько контрактов
            html_contracts = get_html(CONTRACT_URL[law_number], params = {'orderNumber': purchase_number,
                                                                               'pageNumber': page_number})
            soup = BeautifulSoup(html_contracts.text, 'html.parser')
            items = soup.find_all('div', class_ = 'registry-entry__header-mid__number')
            if html_contracts.status_code == 200 and items:
                for item in items:
                    contract_list.append(item.find('a').get_text().replace('\n', '').replace(' ', '').replace('№', ''))
                page_number += 1
            else:
                break

        for contract in contract_list:
            print(f'Найден контракт {contract}')
            contract_docs = get_html(CONTRACT_DOCS_URL[law_number], params = {'reestrNumber': contract}).text
            soup = BeautifulSoup(contract_docs, 'html.parser')
            items = soup.find_all('span', class_ = 'section__value')
            for item in items:
                res.append({
                    'name': item.find('a').get('title'),
                    'category': item.find_previous('div', class_ = 'title pb-0').get_text(),
                    'link': item.find('a').get('href'),
                    'contract_num': contract
                })
    return res


def save_docs(dir_names, files, law_number, work_with_contracts = False):
    if work_with_contracts == False:  # Тут скачиваем документы по закупке
        if not os.path.exists('Purchase ' + dir_names):
            os.mkdir('Purchase ' + dir_names)
        copy_number = 1
        for file in files:
            # Создаем попки для документов по категориям, как на сайте
            category = file['category'].replace('\r\n', '').replace('\n', '').replace('  ', '')
            if not os.path.exists(f"Purchase {dir_names}/{category}"):
                os.mkdir(f"Purchase {dir_names}/{category}")

            if law_number == 'fz223':
                # Ищем расширение файла в заголовках response по ссылке на скачивание,
                # если его нет в названии или в title, что встречается только для 223 ФЗ
                response = get_html(file['link'])
                headers = response.headers
                if "content-disposition" in headers and "filename" in headers["content-disposition"]:
                    extension = '.' + \
                                (re.match(r'.*filename=\"(.{1,})\".*', headers["content-disposition"]).group(1)).split(
                                    '.')[-1]
                    file['name'] += extension
                else:
                    print('Не удалось определить расширение файла')

            document = get_html(file['link']).content
            print(f"Скачивается {file['name']}")
            if os.path.exists(f"Purchase {dir_names}/{category}/{file['name']}"):
                # Чтобы качать файлы с одинаковыми именами из одной категории
                file['name'] = str(copy_number) + file['name']
                copy_number += 1
            with open(f"Purchase {dir_names}/{category}/{file['name']}", 'wb') as f:
                f.write(document)
    else:  # Тут скачиваем документы по КОНТРАКТАМ закупки
        if law_number == 'fz223':
            pass

        else:
            # Защита от документов с одинаковыми названиями не нужна
            # - тут в каждой категории все доки имеют уникальные имена
            if not os.path.exists(f"Purchase {dir_names}"):
                os.mkdir(f"Purchase {dir_names}")
            if not os.path.exists(f"Purchase {dir_names}/Contract {files['contract_num']}"):
                os.mkdir(f"Purchase {dir_names}/Contract {files['contract_num']}")
            if not os.path.exists(f"Purchase {dir_names}/Contract {files['contract_num']}/{files['category']}"):
                os.mkdir(f"Purchase {dir_names}/Contract {files['contract_num']}/{files['category']}")
            document = get_html(files['link']).content
            name_of_file = files['name'].split(' ')  # Избавляемся от размера файла, указанного в названии
            del name_of_file[-1]; del name_of_file[-1]
            name_of_file = (' '.join(name_of_file))  # ... и собираем название файла обратно
            print(f"Скачивается {name_of_file}")
            with open(f"Purchase {dir_names}/Contract {files['contract_num']}/{files['category']}/{name_of_file}", 'wb') as f:
                f.write(document)


def parse(num):
    user_numbers = num.split(' ')
    start_time = time.time()
    for number in user_numbers:
        law_number = law_define(number)
        if law_number == None:
            print(f"Некорректный номер закупки № {number}")
            continue
        html = get_html(URL[law_number], params = {'regNumber': f'{number}'})
        if html.status_code == 200:
            files = get_content(html.text, law_number)
            print(f"Скачивание документов по закупке № {number}")
            save_docs(number, files, law_number, work_with_contracts = False)
            print(f"Скачаны документы по закупке № {number}")
        else:
            print("Error")
            continue
        print(f"Поиск контрактов по закупке {number}")
        all_contract_docs = contract_docs_search(number, law_number)
        if all_contract_docs != None:
            print('Скачивание документов по найденным контрактам')
            for doc in all_contract_docs:
                save_docs(number, doc, law_number, work_with_contracts = True)
        else:
            print("Контракты не найдены")
    print(f"Выполнено за {time.time() - start_time} сек")

########################
# Графический интерфейс#
########################
sg.theme('Material1')

layout = [
          [sg.Text('Введите номер или номера закупок через пробел(без №)')],
          [sg.Input(key='-IN-')],
          [sg.Button('Read'), sg.Exit()],
          [sg.Text('Ход работы программы')],
          [sg.Output(size=(88, 20), key = 'outp')],
          [sg.Button('Clear')]
          ]

window = sg.Window('Скачивание документов по закупке', layout)

while True:
    event, values = window.read()
    try:
        if event == 'Read':
            if values['-IN-'].isalpha():
                print("Номер не должен содержать буквы")
            else:
                parse(values['-IN-'])
    except:
        print("Something go wrong")
    if event == sg.WIN_CLOSED or event == 'Exit':
        break
    if event == 'Clear':
        window.find_element(key='outp').Update('')

window.close()
