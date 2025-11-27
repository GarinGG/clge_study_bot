from typing import Dict, Any


def get_day_number(day_name: str) -> int:
    """Преобразовать название дня недели в номер"""
    days = {
        "понедельник": 1,
        "вторник": 2,
        "среда": 3,
        "четверг": 4,
        "пятница": 5,
        "суббота": 6
    }
    return days.get(day_name.lower(), 0)


def get_day_name(day_number: int) -> str:
    """Преобразовать номер дня недели в название"""
    days = {
        1: "Понедельник",
        2: "Вторник",
        3: "Среда",
        4: "Четверг",
        5: "Пятница",
        6: "Суббота"
    }
    return days.get(day_number, "Неизвестно")


def format_schedule(schedule: list) -> str:
    """Форматировать расписание для вывода"""
    if not schedule:
        return "Расписание пока не добавлено."
    
    result = []
    current_day = None
    
    for item in schedule:
        day = get_day_name(item['day_of_week'])
        if day != current_day:
            if current_day is not None:
                result.append("")
            result.append(f"📅 {day}:")
            current_day = day
        
        result.append(
            f"{item['lesson_number']}. {item['subject']} - {item.get('teacher_name', 'Неизвестно')}"
        )
    
    return "\n".join(result)


def format_grades(grades: list) -> str:
    """Форматировать отметки для вывода"""
    if not grades:
        return "У вас пока нет отметок."
    
    result = ["📊 Ваши отметки:\n"]
    
    # Группируем по предметам
    subjects = {}
    for grade in grades:
        subject = grade['subject']
        if subject not in subjects:
            subjects[subject] = []
        subjects[subject].append(grade)
    
    for subject, subject_grades in subjects.items():
        result.append(f"📚 {subject}:")
        grades_list = [str(g['grade']) for g in subject_grades]
        avg = sum([g['grade'] for g in subject_grades]) / len(subject_grades)
        result.append(f"   Оценки: {', '.join(grades_list)}")
        result.append(f"   Средний балл: {avg:.2f}")
        result.append("")
    
    return "\n".join(result)

