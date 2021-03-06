from . import BaseAgent
from .. import characters
from ..constants import *
import numpy as np
import ctypes
import time
import sys

class DortmundAgent(BaseAgent):
    """Parent abstract Agent."""
    turn_times = []

    def __init__(self, character=characters.Bomber):
        self._character = character
        self.avg_simsteps_per_turns = []

    def __getattr__(self, attr):
        return getattr(self._character, attr)

    def act(self, obs, action_space):

        #for attr in ['alive', 'board', 'bomb_life', 'bomb_blast_strength', 'position', 'blast_strength', 'can_kick', 'teammate', 'ammo', 'enemies']:
        #    print(attr, type(obs[attr]), obs[attr])
        #    if 'numpy' in str(type(obs[attr])):
        #        print(' ', obs[attr].dtype)

        
        #print(obs['enemies'][0].__dict__) is sent to cpp, because only contains enum ids?
        #print(obs['position'][0])
        #print(type(obs['position'][0]))
        start_time = time.time()
        decision = self.c.c_getStep_dortmund(
            self.id,
            Item.Agent0.value in obs['alive'], Item.Agent1.value in obs['alive'], Item.Agent2.value in obs['alive'], Item.Agent3.value in obs['alive'],
            obs['board'].ctypes.data_as(ctypes.POINTER(ctypes.c_uint8)), 
            obs['bomb_life'].ctypes.data_as(ctypes.POINTER(ctypes.c_double)), 
            obs['bomb_blast_strength'].ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
            int(obs['position'][0]), int(obs['position'][1]),
            obs['blast_strength'],
            obs['can_kick'],
            obs['ammo'],
            obs['teammate'].value
            )
        self.turn_times.append(time.time() - start_time)

        return decision
        

    def episode_end(self, reward):
        """This is called at the end of the episode to let the agent know that
        the episode has ended and what is the reward.

        Args:
          reward: The single reward scalar to this agent.
        """
        self.c.c_episode_end_dortmund.restype = ctypes.c_float
        avg_simsteps_per_turn = self.c.c_episode_end_dortmund(self.id)
        self.avg_simsteps_per_turns.append(avg_simsteps_per_turn)

    def init_agent(self, id, game_type):
        self.id = id
        self._character = self._character(id, game_type)

        if sys.platform == "win32":
            self.c = ctypes.cdll.LoadLibrary("build/Release/munchen.dll")
            # self.c = ctypes.cdll.LoadLibrary("build/Debug/munchen.dll")
        else:
            self.c = ctypes.cdll.LoadLibrary("/opt/work/pommerman_cpp/cmake-build-debug/libmunchen.so")

        self.c.c_init_agent_dortmund(id)

    @staticmethod
    def has_user_input():
        return False

    def shutdown(self):
        turn_times_np = np.array(self.turn_times)
        print("dortmund shutdown, avg simsteps per turns: ", np.round(np.array(self.avg_simsteps_per_turns).mean())/1000.0, " k",
              ", avg time: ", np.round(turn_times_np.mean()*1000, 1), " ms",
              ", max time: ", np.round(turn_times_np.max()*1000, 1), " ms",
              ", overtime: ", np.round((turn_times_np > 0.099).sum() / turn_times_np.shape[0] *100, 1), ' %')