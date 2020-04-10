from flask import Flask, request
import logging
import json
# импортируем функции из нашего второго файла geo
from flask_ngrok import run_with_ngrok

from geo import get_distance, get_geo_info

app = Flask(__name__)

sessionStorage = {}
# Добавляем логирование в файл.
# Чтобы найти файл, перейдите на pythonwhere в раздел files,
# он лежит в корневой папке
logging.basicConfig(level=logging.INFO, filename='app.log',
                    format='%(asctime)s %(levelname)s %(name)s %(message)s')
run_with_ngrok(app)


@app.route('/post', methods=['POST'])
def main():
    logging.info('Request: %r', request.json)
    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False
        }
    }
    handle_dialog(response, request.json)
    logging.info('Request: %r', response)
    return json.dumps(response)


def handle_dialog(res, req):
    user_id = req['session']['user_id']
    if req['session']['new']:
        res['response']['text'] = 'Привет! Назови свое имя!'
        sessionStorage[user_id] = {
            'first_name': None
        }
        return
    if sessionStorage[user_id]['first_name'] is None:
        first_name = get_first_name(req)
        if first_name is None:
            res['response']['text'] = 'Не расслышала имя. Повтори, пожалуйста!'
        else:
            sessionStorage[user_id]['first_name'] = first_name
            res['response'][
                'text'] = f'Приятно познакомиться, {first_name.title()}. Я Алиса. Я могу показать город или сказать расстояние между городами! '
    # Получаем города из нашего
    else:

        name = sessionStorage[user_id]['first_name']
        cities = get_cities(req)
        if not cities:
            res['response'][
                'text'] = f'{name}, ты не написал название не одного города!'
        elif len(cities) == 1:
            res['response']['text'] = f'{name}, этот город в стране - ' + \
                                      get_geo_info(cities[0], 'country')

        elif len(cities) == 2:
            distance = get_distance(get_geo_info(
                cities[0], 'coordinates'),
                get_geo_info(cities[1], 'coordinates'))
            res['response'][
                'text'] = f'{name}, расстояние между этими городами: ' + \
                          str(round(distance)) + ' км.'
        else:
            res['response']['text'] = f'{name}, слишком много городов!'


def get_cities(req):
    cities = []
    for entity in req['request']['nlu']['entities']:
        if entity['type'] == 'YANDEX.GEO':
            if 'city' in entity['value']:
                cities.append(entity['value']['city'])
    return cities


def get_first_name(req):
    # перебираем сущности
    for entity in req['request']['nlu']['entities']:
        # находим сущность с типом 'YANDEX.FIO'
        if entity['type'] == 'YANDEX.FIO':
            # Если есть сущность с ключом 'first_name', то возвращаем её значение.
            # Во всех остальных случаях возвращаем None.
            return entity['value'].get('first_name', None)


if __name__ == '__main__':
    app.run()
