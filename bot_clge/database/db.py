import aiosqlite
from typing import Optional, List, Dict, Any


class Database:
    def __init__(self, db_path: str = "college_bot.db"):
        self.db_path = db_path

    async def init_db(self):
        """Инициализация базы данных и создание таблиц"""
        async with aiosqlite.connect(self.db_path) as db:
            # Таблица пользователей
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    full_name TEXT,
                    role TEXT NOT NULL DEFAULT 'student',
                    group_id INTEGER,
                    FOREIGN KEY (group_id) REFERENCES groups(group_id)
                )
            """)

            # Таблица групп
            await db.execute("""
                CREATE TABLE IF NOT EXISTS groups (
                    group_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    group_name TEXT NOT NULL UNIQUE
                )
            """)

            # Таблица расписания
            await db.execute("""
                CREATE TABLE IF NOT EXISTS schedule (
                    schedule_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    group_id INTEGER NOT NULL,
                    day_of_week INTEGER NOT NULL,
                    lesson_number INTEGER NOT NULL,
                    subject TEXT NOT NULL,
                    teacher_id INTEGER NOT NULL,
                    FOREIGN KEY (group_id) REFERENCES groups(group_id),
                    FOREIGN KEY (teacher_id) REFERENCES users(user_id)
                )
            """)

            # Таблица отметок
            await db.execute("""
                CREATE TABLE IF NOT EXISTS grades (
                    grade_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER NOT NULL,
                    teacher_id INTEGER NOT NULL,
                    subject TEXT NOT NULL,
                    grade INTEGER NOT NULL,
                    date TEXT NOT NULL,
                    FOREIGN KEY (student_id) REFERENCES users(user_id),
                    FOREIGN KEY (teacher_id) REFERENCES users(user_id)
                )
            """)

            # Таблица сообщений
            await db.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    from_user_id INTEGER NOT NULL,
                    to_user_id INTEGER NOT NULL,
                    message_text TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (from_user_id) REFERENCES users(user_id),
                    FOREIGN KEY (to_user_id) REFERENCES users(user_id)
                )
            """)

            await db.commit()

    async def add_user(self, user_id: int, username: str, full_name: str, role: str = "student", group_id: Optional[int] = None):
        """Добавить пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO users (user_id, username, full_name, role, group_id)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, username, full_name, role, group_id))
            await db.commit()

    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получить информацию о пользователе"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def update_user_role(self, user_id: int, role: str):
        """Изменить роль пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("UPDATE users SET role = ? WHERE user_id = ?", (role, user_id))
            await db.commit()

    async def update_user_group(self, user_id: int, group_id: Optional[int]):
        """Изменить группу пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("UPDATE users SET group_id = ? WHERE user_id = ?", (group_id, user_id))
            await db.commit()

    async def create_group(self, group_name: str) -> int:
        """Создать группу"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("INSERT INTO groups (group_name) VALUES (?)", (group_name,))
            await db.commit()
            return cursor.lastrowid

    async def get_all_groups(self) -> List[Dict[str, Any]]:
        """Получить все группы"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM groups") as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def get_group_by_name(self, group_name: str) -> Optional[Dict[str, Any]]:
        """Получить группу по имени"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM groups WHERE group_name = ?", (group_name,)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def get_group_by_id(self, group_id: int) -> Optional[Dict[str, Any]]:
        """Получить группу по ID"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM groups WHERE group_id = ?", (group_id,)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def get_users_by_role(self, role: str) -> List[Dict[str, Any]]:
        """Получить всех пользователей с определенной ролью"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM users WHERE role = ?", (role,)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def get_users_by_group(self, group_id: int) -> List[Dict[str, Any]]:
        """Получить всех пользователей в группе"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM users WHERE group_id = ?", (group_id,)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def add_schedule(self, group_id: int, day_of_week: int, lesson_number: int, subject: str, teacher_id: int):
        """Добавить запись в расписание"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO schedule (group_id, day_of_week, lesson_number, subject, teacher_id)
                VALUES (?, ?, ?, ?, ?)
            """, (group_id, day_of_week, lesson_number, subject, teacher_id))
            await db.commit()

    async def get_schedule_by_group(self, group_id: int) -> List[Dict[str, Any]]:
        """Получить расписание для группы"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT s.*, u.full_name as teacher_name
                FROM schedule s
                LEFT JOIN users u ON s.teacher_id = u.user_id
                WHERE s.group_id = ?
                ORDER BY s.day_of_week, s.lesson_number
            """, (group_id,)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def add_grade(self, student_id: int, teacher_id: int, subject: str, grade: int, date: str):
        """Добавить отметку"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO grades (student_id, teacher_id, subject, grade, date)
                VALUES (?, ?, ?, ?, ?)
            """, (student_id, teacher_id, subject, grade, date))
            await db.commit()

    async def get_grades_by_student(self, student_id: int) -> List[Dict[str, Any]]:
        """Получить все отметки студента"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT g.*, u.full_name as teacher_name
                FROM grades g
                LEFT JOIN users u ON g.teacher_id = u.user_id
                WHERE g.student_id = ?
                ORDER BY g.date DESC
            """, (student_id,)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def get_students_by_teacher(self, teacher_id: int) -> List[Dict[str, Any]]:
        """Получить всех студентов учителя"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT DISTINCT u.*
                FROM users u
                INNER JOIN schedule s ON u.group_id = s.group_id
                WHERE s.teacher_id = ? AND u.role = 'student'
            """, (teacher_id,)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def add_message(self, from_user_id: int, to_user_id: int, message_text: str, timestamp: str):
        """Добавить сообщение"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO messages (from_user_id, to_user_id, message_text, timestamp)
                VALUES (?, ?, ?, ?)
            """, (from_user_id, to_user_id, message_text, timestamp))
            await db.commit()

    async def delete_user_from_group(self, user_id: int):
        """Удалить пользователя из группы"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("UPDATE users SET group_id = NULL WHERE user_id = ?", (user_id,))
            await db.commit()

    async def delete_group(self, group_id: int):
        """Удалить группу"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM groups WHERE group_id = ?", (group_id,))
            await db.commit()

