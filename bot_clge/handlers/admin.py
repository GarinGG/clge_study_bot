from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import Database
from keyboards import (
    get_main_menu, get_cancel_keyboard, get_groups_keyboard,
    get_users_keyboard, get_action_keyboard
)

router = Router()


class AdminStates(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_group_name = State()
    waiting_for_teacher_username = State()
    waiting_for_student_username = State()
    waiting_for_broadcast_message = State()
    waiting_for_new_admin_username = State()
    selecting_group_for_user = State()


@router.message(F.text == "👥 Управление учителями")
async def manage_teachers(message: Message, db: Database):
    """Управление учителями"""
    user = await db.get_user(message.from_user.id)
    if not user or user['role'] != 'admin':
        await message.answer("❌ У вас нет доступа к этой функции.")
        return
    
    teachers = await db.get_users_by_role("teacher")
    if not teachers:
        await message.answer("📭 Учителей пока нет в системе.")
        return
    
    await message.answer(
        "👥 Выберите учителя:",
        reply_markup=get_users_keyboard(teachers, "teacher_action")
    )


@router.message(F.text == "👨‍🎓 Управление студентами")
async def manage_students(message: Message, db: Database):
    """Управление студентами"""
    user = await db.get_user(message.from_user.id)
    if not user or user['role'] != 'admin':
        await message.answer("❌ У вас нет доступа к этой функции.")
        return
    
    students = await db.get_users_by_role("student")
    if not students:
        await message.answer("📭 Студентов пока нет в системе.")
        return
    
    await message.answer(
        "👨‍🎓 Выберите студента:",
        reply_markup=get_users_keyboard(students, "student_action")
    )


@router.message(F.text == "📚 Управление группами")
async def manage_groups(message: Message, state: FSMContext):
    """Управление группами"""
    user = await db.get_user(message.from_user.id)
    if not user or user['role'] != 'admin':
        await message.answer("❌ У вас нет доступа к этой функции.")
        return
    
    await message.answer(
        "📚 Введите название новой группы:",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(AdminStates.waiting_for_group_name)


@router.message(AdminStates.waiting_for_group_name, F.text != "❌ Отмена")
async def create_group(message: Message, state: FSMContext, db: Database):
    """Создать группу"""
    group_name = message.text.strip()
    
    # Проверяем, существует ли уже такая группа
    existing_group = await db.get_group_by_name(group_name)
    if existing_group:
        await message.answer(f"❌ Группа '{group_name}' уже существует.")
        return
    
    try:
        await db.create_group(group_name)
        await message.answer(
            f"✅ Группа '{group_name}' успешно создана!",
            reply_markup=get_main_menu("admin")
        )
    except Exception as e:
        await message.answer(f"❌ Ошибка при создании группы: {e}")
    
    await state.clear()


@router.message(F.text == "📢 Рассылка")
async def start_broadcast(message: Message, state: FSMContext, db: Database):
    """Начать рассылку"""
    user = await db.get_user(message.from_user.id)
    if not user or user['role'] != 'admin':
        await message.answer("❌ У вас нет доступа к этой функции.")
        return
    
    await message.answer(
        "📢 Введите сообщение для рассылки:",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(AdminStates.waiting_for_broadcast_message)


@router.message(AdminStates.waiting_for_broadcast_message, F.text != "❌ Отмена")
async def send_broadcast(message: Message, state: FSMContext, db: Database):
    """Отправить рассылку"""
    broadcast_text = message.text
    
    # Получаем всех пользователей
    all_users = []
    for role in ["admin", "teacher", "student"]:
        users = await db.get_users_by_role(role)
        all_users.extend(users)
    
    sent = 0
    failed = 0
    
    for user in all_users:
        try:
            await message.bot.send_message(user['user_id'], f"📢 Рассылка от администратора:\n\n{broadcast_text}")
            sent += 1
        except Exception:
            failed += 1
    
    await message.answer(
        f"✅ Рассылка завершена!\nОтправлено: {sent}\nНе удалось отправить: {failed}",
        reply_markup=get_main_menu("admin")
    )
    await state.clear()


@router.message(F.text == "👤 Добавить администратора")
async def add_admin_start(message: Message, state: FSMContext, db: Database):
    """Начать процесс добавления администратора"""
    user = await db.get_user(message.from_user.id)
    if not user or user['role'] != 'admin':
        await message.answer("❌ У вас нет доступа к этой функции.")
        return
    
    await message.answer(
        "👤 Введите username пользователя для назначения администратором (без @):",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(AdminStates.waiting_for_new_admin_username)


@router.message(AdminStates.waiting_for_new_admin_username, F.text != "❌ Отмена")
async def add_admin_process(message: Message, state: FSMContext, db: Database):
    """Обработать добавление администратора"""
    username = message.text.strip().replace("@", "")
    
    # Находим пользователя по username - проверяем всех пользователей
    all_users = []
    for role in ["student", "teacher", "admin"]:
        users = await db.get_users_by_role(role)
        all_users.extend(users)
    
    target_user = None
    for user in all_users:
        if user.get('username') == username:
            target_user = user
            break
    
    if not target_user:
        await message.answer(f"❌ Пользователь с username '{username}' не найден. Убедитесь, что пользователь использовал /start в боте.")
        return
    
    if target_user['role'] == 'admin':
        await message.answer(f"ℹ️ Пользователь {target_user['full_name']} уже является администратором.")
        await state.clear()
        return
    
    # Обновляем роль
    await db.update_user_role(target_user['user_id'], "admin")
    
    await message.answer(
        f"✅ Пользователь {target_user['full_name']} теперь администратор!",
        reply_markup=get_main_menu("admin")
    )
    
    # Уведомляем нового администратора
    try:
        await message.bot.send_message(
            target_user['user_id'],
            "🎉 Вас назначили администратором! Используйте /start для обновления меню."
        )
    except Exception:
        pass
    
    await state.clear()


@router.callback_query(F.data.startswith("teacher_action_"))
async def teacher_action(callback: CallbackQuery, state: FSMContext):
    """Обработка действий с учителем"""
    teacher_id = int(callback.data.split("_")[-1])
    await state.update_data(target_user_id=teacher_id)
    
    await callback.message.edit_text(
        "Выберите действие:",
        reply_markup=get_action_keyboard(is_teacher=True)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("student_action_"))
async def student_action(callback: CallbackQuery, state: FSMContext):
    """Обработка действий со студентом"""
    student_id = int(callback.data.split("_")[-1])
    await state.update_data(target_user_id=student_id)
    
    await callback.message.edit_text(
        "Выберите действие:",
        reply_markup=get_action_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "add_to_group")
async def add_to_group_start(callback: CallbackQuery, db: Database, state: FSMContext):
    """Начать добавление пользователя в группу"""
    groups = await db.get_all_groups()
    if not groups:
        await callback.answer("Нет доступных групп.", show_alert=True)
        return
    
    await callback.message.edit_text(
        "Выберите группу:",
        reply_markup=get_groups_keyboard(groups, "group_add")
    )
    await callback.answer()


@router.callback_query(F.data == "remove_from_group")
async def remove_from_group_process(callback: CallbackQuery, db: Database, state: FSMContext):
    """Удалить пользователя из группы"""
    data = await state.get_data()
    target_user_id = data.get('target_user_id')
    
    if not target_user_id:
        await callback.answer("Ошибка: не выбран пользователь.", show_alert=True)
        return
    
    try:
        await db.delete_user_from_group(target_user_id)
        user = await db.get_user(target_user_id)
        user_name = user['full_name'] if user else "Пользователь"
        await callback.message.edit_text(f"✅ Пользователь {user_name} удален из группы!")
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка: {e}")
    
    await state.clear()
    await callback.answer()


@router.callback_query(F.data.startswith("group_add_"))
async def add_to_group_process(callback: CallbackQuery, db: Database, state: FSMContext):
    """Добавить пользователя в группу"""
    group_id = int(callback.data.split("_")[-1])
    data = await state.get_data()
    target_user_id = data.get('target_user_id')
    
    if not target_user_id:
        await callback.answer("Ошибка: не выбран пользователь.", show_alert=True)
        return
    
    try:
        await db.update_user_group(target_user_id, group_id)
        user = await db.get_user(target_user_id)
        group = await db.get_group_by_id(group_id)
        group_name = group['group_name'] if group else "Группа"
        user_name = user['full_name'] if user else "Пользователь"
        await callback.message.edit_text(f"✅ Пользователь {user_name} добавлен в группу {group_name}!")
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка: {e}")
    
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "set_teacher_role")
async def set_teacher_role(callback: CallbackQuery, db: Database, state: FSMContext):
    """Назначить пользователя учителем"""
    data = await state.get_data()
    target_user_id = data.get('target_user_id')
    
    if not target_user_id:
        await callback.answer("Ошибка: не выбран пользователь.", show_alert=True)
        return
    
    try:
        await db.update_user_role(target_user_id, "teacher")
        user = await db.get_user(target_user_id)
        user_name = user['full_name'] if user else "Пользователь"
        await callback.message.edit_text(f"✅ Пользователь {user_name} теперь учитель!")
        
        # Уведомляем пользователя
        try:
            await callback.message.bot.send_message(
                target_user_id,
                "🎉 Вас назначили учителем! Используйте /start для обновления меню."
            )
        except Exception:
            pass
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка: {e}")
    
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "set_student_role")
async def set_student_role(callback: CallbackQuery, db: Database, state: FSMContext):
    """Назначить пользователя студентом"""
    data = await state.get_data()
    target_user_id = data.get('target_user_id')
    
    if not target_user_id:
        await callback.answer("Ошибка: не выбран пользователь.", show_alert=True)
        return
    
    try:
        await db.update_user_role(target_user_id, "student")
        user = await db.get_user(target_user_id)
        user_name = user['full_name'] if user else "Пользователь"
        await callback.message.edit_text(f"✅ Пользователь {user_name} теперь студент!")
        
        # Уведомляем пользователя
        try:
            await callback.message.bot.send_message(
                target_user_id,
                "ℹ️ Ваша роль изменена на студента. Используйте /start для обновления меню."
            )
        except Exception:
            pass
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка: {e}")
    
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "cancel")
async def cancel_action(callback: CallbackQuery):
    """Отменить действие"""
    await callback.message.delete()
    await callback.answer()


@router.message(F.text == "❌ Отмена")
async def cancel_text(message: Message, state: FSMContext, db: Database):
    """Отменить действие (текстовое)"""
    user = await db.get_user(message.from_user.id)
    role = user['role'] if user else "student"
    await message.answer(
        "❌ Действие отменено.",
        reply_markup=get_main_menu(role)
    )
    await state.clear()

