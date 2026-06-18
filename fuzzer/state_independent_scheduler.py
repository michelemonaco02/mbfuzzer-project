import random
import numpy as np
import globals as g


class StateIndependentScheduler:
    """State-independent reward-based message scheduler.

    This scheduler is a simplified version of the original Q-learning
    scheduler: it learns one global value per MQTT message type, without
    indexing values by protocol state.

    Original Q-learning scheduler:
        Q[state][message_type]

    State-independent scheduler:
        Q[message_type]

    The scheduler keeps the same public interface as QLearningTable so it can
    be used by the existing fuzzing engine without changing the feedback logic.
    """

    def __init__(self, actions=g.ACTIONS):
        self.actions = list(actions)
        self.values = {action: 0.0 for action in self.actions}
        self.selection_counts = {action: 0 for action in self.actions}
        self.reward_counts = {action: 0 for action in self.actions}

    def choose_next_action(self, state):
        # The state argument is intentionally ignored.
        # If no action has any reward yet, behave like the original
        # QLearningTable implementation and choose randomly.
        if all(value == 0 for value in self.values.values()):
            action = random.choice(self.actions)
        else:
            q_values = np.array([self.values[action] for action in self.actions])
            probabilities = np.exp(q_values / g.TAU) / np.sum(
                np.exp(q_values / g.TAU)
            )

            rand_num = np.random.rand()
            cumulative_prob = 0.0

            action = self.actions[-1]
            for candidate_action, prob in zip(self.actions, probabilities):
                cumulative_prob += prob
                if rand_num < cumulative_prob:
                    action = candidate_action
                    break

        self.selection_counts[action] += 1

        # Since the current fuzzing loop usually calls learn() only on positive
        # feedback, we update the empirical value also after non-rewarding
        # selections. This prevents old rewards from dominating forever.
        self._update_value(action)

        return action

    def check_state_exist(self, state):
        # Kept for compatibility with QLearningTable.
        pass

    def learn(self, cur_state, action, reward, next_state):
        if action not in self.values:
            return

        # If the action was selected through the dependency queue, it may
        # receive a reward even if choose_next_action() did not select it.
        # We still count it to keep the scheduler robust.
        if self.selection_counts[action] == 0:
            self.selection_counts[action] = 1

        self.reward_counts[action] += reward
        self._update_value(action)

    def _update_value(self, action):
        if self.selection_counts[action] == 0:
            self.values[action] = 0.0
        else:
            self.values[action] = (
                self.reward_counts[action] / self.selection_counts[action]
            )

    def print_q_table(self):
        print(self.log_q_table())

    def log_q_table(self):
        content = "State-Independent Scheduler Table:\n"

        for action in self.actions:
            content += (
                f"{action}: value={self.values[action]:.4f}, "
                f"selected={self.selection_counts[action]}, "
                f"rewards={self.reward_counts[action]}\n"
            )

        q_values = np.array([self.values[action] for action in self.actions])
        probabilities = np.exp(q_values / g.TAU) / np.sum(
            np.exp(q_values / g.TAU)
        )
        content += "\tprobabilities=" + str(probabilities) + "\n\n"

        return content