from models import Car, CarFullInfo, CarStatus, Model, ModelSaleStats, Sale
import os
import bisect
from decimal import Decimal
from datetime import datetime


class CarService:
    def __init__(self, root_directory_path: str) -> None:
        self.root_directory_path = root_directory_path
        self.models_file = os.path.join(root_directory_path, 'models.txt')
        self.models_index_file = os.path.join(root_directory_path, 'models_index.txt')
        self.cars_file = os.path.join(root_directory_path, 'cars.txt')
        self.cars_index_file = os.path.join(root_directory_path, 'cars_index.txt')
        self.sales_file = os.path.join(root_directory_path, 'sales.txt')
        self.sales_index_file = os.path.join(root_directory_path, 'sales_index.txt')

        # Создаем все необходимые файлы
        for file_path in [self.models_file, self.models_index_file,
                self.cars_file, self.cars_index_file, self.sales_file, self.sales_index_file]:
            if not os.path.exists(file_path):
                with open(file_path, 'w', encoding='utf-8') as f:
                    pass

    # Задание 1. Сохранение автомобилей и моделей
    # Добавляем модель
    def add_model(self, model: Model) -> Model:
        # проверяем существование модели в файле
        existings_id = set()
        if os.path.exists(self.models_file):
            with open(self.models_file, 'r', encoding='utf-8') as f:
                for line in f:
                    data = line.strip()
                    if data:
                        parts = data.split(';')
                        existings_id.add(parts[0])
        if str(model.id) in existings_id:
            raise ValueError(f'Модель {model.name} бренд {model.brand} уже существует')
        # Добавляем модель в файл
        with open(self.models_file, 'a', encoding='utf-8') as f:
            # вычисляем номер строки перед вставкой данных
            line_number = os.path.getsize(self.models_file) // 501
            model_str = f'{model.id};{model.name};{model.brand}'.ljust(500) + '\n'
            f.write(model_str)
        # Обновляем индекс
        self._update_model_index(str(model.id), line_number)
        return model
    
    # Добавляем автомобиль
    def add_car(self, car: Car) -> Car:
        # Проверяем существование автомобиля в файле по vin
        existing_vin = set()
        if os.path.exists(self.cars_file):
            with open(self.cars_file, 'r', encoding='utf-8') as f:
                for line in f:
                    data = line.strip()
                    if data:
                        parts = data.split(';')
                        existing_vin.add(parts[0])
        if car.vin in existing_vin:
            raise ValueError(f'Автомобиль {car.model} vin {car.vin} уже существует')
        # Добавляем автомобиль в файл
        with open(self.cars_file, 'a', encoding='utf-8') as f:
            # вычисляем номер строки на которую будет вставка
            line_number = os.path.getsize(self.cars_file) // 501
            car_str = f"{car.vin};{car.model};{car.price};{car.date_start};{car.status.value}".ljust(500) + '\n'
            f.write(car_str)
        # Обновляем индекс
        self._update_car_index(str(car.vin), line_number)
        return car
    
    def _update_model_index(self, model_id: str, line_number: int):
        '''Обновляет индексы моделей'''
        index_list = []
        # Читаем существующий файл с индексами
        if os.path.exists(self.models_index_file):
            with open(self.models_index_file, 'r', encoding='utf-8') as f:
                for line in f:
                    data = line.strip()
                    if data:
                        parts = data.split(';')
                        index_list.append((parts[0], parts[1]))
        # Вычисляем позицию для вставки индекса
        keys = [item[0] for item in index_list]
        insert_pos = bisect.bisect_left(keys, model_id)
        # Делаем вставку в список на нужное место с учетом сортировки бинарным поиском
        index_list.insert(insert_pos, (model_id, str(line_number)))

        # Делаем замену файла с индексами
        with open(self.models_index_file, 'w', encoding='utf-8') as f:
            for key, line_num in index_list:
                line = f'{key};{line_num}'.ljust(500) + '\n'
                f.write(line)

    def _update_car_index(self, vin_num: str, line_number: int):
        '''Обновляет индексы моделей'''
        index_list = []
        # Читаем файл с существующими индексами
        if os.path.exists(self.cars_index_file):
            with open(self.cars_index_file, 'r', encoding='utf-8') as f:
                for line in f:
                    data = line.strip()
                    if data:
                        parts = data.split(';')
                        index_list.append((parts[0], parts[1]))
        # Вычисляем позицию для вставки индекса
        keys = [item[0] for item in index_list]
        insert_pos = bisect.bisect_left(keys, vin_num)
        index_list.insert(insert_pos, (vin_num, str(line_number)))

        # пересохраняем файл с новыми индексами
        with open(self.cars_index_file, 'w', encoding='utf-8') as f:
            for key, line_num in index_list:
                line = f'{key};{line_num}'.ljust(500) + '\n'
                f.write(line)

        
    # Задание 2. Сохранение продаж.
    def sell_car(self, sale: Sale) -> Car:
        # Находим номер строки в файле индексов по vin
        car_line_number = None
        with open(self.cars_index_file, 'r', encoding='utf-8') as f:
            for line in f:
                data = line.strip()
                parts = data.split(';')
                if parts[0] == sale.car_vin:
                    car_line_number = parts[1]
                    break
        # Находим машину в списке машин и меняем статус
        with open(self.cars_file, 'r+', encoding='utf-8') as f:
            if car_line_number:
                f.seek(int(car_line_number) * 501)
                current_line = f.read(501).rstrip()
                parts = current_line.split(';')
                vin, model, price_str, date_start, current_status = parts[:5]
                car = Car(
                    vin=vin,
                    model=int(model.strip()),
                    price=Decimal(price_str),
                    date_start=datetime.strptime(date_start.strip(), '%Y-%m-%d %H:%M:%S'),
                    status=CarStatus(current_status)
                )
            # Обновляем статус
            car.status = CarStatus.sold
            # Формируем строку с новым статусом
            updated_line = f"{car.vin};{car.model};{car.price};{car.date_start};{car.status}".ljust(500) + '\n'
            f.seek(int(car_line_number) * 501)
            f.write(updated_line)
        # Сохраняем информацию о продаже
        self._save_sale_info(sale)
        return car
            
    def _save_sale_info(self, sale: Sale):
        '''Сохраняет информацию о продаже в файл и обновляет индекс'''
        # Добавляем продажу в файл
        with open(self.sales_file, 'a', encoding='utf-8') as f:
            # вычисляем номер строки перед вставкой данных
            line_number = os.path.getsize(self.sales_file) // 501
            # Форматируем дату в строку
            date_str = sale.sales_date.strftime('%Y-%m-%d %H:%M:%S')
            # Формируем строку для записи
            sale_str = f"{sale.sales_number};{sale.car_vin};{date_str};{sale.cost}".ljust(500) + '\n'
            f.write(sale_str)
        
        # Обновляем индекс продаж
        index_list = []
        # Читаем существующий файл с индексами
        if os.path.exists(self.sales_index_file):
            with open(self.sales_index_file, 'r', encoding='utf-8') as f:
                for line in f:
                    data = line.strip()
                    if data:
                        parts = data.split(';')
                        index_list.append((parts[0], parts[1]))
        
        # Вычисляем позицию для вставки индекса
        keys = [item[0] for item in index_list]
        insert_pos = bisect.bisect_left(keys, sale.car_vin)
        # Делаем вставку в список на нужное место с учетом сортировки
        index_list.insert(insert_pos, (sale.car_vin, str(line_number)))

        # Сохраняем обновленный индекс
        with open(self.sales_index_file, 'w', encoding='utf-8') as f:
            for key, line_num in index_list:
                line = f'{key};{line_num}'.ljust(500) + '\n'
                f.write(line)

    # Задание 3. Доступные к продаже
    def get_cars(self, status: CarStatus) -> list[Car]:
        '''Возвращает список автомобилей с указанным статусом, отсортированный по VIN'''
        cars = []
        # Читаем все автомобили из файла
        with open(self.cars_file, 'r', encoding='utf-8') as f:
            for line in f:
                data = line.strip()
                if not data:
                    continue
                parts = data.split(';')
                vin, model, price_str, date_start, current_status = parts[:5]
                # Если статус совпадает, добавляем автомобиль в список
                if current_status == status.value:
                    car = Car(
                        vin=vin,
                        model=int(model.strip()),
                        price=Decimal(price_str),
                        date_start=datetime.strptime(date_start.strip(), '%Y-%m-%d %H:%M:%S'),
                        status=CarStatus(current_status)
                    )
                    cars.append(car)
        
        # Сортируем список по VIN
        # cars.sort(key=lambda x: x.vin)
        
        return cars

    # Задание 4. Детальная информация
    def get_car_info(self, vin: str) -> CarFullInfo | None:
        '''Получает полную информацию об автомобиле по VIN'''
        # Находим номер строки в файле индексов по vin
        car_line_number = None
        with open(self.cars_index_file, 'r', encoding='utf-8') as f:
            for line in f:
                data = line.strip()
                parts = data.split(';')
                if parts[0] == vin:
                    car_line_number = parts[1]
                    break
        
        if not car_line_number:
            return None
            
        # Читаем информацию об автомобиле
        with open(self.cars_file, 'r', encoding='utf-8') as f:
            f.seek(int(car_line_number) * 501)
            current_line = f.read(501).rstrip()
            parts = current_line.split(';')
            vin, model_id, price_str, date_start, status = parts[:5]
            
            # Читаем информацию о модели
            model_line_number = None
            with open(self.models_index_file, 'r', encoding='utf-8') as f_model:
                for line in f_model:
                    data = line.strip()
                    parts = data.split(';')
                    if parts[0] == model_id:
                        model_line_number = parts[1]
                        break
            
            if not model_line_number:
                return None
                
            # Читаем данные модели
            with open(self.models_file, 'r', encoding='utf-8') as f_model:
                f_model.seek(int(model_line_number) * 501)
                model_line = f_model.read(501).rstrip()
                model_parts = model_line.split(';')
                _, model_name, model_brand = model_parts[:3]
            
            # Ищем информацию о продаже
            sales_date = None
            sales_cost = None
            with open(self.sales_index_file, 'r', encoding='utf-8') as f_sales:
                for line in f_sales:
                    data = line.strip()
                    parts = data.split(';')
                    if parts[0] == vin:
                        sale_line_number = parts[1]
                        with open(self.sales_file, 'r', encoding='utf-8') as f_sale:
                            f_sale.seek(int(sale_line_number) * 501)
                            sale_line = f_sale.read(501).rstrip()
                            sale_parts = sale_line.split(';')
                            sales_date = datetime.strptime(sale_parts[2], '%Y-%m-%d %H:%M:%S')
                            sales_cost = Decimal(sale_parts[3])
                        break
            
            return CarFullInfo(
                vin=vin,
                car_model_name=model_name,
                car_model_brand=model_brand,
                price=Decimal(price_str),
                date_start=datetime.strptime(date_start.strip(), '%Y-%m-%d %H:%M:%S'),
                status=CarStatus(status),
                sales_date=sales_date,
                sales_cost=sales_cost
            )

    # Задание 5. Обновление ключевого поля
    def update_vin(self, vin: str, new_vin: str) -> Car:
        '''Обновляет VIN номер автомобиля и все связанные записи'''
        # Находим номер строки в файле индексов по vin
        car_line_number = None
        with open(self.cars_index_file, 'r', encoding='utf-8') as f:
            for line in f:
                data = line.strip()
                parts = data.split(';')
                if parts[0] == vin:
                    car_line_number = parts[1]
                    break
        
        if not car_line_number:
            raise ValueError(f'Автомобиль с VIN {vin} не найден')
            
        # Читаем информацию об автомобиле
        with open(self.cars_file, 'r+', encoding='utf-8') as f:
            f.seek(int(car_line_number) * 501)
            current_line = f.read(501).rstrip()
            parts = current_line.split(';')
            _, model, price_str, date_start, status = parts[:5]
            
            # Создаем обновленный объект Car
            car = Car(
                vin=new_vin,
                model=int(model.strip()),
                price=Decimal(price_str),
                date_start=datetime.strptime(date_start.strip(), '%Y-%m-%d %H:%M:%S'),
                status=CarStatus(status)
            )
            
            # Обновляем запись в файле cars.txt
            updated_line = f"{new_vin};{model};{price_str};{date_start};{status}".ljust(500) + '\n'
            f.seek(int(car_line_number) * 501)
            f.write(updated_line)
        
        # Обновляем индекс автомобилей
        index_list = []
        with open(self.cars_index_file, 'r', encoding='utf-8') as f:
            for line in f:
                data = line.strip()
                if data:
                    parts = data.split(';')
                    if parts[0] != vin:  # Пропускаем старый VIN
                        index_list.append((parts[0], parts[1]))
        
        # Добавляем новый VIN в индекс с тем же номером строки
        keys = [item[0] for item in index_list]
        insert_pos = bisect.bisect_left(keys, new_vin)
        index_list.insert(insert_pos, (new_vin, car_line_number))
        
        # Сохраняем обновленный индекс
        with open(self.cars_index_file, 'w', encoding='utf-8') as f:
            for key, line_num in index_list:
                line = f'{key};{line_num}'.ljust(500) + '\n'
                f.write(line)
        
        # Обновляем VIN в файле продаж, если есть
        if os.path.exists(self.sales_file):
            with open(self.sales_file, 'r+', encoding='utf-8') as f:
                lines = f.readlines()
                f.seek(0)
                for line in lines:
                    if line.strip():
                        parts = line.split(';')
                        if parts[1] == vin:  # Если это продажа нашего автомобиля
                            # Обновляем VIN в номере продажи и в записи
                            sales_number = parts[0]
                            new_sales_number = sales_number.replace(vin, new_vin)
                            updated_line = f"{new_sales_number};{new_vin};{parts[2]};{parts[3]}".ljust(500) + '\n'
                            f.write(updated_line)
                        else:
                            f.write(line)
                f.truncate()
        
        # Обновляем индекс продаж
        if os.path.exists(self.sales_index_file):
            index_list = []
            with open(self.sales_index_file, 'r', encoding='utf-8') as f:
                for line in f:
                    data = line.strip()
                    if data:
                        parts = data.split(';')
                        if parts[0] != vin:  # Пропускаем старый VIN
                            index_list.append((parts[0], parts[1]))
            
            # Добавляем новый VIN в индекс продаж с сохранением номера строки из файла продаж
            if os.path.exists(self.sales_file):
                with open(self.sales_file, 'r', encoding='utf-8') as f:
                    for i, line in enumerate(f):
                        if line.strip():
                            parts = line.split(';')
                            if parts[1] == new_vin:  # Если это продажа нашего автомобиля
                                keys = [item[0] for item in index_list]
                                insert_pos = bisect.bisect_left(keys, new_vin)
                                index_list.insert(insert_pos, (new_vin, str(i)))
                                break
            
            # Сохраняем обновленный индекс продаж
            with open(self.sales_index_file, 'w', encoding='utf-8') as f:
                for key, line_num in index_list:
                    line = f'{key};{line_num}'.ljust(500) + '\n'
                    f.write(line)
        
        return car

    # Задание 6. Удаление продажи
    def revert_sale(self, sales_number: str) -> Car:
        '''Отменяет продажу автомобиля и удаляет запись о продаже'''
        # Находим запись о продаже
        car_vin = None
        sale_line_number = None
        with open(self.sales_file, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                data = line.strip()
                if data:
                    parts = data.split(';')
                    if parts[0] == sales_number:
                        car_vin = parts[1]
                        sale_line_number = i
                        break
        
        if not car_vin:
            raise ValueError(f'Продажа с номером {sales_number} не найдена')
        
        # Находим номер строки в файле индексов по vin
        car_line_number = None
        with open(self.cars_index_file, 'r', encoding='utf-8') as f:
            for line in f:
                data = line.strip()
                parts = data.split(';')
                if parts[0] == car_vin:
                    car_line_number = parts[1]
                    break
        
        if not car_line_number:
            raise ValueError(f'Автомобиль с VIN {car_vin} не найден')
        
        # Читаем информацию об автомобиле
        with open(self.cars_file, 'r+', encoding='utf-8') as f:
            f.seek(int(car_line_number) * 501)
            current_line = f.read(501).rstrip()
            parts = current_line.split(';')
            vin, model, price_str, date_start, _ = parts[:5]
            
            # Создаем обновленный объект Car
            car = Car(
                vin=vin,
                model=int(model.strip()),
                price=Decimal(price_str),
                date_start=datetime.strptime(date_start.strip(), '%Y-%m-%d %H:%M:%S'),
                status=CarStatus.available
            )
            
            # Обновляем запись в файле cars.txt
            updated_line = f"{car.vin};{car.model};{car.price};{car.date_start};{car.status.value}".ljust(500) + '\n'
            f.seek(int(car_line_number) * 501)
            f.write(updated_line)
        
        # Помечаем запись о продаже как удаленную
        with open(self.sales_file, 'r+', encoding='utf-8') as f:
            f.seek(sale_line_number * 501)
            current_line = f.read(501).rstrip()
            parts = current_line.split(';')
            # Добавляем флаг is_deleted в конец строки
            updated_line = f"{parts[0]};{parts[1]};{parts[2]};{parts[3]};is_deleted".ljust(500) + '\n'
            f.seek(sale_line_number * 501)
            f.write(updated_line)
        
        # Обновляем индекс продаж
        if os.path.exists(self.sales_index_file):
            index_list = []
            with open(self.sales_index_file, 'r', encoding='utf-8') as f:
                for line in f:
                    data = line.strip()
                    if data:
                        parts = data.split(';')
                        if parts[0] != car_vin:  # Пропускаем удаляемую запись
                            index_list.append((parts[0], parts[1]))
            
            # Сохраняем обновленный индекс продаж
            with open(self.sales_index_file, 'w', encoding='utf-8') as f:
                for key, line_num in index_list:
                    line = f'{key};{line_num}'.ljust(500) + '\n'
                    f.write(line)
        
        return car

    # Задание 7. Самые продаваемые модели
    def top_models_by_sales(self) -> list[ModelSaleStats]:
        '''Возвращает топ-3 самых продаваемых моделей'''
        # Словарь для подсчета продаж по id модели
        model_sales = {}
        
        # Читаем файл продаж и считаем количество продаж для каждой модели
        with open(self.sales_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    parts = line.split(';')
                    car_vin = parts[1]
                    
                    # Находим id модели по VIN
                    car_line_number = None
                    with open(self.cars_index_file, 'r', encoding='utf-8') as f_cars:
                        for line in f_cars:
                            data = line.strip()
                            if data:
                                parts = data.split(';')
                                if parts[0] == car_vin:
                                    car_line_number = parts[1]
                                    break
                    
                    if car_line_number:
                        # Читаем информацию об автомобиле
                        with open(self.cars_file, 'r', encoding='utf-8') as f_cars:
                            f_cars.seek(int(car_line_number) * 501)
                            car_line = f_cars.read(501).rstrip()
                            parts = car_line.split(';')
                            model_id = int(parts[1].strip())
                            
                            # Увеличиваем счетчик продаж для модели
                            model_sales[model_id] = model_sales.get(model_id, 0) + 1
        
        # Сортируем модели по количеству продаж
        sorted_models = sorted(model_sales.items(), key=lambda x: x[1], reverse=True)
        
        # Берем топ-3 модели
        top_models = []
        for model_id, sales_count in sorted_models[:3]:
            # Находим номер строки модели в индексе
            model_line_number = None
            with open(self.models_index_file, 'r', encoding='utf-8') as f:
                for line in f:
                    data = line.strip()
                    if data:
                        parts = data.split(';')
                        if parts[0] == str(model_id):
                            model_line_number = parts[1]
                            break
            
            if model_line_number:
                # Читаем информацию о модели
                with open(self.models_file, 'r', encoding='utf-8') as f:
                    f.seek(int(model_line_number) * 501)
                    model_line = f.read(501).rstrip()
                    parts = model_line.split(';')
                    model_name = parts[1].strip()
                    model_brand = parts[2].strip()
                    
                    # Создаем объект ModelSaleStats
                    top_models.append(ModelSaleStats(
                        car_model_name=model_name,
                        brand=model_brand,
                        sales_number=sales_count
                    ))
        
        return top_models
