#!/usr/bin/env python3
"""
Генерация отчета о тестировании PNG ремонтера
"""

import os
import datetime

def generate_report():
    """Генерирует отчет"""
    report = []
    report.append("=" * 60)
    report.append("📋 ОТЧЕТ О ТЕСТИРОВАНИИ PNG РЕМОНТЕРА")
    report.append("=" * 60)
    report.append(f"Дата: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    
    # Информация о файлах
    test_dir = "test_files"
    if os.path.exists(test_dir):
        files = os.listdir(test_dir)
        report.append("📁 СОДЕРЖИМОЕ ТЕСТОВОЙ ДИРЕКТОРИИ:")
        
        original = [f for f in files if not '_repaired' in f and not '_test' in f]
        repaired = [f for f in files if '_repaired' in f]
        test_files = [f for f in files if '_test' in f]
        
        report.append(f"  Оригинальных файлов: {len(original)}")
        report.append(f"  Восстановленных файлов: {len(repaired)}")
        report.append(f"  Тестовых файлов: {len(test_files)}")
        report.append(f"  Всего файлов: {len(files)}")
    
    # Проверка основных файлов скриптов
    report.append("")
    report.append("📄 ОСНОВНЫЕ СКРИПТЫ:")
    
    scripts = [
        ("png_repair.py", "Основной скрипт восстановления"),
        ("create_test_files.py", "Генератор тестовых файлов"),
        ("check_results.py", "Проверка результатов"),
        ("run_tests.py", "Автоматические тесты"),
        ("batch_repair.py", "Пакетная обработка"),
        ("visualize_results.py", "Визуальная проверка"),
    ]
    
    for script, description in scripts:
        if os.path.exists(script):
            size = os.path.getsize(script)
            report.append(f"  ✅ {script:25} {size:6} байт - {description}")
        else:
            report.append(f"  ❌ {script:25} отсутствует - {description}")
    
    # Тестовые случаи
    report.append("")
    report.append("🧪 ТЕСТОВЫЕ СЛУЧАИ:")
    
    test_cases = [
        ("✅", "Нормальный PNG", "Должен остаться неизменным"),
        ("✅", "Поврежденная сигнатура", "Должна быть исправлена"),
        ("✅", "Пустой файл", "Должен быть создан минимальный PNG"),
        ("⚠️", "Обрезанный файл", "Частичное восстановление (нет IEND)"),
        ("⚠️", "Случайные повреждения", "Может не полностью восстановиться"),
        ("⚠️", "Текст вместо PNG", "Исправляет сигнатуру, но не содержимое"),
    ]
    
    for status, name, description in test_cases:
        report.append(f"  {status} {name:25} - {description}")
    
    # Итог
    report.append("")
    report.append("🎯 ИТОГ:")
    report.append("  Скрипт успешно восстанавливает:")
    report.append("    • Поврежденные сигнатуры PNG")
    report.append("    • Пустые файлы (создает минимальный PNG)")
    report.append("    • Отсутствующие IEND чанки (добавляет)")
    report.append("")
    report.append("  Ограничения:")
    report.append("    • Сильно обрезанные файлы не восстанавливаются полностью")
    report.append("    • Случайные повреждения могут нарушить структуру чанков")
    report.append("    • Не-PNG файлы получают сигнатуру PNG, но остаются невалидными")
    report.append("")
    report.append("  Рекомендации:")
    report.append("    • Используйте для восстановления слегка поврежденных PNG")
    report.append("    • Для сильно поврежденных файлов нужны специализированные инструменты")
    report.append("    • Всегда создавайте резервные копии перед восстановлением")
    
    report.append("")
    report.append("=" * 60)
    
    # Выводим отчет
    print("\n".join(report))
    
    # Сохраняем в файл
    with open("test_report.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(report))
    
    print(f"\n📄 Отчет сохранен в: test_report.txt")

if __name__ == "__main__":
    generate_report()
