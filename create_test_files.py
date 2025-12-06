#!/usr/bin/env python3
"""
Создание тестовых поврежденных PNG файлов
"""

import os
import random

def create_simple_png():
    """Создает простой PNG файл"""
    # Простой валидный PNG (1x1 красный пиксель)
    png_data = bytes.fromhex(
        '89504e470d0a1a0a'  # Сигнатура PNG
        '0000000d'          # Длина IHDR
        '49484452'          # IHDR
        '00000001'          # Ширина: 1
        '00000001'          # Высота: 1
        '0802000000'        # Настройки
        '00000000'          # CRC (упрощенно)
        '00000000'          # Длина IDAT
        '49444154'          # IDAT
        '00000000'          # CRC
        '00000000'          # Длина IEND
        '49454e44'          # IEND
        'ae426082'          # CRC IEND
    )
    return png_data

def create_test_files():
    """Создает набор тестовых файлов"""
    test_dir = "test_files"
    os.makedirs(test_dir, exist_ok=True)
    
    # Создаем нормальный PNG
    normal_png = create_simple_png()
    with open(os.path.join(test_dir, "normal.png"), "wb") as f:
        f.write(normal_png)
    print("✅ Создан normal.png")
    
    # 1. PNG с поврежденной сигнатурой
    damaged_sig = bytearray(normal_png)
    damaged_sig[0:8] = b'BADPNG!!'  # Повреждаем сигнатуру
    with open(os.path.join(test_dir, "bad_signature.png"), "wb") as f:
        f.write(damaged_sig)
    print("✅ Создан bad_signature.png")
    
    # 2. PNG без IEND чанка
    no_iend = normal_png[:-12]  # Удаляем IEND чанк
    with open(os.path.join(test_dir, "no_iend.png"), "wb") as f:
        f.write(no_iend)
    print("✅ Создан no_iend.png")
    
    # 3. Обрезанный PNG (50%)
    half_size = normal_png[:len(normal_png)//2]
    with open(os.path.join(test_dir, "half.png"), "wb") as f:
        f.write(half_size)
    print("✅ Создан half.png")
    
    # 4. PNG со случайными повреждениями
    random_damage = bytearray(normal_png)
    for i in range(10):  # 10 случайных повреждений
        pos = random.randint(0, len(random_damage)-1)
        random_damage[pos] = random.randint(0, 255)
    with open(os.path.join(test_dir, "random_damage.png"), "wb") as f:
        f.write(random_damage)
    print("✅ Создан random_damage.png")
    
    # 5. Пустой файл
    with open(os.path.join(test_dir, "empty.png"), "wb") as f:
        pass
    print("✅ Создан empty.png")
    
    # 6. Текстовый файл с расширением .png
    with open(os.path.join(test_dir, "text_as_png.png"), "w") as f:
        f.write("Это не PNG файл, а просто текст!\n" * 10)
    print("✅ Создан text_as_png.png")
    
    print(f"\n📁 Все тестовые файлы созданы в папке: {test_dir}")
    
    # Показываем размеры файлов
    print("\n📊 Размеры файлов:")
    for file in os.listdir(test_dir):
        size = os.path.getsize(os.path.join(test_dir, file))
        print(f"  {file}: {size} байт")

if __name__ == "__main__":
    create_test_files()
