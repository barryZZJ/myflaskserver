# from pathlib import Path
# from typing import Optional
from wecom_responder.utils.misc import md5int
# from wecom_responder.utils.cache import MessageCacheManager
# from wecom_responder.utils.consts import CACHE_RESPONDER
from wecom_responder.utils.tv_subscribe_bot.tvsubscribebot import User, Chat


class UserManager:
    @staticmethod
    def _gen_userid(username: str) -> int:
        # derive id from hash value, in case the cache file corrupts
        return md5int(username, digits=5)

    @staticmethod
    def new_user(username: str) -> User:
        # if found := self._cache.find_user(username):
        #     if override:
        #         new = User(found.id, first_name=username, is_bot=False)
        #         self._cache.update_user(new)
        #         return new
        #     raise KeyError(f"User '{username}' already exists!")

        user = User(UserManager._gen_userid(username), first_name=username, is_bot=False, username=username)
        # self._cache.insert_user(user)
        return user


class ChatManager:
    @staticmethod
    def _gen_chatid(user: User, agentid: int) -> int:
        # derive id from hash value, in case the cache file corrupts
        return md5int(''.join([user.first_name, str(agentid)]), digits=5)

    @staticmethod
    def new_chat(user: User, agentid: int) -> Chat:
        # if found := self._cache.find_chat(user, agentid):
        #     if override:
        #         new = Chat(found.id, chat_title, user.first_name)
        #         self._cache.update_chat(user, new, agentid)
        #         return new
        #     raise KeyError(f"Chat '({user.first_name}, {agentid})' already exists!")

        chat = Chat(ChatManager._gen_chatid(user, agentid), Chat.PRIVATE, username=user.first_name)
        # self._cache.insert_chat(user, chat, agentid)
        return chat


# class MessageManager:
    # def __init__(self, dbfile: Path = CACHE_RESPONDER):
        # self._cache: MessageCacheManager = MessageCacheManager(dbfile)
        # self._cache.create_table()

    # def get_chat(self, user: User, agentid: str) -> Optional[Chat]:
        # return self._cache.find_chat(user, agentid)

    # def get_user(self, username: str) -> Optional[User]:
        # return self._cache.find_user(username)

    # def set_default_chat(self, user: User, agentid: str, chat_title: str = None) -> Chat:
    #     if chat := self.get_chat(user, agentid):
    #         return chat
    #     return self.new_chat(user, agentid, chat_title, override=False)
    #
    # def set_default_user(self, username: str) -> User:
    #     if user := self.get_user(username):
    #         return user
    #     return self.new_user(username, override=False)


# message_manager = MessageManager()
# user_manager = UserManager()
# chat_manager = ChatManager()

# __all__ = (user_manager, chat_manager)

