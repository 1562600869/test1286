import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'science_center.db')

COURSE_TYPES = ['化学', '物理', '生物', '编程', '天文']
AGE_GROUPS = ['3-6岁', '6-9岁', '9-12岁', '亲子通用']
COURSE_STATUSES = ['开放报名', '已满', '已结束']


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            course_type TEXT NOT NULL,
            age_group TEXT NOT NULL,
            fee INTEGER NOT NULL,
            max_students INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT '开放报名',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS families (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            parent_name TEXT NOT NULL,
            parent_phone TEXT NOT NULL,
            child_name TEXT NOT NULL,
            child_age INTEGER NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS registrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER NOT NULL,
            family_id INTEGER NOT NULL,
            registered_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (course_id) REFERENCES courses (id),
            FOREIGN KEY (family_id) REFERENCES families (id),
            UNIQUE (course_id, family_id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            registration_id INTEGER NOT NULL,
            course_id INTEGER NOT NULL,
            family_id INTEGER NOT NULL,
            attendance_date TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (registration_id) REFERENCES registrations (id),
            FOREIGN KEY (course_id) REFERENCES courses (id),
            FOREIGN KEY (family_id) REFERENCES families (id),
            UNIQUE (course_id, family_id, attendance_date)
        )
    ''')

    conn.commit()
    conn.close()


def list_courses():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT c.*, 
               (SELECT COUNT(*) FROM registrations r WHERE r.course_id = c.id) as registered_count
        FROM courses c
        ORDER BY c.id DESC
    ''')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_course(course_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT c.*, 
               (SELECT COUNT(*) FROM registrations r WHERE r.course_id = c.id) as registered_count
        FROM courses c
        WHERE c.id = ?
    ''', (course_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def add_course(name, course_type, age_group, fee, max_students, status='开放报名'):
    if course_type not in COURSE_TYPES:
        raise ValueError('无效的课程类型')
    if age_group not in AGE_GROUPS:
        raise ValueError('无效的适龄分组')
    if not isinstance(fee, int) or fee < 0:
        raise ValueError('费用必须是非负整数分')
    if not isinstance(max_students, int) or max_students <= 0:
        raise ValueError('最大人数必须是正整数')
    if status not in COURSE_STATUSES:
        raise ValueError('无效的课程状态')

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO courses (name, course_type, age_group, fee, max_students, status) VALUES (?, ?, ?, ?, ?, ?)',
        (name, course_type, age_group, fee, max_students, status)
    )
    conn.commit()
    course_id = cursor.lastrowid
    conn.close()
    return get_course(course_id)


def update_course(course_id, name, course_type, age_group, fee, max_students, status):
    if course_type not in COURSE_TYPES:
        raise ValueError('无效的课程类型')
    if age_group not in AGE_GROUPS:
        raise ValueError('无效的适龄分组')
    if not isinstance(fee, int) or fee < 0:
        raise ValueError('费用必须是非负整数分')
    if not isinstance(max_students, int) or max_students <= 0:
        raise ValueError('最大人数必须是正整数')
    if status not in COURSE_STATUSES:
        raise ValueError('无效的课程状态')

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        'UPDATE courses SET name=?, course_type=?, age_group=?, fee=?, max_students=?, status=? WHERE id=?',
        (name, course_type, age_group, fee, max_students, status, course_id)
    )
    conn.commit()
    conn.close()
    return get_course(course_id)


def delete_course(course_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM attendances WHERE course_id = ?', (course_id,))
    cursor.execute('DELETE FROM registrations WHERE course_id = ?', (course_id,))
    cursor.execute('DELETE FROM courses WHERE id = ?', (course_id,))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0


def list_families():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM families ORDER BY id DESC')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_family(family_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM families WHERE id = ?', (family_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def add_family(parent_name, parent_phone, child_name, child_age):
    if not parent_name or not parent_phone or not child_name:
        raise ValueError('家长姓名、手机和孩子姓名不能为空')
    if not isinstance(child_age, int) or child_age < 0:
        raise ValueError('孩子年龄必须是非负整数')

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO families (parent_name, parent_phone, child_name, child_age) VALUES (?, ?, ?, ?)',
        (parent_name, parent_phone, child_name, child_age)
    )
    conn.commit()
    family_id = cursor.lastrowid
    conn.close()
    return get_family(family_id)


def update_family(family_id, parent_name, parent_phone, child_name, child_age):
    if not parent_name or not parent_phone or not child_name:
        raise ValueError('家长姓名、手机和孩子姓名不能为空')
    if not isinstance(child_age, int) or child_age < 0:
        raise ValueError('孩子年龄必须是非负整数')

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        'UPDATE families SET parent_name=?, parent_phone=?, child_name=?, child_age=? WHERE id=?',
        (parent_name, parent_phone, child_name, child_age, family_id)
    )
    conn.commit()
    conn.close()
    return get_family(family_id)


def delete_family(family_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM attendances WHERE family_id = ?', (family_id,))
    cursor.execute('DELETE FROM registrations WHERE family_id = ?', (family_id,))
    cursor.execute('DELETE FROM families WHERE id = ?', (family_id,))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0


def register_course(course_id, family_id):
    conn = get_connection()
    try:
        conn.execute('BEGIN')

        cursor = conn.cursor()
        cursor.execute('SELECT * FROM courses WHERE id = ?', (course_id,))
        course = cursor.fetchone()
        if not course:
            raise ValueError('课程不存在')
        if course['status'] != '开放报名':
            raise ValueError(f'课程当前状态为「{course["status"]}」，无法报名')

        cursor.execute(
            'SELECT COUNT(*) as cnt FROM registrations WHERE course_id = ?',
            (course_id,)
        )
        count = cursor.fetchone()['cnt']
        if count >= course['max_students']:
            cursor.execute('UPDATE courses SET status = ? WHERE id = ?', ('已满', course_id))
            raise ValueError('课程名额已满')

        cursor.execute(
            'SELECT id FROM registrations WHERE course_id = ? AND family_id = ?',
            (course_id, family_id)
        )
        if cursor.fetchone():
            raise ValueError('该家庭已报名此课程')

        cursor.execute(
            'INSERT INTO registrations (course_id, family_id) VALUES (?, ?)',
            (course_id, family_id)
        )

        new_count = count + 1
        if new_count >= course['max_students']:
            cursor.execute('UPDATE courses SET status = ? WHERE id = ?', ('已满', course_id))

        conn.commit()

        result_course = get_course(course_id)
        return {
            'success': True,
            'course': result_course,
            'registered_count': new_count
        }
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def list_registrations(course_id=None, family_id=None):
    conn = get_connection()
    cursor = conn.cursor()
    query = '''
        SELECT r.*, c.name as course_name, c.course_type, c.age_group, c.fee,
               f.parent_name, f.parent_phone, f.child_name, f.child_age
        FROM registrations r
        JOIN courses c ON r.course_id = c.id
        JOIN families f ON r.family_id = f.id
    '''
    params = []
    conditions = []
    if course_id:
        conditions.append('r.course_id = ?')
        params.append(course_id)
    if family_id:
        conditions.append('r.family_id = ?')
        params.append(family_id)
    if conditions:
        query += ' WHERE ' + ' AND '.join(conditions)
    query += ' ORDER BY r.id DESC'

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_registration_families(course_id):
    return list_registrations(course_id=course_id)


def add_attendance(course_id, family_id, attendance_date=None):
    if attendance_date is None:
        attendance_date = datetime.now().strftime('%Y-%m-%d')

    conn = get_connection()
    try:
        cursor = conn.cursor()

        cursor.execute(
            'SELECT id FROM registrations WHERE course_id = ? AND family_id = ?',
            (course_id, family_id)
        )
        registration = cursor.fetchone()
        if not registration:
            raise ValueError('该家庭未报名此课程，无法签到')

        cursor.execute(
            'SELECT id FROM attendances WHERE course_id = ? AND family_id = ? AND attendance_date = ?',
            (course_id, family_id, attendance_date)
        )
        if cursor.fetchone():
            raise ValueError('该家庭今日已签到')

        cursor.execute(
            'INSERT INTO attendances (registration_id, course_id, family_id, attendance_date) VALUES (?, ?, ?, ?)',
            (registration['id'], course_id, family_id, attendance_date)
        )
        conn.commit()
        attendance_id = cursor.lastrowid

        cursor.execute('SELECT * FROM attendances WHERE id = ?', (attendance_id,))
        result = dict(cursor.fetchone())
        conn.close()
        return result
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def list_attendances(course_id=None, family_id=None, attendance_date=None):
    conn = get_connection()
    cursor = conn.cursor()
    query = '''
        SELECT a.*, c.name as course_name,
               f.parent_name, f.parent_phone, f.child_name, f.child_age
        FROM attendances a
        JOIN courses c ON a.course_id = c.id
        JOIN families f ON a.family_id = f.id
    '''
    params = []
    conditions = []
    if course_id:
        conditions.append('a.course_id = ?')
        params.append(course_id)
    if family_id:
        conditions.append('a.family_id = ?')
        params.append(family_id)
    if attendance_date:
        conditions.append('a.attendance_date = ?')
        params.append(attendance_date)
    if conditions:
        query += ' WHERE ' + ' AND '.join(conditions)
    query += ' ORDER BY a.id DESC'

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_monthly_stats(year=None, month=None):
    now = datetime.now()
    if year is None:
        year = now.year
    if month is None:
        month = now.month

    start_date = f'{year:04d}-{month:02d}-01'
    if month == 12:
        end_date = f'{year + 1:04d}-01-01'
    else:
        end_date = f'{year:04d}-{month + 1:02d}-01'

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT 
            c.course_type,
            COUNT(r.id) as registration_count,
            SUM(c.fee) as total_fee
        FROM registrations r
        JOIN courses c ON r.course_id = c.id
        WHERE r.registered_at >= ? AND r.registered_at < ?
        GROUP BY c.course_type
        ORDER BY c.course_type
    ''', (start_date, end_date))
    rows = cursor.fetchall()
    conn.close()

    stats = [dict(row) for row in rows]
    for s in stats:
        s['total_fee'] = s['total_fee'] or 0

    return {
        'year': year,
        'month': month,
        'stats': stats
    }
