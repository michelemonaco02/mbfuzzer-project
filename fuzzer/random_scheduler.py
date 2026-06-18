import random
import globals as g


class RandomScheduler:
    def __init__(self, actions=g.ACTIONS):
        self.actions = list(actions)

    def choose_next_action(self, state):
        return random.choice(self.actions)

    def check_state_exist(self, state):
        # Kept for compatibility with QLearningTable.
        pass

    def learn(self, cur_state, action, reward, next_state):
        # Random scheduling does not learn from feedback.
        pass

    def print_q_table(self):
        print("RandomScheduler: no Q-table available.")

    def log_q_table(self):
        return "RandomScheduler: no Q-table available.\n"