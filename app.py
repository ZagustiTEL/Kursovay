from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

def get_db():
    conn = sqlite3.connect('avtovokzal.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/', methods=['GET', 'POST'])
def index():
    conn = get_db()
    
    routes = conn.execute('SELECT * FROM Routes').fetchall()
    drivers = conn.execute('SELECT * FROM Drivers').fetchall()
    buses = conn.execute('''
        SELECT b.*, d.first_name, d.last_name 
        FROM Buses b
        LEFT JOIN Drivers d ON b.driver_id = d.driver_id
    ''').fetchall()
    passengers = conn.execute('SELECT * FROM Passengers').fetchall()
    
    schedule = conn.execute('''
        SELECT s.*, 
               r.route_number, r.departure_city, r.arrival_city,
               b.license_plate, b.model,
               d.first_name, d.last_name
        FROM BusSchedule s
        JOIN Routes r ON s.route_id = r.route_id
        JOIN Buses b ON s.bus_id = b.bus_id
        JOIN Drivers d ON s.driver_id = d.driver_id
        ORDER BY s.departure_time
    ''').fetchall()
    
    tickets = conn.execute('''
        SELECT t.*, 
               p.first_name, p.last_name, p.passport_number,
               r.departure_city, r.arrival_city,
               s.departure_time
        FROM Tickets t
        JOIN Passengers p ON t.passenger_id = p.passenger_id
        JOIN BusSchedule s ON t.schedule_id = s.schedule_id
        JOIN Routes r ON s.route_id = r.route_id
    ''').fetchall()
    
    conn.close()
    
    
    conn = get_db()
    schedules_for_form = conn.execute('''
        SELECT s.schedule_id, r.departure_city, r.arrival_city, s.departure_time
        FROM BusSchedule s
        JOIN Routes r ON s.route_id = r.route_id
        WHERE s.schedule_status = 'запланирован'
        ORDER BY s.departure_time
    ''').fetchall()
    
    passengers_for_form = conn.execute('SELECT * FROM Passengers').fetchall()
    conn.close()
    
    return render_template('index.html', 
                         routes=routes, 
                         drivers=drivers, 
                         buses=buses,
                         passengers=passengers,
                         schedule=schedule,
                         tickets=tickets,
                         schedules_for_form=schedules_for_form,
                         passengers_for_form=passengers_for_form)

@app.route('/add_passenger', methods=['POST'])
def add_passenger():
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    middle_name = request.form.get('middle_name', '')
    passport_number = request.form['passport_number']
    phone = request.form.get('phone', '')
    email = request.form.get('email', '')
    
    conn = get_db()
    try:
        conn.execute('''
            INSERT INTO Passengers (first_name, last_name, middle_name, passport_number, phone, email)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (first_name, last_name, middle_name, passport_number, phone, email))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return "Ошибка: пассажир с таким номером паспорта уже существует", 400
    conn.close()
    
    return redirect(url_for('index'))

@app.route('/buy_ticket', methods=['POST'])
def buy_ticket():
    schedule_id = request.form['schedule_id']
    passenger_id = request.form['passenger_id']
    price = request.form['price']
    
    conn = get_db()
    conn.execute('''
        INSERT INTO Tickets (schedule_id, passenger_id, price)
        VALUES (?, ?, ?)
    ''', (schedule_id, passenger_id, price))
    conn.commit()
    conn.close()
    
    return redirect(url_for('index'))

@app.route('/delete_ticket/<int:ticket_id>')
def delete_ticket(ticket_id):
    conn = get_db()
    conn.execute('DELETE FROM Tickets WHERE ticket_id = ?', (ticket_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/delete_passenger/<int:passenger_id>')
def delete_passenger(passenger_id):
    conn = get_db()
    conn.execute('DELETE FROM Passengers WHERE passenger_id = ?', (passenger_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/delete_schedule/<int:schedule_id>')
def delete_schedule(schedule_id):
    conn = get_db()
    conn.execute('DELETE FROM BusSchedule WHERE schedule_id = ?', (schedule_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/add_route', methods=['POST'])
def add_route():
    route_number = request.form['route_number']
    departure_city = request.form['departure_city']
    arrival_city = request.form['arrival_city']
    distance_km = request.form.get('distance_km')
    travel_time_minutes = request.form.get('travel_time_minutes')
    
    conn = get_db()
    conn.execute('''
        INSERT INTO Routes (route_number, departure_city, arrival_city, distance_km, travel_time_minutes)
        VALUES (?, ?, ?, ?, ?)
    ''', (route_number, departure_city, arrival_city, distance_km, travel_time_minutes))
    conn.commit()
    conn.close()
    
    return redirect(url_for('index'))

@app.route('/add_schedule', methods=['POST'])
def add_schedule():
    bus_id = request.form['bus_id']
    driver_id = request.form['driver_id']
    route_id = request.form['route_id']
    departure_time = request.form['departure_time']
    arrival_time = request.form['arrival_time']
    
    conn = get_db()
    try:
        conn.execute('''
            INSERT INTO BusSchedule (bus_id, driver_id, route_id, departure_time, arrival_time, schedule_status)
            VALUES (?, ?, ?, ?, ?, 'запланирован')
        ''', (bus_id, driver_id, route_id, departure_time, arrival_time))
        conn.commit()
    except sqlite3.IntegrityError: 
        conn.close()
        return "Ошибка: автобус уже занят в это время", 400
    conn.close()
    
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True, port=5000)