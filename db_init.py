import sqlite3
import hashlib

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

conn = sqlite3.connect('avtovokzal.db')
cursor = conn.cursor()

cursor.execute('PRAGMA foreign_keys = ON')

# 1. Таблица маршрутов
cursor.execute('''
CREATE TABLE Routes (
    route_id INTEGER PRIMARY KEY AUTOINCREMENT,
    route_number TEXT NOT NULL UNIQUE,
    departure_city TEXT NOT NULL,
    arrival_city TEXT NOT NULL,
    distance_km INTEGER,
    travel_time_minutes INTEGER,
    base_price DECIMAL(10,2)
)
''')

# 2. Таблица водителей
cursor.execute('''
CREATE TABLE Drivers (
    driver_id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    middle_name TEXT,
    license_number TEXT UNIQUE NOT NULL,
    experience_years INTEGER,
    phone TEXT
)
''')

# 3. Таблица автобусов
cursor.execute('''
CREATE TABLE Buses (
    bus_id INTEGER PRIMARY KEY AUTOINCREMENT,
    license_plate TEXT UNIQUE NOT NULL,
    model TEXT,
    capacity INTEGER NOT NULL,
    manufacture_year INTEGER,
    bus_condition TEXT DEFAULT 'исправен',
    driver_id INTEGER,
    FOREIGN KEY (driver_id) REFERENCES Drivers(driver_id) ON DELETE SET NULL
)
''')

# 4. Таблица пассажиров
cursor.execute('''
CREATE TABLE Passengers (
    passenger_id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    middle_name TEXT,
    passport_number TEXT UNIQUE NOT NULL,
    phone TEXT,
    email TEXT
)
''')

# 5. Таблица расписания
cursor.execute('''
CREATE TABLE BusSchedule (
    schedule_id INTEGER PRIMARY KEY AUTOINCREMENT,
    bus_id INTEGER NOT NULL,
    driver_id INTEGER NOT NULL,
    route_id INTEGER NOT NULL,
    departure_time DATETIME NOT NULL,
    arrival_time DATETIME NOT NULL,
    available_seats INTEGER,
    schedule_status TEXT DEFAULT 'запланирован',
    FOREIGN KEY (bus_id) REFERENCES Buses(bus_id) ON DELETE CASCADE,
    FOREIGN KEY (driver_id) REFERENCES Drivers(driver_id) ON DELETE CASCADE,
    FOREIGN KEY (route_id) REFERENCES Routes(route_id) ON DELETE CASCADE,
    UNIQUE(bus_id, departure_time)
)
''')

# 6. Таблица пользователей (НОВАЯ)
cursor.execute('''
CREATE TABLE Users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT,
    email TEXT,
    phone TEXT,
    role TEXT DEFAULT 'user',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
''')

# 7. Таблица билетов (обновлена с user_id)
cursor.execute('''
CREATE TABLE Tickets (
    ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
    schedule_id INTEGER NOT NULL,
    passenger_id INTEGER NOT NULL,
    user_id INTEGER,
    seat_number INTEGER,
    price DECIMAL(10,2),
    purchase_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    ticket_status TEXT DEFAULT 'active',
    FOREIGN KEY (schedule_id) REFERENCES BusSchedule(schedule_id),
    FOREIGN KEY (passenger_id) REFERENCES Passengers(passenger_id),
    FOREIGN KEY (user_id) REFERENCES Users(user_id)
)
''')

print("Таблицы успешно созданы!")

print("\nЗаполнение базы данных тестовыми данными...")

# Добавляем маршруты
routes_data = [
    ('101', 'Москва', 'Санкт-Петербург', 700, 480, 1500.00),
    ('102', 'Москва', 'Нижний Новгород', 420, 360, 1200.00),
    ('103', 'Санкт-Петербург', 'Москва', 700, 480, 1500.00),
    ('104', 'Казань', 'Москва', 820, 600, 1800.00),
    ('105', 'Москва', 'Ярославль', 260, 210, 800.00),
    ('106', 'Москва', 'Владимир', 180, 150, 600.00),
    ('107', 'Нижний Новгород', 'Казань', 380, 330, 1000.00)
]

cursor.executemany('''
INSERT INTO Routes (route_number, departure_city, arrival_city, distance_km, travel_time_minutes, base_price)
VALUES (?, ?, ?, ?, ?, ?)
''', routes_data)

print(f"Добавлено {len(routes_data)} маршрутов")

# Добавляем водителей
drivers_data = [
    ('Иван', 'Петров', 'Сергеевич', '77 АВ 123456', 15, '+79127573082'),
    ('Петр', 'Иванов', 'Алексеевич', '77 АВ 234567', 10, '+79865325489'),
    ('Сергей', 'Сидоров', 'Николаевич', '77 АВ 345678', 8, '+7989565965'),
    ('Алексей', 'Козлов', 'Петрович', '77 АВ 456789', 20, '+7985356897'),
    ('Дмитрий', 'Михайлов', 'Иванович', '77 АВ 567890', 5, '+7989565889')
]

cursor.executemany('''
INSERT INTO Drivers (first_name, last_name, middle_name, license_number, experience_years, phone)
VALUES (?, ?, ?, ?, ?, ?)
''', drivers_data)

print(f"Добавлено {len(drivers_data)} водителей")

# Добавляем автобусы
buses_data = [
    ('А101ВВ', 'Мерседес Sprinter', 20, 2020, 'исправен', 1),
    ('А202ВВ', 'ПАЗ Vector', 30, 2021, 'исправен', 2),
    ('А303ВВ', 'МАЗ 231', 45, 2019, 'исправен', 3),
    ('А404ВВ', 'ЛиАЗ 5292', 50, 2022, 'исправен', 4),
    ('А505ВВ', 'НефАЗ 5299', 40, 2020, 'ремонт', 5),
    ('А606ВВ', 'Мерседес Travego', 55, 2023, 'исправен', 1)
]

cursor.executemany('''
INSERT INTO Buses (license_plate, model, capacity, manufacture_year, bus_condition, driver_id)
VALUES (?, ?, ?, ?, ?, ?)
''', buses_data)

print(f"Добавлено {len(buses_data)} автобусов")

# Добавляем пассажиров
passengers_data = [
    ('Анна', 'Смирнова', 'Владимировна', '4512345678', '+79598123486', 'anna@mail.ru'),
    ('Михаил', 'Кузнецов', 'Дмитриевич', '4512456789', '+79853178264', 'mikhail@mail.ru'),
    ('Елена', 'Попова', 'Александровна', '4512567890', '+79823156795', 'elena@mail.ru'),
    ('Александр', 'Васильев', 'Игоревич', '4512678901', '+79561237894', 'alex@mail.ru'),
    ('Татьяна', 'Павлова', 'Сергеевна', '4512789012', '+79842357912', 'tanya@mail.ru'),
    ('Владимир', 'Николаев', 'Петрович', '4512890123', '+79513245678', 'vladimir@mail.ru'),
    ('Наталья', 'Морозова', 'Алексеевна', '4512901234', '+79865781245', 'natalia@mail.ru')
]

cursor.executemany('''
INSERT INTO Passengers (first_name, last_name, middle_name, passport_number, phone, email)
VALUES (?, ?, ?, ?, ?, ?)
''', passengers_data)

print(f"Добавлено {len(passengers_data)} пассажиров")

# Добавляем пользователей (включая админа)
users_data = [
    ('admin', hash_password('admin'), 'Системный администратор', 'admin@avtovokzal.ru', '+70000000000', 'admin'),
    ('ivanov', hash_password('123456'), 'Иван Иванов', 'ivanov@mail.ru', '+79161234567', 'user'),
    ('petrov', hash_password('123456'), 'Петр Петров', 'petrov@mail.ru', '+79162345678', 'user'),
    ('sidorov', hash_password('123456'), 'Сидор Сидоров', 'sidorov@mail.ru', '+79163456789', 'user')
]

cursor.executemany('''
INSERT INTO Users (username, password_hash, full_name, email, phone, role)
VALUES (?, ?, ?, ?, ?, ?)
''', users_data)

print(f"Добавлено {len(users_data)} пользователей")

# Добавляем расписание (несколько рейсов на сегодня и завтра)
from datetime import datetime, timedelta

now = datetime.now()
schedules_data = []

# Рейс Москва -> Санкт-Петербург (сегодня в 10:00)
dep1 = now.replace(hour=10, minute=0, second=0, microsecond=0)
if dep1 < now:
    dep1 += timedelta(days=1)
arr1 = dep1 + timedelta(minutes=480)
schedules_data.append((1, 1, 1, dep1.strftime('%Y-%m-%d %H:%M:%S'), arr1.strftime('%Y-%m-%d %H:%M:%S'), 20, 'запланирован'))

# Рейс Москва -> Нижний Новгород (сегодня в 12:00)
dep2 = now.replace(hour=12, minute=0, second=0, microsecond=0)
if dep2 < now:
    dep2 += timedelta(days=1)
arr2 = dep2 + timedelta(minutes=360)
schedules_data.append((2, 2, 2, dep2.strftime('%Y-%m-%d %H:%M:%S'), arr2.strftime('%Y-%m-%d %H:%M:%S'), 30, 'запланирован'))

# Рейс Казань -> Москва (сегодня в 08:00)
dep3 = now.replace(hour=8, minute=0, second=0, microsecond=0)
if dep3 < now:
    dep3 += timedelta(days=1)
arr3 = dep3 + timedelta(minutes=600)
schedules_data.append((4, 4, 4, dep3.strftime('%Y-%m-%d %H:%M:%S'), arr3.strftime('%Y-%m-%d %H:%M:%S'), 50, 'запланирован'))

# Рейс Москва -> Санкт-Петербург (завтра в 22:00)
dep4 = now.replace(hour=22, minute=0, second=0, microsecond=0) + timedelta(days=1)
arr4 = dep4 + timedelta(minutes=480)
schedules_data.append((1, 5, 1, dep4.strftime('%Y-%m-%d %H:%M:%S'), arr4.strftime('%Y-%m-%d %H:%M:%S'), 55, 'запланирован'))

cursor.executemany('''
INSERT INTO BusSchedule (bus_id, driver_id, route_id, departure_time, arrival_time, available_seats, schedule_status)
VALUES (?, ?, ?, ?, ?, ?, ?)
''', schedules_data)

print(f"Добавлено {len(schedules_data)} рейсов в расписание")

print("\nБаза данных успешно создана и заполнена!\n")

# Вывод статистики
print("Статистика базы данных:")
print(f"Маршрутов: {cursor.execute('SELECT COUNT(*) FROM Routes').fetchone()[0]}")
print(f"Водителей: {cursor.execute('SELECT COUNT(*) FROM Drivers').fetchone()[0]}")
print(f"Автобусов: {cursor.execute('SELECT COUNT(*) FROM Buses').fetchone()[0]}")
print(f"Пассажиров: {cursor.execute('SELECT COUNT(*) FROM Passengers').fetchone()[0]}")
print(f"Пользователей: {cursor.execute('SELECT COUNT(*) FROM Users').fetchone()[0]}")
print(f"Рейсов: {cursor.execute('SELECT COUNT(*) FROM BusSchedule').fetchone()[0]}")

# Сохраняем изменения и закрываем соединение
conn.commit()
conn.close()

print("\nБаза данных сохранена в файле 'avtovokzal.db'")