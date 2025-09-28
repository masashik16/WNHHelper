import os

import aiomysql
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), './.env')
load_dotenv(env_path, override=True)
DB_HOST = os.environ.get("DB_HOST")
DB_PORT = int(os.environ.get("DB_PORT"))
DB_USER = os.environ.get("DB_USER")
DB_PASS = os.environ.get("DB_PASS")
DB_NAME = os.environ.get("DB_NAME")


async def add_user(discord_id: int, account_id: str, region: str):
    """ユーザーを追加（認証系）"""
    db_connect = await aiomysql.connect(host=DB_HOST, port=DB_PORT,
                                        user=DB_USER, password=DB_PASS,
                                        db=DB_NAME)
    db_cur = await db_connect.cursor()
    await db_cur.execute("SELECT * FROM user_info")
    await db_cur.execute("SELECT * FROM user_info WHERE discord_id = %s", (discord_id,))
    result = await db_cur.fetchone()
    if result is None:
        await db_cur.execute("INSERT INTO user_info(discord_id, account_id, region) VALUES(%s, %s, %s)",
                             (discord_id, account_id, region))
        await db_connect.commit()
        await db_cur.close()
        db_connect.close()
        return "ADDED"
    else:
        await db_cur.execute("UPDATE user_info SET account_id = %s WHERE discord_id = %s", (account_id, discord_id))
        await db_connect.commit()
        await db_cur.execute("UPDATE user_info SET region = %s WHERE discord_id = %s", (region, discord_id))
        await db_connect.commit()
        await db_cur.close()
        db_connect.close()
        return "UPDATED"


async def search_user(discord_id: int):
    """ユーザーを取得（認証系）"""
    db_connect = await aiomysql.connect(host=DB_HOST, port=DB_PORT,
                                        user=DB_USER, password=DB_PASS,
                                        db=DB_NAME)
    db_cur = await db_connect.cursor()
    await db_cur.execute("SELECT * FROM user_info")
    await db_cur.execute("SELECT * FROM user_info WHERE discord_id = %s", (discord_id,))
    result = await db_cur.fetchone()
    await db_cur.close()
    db_connect.close()
    if result is None:
        return "ERROR"
    else:
        return result


async def save_message(name: str, channel_id: int, message_id: int):
    """メッセージ情報を保存（ボタン系）"""
    db_connect = await aiomysql.connect(host=DB_HOST, port=DB_PORT,
                                        user=DB_USER, password=DB_PASS,
                                        db=DB_NAME)
    db_cur = await db_connect.cursor()
    await db_cur.execute("SELECT * FROM message")
    await db_cur.execute("SELECT * FROM message WHERE name = %s", (name,))
    result = await db_cur.fetchone()
    # 既存データがない場合
    if result is None:
        await db_cur.execute("INSERT INTO message(name, channel_id, message_id) VALUES(%s, %s, %s)",
                             (name, channel_id, message_id))
        await db_connect.commit()
        await db_cur.close()
        db_connect.close()
    # 既存データがある場合（削除して追加）
    else:
        await db_cur.execute("DELETE FROM message WHERE name = %s", (name,))
        await db_cur.execute("INSERT INTO message(name, channel_id, message_id) VALUES(%s, %s, %s)",
                             (name, channel_id, message_id))
        await db_connect.commit()
        await db_cur.close()
        db_connect.close()


async def get_message(name: str):
    """メッセージ情報を取得（ボタン系）"""
    db_connect = await aiomysql.connect(host=DB_HOST, port=DB_PORT,
                                        user=DB_USER, password=DB_PASS,
                                        db=DB_NAME)
    db_cur = await db_connect.cursor()
    await db_cur.execute("SELECT * FROM message")
    await db_cur.execute("SELECT * FROM message WHERE name = %s", (name,))
    result = await db_cur.fetchone()
    await db_cur.close()
    db_connect.close()
    return result


async def save_status(name: str, status: str):
    """イベントの受付状況を保存（イベントフォーム）"""
    db_connect = await aiomysql.connect(host=DB_HOST, port=DB_PORT,
                                        user=DB_USER, password=DB_PASS,
                                        db=DB_NAME)
    db_cur = await db_connect.cursor()
    await db_cur.execute("SELECT * FROM status")
    await db_cur.execute("SELECT * FROM status WHERE name = %s", (name,))
    result = await db_cur.fetchone()
    if result is None:
        await db_cur.execute("INSERT INTO status(name, status) VALUES(%s, %s)", (name, status))
        await db_connect.commit()
        await db_cur.close()
        db_connect.close()
    else:
        await db_cur.execute("DELETE FROM status WHERE name = %s", (name,))
        await db_cur.execute("INSERT INTO status(name, status) VALUES(%s, %s)", (name, status))
        await db_connect.commit()
        await db_cur.close()
        db_connect.close()


async def get_status(name: str):
    """イベントの受付状況を取得（イベントフォーム）"""
    db_connect = await aiomysql.connect(host=DB_HOST, port=DB_PORT,
                                        user=DB_USER, password=DB_PASS,
                                        db=DB_NAME)
    db_cur = await db_connect.cursor()
    await db_cur.execute("SELECT * FROM status")
    await db_cur.execute("SELECT * FROM status WHERE name = %s", (name,))
    result = await db_cur.fetchone()
    await db_cur.close()
    db_connect.close()
    return result


async def save_modlog(moderate_type: int, user_id: int, moderator_id: int, length, reason: str, datetime: str,
                      point: int):
    """モデレーション記録の保存"""
    db_connect = await aiomysql.connect(host=DB_HOST, port=DB_PORT,
                                        user=DB_USER, password=DB_PASS,
                                        db=DB_NAME)
    db_cur = await db_connect.cursor()
    await db_cur.execute("SELECT max(case_id) case_id FROM moderation")
    result = await db_cur.fetchone()
    if result[0] is None:
        case_id = 1
    else:
        case_id = result[0] + 1
    if length == "":
        await db_cur.execute(
            "INSERT INTO moderation(case_id, moderate_type, user_id, moderator_id, reason, datetime, point)"
            " VALUES(%s, %s, %s, %s, %s, %s, %s)",
            (case_id, moderate_type, user_id, moderator_id, reason, datetime, point))
    else:
        await db_cur.execute(
            "INSERT INTO moderation(case_id, moderate_type, user_id, moderator_id, length, reason, datetime, point)"
            " VALUES(%s, %s, %s, %s, %s, %s, %s, %s)",
            (case_id, moderate_type, user_id, moderator_id, length, reason, datetime, point))
    await db_connect.commit()
    await db_cur.close()
    db_connect.close()
    return case_id


async def update_modlog(old_case_id: int, change_type: int, new_case_id: int, change_datetime: str):
    """モデレーション記録へケースIDとスレッドIDを追加"""
    db_connect = await aiomysql.connect(host=DB_HOST, port=DB_PORT,
                                        user=DB_USER, password=DB_PASS,
                                        db=DB_NAME)
    db_cur = await db_connect.cursor()
    a = await db_cur.execute(
        "UPDATE moderation SET change_type = %s, changed_case_id = %s, change_datetime = %s WHERE case_id = %s",
        (change_type, new_case_id, change_datetime, old_case_id))
    await db_connect.commit()
    await db_cur.close()
    db_connect.close()
    return


async def update_modlog_id(case_id: int, thread_id: int):
    """モデレーション記録へケースIDとスレッドIDを追加"""
    db_connect = await aiomysql.connect(host=DB_HOST, port=DB_PORT,
                                        user=DB_USER, password=DB_PASS,
                                        db=DB_NAME)
    db_cur = await db_connect.cursor()
    await db_cur.execute("UPDATE moderation SET thread_id = %s WHERE case_id = %s", (thread_id, case_id))
    await db_connect.commit()
    await db_cur.close()
    db_connect.close()
    return case_id


async def get_modlog_single(case_id: int):
    """モデレーション記録（単一）の取得"""
    db_connect = await aiomysql.connect(host=DB_HOST, port=DB_PORT,
                                        user=DB_USER, password=DB_PASS,
                                        db=DB_NAME)
    db_cur = await db_connect.cursor()
    await db_cur.execute("SELECT * FROM moderation WHERE case_id = %s", (case_id,))
    result = await db_cur.fetchone()
    await db_cur.close()
    db_connect.close()
    return result


async def get_modlog_multi(user_id: int):
    """モデレーション記録（ユーザー単位）の取得"""
    db_connect = await aiomysql.connect(host=DB_HOST, port=DB_PORT,
                                        user=DB_USER, password=DB_PASS,
                                        db=DB_NAME)
    db_cur = await db_connect.cursor()
    await db_cur.execute("SELECT * FROM moderation WHERE user_id = %s", (user_id,))
    result = await db_cur.fetchall()
    await db_cur.close()
    db_connect.close()
    return result


async def get_point(user_id: int):
    """ポイントを取得（モデレーション）"""
    db_connect = await aiomysql.connect(host=DB_HOST, port=DB_PORT,
                                        user=DB_USER, password=DB_PASS,
                                        db=DB_NAME)
    db_cur = await db_connect.cursor()
    await db_cur.execute("SELECT point FROM point WHERE user_id = %s", (user_id,))
    result = await db_cur.fetchone()
    await db_cur.close()
    db_connect.close()
    return result


async def save_point(user_id: int, point: int):
    """ポイントの保存・更新（モデレーション）"""
    db_connect = await aiomysql.connect(host=DB_HOST, port=DB_PORT,
                                        user=DB_USER, password=DB_PASS,
                                        db=DB_NAME)
    db_cur = await db_connect.cursor()
    old_point = await get_point(user_id=user_id)
    if old_point is not None:
        await db_cur.execute("UPDATE point SET point = %s WHERE user_id = %s", (point, user_id))
    else:
        await db_cur.execute("INSERT INTO point(user_id, point) VALUES(%s, %s)", (user_id, point))
    await db_connect.commit()
    await db_cur.close()
    db_connect.close()
    result = await get_point(user_id=user_id)
    return result


async def save_division_log(user_id: int, action_datetime: float):
    """分隊募集記録の保存"""
    db_connect = await aiomysql.connect(host=DB_HOST, port=DB_PORT,
                                        user=DB_USER, password=DB_PASS,
                                        db=DB_NAME)
    db_cur = await db_connect.cursor()
    await db_cur.execute("INSERT INTO log_division(user_id, datetime) VALUES(%s, %s)", (user_id, action_datetime))
    await db_connect.commit()
    await db_cur.close()
    db_connect.close()


async def get_division_log():
    """分隊募集記録の取得"""
    db_connect = await aiomysql.connect(host=DB_HOST, port=DB_PORT,
                                        user=DB_USER, password=DB_PASS,
                                        db=DB_NAME)
    db_cur = await db_connect.cursor()
    await db_cur.execute("SELECT * FROM log_division")
    result = await db_cur.fetchall()
    await db_cur.close()
    db_connect.close()
    return result


async def save_question_log(user_id: int, action_datetime: float):
    """質問記録の保存"""
    db_connect = await aiomysql.connect(host=DB_HOST, port=DB_PORT,
                                        user=DB_USER, password=DB_PASS,
                                        db=DB_NAME)
    db_cur = await db_connect.cursor()
    await db_cur.execute("INSERT INTO log_question(user_id, datetime) VALUES(%s, %s)", (user_id, action_datetime))
    await db_connect.commit()
    await db_cur.close()
    db_connect.close()


async def get_question_log():
    """質問記録の取得"""
    db_connect = await aiomysql.connect(host=DB_HOST, port=DB_PORT,
                                        user=DB_USER, password=DB_PASS,
                                        db=DB_NAME)
    db_cur = await db_connect.cursor()
    await db_cur.execute("SELECT * FROM log_question")
    result = await db_cur.fetchall()
    await db_cur.close()
    db_connect.close()
    return result


async def get_inquiry_number(category: str):
    """問い合わせチケット番号の取得と更新"""
    db_connect = await aiomysql.connect(host=DB_HOST, port=DB_PORT,
                                        user=DB_USER, password=DB_PASS,
                                        db=DB_NAME)
    db_cur = await db_connect.cursor()
    await db_cur.execute("SELECT current_number FROM inquiry_number WHERE category = %s", (category,))
    result = await db_cur.fetchone()
    current_number = result[0]
    new_number = current_number + 1
    await db_cur.execute("UPDATE inquiry_number SET current_number = %s WHERE category = %s", (new_number, category))
    await db_connect.commit()
    await db_cur.close()
    db_connect.close()
    return new_number


