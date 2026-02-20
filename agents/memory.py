class Memory:
    def __init__(self,system_prompt):
        self.message = [
            {"role": "system", "content": system_prompt}
        ]
    
    def add_message(self, role: 'user' | 'assistant' | 'system' | 'function', content):
        self.message.append({"role": role, "content": content})
    
    def get_message(self):
        return self.message