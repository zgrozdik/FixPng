#!/usr/bin/env python3
"""
Пакетное восстановление PNG файлов
"""

import os
import sys
import glob
import subprocess

def batch_repair(directory, pattern="*.png", recursive=False):
    """Восстанавливает все PNG файлы в директории"""
    if not os.path.exists(directory):
        print(f"❌ Директория не найдена: {directory}")
        return
    
    print(f"🔧 Пакетное восстановление PNG в: {directory}")
    print(f"📁 Шаблон поиска: {pattern}")
    print("="*50)
    
    # Находим все файлы
    if recursive:
        search_pattern = os.path.join(directory, "**", pattern)
    else:
        search_pattern = os.path.join(directory, pattern)
    
    files = glob.glob(search_pattern, recursive=recursive)
    
    if not files:
        print(f"⚠️  Файлы не найдены по шаблону: {search_pattern}")
        return
    
    print(f"📊 Найдено файлов: {len(files)}")
    
    success_count = 0
    fail_count = 0
    
    for input_file in files:
        print(f"\n{'─'*40}")
        print(f"📂 Обработка: {os.path.basename(input_file)}")
        
        # Запускаем скрипт восстановления
        output_file = input_file.replace('.png', '_batch_repaired.png')
        cmd = ['python', 'png_repair.py', input_file, output_file]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                success_count += 1
                print("✅ Успешно восстановлен")
                
                # Проверяем результат
                if os.path.exists(output_file):
                    size = os.path.getsize(output_file)
                    print(f"   📊 Размер: {size} байт")
            else:
                fail_count += 1
                print("❌ Ошибка восстановления")
                if result.stderr:
                    print(f"   💥 {result.stderr[:100]}")
                    
        except Exception as e:
            fail_count += 1
            print(f"❌ Исключение: {e}")
    
    # Итоги
    print(f"\n{'='*50}")
    print("📊 ИТОГИ ПАКЕТНОЙ ОБРАБОТКИ")
    print("="*50)
    print(f"✅ Успешно: {success_count}")
    print(f"❌ С ошибками: {fail_count}")
    print(f"📁 Всего обработано: {len(files)}")
    
    if fail_count == 0:
        print("\n🎉 Все файлы успешно восстановлены!")
    else:
        print(f"\n⚠️  {fail_count} файлов не удалось восстановить")

def main():
    """Основная функция"""
    if len(sys.argv) < 2:
        print("Использование: python batch_repair.py <директория> [опции]")
        print("\nОпции:")
        print("  -p, --pattern PATTERN   Шаблон поиска (по умолчанию: *.png)")
        print("  -r, --recursive         Рекурсивный поиск в поддиректориях")
        print("\nПримеры:")
        print("  python batch_repair.py test_files")
        print("  python batch_repair.py . --pattern *.png")
        print("  python batch_repair.py ./images --recursive")
        sys.exit(1)
    
    directory = sys.argv[1]
    
    # Парсим аргументы
    pattern = "*.png"
    recursive = False
    
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] in ['-p', '--pattern']:
            if i + 1 < len(sys.argv):
                pattern = sys.argv[i + 1]
                i += 2
            else:
                print("❌ Ошибка: не указан шаблон после -p/--pattern")
                sys.exit(1)
        elif sys.argv[i] in ['-r', '--recursive']:
            recursive = True
            i += 1
        else:
            print(f"❌ Неизвестный аргумент: {sys.argv[i]}")
            sys.exit(1)
    
    batch_repair(directory, pattern, recursive)

if __name__ == "__main__":
    main()
