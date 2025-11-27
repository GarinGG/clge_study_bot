from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder


def get_main_menu(role: str) -> ReplyKeyboardMarkup:
    """Главное меню в зависимости от роли"""
    builder = ReplyKeyboardBuilder()

    if role == "admin":
        builder.add(KeyboardButton(text="👥 Управление учителями"))
        builder.add(KeyboardButton(text="👨‍🎓 Управление студентами"))
        builder.add(KeyboardButton(text="📚 Управление группами"))
        builder.add(KeyboardButton(text="📢 Рассылка"))
        builder.add(KeyboardButton(text="👤 Добавить администратора"))
    elif role == "teacher":
        builder.add(KeyboardButton(text="📝 Поставить отметку"))
        builder.add(KeyboardButton(text="📅 Добавить расписание"))
        builder.add(KeyboardButton(text="📨 Отправить сообщение студенту"))
        builder.add(KeyboardButton(text="📊 Посмотреть расписание"))
    elif role == "student":
        builder.add(KeyboardButton(text="📅 Расписание"))
        builder.add(KeyboardButton(text="📊 Мои отметки"))
        builder.add(KeyboardButton(text="📨 Написать учителю"))

    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура с кнопкой отмены"""
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="❌ Отмена"))
    return builder.as_markup(resize_keyboard=True)


def get_groups_keyboard(groups: list, prefix: str = "group") -> InlineKeyboardMarkup:
    """Клавиатура с группами"""
    builder = InlineKeyboardBuilder()
    for group in groups:
        builder.add(InlineKeyboardButton(
            text=group['group_name'],
            callback_data=f"{prefix}_{group['group_id']}"
        ))
    builder.add(InlineKeyboardButton(text="❌ Отмена", callback_data="cancel"))
    builder.adjust(1)
    return builder.as_markup()


def get_users_keyboard(users: list, action: str) -> InlineKeyboardMarkup:
    """Клавиатура с пользователями"""
    builder = InlineKeyboardBuilder()
    for user in users:
        name = user.get('full_name', f"@{user.get('username', 'Unknown')}")
        builder.add(InlineKeyboardButton(
            text=name,
            callback_data=f"{action}_{user['user_id']}"
        ))
    builder.add(InlineKeyboardButton(text="❌ Отмена", callback_data="cancel"))
    builder.adjust(1)
    return builder.as_markup()


def get_days_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура с днями недели"""
    builder = ReplyKeyboardBuilder()
    days = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота"]
    for day in days:
        builder.add(KeyboardButton(text=day))
    builder.add(KeyboardButton(text="❌ Отмена"))
    builder.adjust(2)
    return builder.as_markup()


def get_lesson_numbers_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура с номерами уроков"""
    builder = ReplyKeyboardBuilder()
    for i in range(1, 9):
        builder.add(KeyboardButton(text=str(i)))
    builder.add(KeyboardButton(text="❌ Отмена"))
    builder.adjust(4)
    return builder.as_markup()


def get_grades_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура с оценками"""
    builder = ReplyKeyboardBuilder()
    grades = ["2", "3", "4", "5"]
    for grade in grades:
        builder.add(KeyboardButton(text=grade))
    builder.add(KeyboardButton(text="❌ Отмена"))
    builder.adjust(2)
    return builder.as_markup()


def get_action_keyboard(is_teacher: bool = False) -> InlineKeyboardMarkup:
    """Клавиатура действий для администратора"""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="➕ Добавить в группу", callback_data="add_to_group"))
    builder.add(InlineKeyboardButton(text="➖ Удалить из группы", callback_data="remove_from_group"))
    if not is_teacher:
        builder.add(InlineKeyboardButton(text="👨‍🏫 Назначить учителем", callback_data="set_teacher_role"))
    else:
        builder.add(InlineKeyboardButton(text="👨‍🎓 Назначить студентом", callback_data="set_student_role"))
    builder.add(InlineKeyboardButton(text="❌ Отмена", callback_data="cancel"))
    builder.adjust(1)
    return builder.as_markup()

