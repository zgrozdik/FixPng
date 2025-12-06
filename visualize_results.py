#!/usr/bin/env python3
"""
Визуальная проверка восстановленных PNG файлов
"""

import os
import subprocess

def display_file_info():
    """Показывает информацию о файлах"""
    test_dir = "test_files"
    
    if not os.path.exists(test_dir):
        print(f"❌ Директория не найдена: {test_dir}")
        return
    
    print("📊 АНАЛИЗ ФАЙЛОВ В test_files/")
    print("="*60)
    
    files = sorted(os.listdir(test_dir))
    
    # Группируем файлы по типам
    original_files = []
    repaired_files = []
    test_files = []
    
    for f in files:
        if '_repaired' in f:
            repaired_files.append(f)
        elif '_test' in f:
            test_files.append(f)
        else:
            original_files.append(f)
    
    print("\n📋 ОРИГИНАЛЬНЫЕ ФАЙЛЫ:")
    for f in sorted(original_files):
        if f.endswith('.png'):
            size = os.path.getsize(os.path.join(test_dir, f))
            print(f"  📄 {f:30} {size:6} байт")
    
    print("\n🔧 ВОССТАНОВЛЕННЫЕ ФАЙЛЫ (_repaired):")
    for f in sorted(repaired_files):
        size = os.path.getsize(os.path.join(test_dir, f))
        original = f.replace('_repaired', '')
        orig_size = os.path.getsize(os.path.join(test_dir, original)) if os.path.exists(os.path.join(test_dir, original)) else 0
        diff = size - orig_size
        diff_sign = "+" if diff > 0 else ""
        print(f"  🔄 {f:30} {size:6} байт ({diff_sign}{diff})")
    
    print("\n🧪 ТЕСТОВЫЕ ФАЙЛЫ (_test):")
    for f in sorted(test_files):
        size = os.path.getsize(os.path.join(test_dir, f))
        print(f"  🧪 {f:30} {size:6} байт")
    
    # Статистика
    print(f"\n{'='*60}")
    print("📈 СТАТИСТИКА:")
    print(f"  Всего файлов: {len(files)}")
    print(f"  Оригинальных: {len(original_files)}")
    print(f"  Восстановленных: {len(repaired_files)}")
    print(f"  Тестовых: {len(test_files)}")
    
    # Проверяем валидность PNG
    print(f"\n{'='*60}")
    print("🔍 ПРОВЕРКА ВАЛИДНОСТИ PNG:")
    
    def check_png(filepath):
        """Быстрая проверка PNG"""
        try:
            with open(filepath, 'rb') as f:
                data = f.read(100)  # Читаем только начало
            
            if len(data) < 8:
                return False, "слишком короткий"
            
            # Проверяем сигнатуру
            if data[:8] != b'\x89PNG\r\n\x1a\n':
                return False, "неверная сигнатура"
            
            # Проверяем ключевые чанки
            has_ihdr = b'IHDR' in data
            has_iend = b'IEND' in data
            
            if has_ihdr and has_iend:
                return True, "валидный PNG"
            elif has_ihdr:
                return False, "нет IEND"
            else:
                return False, "нет IHDR"
                
        except Exception as e:
            return False, f"ошибка: {e}"
    
    print("\n  Оригинальные файлы:")
    for f in sorted(original_files):
        if f.endswith('.png'):
            filepath = os.path.join(test_dir, f)
            valid, msg = check_png(filepath)
            status = "✅" if valid else "❌"
            print(f"    {status} {f:25} - {msg}")
    
    print("\n  Восстановленные файлы:")
    for f in sorted(repaired_files):
        filepath = os.path.join(test_dir, f)
        valid, msg = check_png(filepath)
        status = "✅" if valid else "❌"
        print(f"    {status} {f:25} - {msg}")

def main():
    """Основная функция"""
    print("👁️  ВИЗУАЛЬНАЯ ПРОВЕРКА РЕЗУЛЬТАТОВ")
    print("="*60)
    
    display_file_info()
    
    # Дополнительно: показываем HEX дамп первых байт
    print(f"\n{'='*60}")
    print("🔬 HEX ДАМП ПЕРВЫХ 32 БАЙТ:")
    
    sample_files = [
        "test_files/normal.png",
        "test_files/bad_signature.png", 
        "test_files/bad_signature_repaired.png"
    ]
    
    for filepath in sample_files:
        if os.path.exists(filepath):
            print(f"\n📁 {os.path.basename(filepath)}:")
            try:
                with open(filepath, 'rb') as f:
                    data = f.read(32)
                
                hex_str = ' '.join(f'{b:02x}' for b in data)
                ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data)
                
                print(f"  HEX: {hex_str}")
                print(f"  ASC: {ascii_str}")
            except Exception as e:
                print(f"  ❌ Ошибка: {e}")

if __name__ == "__main__":
    main()
