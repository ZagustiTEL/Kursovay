import sqlite3

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
    travel_time_minutes INTEGER
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

# 5. Таблица расписания автобусов
cursor.execute('''
CREATE TABLE BusSchedule (
    schedule_id INTEGER PRIMARY KEY AUTOINCREMENT,
    bus_id INTEGER NOT NULL,
    driver_id INTEGER NOT NULL,
    route_id INTEGER NOT NULL,
    departure_time DATETIME NOT NULL,
    arrival_time DATETIME NOT NULL,
    schedule_status TEXT DEFAULT 'запланирован',
    FOREIGN KEY (bus_id) REFERENCES Buses(bus_id) ON DELETE CASCADE,
    FOREIGN KEY (driver_id) REFERENCES Drivers(driver_id) ON DELETE CASCADE,
    FOREIGN KEY (route_id) REFERENCES Routes(route_id) ON DELETE CASCADE,
    UNIQUE(bus_id, departure_time)
)
''')
# 6. Создаем простую таблицу для билетов
cursor.execute('''
CREATE TABLE IF NOT EXISTS Tickets (
    ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
    schedule_id INTEGER,
    passenger_id INTEGER,
    price DECIMAL(10,2)
)
''')


cursor.execute("SELECT COUNT(*) FROM Tickets")
if cursor.fetchone()[0] == 0:
    # Добавляем несколько тестовых продаж
    cursor.executemany('''
    INSERT INTO Tickets (schedule_id, passenger_id, price)
    VALUES (?, ?, ?)
    ''', [
        (1, 1, 1500), (1, 2, 1500), (2, 1, 1200), (2, 3, 1200),
        (3, 1, 1500), (4, 2, 1800), (5, 4, 800), (6, 5, 600)
    ])

print("Таблицы успешно созданы!")

print("\nЗаполнение базы данных тестовыми данными...")

# Добавляем маршруты
routes_data = [
    ('101', 'Москва', 'Санкт-Петербург', 700, 480),
    ('102', 'Москва', 'Нижний Новгород', 420, 360),
    ('103', 'Санкт-Петербург', 'Москва', 700, 480),
    ('104', 'Казань', 'Москва', 820, 600),
    ('105', 'Москва', 'Ярославль', 260, 210),
    ('106', 'Москва', 'Владимир', 180, 150),
    ('107', 'Нижний Новгород', 'Казань', 380, 330)
]

cursor.executemany('''
INSERT INTO Routes (route_number, departure_city, arrival_city, distance_km, travel_time_minutes)
VALUES (?, ?, ?, ?, ?)
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
    ('А 101 ВВ', 'Мерседес Sprinter', 20, 2020, 'исправен', 1),
    ('А 202 ВВ', 'ПАЗ Vector', 30, 2021, 'исправен', 2),
    ('А 303 ВВ', 'МАЗ 231', 45, 2019, 'исправен', 3),
    ('А 404 ВВ', 'ЛиАЗ 5292', 50, 2022, 'исправен', 4),
    ('А 505 ВВ', 'НефАЗ 5299', 40, 2020, 'ремонт', 5),
    ('А 606 ВВ', 'Мерседес Travego', 55, 2023, 'исправен', 1)
]

cursor.executemany('''
INSERT INTO Buses (license_plate, model, capacity, manufacture_year, bus_condition, driver_id)
VALUES (?, ?, ?, ?, ?, ?)
''', buses_data)

print(f"Добавлено {len(buses_data)} автобусов")
# Добавляем пассажиров
passengers_data = [
    ('Анна', 'Смирнова', 'Владимировна', '45 12 345678', '+79598123486', 'anna@mail.ru'),
    ('Михаил', 'Кузнецов', 'Дмитриевич', '45 12 456789', '+79853178264', 'mikhail@mail.ru'),
    ('Елена', 'Попова', 'Александровна', '45 12 567890', '+79823156795', 'elena@mail.ru'),
    ('Александр', 'Васильев', 'Игоревич', '45 12 678901', '+79561237894', 'alex@mail.ru'),
    ('Татьяна', 'Павлова', 'Сергеевна', '45 12 789012', '+79842357912', 'tanya@mail.ru'),
    ('Владимир', 'Николаев', 'Петрович', '45 12 890123', '+79513245678', 'vladimir@mail.ru'),
    ('Наталья', 'Морозова', 'Алексеевна', '45 12 901234', '+79865781245', 'natalia@mail.ru')
]

cursor.executemany('''
INSERT INTO Passengers (first_name, last_name, middle_name, passport_number, phone, email)
VALUES (?, ?, ?, ?, ?, ?)
''', passengers_data)

print(f"Добавлено {len(passengers_data)} пассажиров")

# Добавляем расписание автобусов
schedule_data = [
    (1, 1, 1, '2026-02-20 08:00:00', '2026-02-20 16:00:00', 'запланирован'),
    (2, 2, 2, '2026-02-20 09:30:00', '2026-02-20 15:30:00', 'запланирован'),
    (3, 3, 3, '2026-02-20 10:00:00', '2026-02-20 18:00:00', 'запланирован'),
    (4, 4, 4, '2026-02-20 11:00:00', '2026-02-20 21:00:00', 'запланирован'),
    (6, 1, 5, '2026-02-20 12:00:00', '2026-02-20 15:30:00', 'запланирован'),
    (1, 1, 1, '2026-02-21 08:00:00', '2026-02-21 16:00:00', 'запланирован'),
    (2, 2, 6, '2026-02-21 09:00:00', '2026-02-21 11:30:00', 'запланирован'),
    (3, 3, 7, '2026-02-21 10:30:00', '2026-02-21 16:00:00', 'запланирован'),
    (4, 4, 2, '2026-02-21 12:00:00', '2026-02-21 18:00:00', 'запланирован'),
    (6, 1, 3, '2026-02-21 14:00:00', '2026-02-21 22:00:00', 'запланирован'),
    (1, 1, 1, '2026-02-22 08:00:00', '2026-02-22 16:00:00', 'запланирован'),
    (2, 2, 5, '2026-02-22 15:00:00', '2026-02-22 18:30:00', 'запланирован'),
    (3, 3, 4, '2026-03-03 20:00:00', '2026-03-04 06:00:00', 'запланирован')
]

cursor.executemany('''
INSERT INTO BusSchedule (bus_id, driver_id, route_id, departure_time, arrival_time, schedule_status)
VALUES (?, ?, ?, ?, ?, ?)
''', schedule_data)

print(f"Добавлено {len(schedule_data)} записей в расписание")

print("База данных успешно создана и заполнена!\n")

cursor.execute('SELECT COUNT(*) FROM Routes')
print(f"Маршрутов: {cursor.fetchone()[0]}")

cursor.execute('SELECT COUNT(*) FROM Drivers')
print(f"Водителей: {cursor.fetchone()[0]}")

cursor.execute('SELECT COUNT(*) FROM Buses')
print(f"Автобусов: {cursor.fetchone()[0]}")

cursor.execute('SELECT COUNT(*) FROM Passengers')
print(f"Пассажиров: {cursor.fetchone()[0]}")

cursor.execute('SELECT COUNT(*) FROM BusSchedule')
print(f"Записей в расписании: {cursor.fetchone()[0]}")

conn.commit()
conn.close()

print("\nБаза данных сохранена в файле 'avtovokzal.db'")