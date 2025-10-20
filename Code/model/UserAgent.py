from random import choice

USER_AGENTS = [
    
]

class UserAgent:
    def __init__(self):
        self.using = choice(USER_AGENTS)
        self.used_user_agents = set()
    
    def change_user_agent(self)->None:
        self.used_user_agents.add(self.using)
        availabe = list(set(USER_AGENTS) - self.used_user_agents)
        
        if not availabe: availabe = USER_AGENTS # if run out of availabe user-agents, then reset the rotation 
        
        self.using = choice(availabe)