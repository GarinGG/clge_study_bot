from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import Database
from keyboards import (
    get_main_menu, get_cancel_keyboard, get_groups_keyboard,
    get_users_keyboard, get_days_keyboard, get_lesson_numbers_keyboard
)
from utils import get_day_number, format_schedule
from datetime import datetime

router = Router()


class TeacherStates(StatesGroup):
    waiting_for_student = State()
    waiting_for_subject = State()
    waiting_for_grade = State()
    waiting_for_group_schedule = State()
    waiting_for_day = State()
    waiting_for_lesson_number = State()
    waiting_for_subject_name = State()
    waiting_for_student_message = State()
    waiting_for_message_text = State()


@router.message(F.text == "📝 Поставить отметку")
async def start_add_grade(message: Message, state: FSMContext, db: Database):
    """Начать процесс выставления отметки"""
    user = await db.get_user(message.from_user.id)
    if not user or user['role'] != 'teacher':
        await message.answer("❌ У вас нет доступа к этой функции.")
        return
    
    # Получаем всех студентов учителя
    students = await db.get_students_by_teacher(message.from_user.id)
    if not students:
        await message.answer("📭 У вас пока нет студентов.")
        return
    
    await message.answer(
        "👨‍🎓 Выберите студента:",
        reply_markup=get_users_keyboard(students, "grade_student")
    )
    await state.set_state(TeacherStates.waiting_for_student)


@router.callback_query(F.data.startswith("grade_student_"), TeacherStates.waiting_for_student)
async def select_student_for_grade(callback: CallbackQuery, state: FSMContext):
    """Выбрать студента для оценки"""
    student_id = int(callback.data.split("_")[-1])
    await state.update_data(student_id=student_id)
    await callback.message.edit_text("📚 Введите название предмета:")
    await state.set_state(TeacherStates.waiting_for_subject)
    await callback.answer()


@router.message(TeacherStates.waiting_for_subject, F.text != "❌ Отмена")
async def get_subject_for_grade(message: Message, state: FSMContext):
    """Получить предмет для оценки"""
    subject = message.text.strip()
    await state.update_data(subject=subject)
    await message.answer(
        "📝 Выберите оценку:",
        reply_markup=get_grades_keyboard()
    )
    await state.set_state(TeacherStates.waiting_for_grade)


@router.message(TeacherStates.waiting_for_grade, F.text != "❌ Отмена")
async def add_grade(message: Message, state: FSMContext, db: Database):
    """Добавить оценку"""
    try:
        grade = int(message.text.strip())
        if grade not in [2, 3, 4, 5]:
            await message.answer("❌ Оценка должна быть от 2 до 5.")
            return
        
        data = await state.get_data()
        student_id = data['student_id']
        subject = data['subject']
        teacher_id = message.from_user.id
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        await db.add_grade(student_id, teacher_id, subject, grade, date)
        
        student = await db.get_user(student_id)
        student_name = student['full_name'] if student else "Студент"
        
        await message.answer(
            f"✅ Оценка {grade} по предмету '{subject}' поставлена студенту {student_name}!",
            reply_markup=get_main_menu("teacher")
        )
        
        # Уведомляем студента
        try:
            await message.bot.send_message(
                student_id,
                f"📊 Вам поставлена оценка {grade} по предмету '{subject}'."
            )
        except Exception:
            pass
        
    except ValueError:
        await message.answer("❌ Оценка должна быть числом от 2 до 5.")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
    
    await state.clear()


@router.message(F.text == "📅 Добавить расписание")
async def start_add_schedule(message: Message, state: FSMContext, db: Database):
    """Начать добавление расписания"""
    user = await db.get_user(message.from_user.id)
    if not user or user['role'] != 'teacher':
        await message.answer("❌ У вас нет доступа к этой функции.")
        return
    
    groups = await db.get_all_groups()
    if not groups:
        await message.answer("📭 Групп пока нет. Обратитесь к администратору.")
        return
    
    await message.answer(
        "📚 Выберите группу:",
        reply_markup=get_groups_keyboard(groups, "schedule_group")
    )
    await state.set_state(TeacherStates.waiting_for_group_schedule)


@router.callback_query(F.data.startswith("schedule_group_"), TeacherStates.waiting_for_group_schedule)
async def select_group_for_schedule(callback: CallbackQuery, state: FSMContext):
    """Выбрать группу для расписания"""
    group_id = int(callback.data.split("_")[-1])
    await state.update_data(group_id=group_id)
    await callback.message.edit_text(
        "📅 Выберите день недели:",
        reply_markup=get_days_keyboard()
    )
    await state.set_state(TeacherStates.waiting_for_day)
    await callback.answer()


@router.message(TeacherStates.waiting_for_day, F.text != "❌ Отмена")
async def get_day_for_schedule(message: Message, state: FSMContext):
    """Получить день недели для расписания"""
    day_name = message.text.strip()
    day_number = get_day_number(day_name.lower())
    
    if day_number == 0:
        await message.answer("❌ Неверный день недели. Выберите из предложенных.")
        return
    
    await state.update_data(day_of_week=day_number)
    await message.answer(
        "🔢 Выберите номер урока:",
        reply_markup=get_lesson_numbers_keyboard()
    )
    await state.set_state(TeacherStates.waiting_for_lesson_number)


@router.message(TeacherStates.waiting_for_lesson_number, F.text != "❌ Отмена")
async def get_lesson_number_for_schedule(message: Message, state: FSMContext):
    """Получить номер урока для расписания"""
    try:
        lesson_number = int(message.text.strip())
        if lesson_number < 1 or lesson_number > 8:
            await message.answer("❌ Номер урока должен быть от 1 до 8.")
            return
        
        await state.update_data(lesson_number=lesson_number)
        await message.answer(
            "📚 Введите название предмета:",
            reply_markup=get_cancel_keyboard()
        )
        await state.set_state(TeacherStates.waiting_for_subject_name)
    except ValueError:
        await message.answer("❌ Номер урока должен быть числом.")


@router.message(TeacherStates.waiting_for_subject_name, F.text != "❌ Отмена")
async def add_schedule_item(message: Message, state: FSMContext, db: Database):
    """Добавить запись в расписание"""
    subject = message.text.strip()
    data = await state.get_data()
    
    group_id = data['group_id']
    day_of_week = data['day_of_week']
    lesson_number = data['lesson_number']
    teacher_id = message.from_user.id
    
    try:
        await db.add_schedule(group_id, day_of_week, lesson_number, subject, teacher_id)
        
        groups = await db.get_all_groups()
        group_name = next((g['group_name'] for g in groups if g['group_id'] == group_id), "Группа")
        
        await message.answer(
            f"✅ Расписание успешно добавлено для группы {group_name}!",
            reply_markup=get_main_menu("teacher")
        )
    except Exception as e:
        await message.answer(f"❌ Ошибка при добавлении расписания: {e}")
    
    await state.clear()


@router.message(F.text == "📊 Посмотреть расписание")
async def view_schedule_teacher(message: Message, db: Database):
    """Просмотр расписания (для учителя)"""
    user = await db.get_user(message.from_user.id)
    if not user or user['role'] != 'teacher':
        await message.answer("❌ У вас нет доступа к этой функции.")
        return
    
    groups = await db.get_all_groups()
    if not groups:
        await message.answer("📭 Групп пока нет.")
        return
    
    await message.answer(
        "📚 Выберите группу для просмотра расписания:",
        reply_markup=get_groups_keyboard(groups, "view_schedule_group")
    )


@router.callback_query(F.data.startswith("view_schedule_group_"))
async def show_schedule_for_group(callback: CallbackQuery, db: Database):
    """Показать расписание группы"""
    group_id = int(callback.data.split("_")[-1])
    schedule = await db.get_schedule_by_group(group_id)
    
    if not schedule:
        await callback.answer("Расписание для этой группы пока не добавлено.", show_alert=True)
        return
    
    group = await db.get_group_by_id(group_id)
    group_name = group['group_name'] if group else "Группа"
    
    schedule_text = f"📅 Расписание группы {group_name}:\n\n{format_schedule(schedule)}"
    await callback.message.edit_text(schedule_text)
    await callback.answer()


@router.message(F.text == "📨 Отправить сообщение студенту")
async def start_send_message_to_student(message: Message, state: FSMContext, db: Database):
    """Начать отправку сообщения студенту"""
    user = await db.get_user(message.from_user.id)
    if not user or user['role'] != 'teacher':
        await message.answer("❌ У вас нет доступа к этой функции.")
        return
    
    students = await db.get_students_by_teacher(message.from_user.id)
    if not students:
        await message.answer("📭 У вас пока нет студентов.")
        return
    
    await message.answer(
        "👨‍🎓 Выберите студента:",
        reply_markup=get_users_keyboard(students, "message_student")
    )
    await state.set_state(TeacherStates.waiting_for_student_message)


@router.callback_query(F.data.startswith("message_student_"), TeacherStates.waiting_for_student_message)
async def select_student_for_message(callback: CallbackQuery, state: FSMContext):
    """Выбрать студента для сообщения"""
    student_id = int(callback.data.split("_")[-1])
    await state.update_data(student_id=student_id)
    await callback.message.edit_text(
        "📨 Введите сообщение для студента:",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(TeacherStates.waiting_for_message_text)
    await callback.answer()


@router.message(TeacherStates.waiting_for_message_text, F.text != "❌ Отмена")
async def send_message_to_student(message: Message, state: FSMContext, db: Database):
    """Отправить сообщение студенту"""
    message_text = message.text
    data = await state.get_data()
    student_id = data['student_id']
    teacher_id = message.from_user.id
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        # Сохраняем сообщение в БД
        await db.add_message(teacher_id, student_id, message_text, timestamp)
        
        # Отправляем студенту
        teacher = await db.get_user(teacher_id)
        teacher_name = teacher['full_name'] if teacher else "Учитель"
        
        await message.bot.send_message(
            student_id,
            f"📨 Сообщение от {teacher_name}:\n\n{message_text}"
        )
        
        await message.answer(
            "✅ Сообщение успешно отправлено!",
            reply_markup=get_main_menu("teacher")
        )
    except Exception as e:
        await message.answer(f"❌ Ошибка при отправке сообщения: {e}")
    
    await state.clear()


@router.message(F.text == "❌ Отмена")
async def cancel_teacher_action(message: Message, state: FSMContext, db: Database):
    """Отменить действие"""
    user = await db.get_user(message.from_user.id)
    role = user['role'] if user else "teacher"
    await message.answer(
        "❌ Действие отменено.",
        reply_markup=get_main_menu(role)
    )
    await state.clear()

