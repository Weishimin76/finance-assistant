# -*- coding: utf-8 -*-
"""
多用户数据库管理模块
使用SQLite实现用户注册、登录、数据隔离功能
"""

import sqlite3
import hashlib
import os
from datetime import datetime
from typing import Optional, List, Dict, Any


# 数据库文件路径
DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
DB_PATH = os.path.join(DB_DIR, "users.db")


def _get_connection() -> sqlite3.Connection:
    """获取数据库连接，启用外键约束"""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row
    return conn


def _hash_password(password: str) -> str:
    """使用SHA-256对密码进行哈希加密"""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def init_db() -> None:
    """初始化数据库，创建所有表结构"""
    try:
        conn = _get_connection()
        cursor = conn.cursor()

        # 用户表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                email TEXT DEFAULT '',
                company TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                last_login TEXT,
                is_active INTEGER DEFAULT 1,
                plan TEXT DEFAULT 'free'
            )
        """)

        # 用户数据表（存储上传的文件和解析后的数据）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                data_type TEXT NOT NULL,
                content TEXT,
                filename TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        """)

        # AI对话记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                question TEXT NOT NULL,
                answer TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        """)

        # 创建索引以提升查询性能
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_data_user_id
            ON user_data (user_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_chat_history_user_id
            ON chat_history (user_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_users_username
            ON users (username)
        """)

        conn.commit()
        conn.close()
        print(f"[数据库] 初始化完成，数据库文件：{DB_PATH}")
    except Exception as e:
        print(f"[数据库] 初始化失败：{e}")
        raise


def register_user(username: str, password: str, email: str = "",
                  company: str = "") -> Optional[int]:
    """
    注册新用户

    Args:
        username: 用户名（唯一）
        password: 明文密码
        email: 邮箱地址
        company: 公司名称

    Returns:
        成功返回 user_id，失败返回 None
    """
    try:
        conn = _get_connection()
        cursor = conn.cursor()

        # 检查用户名是否已存在
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            print(f"[注册] 用户名 '{username}' 已存在")
            conn.close()
            return None

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        password_hash = _hash_password(password)

        cursor.execute("""
            INSERT INTO users (username, password_hash, email, company, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (username, password_hash, email, company, now))

        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        print(f"[注册] 用户 '{username}' 注册成功，ID: {user_id}")
        return user_id
    except Exception as e:
        print(f"[注册] 注册失败：{e}")
        return None


def login_user(username: str, password: str) -> Optional[int]:
    """
    用户登录验证

    Args:
        username: 用户名
        password: 明文密码

    Returns:
        验证成功返回 user_id，失败返回 None
    """
    try:
        conn = _get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id, password_hash, is_active FROM users WHERE username = ?",
            (username,)
        )
        row = cursor.fetchone()

        if not row:
            print(f"[登录] 用户 '{username}' 不存在")
            conn.close()
            return None

        if not row["is_active"]:
            print(f"[登录] 用户 '{username}' 已被禁用")
            conn.close()
            return None

        if row["password_hash"] != _hash_password(password):
            print(f"[登录] 用户 '{username}' 密码错误")
            conn.close()
            return None

        # 更新最后登录时间
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            "UPDATE users SET last_login = ? WHERE id = ?",
            (now, row["id"])
        )
        conn.commit()
        conn.close()
        print(f"[登录] 用户 '{username}' 登录成功")
        return row["id"]
    except Exception as e:
        print(f"[登录] 登录验证失败：{e}")
        return None


def get_user(user_id: int) -> Optional[Dict[str, Any]]:
    """
    获取用户信息

    Args:
        user_id: 用户ID

    Returns:
        用户信息字典，失败返回 None
    """
    try:
        conn = _get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return dict(row)
        return None
    except Exception as e:
        print(f"[用户] 获取用户信息失败：{e}")
        return None


def save_user_data(user_id: int, data_type: str, content: str,
                   filename: str = "") -> Optional[int]:
    """
    保存用户数据（上传的文件和解析后的数据）

    Args:
        user_id: 用户ID
        data_type: 数据类型（如 csv, json, parsed 等）
        content: 数据内容
        filename: 原始文件名

    Returns:
        成功返回数据记录ID，失败返回 None
    """
    try:
        conn = _get_connection()
        cursor = conn.cursor()

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO user_data (user_id, data_type, content, filename, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, data_type, content, filename, now))

        data_id = cursor.lastrowid
        conn.commit()
        conn.close()
        print(f"[数据] 用户 {user_id} 的数据已保存，记录ID: {data_id}")
        return data_id
    except Exception as e:
        print(f"[数据] 保存用户数据失败：{e}")
        return None


def get_user_data(user_id: int) -> List[Dict[str, Any]]:
    """
    获取用户的所有数据记录

    Args:
        user_id: 用户ID

    Returns:
        数据记录列表
    """
    try:
        conn = _get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM user_data WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,)
        )
        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]
    except Exception as e:
        print(f"[数据] 获取用户数据失败：{e}")
        return []


def save_chat(user_id: int, question: str, answer: str) -> Optional[int]:
    """
    保存AI对话记录

    Args:
        user_id: 用户ID
        question: 用户提问
        answer: AI回答

    Returns:
        成功返回记录ID，失败返回 None
    """
    try:
        conn = _get_connection()
        cursor = conn.cursor()

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO chat_history (user_id, question, answer, created_at)
            VALUES (?, ?, ?, ?)
        """, (user_id, question, answer, now))

        chat_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return chat_id
    except Exception as e:
        print(f"[对话] 保存对话记录失败：{e}")
        return None


def get_chat_history(user_id: int, limit: int = 20) -> List[Dict[str, Any]]:
    """
    获取用户的AI对话历史

    Args:
        user_id: 用户ID
        limit: 返回记录数量上限，默认20条

    Returns:
        对话记录列表，按时间倒序排列
    """
    try:
        conn = _get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM chat_history
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (user_id, limit))
        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]
    except Exception as e:
        print(f"[对话] 获取对话历史失败：{e}")
        return []


def list_users() -> List[Dict[str, Any]]:
    """
    列出所有用户（管理员功能）

    Returns:
        用户信息列表
    """
    try:
        conn = _get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id, username, email, company, created_at, last_login, "
            "is_active, plan FROM users ORDER BY created_at DESC"
        )
        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]
    except Exception as e:
        print(f"[管理] 列出用户失败：{e}")
        return []


def delete_user_data(user_id: int) -> bool:
    """
    删除用户的所有数据（包括用户数据和对话记录）

    Args:
        user_id: 用户ID

    Returns:
        成功返回 True，失败返回 False
    """
    try:
        conn = _get_connection()
        cursor = conn.cursor()

        # 删除用户数据
        cursor.execute("DELETE FROM user_data WHERE user_id = ?", (user_id,))
        deleted_data = cursor.rowcount

        # 删除对话记录
        cursor.execute("DELETE FROM chat_history WHERE user_id = ?", (user_id,))
        deleted_chat = cursor.rowcount

        conn.commit()
        conn.close()
        print(f"[删除] 用户 {user_id} 的数据已清除："
              f"数据记录 {deleted_data} 条，对话记录 {deleted_chat} 条")
        return True
    except Exception as e:
        print(f"[删除] 删除用户数据失败：{e}")
        return False


# ============================================================
# 模块自测入口
# ============================================================
if __name__ == "__main__":
    print("=" * 50)
    print("  数据库模块自测")
    print("=" * 50)

    # 1. 初始化数据库
    init_db()

    # 2. 注册测试用户
    uid1 = register_user("testuser", "123456", "test@example.com", "测试公司")
    uid2 = register_user("admin_user", "admin123", "admin@example.com", "管理公司")
    print(f"注册结果: uid1={uid1}, uid2={uid2}")

    # 3. 重复注册测试
    uid_dup = register_user("testuser", "654321")
    print(f"重复注册结果: {uid_dup} (应为 None)")

    # 4. 登录验证
    login_ok = login_user("testuser", "123456")
    login_fail = login_user("testuser", "wrong_pwd")
    print(f"登录成功: {login_ok} (应为 {uid1})")
    print(f"登录失败: {login_fail} (应为 None)")

    # 5. 获取用户信息
    user_info = get_user(uid1)
    print(f"用户信息: {user_info}")

    # 6. 保存用户数据
    data_id = save_user_data(uid1, "csv", "order_id,amount\n1,100.00", "orders.csv")
    print(f"数据保存ID: {data_id}")

    # 7. 获取用户数据
    user_data = get_user_data(uid1)
    print(f"用户数据条数: {len(user_data)}")

    # 8. 保存对话记录
    chat_id = save_chat(uid1, "如何计算VAT？", "VAT计算公式为...")
    print(f"对话记录ID: {chat_id}")

    # 9. 获取对话历史
    history = get_chat_history(uid1)
    print(f"对话历史条数: {len(history)}")

    # 10. 列出所有用户
    users = list_users()
    print(f"用户总数: {len(users)}")

    # 11. 删除用户数据
    result = delete_user_data(uid1)
    print(f"删除用户数据结果: {result}")

    # 12. 验证删除
    data_after = get_user_data(uid1)
    history_after = get_chat_history(uid1)
    print(f"删除后数据条数: {len(data_after)} (应为 0)")
    print(f"删除后对话条数: {len(history_after)} (应为 0)")

    print("=" * 50)
    print("  自测完成")
    print("=" * 50)
