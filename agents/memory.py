class Memory:
    def __init__(self,system_prompt):
        self.message = [
            {"role": "system", "content": system_prompt}
        ]
    
    def add_message(self, role: 'user' | 'assistant' | 'system' | 'developer' , content):
        message = {"role": role, "content": content}
        self.message.append(message)
    
    def get_message(self):
        return self.message