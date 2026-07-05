import random
import numpy as np
import globals as g


class StateIndependentScheduler:
    """State-independent reward-driven message scheduler.

    This scheduler keeps the same public interface as QLearningTable, but
    removes the response-state dimension.

    Original MBFuzzer Q-learning:
        Q[state][message_type]

    This scheduler:
        value[message_type]

    The fuzzing engine still computes and passes response_state, cur_state,
    and next_state, but this scheduler intentionally ignores them.

    Since the update rule uses both positive and negative feedback, this
    scheduler requests learn() calls also when reward = 0.
    """

    def __init__(
        self,
        actions=g.ACTIONS,
        learning_rate=g.ALPHA,
        e_greedy=g.EPSILON,
    ):
        self.actions = list(actions)
        self.learning_rate = learning_rate
        self.epsilon = e_greedy

        # One global value per MQTT message type.
        self.values = {action: 0.0 for action in self.actions}

        # Compatibility/debug view similar to QLearningTable.
        self.global_state = "GLOBAL_STATE"
        self.q_table = {self.global_state: self.values}

        # Used by fuzzing_engine.py:
        # if True, learn() is called also when no new inconsistency is found.
        #self.learn_on_zero_reward = True
        self.learn_on_zero_reward = False

    def choose_next_action(self, state):
        # The state argument is intentionally ignored.
        if all(value == 0 for value in self.values.values()):
            return random.choice(self.actions)

        q_values = np.array([self.values[action] for action in self.actions])

        # Numerically stable softmax.
        shifted_q_values = q_values - np.max(q_values)
        probabilities = np.exp(shifted_q_values / g.TAU) / np.sum(
            np.exp(shifted_q_values / g.TAU)
        )

        rand_num = np.random.rand()
        cumulative_prob = 0.0

        for action, prob in zip(self.actions, probabilities):
            cumulative_prob += prob
            if rand_num < cumulative_prob:
                return action

        return self.actions[-1]

    def check_state_exist(self, state):
        # Kept for compatibility with QLearningTable.
        # No state is created because all response states are ignored.
        pass

    def learn(self, cur_state, action, reward, next_state):
        # cur_state and next_state are intentionally ignored.
        if action not in self.values:
            return

        predict = self.values[action]
        target = reward
        self.values[action] += self.learning_rate * (target - predict)

    def print_q_table(self):
        print(self.log_q_table())

    def log_q_table(self):
        content = "State-Independent Scheduler Table:\n"

        for action in self.actions:
            content += f"{action}: value={self.values[action]:.4f}\n"

        q_values = np.array([self.values[action] for action in self.actions])
        shifted_q_values = q_values - np.max(q_values)
        probabilities = np.exp(shifted_q_values / g.TAU) / np.sum(
            np.exp(shifted_q_values / g.TAU)
        )

        content += "\tprobabilities=" + str(probabilities) + "\n\n"
        return content