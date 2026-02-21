from .constants import MessageRole, MessageRoleType


class Memory:
    def __init__(self,system_prompt):
        self.message = [
            {"role": MessageRole.SYSTEM, "content": system_prompt}
        ]
    
    def add_message(self, role: MessageRoleType , content):
        message = {"role": role, "content": content}
        self.message.append(message)
    
    def get_message(self):
        return self.message