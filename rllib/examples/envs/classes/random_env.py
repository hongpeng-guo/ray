import copy
import gymnasium as gym
from gymnasium.spaces import Discrete, Tuple
import numpy as np

from ray.rllib.examples.envs.classes.multi_agent import make_multi_agent


class RandomEnv(gym.Env):
    """A randomly acting environment.

    Can be instantiated with arbitrary action-, observation-, and reward
    spaces. Observations and rewards are generated by simply sampling from the
    observation/reward spaces. The probability of a `terminated=True` after each
    action can be configured, as well as the max episode length.
    """

    def __init__(self, config=None):
        config = config or {}

        # Action space.
        self.action_space = config.get("action_space", Discrete(2))
        # Observation space from which to sample.
        self.observation_space = config.get("observation_space", Discrete(2))
        # Reward space from which to sample.
        self.reward_space = config.get(
            "reward_space",
            gym.spaces.Box(low=-1.0, high=1.0, shape=(), dtype=np.float32),
        )
        self.static_samples = config.get("static_samples", False)
        if self.static_samples:
            self.observation_sample = self.observation_space.sample()
            self.reward_sample = self.reward_space.sample()

        # Chance that an episode ends at any step.
        # Note that a max episode length can be specified via
        # `max_episode_len`.
        self.p_terminated = config.get("p_terminated")
        if self.p_terminated is None:
            self.p_terminated = config.get("p_done", 0.1)
        # A max episode length. Even if the `p_terminated` sampling does not lead
        # to a terminus, the episode will end after at most this many
        # timesteps.
        # Set to 0 or None for using no limit on the episode length.
        self.max_episode_len = config.get("max_episode_len", None)
        # Whether to check action bounds.
        self.check_action_bounds = config.get("check_action_bounds", False)
        # Steps taken so far (after last reset).
        self.steps = 0

    def reset(self, *, seed=None, options=None):
        self.steps = 0
        if not self.static_samples:
            return self.observation_space.sample(), {}
        else:
            return copy.deepcopy(self.observation_sample), {}

    def step(self, action):
        if self.check_action_bounds and not self.action_space.contains(action):
            raise ValueError(
                "Illegal action for {}: {}".format(self.action_space, action)
            )
        if isinstance(self.action_space, Tuple) and len(action) != len(
            self.action_space.spaces
        ):
            raise ValueError(
                "Illegal action for {}: {}".format(self.action_space, action)
            )

        self.steps += 1
        terminated = False
        truncated = False
        # We are `truncated` as per our max-episode-len.
        if self.max_episode_len and self.steps >= self.max_episode_len:
            truncated = True
        # Max episode length not reached yet -> Sample `terminated` via `p_terminated`.
        elif self.p_terminated > 0.0:
            terminated = bool(
                np.random.choice(
                    [True, False], p=[self.p_terminated, 1.0 - self.p_terminated]
                )
            )

        if not self.static_samples:
            return (
                self.observation_space.sample(),
                self.reward_space.sample(),
                terminated,
                truncated,
                {},
            )
        else:
            return (
                copy.deepcopy(self.observation_sample),
                copy.deepcopy(self.reward_sample),
                terminated,
                truncated,
                {},
            )


# Multi-agent version of the RandomEnv.
RandomMultiAgentEnv = make_multi_agent(lambda c: RandomEnv(c))


# Large observation space "pre-compiled" random env (for testing).
class RandomLargeObsSpaceEnv(RandomEnv):
    def __init__(self, config=None):
        config = config or {}
        config.update({"observation_space": gym.spaces.Box(-1.0, 1.0, (5000,))})
        super().__init__(config=config)


# Large observation space + cont. actions "pre-compiled" random env
# (for testing).
class RandomLargeObsSpaceEnvContActions(RandomEnv):
    def __init__(self, config=None):
        config = config or {}
        config.update(
            {
                "observation_space": gym.spaces.Box(-1.0, 1.0, (5000,)),
                "action_space": gym.spaces.Box(-1.0, 1.0, (5,)),
            }
        )
        super().__init__(config=config)
