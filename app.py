from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from datetime import datetime, timedelta
import hashlib

app = Flask(__name__)
app.secret_key = 'bus-station-secret-key-2026'

DATABASE = 'avtovokzal.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# Хеширование паролей
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ==================== ГЛАВНАЯ СТРАНИЦА ====================
@app.route('/')
def index():
    return render_template('index.html')

# ==================== РЕГИСТРАЦИЯ ====================
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        email = request.form.get('email')
        full_name = request.form.get('full_name')
        phone = request.form.get('phone')
        
        # Валидация
        if not username or not password:
            flash('Имя пользователя и пароль обязательны', 'error')
            return redirect(url_for('register'))
        
        if password != confirm_password:
            flash('Пароли не совпадают', 'error')
            return redirect(url_for('register'))
        
        if len(password) < 4:
            flash('Пароль должен быть не менее 4 символов', 'error')
            return redirect(url_for('register'))
        
        conn = get_db_connection()
        
        # Проверка существования пользователя
        existing = conn.execute('SELECT user_id FROM Users WHERE username = ?', (username,)).fetchone()
        if existing:
            flash('Пользователь с таким именем уже существует', 'error')
            conn.close()
            return redirect(url_for('register'))
        
        # Создание пользователя
        password_hash = hash_password(password)
        try:
            conn.execute('''
                INSERT INTO Users (username, password_hash, email, full_name, phone)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, password_hash, email, full_name, phone))
            conn.commit()
            flash('Регистрация успешна! Теперь вы можете войти', 'success')
            conn.close()
            return redirect(url_for('login'))
        except Exception as e:
            conn.close()
            flash(f'Ошибка при регистрации: {str(e)}', 'error')
            return redirect(url_for('register'))
    
    return render_template('register.html')

# ==================== ВХОД ====================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        password_hash = hash_password(password)
        
        conn = get_db_connection()
        user = conn.execute('''
            SELECT user_id, username, role FROM Users 
            WHERE username = ? AND password_hash = ?
        ''', (username, password_hash)).fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user['user_id']
            session['username'] = user['username']
            session['role'] = user['role']
            flash(f'Добро пожаловать, {username}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Неверное имя пользователя или пароль', 'error')
    
    return render_template('login.html')

# ==================== ВЫХОД ====================
@app.route('/logout')
def logout():
    session.clear()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('index'))

# ==================== ПРОФИЛЬ ====================
@app.route('/profile')
def profile():
    if 'user_id' not in session:
        flash('Пожалуйста, войдите в систему', 'error')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    user = conn.execute('''
        SELECT user_id, username, full_name, email, phone, role, created_at 
        FROM Users WHERE user_id = ?
    ''', (session['user_id'],)).fetchone()
    
    # Получение билетов пользователя
    tickets = conn.execute('''
        SELECT t.ticket_id, t.purchase_time, t.price, t.ticket_status,
               s.departure_time, r.departure_city, r.arrival_city, r.base_price
        FROM Tickets t
        JOIN BusSchedule s ON t.schedule_id = s.schedule_id
        JOIN Routes r ON s.route_id = r.route_id
        WHERE t.user_id = ?
        ORDER BY t.purchase_time DESC
    ''', (session['user_id'],)).fetchall()
    
    conn.close()
    return render_template('profile.html', user=user, tickets=tickets)

# ==================== РАСПИСАНИЕ РЕЙСОВ ====================
@app.route('/schedule')
def schedule():
    conn = get_db_connection()
    
    cursor = conn.execute('''
        SELECT 
            s.schedule_id,
            s.departure_time,
            s.arrival_time,
            s.available_seats,
            s.schedule_status,
            r.route_number,
            r.departure_city,
            r.arrival_city,
            r.travel_time_minutes,
            r.base_price,
            b.license_plate,
            b.model,
            d.last_name || ' ' || d.first_name as driver_name
        FROM BusSchedule s
        JOIN Routes r ON s.route_id = r.route_id
        JOIN Buses b ON s.bus_id = b.bus_id
        JOIN Drivers d ON s.driver_id = d.driver_id
        WHERE s.departure_time >= datetime('now')
        ORDER BY s.departure_time ASC
        LIMIT 50
    ''')
    
    schedules = cursor.fetchall()
    conn.close()
    
    return render_template('schedule.html', schedules=schedules)

# ==================== ПОИСК БИЛЕТОВ ====================
@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        from_city = request.form.get('from_city')
        to_city = request.form.get('to_city')
        travel_date = request.form.get('travel_date')
        
        if not from_city or not to_city or not travel_date:
            flash('Пожалуйста, заполните все поля поиска', 'error')
            return redirect(url_for('search'))
        
        conn = get_db_connection()
        
        cursor = conn.execute('''
            SELECT 
                s.schedule_id,
                s.departure_time,
                s.arrival_time,
                s.available_seats,
                s.schedule_status,
                r.route_number,
                r.departure_city,
                r.arrival_city,
                r.travel_time_minutes,
                r.base_price,
                b.license_plate,
                b.model,
                d.last_name || ' ' || d.first_name as driver_name
            FROM BusSchedule s
            JOIN Routes r ON s.route_id = r.route_id
            JOIN Buses b ON s.bus_id = b.bus_id
            JOIN Drivers d ON s.driver_id = d.driver_id
            WHERE r.departure_city = ? 
                AND r.arrival_city = ?
                AND date(s.departure_time) = date(?)
                AND s.available_seats > 0
            ORDER BY s.departure_time ASC
        ''', (from_city, to_city, travel_date))
        
        results = cursor.fetchall()
        conn.close()
        
        if not results:
            flash('Рейсов не найдено. Попробуйте изменить параметры поиска.', 'info')
        
        return render_template('schedule.html', schedules=results, search_params={
            'from': from_city,
            'to': to_city,
            'date': travel_date
        })
    
    return render_template('search.html')

# ==================== ПОКУПКА БИЛЕТА ====================
@app.route('/buy/<int:schedule_id>', methods=['GET', 'POST'])
def buy_ticket(schedule_id):
    if 'user_id' not in session:
        flash('Для покупки билетов необходимо войти в систему', 'error')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    
    # Получаем информацию о рейсе
    cursor = conn.execute('''
        SELECT 
            s.schedule_id,
            s.departure_time,
            s.arrival_time,
            s.available_seats,
            r.route_number,
            r.departure_city,
            r.arrival_city,
            r.base_price,
            b.license_plate
        FROM BusSchedule s
        JOIN Routes r ON s.route_id = r.route_id
        JOIN Buses b ON s.bus_id = b.bus_id
        WHERE s.schedule_id = ?
    ''', (schedule_id,))
    
    schedule = cursor.fetchone()
    
    if not schedule:
        flash('Рейс не найден', 'error')
        return redirect(url_for('schedule'))
    
    if request.method == 'POST':
        passenger_name = request.form.get('passenger_name')
        passport_number = request.form.get('passport_number')
        phone = request.form.get('phone')
        seat_count = int(request.form.get('seat_count', 1))
        
        # Проверяем, есть ли свободные места
        if schedule['available_seats'] < seat_count:
            flash(f'Недостаточно свободных мест. Доступно: {schedule["available_seats"]}', 'error')
            return redirect(url_for('buy_ticket', schedule_id=schedule_id))
        
        # Проверяем/создаём пассажира
        cursor = conn.execute('SELECT passenger_id FROM Passengers WHERE passport_number = ?', (passport_number,))
        passenger = cursor.fetchone()
        
        if passenger:
            passenger_id = passenger['passenger_id']
        else:
            # Разбиваем ФИО
            names = passenger_name.split()
            first_name = names[0] if len(names) > 0 else ''
            last_name = names[1] if len(names) > 1 else ''
            middle_name = names[2] if len(names) > 2 else ''
            
            cursor = conn.execute('''
                INSERT INTO Passengers (first_name, last_name, middle_name, passport_number, phone)
                VALUES (?, ?, ?, ?, ?)
            ''', (first_name, last_name, middle_name, passport_number, phone))
            passenger_id = cursor.lastrowid
        
        # Создаём билет
        total_price = seat_count * schedule['base_price']
        user_id = session['user_id']
        
        conn.execute('''
            INSERT INTO Tickets (schedule_id, passenger_id, user_id, price)
            VALUES (?, ?, ?, ?)
        ''', (schedule_id, passenger_id, user_id, total_price))
        
        # Обновляем количество свободных мест
        conn.execute('''
            UPDATE BusSchedule 
            SET available_seats = available_seats - ?
            WHERE schedule_id = ?
        ''', (seat_count, schedule_id))
        
        conn.commit()
        
        flash(f'Билет(ы) успешно куплен(ы)! Стоимость: {total_price} руб.', 'success')
        return redirect(url_for('profile'))
    
    conn.close()
    return render_template('buy_ticket.html', schedule=schedule)

# ==================== АДМИНКА: УПРАВЛЕНИЕ МАРШРУТАМИ ====================
@app.route('/admin/routes')
def admin_routes():
    if session.get('role') != 'admin':
        flash('Доступ запрещен. Требуются права администратора.', 'error')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    routes = conn.execute('SELECT * FROM Routes ORDER BY route_number').fetchall()
    conn.close()
    return render_template('admin_routes.html', routes=routes)

# ==================== АДМИНКА: УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ ====================
@app.route('/admin/users')
def admin_users():
    if session.get('role') != 'admin':
        flash('Доступ запрещен. Требуются права администратора.', 'error')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    users = conn.execute('SELECT * FROM Users ORDER BY user_id').fetchall()
    conn.close()
    return render_template('admin_users.html', users=users)

# ==================== АДМИНКА: ДОБАВЛЕНИЕ РЕЙСА ====================
@app.route('/admin/add_schedule', methods=['GET', 'POST'])
def add_schedule():
    if session.get('role') != 'admin':
        flash('Доступ запрещен. Требуются права администратора.', 'error')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    
    if request.method == 'POST':
        route_id = request.form.get('route_id')
        bus_id = request.form.get('bus_id')
        driver_id = request.form.get('driver_id')
        departure_time = request.form.get('departure_time')
        
        if not all([route_id, bus_id, driver_id, departure_time]):
            flash('Пожалуйста, заполните все поля', 'error')
            return redirect(url_for('add_schedule'))
        
        # Получаем информацию о маршруте для расчёта времени прибытия
        route = conn.execute('SELECT travel_time_minutes FROM Routes WHERE route_id = ?', (route_id,)).fetchone()
        
        if not route:
            flash('Маршрут не найден', 'error')
            return redirect(url_for('add_schedule'))
        
        # Расчёт времени прибытия
        dep_dt = datetime.strptime(departure_time, '%Y-%m-%dT%H:%M')
        arr_dt = dep_dt + timedelta(minutes=route['travel_time_minutes'])
        arrival_time = arr_dt.strftime('%Y-%m-%d %H:%M:%S')
        departure_time_formatted = dep_dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # Получаем вместимость автобуса
        bus = conn.execute('SELECT capacity FROM Buses WHERE bus_id = ?', (bus_id,)).fetchone()
        
        if not bus:
            flash('Автобус не найден', 'error')
            return redirect(url_for('add_schedule'))
        
        try:
            conn.execute('''
                INSERT INTO BusSchedule (bus_id, driver_id, route_id, departure_time, arrival_time, available_seats, schedule_status)
                VALUES (?, ?, ?, ?, ?, ?, 'запланирован')
            ''', (bus_id, driver_id, route_id, departure_time_formatted, arrival_time, bus['capacity']))
            
            conn.commit()
            flash('Рейс успешно добавлен в расписание!', 'success')
            return redirect(url_for('schedule'))
        except Exception as e:
            conn.rollback()
            flash(f'Ошибка при добавлении рейса: {str(e)}', 'error')
            return redirect(url_for('add_schedule'))
    
    routes = conn.execute('SELECT * FROM Routes ORDER BY route_number').fetchall()
    buses = conn.execute('SELECT * FROM Buses WHERE bus_condition = "исправен"').fetchall()
    drivers = conn.execute('SELECT * FROM Drivers ORDER BY last_name').fetchall()
    
    conn.close()
    return render_template('add_schedule.html', routes=routes, buses=buses, drivers=drivers)

# ==================== АДМИНКА: ДОБАВЛЕНИЕ МАРШРУТА ====================
@app.route('/admin/add_route', methods=['GET', 'POST'])
def admin_add_route():
    if session.get('role') != 'admin':
        flash('Доступ запрещен. Требуются права администратора.', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        route_number = request.form.get('route_number')
        departure_city = request.form.get('departure_city')
        arrival_city = request.form.get('arrival_city')
        distance_km = request.form.get('distance_km')
        travel_time_minutes = request.form.get('travel_time_minutes')
        base_price = request.form.get('base_price')
        
        # Валидация
        if not all([route_number, departure_city, arrival_city, travel_time_minutes, base_price]):
            flash('Пожалуйста, заполните все обязательные поля', 'error')
            return redirect(url_for('admin_add_route'))
        
        conn = get_db_connection()
        
        # Проверка существования маршрута с таким номером
        existing = conn.execute('SELECT route_id FROM Routes WHERE route_number = ?', (route_number,)).fetchone()
        if existing:
            flash(f'Маршрут с номером {route_number} уже существует', 'error')
            conn.close()
            return redirect(url_for('admin_add_route'))
        
        try:
            conn.execute('''
                INSERT INTO Routes (route_number, departure_city, arrival_city, distance_km, travel_time_minutes, base_price)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (route_number, departure_city, arrival_city, distance_km or None, travel_time_minutes, base_price))
            conn.commit()
            flash(f'Маршрут {route_number} ({departure_city} → {arrival_city}) успешно добавлен!', 'success')
            conn.close()
            return redirect(url_for('admin_routes'))
        except Exception as e:
            conn.close()
            flash(f'Ошибка при добавлении маршрута: {str(e)}', 'error')
            return redirect(url_for('admin_add_route'))
    
    return render_template('admin_add_route.html')


# ==================== АДМИНКА: РЕДАКТИРОВАНИЕ МАРШРУТА ====================
@app.route('/admin/edit_route/<int:route_id>', methods=['GET', 'POST'])
def admin_edit_route(route_id):
    if session.get('role') != 'admin':
        flash('Доступ запрещен. Требуются права администратора.', 'error')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    route = conn.execute('SELECT * FROM Routes WHERE route_id = ?', (route_id,)).fetchone()
    
    if not route:
        flash('Маршрут не найден', 'error')
        conn.close()
        return redirect(url_for('admin_routes'))
    
    if request.method == 'POST':
        route_number = request.form.get('route_number')
        departure_city = request.form.get('departure_city')
        arrival_city = request.form.get('arrival_city')
        distance_km = request.form.get('distance_km')
        travel_time_minutes = request.form.get('travel_time_minutes')
        base_price = request.form.get('base_price')
        
        if not all([route_number, departure_city, arrival_city, travel_time_minutes, base_price]):
            flash('Пожалуйста, заполните все обязательные поля', 'error')
            conn.close()
            return redirect(url_for('admin_edit_route', route_id=route_id))
        
        # Проверка уникальности номера маршрута (кроме текущего)
        existing = conn.execute('SELECT route_id FROM Routes WHERE route_number = ? AND route_id != ?', 
                               (route_number, route_id)).fetchone()
        if existing:
            flash(f'Маршрут с номером {route_number} уже существует', 'error')
            conn.close()
            return redirect(url_for('admin_edit_route', route_id=route_id))
        
        try:
            conn.execute('''
                UPDATE Routes 
                SET route_number = ?, departure_city = ?, arrival_city = ?, 
                    distance_km = ?, travel_time_minutes = ?, base_price = ?
                WHERE route_id = ?
            ''', (route_number, departure_city, arrival_city, distance_km or None, travel_time_minutes, base_price, route_id))
            conn.commit()
            flash(f'Маршрут {route_number} успешно обновлён!', 'success')
            conn.close()
            return redirect(url_for('admin_routes'))
        except Exception as e:
            conn.close()
            flash(f'Ошибка при обновлении маршрута: {str(e)}', 'error')
            return redirect(url_for('admin_edit_route', route_id=route_id))
    
    conn.close()
    return render_template('admin_edit_route.html', route=route)


# ==================== АДМИНКА: УДАЛЕНИЕ МАРШРУТА ====================
@app.route('/admin/delete_route/<int:route_id>', methods=['POST'])
def admin_delete_route(route_id):
    if session.get('role') != 'admin':
        flash('Доступ запрещен. Требуются права администратора.', 'error')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    
    # Проверяем, есть ли связанные рейсы в расписании
    has_schedules = conn.execute('SELECT COUNT(*) as count FROM BusSchedule WHERE route_id = ?', (route_id,)).fetchone()['count']
    if has_schedules > 0:
        flash(f'Невозможно удалить маршрут: существует {has_schedules} связанных рейсов в расписании.', 'error')
        conn.close()
        return redirect(url_for('admin_routes'))
    
    try:
        conn.execute('DELETE FROM Routes WHERE route_id = ?', (route_id,))
        conn.commit()
        flash('Маршрут успешно удалён!', 'success')
    except Exception as e:
        flash(f'Ошибка при удалении маршрута: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('admin_routes'))

# ==================== СТАТИСТИКА ====================
@app.route('/stats')
def stats():
    conn = get_db_connection()
    
    total_routes = conn.execute('SELECT COUNT(*) as count FROM Routes').fetchone()['count']
    total_buses = conn.execute('SELECT COUNT(*) as count FROM Buses').fetchone()['count']
    total_drivers = conn.execute('SELECT COUNT(*) as count FROM Drivers').fetchone()['count']
    active_schedules = conn.execute('SELECT COUNT(*) as count FROM BusSchedule WHERE departure_time >= datetime("now")').fetchone()['count']
    total_users = conn.execute('SELECT COUNT(*) as count FROM Users').fetchone()['count']
    tickets_sold = conn.execute('SELECT COUNT(*) as count FROM Tickets').fetchone()['count']
    
    conn.close()
    
    return render_template('stats.html', 
                         total_routes=total_routes,
                         total_buses=total_buses,
                         total_drivers=total_drivers,
                         active_schedules=active_schedules,
                         total_users=total_users,
                         tickets_sold=tickets_sold)

if __name__ == '__main__':
    app.run(debug=True)