from typing import Optional

from wecom_responder.utils.tvsubscribebot import User, Chat


class MessageManager:
    def __init__(self):
        # TODO 持久化这些字典
        self._users: dict[str, User] = {}
        self._chats: dict[User, dict[str, Chat]] = {}

    def new_user(self, userid: str, exist_ok: bool = False) -> User:
        if self._users.get(userid) and not exist_ok:
            raise KeyError(f"'{userid}' already exists!")
        self._users[userid] = User(len(self._users), userid)
        return self._users[userid]

    def get_user(self, userid: str) -> Optional[User]:
        return self._users.get(userid)

    def set_default_user(self, userid: str) -> User:
        if user := self.get_user(userid):
            return user
        return self.new_user(userid, exist_ok=False)

    def new_chat(self, user: User, chatid: str, chat_title: str = None, exist_ok: bool = False) -> Chat:
        chat_per_user = self._chats.setdefault(user, {})
        if chat_per_user and chat_per_user.get(chatid) and not exist_ok:
            raise KeyError(f"'user {user.username} with chatid {chatid}' already exists!")
        chat_per_user[chatid] = Chat(len(chat_per_user), title=chat_title, username=user.username)
        return chat_per_user[chatid]

    def get_chat(self, user: User, chatid: str) -> Optional[Chat]:
        return self._chats.setdefault(user, {}).get(chatid)

    def set_default_chat(self, user: User, chatid: str, chat_title: str = None) -> Chat:
        if chat := self.get_chat(user, chatid):
            return chat
        return self.new_chat(user, chatid, chat_title, exist_ok=False)


message_manager = MessageManager()

__all__ = (message_manager,)
