from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import Database
from keyboards import get_main_menu, get_cancel_keyboard, get_users_keyboard
from utils import format_schedule, format_grades
from datetime import datetime

router = Router()


class StudentStates(StatesGroup):
    waiting_for_teacher = State()
    waiting_for_message_text = State()


@router.message(F.text == "📅 Расписание")
async def view_schedule_student(message: Message, db: Database):
    """Просмотр расписания (для студента)"""
    user = await db.get_user(message.from_user.id)
    if not user or user['role'] != 'student':
        await message.answer("❌ У вас нет доступа к этой функции.")
        return
    
    if not user.get('group_id'):
        await message.answer("❌ Вы не привязаны к группе. Обратитесь к администратору.")
        return
    
    schedule = await db.get_schedule_by_group(user['group_id'])
    
    if not schedule:
        await message.answer("📭 Расписание для вашей группы пока не добавлено.")
        return
    
    schedule_text = format_schedule(schedule)
    await message.answer(schedule_text)


@router.message(F.text == "📊 Мои отметки")
async def view_grades_student(message: Message, db: Database):
    """Просмотр отметок (для студента)"""
    user = await db.get_user(message.from_user.id)
    if not user or user['role'] != 'student':
        await message.answer("❌ У вас нет доступа к этой функции.")
        return
    
    grades = await db.get_grades_by_student(message.from_user.id)
    grades_text = format_grades(grades)
    await message.answer(grades_text)


@router.message(F.text == "📨 Написать учителю")
async def start_write_to_teacher(message: Message, state: FSMContext, db: Database):
    """Начать отправку сообщения учителю"""
    user = await db.get_user(message.from_user.id)
    if not user or user['role'] != 'student':
        await message.answer("❌ У вас нет доступа к этой функции.")
        return
    
    if not user.get('group_id'):
        await message.answer("❌ Вы не привязаны к группе.")
        return
    
    # Получаем учителей группы из расписания
    schedule = await db.get_schedule_by_group(user['group_id'])
    
    if not schedule:
        await message.answer("📭 В вашей группе пока нет учителей.")
        return
    
    # Собираем уникальных учителей
    teachers_dict = {}
    for item in schedule:
        teacher_id = item['teacher_id']
        if teacher_id not in teachers_dict:
            teachers_dict[teacher_id] = item.get('teacher_name', 'Учитель')
    
    # Формируем список учителей
    teachers = []
    for teacher_id, teacher_name in teachers_dict.items():
        teacher_user = await db.get_user(teacher_id)
        if teacher_user:
            teachers.append(teacher_user)
    
    if not teachers:
        await message.answer("📭 Учителей не найдено.")
        return
    
    await message.answer(
        "👨‍🏫 Выберите учителя:",
        reply_markup=get_users_keyboard(teachers, "message_teacher")
    )
    await state.set_state(StudentStates.waiting_for_teacher)


@router.callback_query(F.data.startswith("message_teacher_"), StudentStates.waiting_for_teacher)
async def select_teacher_for_message(callback: CallbackQuery, state: FSMContext):
    """Выбрать учителя для сообщения"""
    teacher_id = int(callback.data.split("_")[-1])
    await state.update_data(teacher_id=teacher_id)
    await callback.message.edit_text(
        "📨 Введите сообщение для учителя:",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(StudentStates.waiting_for_message_text)
    await callback.answer()


@router.message(StudentStates.waiting_for_message_text, F.text != "❌ Отмена")
async def send_message_to_teacher(message: Message, state: FSMContext, db: Database):
    """Отправить сообщение учителю"""
    message_text = message.text
    data = await state.get_data()
    teacher_id = data['teacher_id']
    student_id = message.from_user.id
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        # Сохраняем сообщение в БД
        await db.add_message(student_id, teacher_id, message_text, timestamp)
        
        # Отправляем учителю
        student = await db.get_user(student_id)
        student_name = student['full_name'] if student else "Студент"
        
        await message.bot.send_message(
            teacher_id,
            f"📨 Сообщение от студента {student_name}:\n\n{message_text}"
        )
        
        await message.answer(
            "✅ Сообщение успешно отправлено!",
            reply_markup=get_main_menu("student")
        )
    except Exception as e:
        await message.answer(f"❌ Ошибка при отправке сообщения: {e}")
    
    await state.clear()


@router.message(F.text == "❌ Отмена")
async def cancel_student_action(message: Message, state: FSMContext, db: Database):
    """Отменить действие"""
    user = await db.get_user(message.from_user.id)
    role = user['role'] if user else "student"
    await message.answer(
        "❌ Действие отменено.",
        reply_markup=get_main_menu(role)
    )
    await state.clear()

