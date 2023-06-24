import json
import sqlite3
from pathlib import Path
from typing import Optional

from wecom_responder.utils.tv_subscribe_bot.tvsubscribebot import User, Chat


class MessageCacheManager:
    def __init__(self, dbfile: Path):
        self.dbfile = dbfile
        self.conn: Optional[sqlite3.Connection] = None
        self._isclosed: bool = True
        self.create_table()

    def connect(self):
        if not self._isclosed:
            return
        self._isclosed = False
        self.conn = sqlite3.connect(str(self.dbfile))
        self.c = self.conn.cursor()

    def close(self):
        if self._isclosed:
            return
        self.conn.close()
        self._isclosed = True

    def create_table(self):
        # note: 频道名不唯一，甚至同一个network下频道名也可能不唯一
        self.connect()
        self.c.execute("""CREATE TABLE IF NOT EXISTS 
            chats (
                chatid INTEGER NOT NULL,
                username TEXT NOT NULL, 
                agentid TEXT NOT NULL, 
                jsonstr TEXT NOT NULL,
                PRIMARY KEY(username, agentid)
            );""")
        self.c.execute("""CREATE TABLE IF NOT EXISTS 
            users (
                userid INTEGER NOT NULL,
                username TEXT NOT NULL, 
                jsonstr TEXT NOT NULL,
                PRIMARY KEY(username)
            );""")
        self.conn.commit()
        self.close()

    def recreate_table(self):
        self.connect()
        self.c.execute('DROP TABLE IF EXISTS users;')
        self.c.execute('DROP TABLE IF EXISTS chats;')
        self.conn.commit()
        self.create_table()
        self.close()

    def insert_chat(self, user: User, chat: Chat, agentid: str):
        self.connect()
        self.c.execute(f"""INSERT INTO 
            chats(chatid, username, agentid, jsonstr) VALUES
            ('{chat.id}, {user.first_name}', '{agentid}', '{chat.to_json()}');""")
        self.conn.commit()
        self.close()

    def insert_user(self, user: User):
        self.connect()
        self.c.execute(f"""INSERT INTO 
            users(userid, username, jsonstr) VALUES
            ('{user.id}, {user.first_name}', '{user.to_json()}');""")
        self.conn.commit()
        self.close()

    def update_chat(self, user: User, chat: Chat, agentid: str) -> Chat:
        self.connect()
        self.c.execute(f"""UPDATE chats
            SET jsonstr='{chat.to_json()}'
            WHERE chatid='{chat.id}' AND username='{user.first_name}' AND agentid='{agentid}';""")
        self.conn.commit()
        self.close()
        return chat

    def update_user(self, user: User) -> User:
        self.connect()
        self.c.execute(f"""UPDATE users
            SET jsonstr='{user.to_json()}'
            WHERE userid='{user.id}' AND username='{user.first_name}';""")
        self.conn.commit()
        self.close()
        return user

    def find_chat(self, user: User, agentid: str) -> Optional[Chat]:
        self.connect()
        cur = self.c.execute(f"SELECT jsonstr from chats WHERE username='{user.first_name}' AND agentid='{agentid}'")
        row = cur.fetchone()
        res = Chat.de_json(json.loads(row[0]), None) if row else None
        self.close()
        return res

    def find_user(self, username: str) -> Optional[User]:
        self.connect()
        cur = self.c.execute(f"SELECT jsonstr from users WHERE username='{username}'")
        row = cur.fetchone()
        res = User.de_json(json.loads(row[0]), None) if row else None
        self.close()
        return res

    def total_chats(self) -> int:
        self.connect()
        cur = self.c.execute(f"SELECT COUNT(rowid) from chats")
        row = cur.fetchone()
        res = row[0] if row else 0
        self.close()
        return res

    def total_users(self) -> int:
        self.connect()
        cur = self.c.execute(f"SELECT COUNT(rowid) from users")
        row = cur.fetchone()
        res = row[0] if row else 0
        self.close()
        return res
