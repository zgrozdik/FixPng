#!/usr/bin/env python3
"""
Проверка восстановленных файлов
"""

import os
import binascii

def check_file(filepath):
    """Проверяет один файл"""
    filename = os.path.basename(filepath)
    
    try:
        size = os.path.getsize(filepath)
        print(f"\n📁 {filename} ({size} байт):")
        
        if size == 0:
            print("  ❌ Файл пуст")
            return False
        
        with open(filepath, 'rb') as f:
            data = f.read()
        
        # Проверяем сигнатуру PNG
        if len(data) >= 8:
            signature = data[:8]
            if signature == b'\x89PNG\r\n\x1a\n':
                print("  ✅ Сигнатура PNG: OK")
            else:
                print(f"  ❌ Не PNG сигнатура: {signature.hex()}")
        else:
            print("  ❌ Файл слишком короткий")
            return False
        
        # Проверяем ключевые чанки
        checks = [
            ("IHDR", b'IHDR'),
            ("IDAT", b'IDAT'),
            ("IEND", b'IEND')
        ]
        
        for name, marker in checks:
            if marker in data:
                print(f"  ✅ {name} чанк: найден")
            else:
                print(f"  ⚠️  {name} чанк: не найден")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Ошибка: {e}")
        return False

def check_all_files():
    """Проверяет все файлы в тестовой директории"""
    test_dir = "test_files"
    
    if not os.path.exists(test_dir):
        print(f"❌ Директория {test_dir} не найдена!")
        return
    
    print("🔍 Проверка всех файлов:")
    print("=" * 50)
    
    all_files = os.listdir(test_dir)
    
    # Проверяем оригинальные файлы
    print("\n📋 ОРИГИНАЛЬНЫЕ ФАЙЛЫ:")
    for file in sorted(all_files):
        if not file.startswith('repaired_'):
            check_file(os.path.join(test_dir, file))
    
    # Проверяем восстановленные файлы
    print("\n📋 ВОССТАНОВЛЕННЫЕ ФАЙЛЫ:")
    repaired_files = [f for f in all_files if f.startswith('repaired_')]
    
    if repaired_files:
        for file in sorted(repaired_files):
            check_file(os.path.join(test_dir, file))
    else:
        print("  (пока нет восстановленных файлов)")
        print("  Запустите сначала: python png_repair.py test_files/*.png")

if __name__ == "__main__":
    check_all_files()
