from flask import Flask, render_template, request, redirect, url_for, jsonify, session
import json
import requests

app = Flask(__name__)
app.secret_key = '6LcnE2kqAAAAAPIhylF5cgwfAo3T_8mDAxBbnhMP'

# путь к JSON-файлу
DATA_FILE = 'apartments_data.json'


# CAPTCHA
@app.route('/captcha', methods=['GET', 'POST'])
def captcha():
    if request.method == 'POST':
        captcha_response = request.form['g-recaptcha-response']
        secret_key = '6LcnE2kqAAAAAPIhylF5cgwfAo3T_8mDAxBbnhMP'
        verification_url = 'https://www.google.com/recaptcha/api/siteverify'

        response = requests.post(verification_url, data={'secret': secret_key, 'response': captcha_response})
        result = response.json()

        if not result.get('success'):
            return "CAPTCHA не пройдена. Попробуйте снова.", 400

        session['captcha_verified'] = True
        return redirect(url_for('index'))

    return render_template('captcha.html')


# функция для загрузки данных
def load_data():
    with open(DATA_FILE, 'r') as file:
        return json.load(file)


# функция для сохранения данных
def save_data(data):
    with open(DATA_FILE, 'w') as file:
        json.dump(data, file, indent=4)


# главная страница с формой, списком квартир и возможностью сортировки
@app.route('/')
def index():
    # если CAPTCHA не пройдена, перенаправляем на страницу с CAPTCHA
    if not session.get('captcha_verified'):
        print("Redirecting to CAPTCHA")
        return redirect(url_for('captcha'))

    print("Captcha already verified")
    data = load_data()
    sort_by = request.args.get('sort_by')

    if sort_by == 'price':
        data = sorted(data, key=lambda x: x['price'])
    elif sort_by == 'rooms':
        data = sorted(data, key=lambda x: x['rooms'])
    elif sort_by == 'area':
        data = sorted(data, key=lambda x: x['area'])
    elif sort_by == 'floor':
        data = sorted(data, key=lambda x: x['floor'])

    return render_template('index.html', apartments=data)


# обработка данных из формы (создание новой записи)
@app.route('/submit', methods=['POST'])
def submit():
    # CAPTCHA не проверяется на этой странице
    address = request.form['address']
    area = float(request.form['area'])
    price = float(request.form['price'])
    rooms = int(request.form['rooms'])
    floor = int(request.form['floor'])

    data = load_data()

    new_apartment = {
        'id': len(data) + 1,
        'address': address,
        'area': area,
        'price': price,
        'rooms': rooms,
        'floor': floor
    }
    data.append(new_apartment)

    save_data(data)
    return redirect(url_for('index'))


# страница со списком всех квартир (сортировка по полю)
@app.route('/apartments')
def list_apartments():
    data = load_data()
    sort_by = request.args.get('sort_by')
    if sort_by:
        data = sorted(data, key=lambda x: x.get(sort_by, ''))
    return jsonify(data)


# удаление записи по ID
@app.route('/delete/<int:apartment_id>', methods=['POST'])
def delete_apartment(apartment_id):
    data = load_data()
    data = [apartment for apartment in data if apartment['id'] != apartment_id]
    save_data(data)
    return redirect(url_for('index'))


# обновление записи по ID
@app.route('/update/<int:apartment_id>', methods=['POST'])
def update_apartment(apartment_id):
    data = load_data()
    for apartment in data:
        if apartment['id'] == apartment_id:
            apartment['address'] = request.form['address']
            apartment['area'] = float(request.form['area'])
            apartment['price'] = float(request.form['price'])
            apartment['rooms'] = int(request.form['rooms'])
            apartment['floor'] = int(request.form['floor'])
            break
    save_data(data)
    return redirect(url_for('index'))


# среднее, максимальное, минимальное значения по числовым полям
@app.route('/stats')
def stats():
    data = load_data()

    if not data:
        return jsonify({'message': 'No data available'})

    area_values = [apartment['area'] for apartment in data]
    price_values = [apartment['price'] for apartment in data]

    stats_data = {
        'area': {
            'average': sum(area_values) / len(area_values),
            'max': max(area_values),
            'min': min(area_values)
        },
        'price': {
            'average': sum(price_values) / len(price_values),
            'max': max(price_values),
            'min': min(price_values)
        }
    }
    return jsonify(stats_data)


if __name__ == '__main__':
    try:
        with open(DATA_FILE, 'r') as file:
            pass
    except FileNotFoundError:
        with open(DATA_FILE, 'w') as file:
            json.dump([], file)

    app.run(debug=True)
