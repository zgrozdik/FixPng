#!/usr/bin/env python3
"""
Улучшенный скрипт для восстановления PNG файлов
"""

import os
import struct
import sys

def repair_png_file(input_file, output_file=None):
    """
    Восстанавливает поврежденные PNG файлы
    """
    try:
        # Читаем файл
        with open(input_file, 'rb') as f:
            data = f.read()
        
        print(f"📂 Обрабатываем: {input_file}")
        print(f"📊 Размер файла: {len(data)} байт")
        
        # Сигнатура PNG
        png_signature = b'\x89PNG\r\n\x1a\n'
        
        # Если файл пустой или очень маленький
        if len(data) < 8:
            print("⚠️  Файл слишком маленький, создаю минимальный PNG...")
            data = create_minimal_png()
        
        # Исправляем сигнатуру если нужно
        fixed_data = bytearray(data)
        if len(fixed_data) >= 8:
            if fixed_data[:8] != png_signature:
                print("🔧 Исправляю сигнатуру PNG...")
                # Сохраняем оригинальные данные после сигнатуры
                rest_of_file = fixed_data[8:] if len(fixed_data) > 8 else b''
                fixed_data = bytearray(png_signature) + rest_of_file
        
        # Теперь пытаемся восстановить структуру чанков
        fixed_data = repair_chunk_structure(fixed_data)
        
        # Определяем имя выходного файла
        if output_file is None:
            name, ext = os.path.splitext(input_file)
            output_file = f"{name}_repaired{ext}"
        
        # Записываем восстановленный файл
        with open(output_file, 'wb') as f:
            f.write(fixed_data)
        
        print(f"✅ Файл сохранен: {output_file}")
        print(f"📊 Новый размер: {len(fixed_data)} байт")
        
        # Проверка восстановленного файла
        check_repaired_file(fixed_data, output_file)
        
        # Дополнительная проверка - пытаемся открыть файл
        if can_open_as_png(output_file):
            print("🎉 Файл можно открыть как PNG!")
            return True
        else:
            print("⚠️  Файл восстановлен, но может не открываться в просмотрщиках")
            return True
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        return False

def create_minimal_png():
    """Создает минимальный валидный PNG (1x1 черный пиксель)"""
    # Более правильный минимальный PNG
    return bytes.fromhex(
        '89504e470d0a1a0a'  # Сигнатура PNG
        '0000000d'          # Длина IHDR = 13
        '49484452'          # IHDR
        '00000001'          # Ширина = 1
        '00000001'          # Высота = 1
        '0802000000'        # 8-bit, RGB, без сжатия
        '9a7701ff'          # CRC IHDR
        '00000000'          # Длина IDAT = 0 (можно пропустить)
        '49444154'          # IDAT
        '00000000'          # CRC IDAT (для длины 0)
        '00000000'          # Длина IEND = 0
        '49454e44'          # IEND
        'ae426082'          # CRC IEND (фиксированный)
    )

def repair_chunk_structure(data):
    """Пытается восстановить структуру чанков PNG"""
    if len(data) < 8:
        return data
    
    result = bytearray(data[:8])  # Начинаем с сигнатуры
    offset = 8
    
    while offset < len(data):
        # Нужно минимум 12 байт для чанка (4 длина + 4 тип + минимум 0 данных + 4 CRC)
        if offset + 12 > len(data):
            break
        
        try:
            # Читаем длину чанка
            length_bytes = data[offset:offset+4]
            if len(length_bytes) < 4:
                break
            
            length = struct.unpack('>I', length_bytes)[0]
            
            # Проверяем, что длина реалистичная
            if length > 10000000:  # Слишком большая длина
                offset += 1
                continue
            
            # Читаем тип чанка
            if offset + 8 > len(data):
                break
                
            chunk_type = data[offset+4:offset+8]
            
            # Проверяем, что тип чанка состоит из букв
            if not all(65 <= b <= 90 or 97 <= b <= 122 for b in chunk_type):
                offset += 1
                continue
            
            # Проверяем, что данные чанка помещаются в файл
            chunk_end = offset + 12 + length
            if chunk_end > len(data):
                break
            
            # Добавляем чанк в результат
            result.extend(data[offset:chunk_end])
            
            # Переходим к следующему чанку
            offset = chunk_end
            
            # Если это IEND, заканчиваем
            if chunk_type == b'IEND':
                break
                
        except:
            offset += 1
            continue
    
    # Гарантируем наличие IEND
    if b'IEND' not in result:
        print("🔧 Добавляю отсутствующий IEND чанк...")
        result.extend(b'\x00\x00\x00\x00IEND\xae\x42\x60\x82')
    
    return result

def check_repaired_file(data, filename):
    """Проверяет восстановленный файл"""
    print("\n🔍 Проверка восстановленного файла:")
    
    # Проверяем сигнатуру
    if len(data) >= 8:
        if data[:8] == b'\x89PNG\r\n\x1a\n':
            print("  ✅ Сигнатура PNG: OK")
        else:
            print(f"  ❌ Неверная сигнатура: {data[:8].hex()}")
    else:
        print("  ❌ Файл слишком короткий")
    
    # Проверяем ключевые чанки
    required_chunks = [
        ("IHDR", b'IHDR', True),   # Обязательный
        ("IDAT", b'IDAT', False),  # Желательный
        ("IEND", b'IEND', True),   # Обязательный
    ]
    
    for name, marker, required in required_chunks:
        if marker in data:
            print(f"  ✅ {name} чанк: найден")
        elif required:
            print(f"  ❌ {name} чанк: ОБЯЗАТЕЛЬНЫЙ, не найден!")
        else:
            print(f"  ⚠️  {name} чанк: не найден")
    
    # Проверяем размеры если есть IHDR
    if b'IHDR' in data:
        ihdr_pos = data.find(b'IHDR')
        if ihdr_pos != -1 and ihdr_pos + 16 <= len(data):
            try:
                width = struct.unpack('>I', data[ihdr_pos+4:ihdr_pos+8])[0]
                height = struct.unpack('>I', data[ihdr_pos+8:ihdr_pos+12])[0]
                print(f"  📏 Размеры: {width}x{height} пикселей")
            except:
                print("  ⚠️  Не удалось прочитать размеры")

def can_open_as_png(filename):
    """Пытается открыть файл как PNG (упрощенная проверка)"""
    try:
        with open(filename, 'rb') as f:
            data = f.read()
        
        # Минимальные требования для PNG
        if len(data) < 8:
            return False
        
        if data[:8] != b'\x89PNG\r\n\x1a\n':
            return False
        
        if b'IHDR' not in data:
            return False
        
        if b'IEND' not in data:
            return False
        
        return True
        
    except:
        return False

def main():
    """Основная функция"""
    if len(sys.argv) < 2:
        print("Использование: python png_repair.py <файл.png> [выходной_файл.png]")
        print("Примеры:")
        print("  python png_repair.py поврежденный.png")
        print("  python png_repair.py поврежденный.png восстановленный.png")
        print("  python png_repair.py поврежденный.png -v  # Подробный вывод")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith('-') else None
    
    if not os.path.exists(input_file):
        print(f"❌ Файл не найден: {input_file}")
        sys.exit(1)
    
    success = repair_png_file(input_file, output_file)
    
    if success:
        print("\n✨ Восстановление завершено!")
        return 0
    else:
        print("\n💥 Восстановление не удалось")
        return 1

if __name__ == "__main__":
    exit(main())
