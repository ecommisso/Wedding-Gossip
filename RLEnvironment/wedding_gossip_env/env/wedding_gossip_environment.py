import random
import functools
from copy import copy
import numpy as np

from gymnasium.spaces import MultiDiscrete

from pettingzoo import ParallelEnv
from pettingzoo.utils import agent_selector, wrappers
from pettingzoo.test import parallel_api_test
from collections import defaultdict

# Action Constants
LISTEN_L = 0
LISTEN_R = 1
TALK_L = 2
TALK_R = 3
MOVE = 4
# Observation Constants (0-3 same as action)
NONE = 4

# Reward Params
EXPLORE = 1

# Truncation condition
N_TURNS = 2048

class WeddingGossipEnvironment(ParallelEnv):
    metadata = {"render_modes": ["human"], 
                "name": "wedding_gossip_environment_v3"}

    def __init__(self, render_mode=None):
        self.possible_agents = ["player_" + str(r) for r in range(90)]
        self.agents = copy(self.possible_agents)

        # optional: a mapping between agent name and player_ID
        self.agent_name_mapping = dict(
            zip(self.possible_agents, 
                list(range(len(self.possible_agents)))
               )
        )
        self.render_mode = render_mode
        
        """
            obs = [[curr_goss, curr_turn] + [is_neighbor, pid, action] * 100 * 3 (memory buffer)
        """
        self.observation_spaces = dict(
            zip(
                self.agents,
                [
                    MultiDiscrete(np.array([90, 2049] + [3, 91, 5] * 100 * 3))
                ]
                * 90,
            )
        )

        """
            action = [action, switch_goss, share]
        """
        self.action_spaces = dict(
            zip(
                self.agents,
                [
                    MultiDiscrete(np.array([5, 3, 5]))
                ]
                * 90,
            )
        )

    def reset(self, seed=None, options=None):
        """
        Reset needs to initialize the `agents` attribute and must set up the
        environment so that render(), and step() can be called without issues.
        Here it initializes the `num_moves` variable which counts the number of
        hands that are played.
        Returns the observations for each agent
        """
        self.timestep = 0

        self.agents = copy(self.possible_agents)

        # a hash mapping player_ids to where they are situated on the board
        # each player_id is mapped to a number from 0-99. 
        # table_num = value % 10 (0-9)
        # seat_num = value / 10 (0-9)
        self.pos = random.sample(range(100), k=90)
        # update the self.seating list - 100 size list based on pos
        self.seating = None
        self._init_seating()

        self.obs_actions = [4 for _ in range(100)] 

        self.agent_gossips = [[] for _ in range(90)]
        self.gossip_idx = [0 for _ in range(90)]

        # distribute gossip
        gossip = random.sample(range(90), 90)
        for i, a in enumerate(self.agents):
            aid = self.agent_name_mapping[a]
            self.agent_gossips[aid].append(gossip[i])

        self.mem_buf = np.array([0, 90, 4] * 200)
        self.pos_mem = [(None, None) for _ in range(90)] 

        self.state = self._get_curr_state()

        observations = {}
        for i, a in enumerate(self.agents):
            observations[a] = self._get_agent_obs(i)

        # Get dummy infos. Necessary for proper parallel_to_aec conversion
        infos = {a: {} for a in self.agents}

        self._update_memory()

        #self.render()
        #print(observations["player_0"][:2])
        #for i in range(10):
        #    print(observations["player_0"][2+i*3*10:2+(i+1)*3*10])

        return observations, infos

    def step(self, actions):
        """
        step(action) takes in an action for each agent and should return the
        - observations
        - rewards
        - terminations
        - truncations
        - infos
        dicts where each dict looks like {agent_1: item_1, agent_2: item_2}
        """
        # If a user passes in actions with no agents, then just return empty observations, etc.
        if not actions:
            self.agents = []
            return {}, {}, {}, {}, {}

        self.timestep += 1

        rewards = {}

        # check switch gossip (noop, inc, dec)
        for agent, action in actions.items():
            aid = self.agent_name_mapping[agent]
            i = self.gossip_idx[aid]
            if action[1] == 1:
                self.gossip_idx[aid] = min(len(self.agent_gossips[aid]) - 1, i + 1)
            elif action[1] == 2:
                self.gossip_idx[aid] = max(0, i - 1)
        
        self.obs_actions = [4 for _ in range(100)]
        feedback = [[] for _ in range(90)]
        moves = []

        # process listens -> talk -> move in order
        for agent, action in sorted(actions.items(), key=(lambda x: x[1][0])):
            # get action 
            act = action[0]
            aid = self.agent_name_mapping[agent]

            self.obs_actions[self.pos[aid]] = act

            rewards[agent] = 0

            # listen
            if act < 2:
                neighbors = self._get_left_neighbors(self.pos[aid]) if act == 0 else \
                            self._get_right_neighbors(self.pos[aid])

                possible_gossips = []
                for n in neighbors:
                    n_act = actions["player_" + str(n)][0]
                    n_goss = self.agent_gossips[n][self.gossip_idx[n]]
                    complement = 2 if act == 1 else 3
                    if n_act == complement:
                        if n_goss in self.agent_gossips[aid]:
                            feedback[n].append(False)
                        else:
                            possible_gossips.append((n_goss, n))

                heard, nbr = max(possible_gossips) if possible_gossips else (-1, None)
                if heard >= 0:
                    i = 0
                    while i < len(self.agent_gossips[aid]) and self.agent_gossips[aid][i] > heard:
                        i += 1
                    self.agent_gossips[aid].insert(i, heard)
                    self.gossip_idx[aid] = min(self.gossip_idx[aid], i)
                    
                    share = actions["player_" + str(nbr)][2]
                    rewards[agent] += self._get_listen_reward(heard, share)

                for g, nbr in possible_gossips:
                    feedback[nbr].append((g == heard))
            # talk 
            elif act < 4:
                goss = self.agent_gossips[aid][self.gossip_idx[aid]]
                for f in feedback[aid]:
                    share = actions[agent][2]
                    r = self._get_talk_reward(goss, share)
                    rewards[agent] += r if f else -r
            # move
            else:
                move_choice_order = random.sample(range(10), 10)
                moves.append((aid, move_choice_order))

        self.available = self._get_available_seats()

        # resolve moves
        random.shuffle(moves)
        for aid, pref in moves:
            if self._move_player(aid, pref):
                rewards["player_" + str(aid)] += EXPLORE 

        self.state = self._get_curr_state()

        observations = {}
        for a in self.agents:
            aid = self.agent_name_mapping[a]
            observations[a] = self._get_agent_obs(aid)

        # Check termination conditions
        terminations = {agent: False for agent in self.agents}

        # Check truncation conditions (overwrites termination conditions)
        truncations = {a: (self.timestep > N_TURNS) for a in self.agents}

        # Exit condition
        if any(terminations.values()) or all(truncations.values()):
            infos = {a: {"terminal_observation": observations} for a in self.agents}
            self.agents = []
        else:
            infos = {a: {} for a in self.agents}

        self._update_memory()

        #self.render()
        #print("curr")
        #print(observations["player_0"][:2])
        #for i in range(10):
        #    print(observations["player_0"][2+i*3*10:2+(i+1)*3*10])
        #print("prev")
        #for i in range(10,20):
        #    print(observations["player_0"][2+i*3*10:2+(i+1)*3*10])
        #print("prev2")
        #for i in range(20,30):
        #    print(observations["player_0"][2+i*3*10:2+(i+1)*3*10])
#
        return observations, rewards, terminations, truncations, infos

    def render(self):
        print("===== SEATING / MOVES =====")
        print(f"Turn {self.timestep}")
        for i in range(10):
            table = []
            for j in range(i*10,(i+1)*10):
                player = self.seating[j]
                move = self.obs_actions[player]
                table.append((player, move))
            print(f'Table {i}: {table}')
        print("===== GOSSIP INVENTORY =====")
        for i, g in enumerate(self.agent_gossips):
            print(f"Player {i}: {g}")
    
    def close(self):
        pass

    @functools.lru_cache(maxsize=None)
    def observation_space(self, agent):
        """
            array([seating, gossip, table actions])
        """
        return self.observation_spaces[agent]

    @functools.lru_cache(maxsize=None)
    def action_space(self, agent):
        """
            array([action, gossip, seat1, seat2])
        """
        return self.action_spaces[agent]

    def _update_memory(self):
        self.mem_buf = np.concatenate((self.state, self.mem_buf[:300]))
        for i in range(90):
            self.pos_mem[i] = self.pos[i], self.pos_mem[i][0]

    def _get_curr_state(self):
        state = np.array([], dtype=np.int64)
        for i in range(100):
            seat_state = [0, self.seating[i], self.obs_actions[i]]
            state = np.concatenate((state, seat_state))

        return state

    def _get_listen_reward(self, gossip, share):
        share_ratio = .1 + .2 * share
        return (gossip + 1) / 10 * share_ratio

    def _get_talk_reward(self, gossip, share):
        share_ratio = .1 + .2 * share
        return (gossip + 1) / 10 * (1 - share_ratio)

    def _get_agent_obs(self, aid):
        obs = np.concatenate((
            [self.agent_gossips[aid][self.gossip_idx[aid]]],
            [self.timestep],
            self.state,
            self.mem_buf
        ))
        # set is_neighbor bit
        hist = self.pos[aid], self.pos_mem[aid][0], self.pos_mem[aid][0]
        for i, p in enumerate(hist):
            if p:
                for nbr in range(1,4):
                    lnbr = (p // 10 * 10) + ((p - nbr) % 10)
                    rnbr = (p // 10 * 10) + ((p + nbr) % 10)
                    obs[2 + lnbr * 3 + i * 300] = 1
                    obs[2 + rnbr * 3 + i * 300] = 1

                obs[2 + p * 3 + i * 300] = 2

        return obs

    def _get_available_seats(self):
        """
            A function that looks at self.pos, and returns a tuple of size 10 containing the available seats.
        """
        return list(set(range(100)).difference(set(self.pos)))

    def _init_seating(self):
        # a function to create and update the self.seating list - 100 size list. 90 represents empty seat!
        self.seating = [90 for _ in range(100)]
        for pid, seat in enumerate(self.pos):
            self.seating[seat] = pid

    def _get_left_neighbors(self, seat_id, _count=3):
        if _count > 9:
            print("CANT HAVE MORE THAN 9 LEFT NEIGHBORS!")
        
        neighbor_ids = []
        for i in range(1, _count+1):
            curr_seat_id = (seat_id // 10 * 10) + ((seat_id - i) % 10)
            if self.seating[curr_seat_id] < 90:
                neighbor_ids.append(self.seating[curr_seat_id])
        return neighbor_ids

    def _get_right_neighbors(self, seat_id, _count=3):
        if _count > 9:
            print("CANT HAVE MORE THAN 9 RIGHT NEIGHBORS!")
        
        neighbor_ids = []
        for i in range(1, _count+1):
            curr_seat_id = (seat_id // 10 * 10) + ((seat_id + i) % 10)
            if self.seating[curr_seat_id] < 90:
                neighbor_ids.append(self.seating[curr_seat_id])
        return neighbor_ids

    def _move_player(self, aid, priority_list):
        curr_seat = self.pos[aid]

        if len(priority_list) > 10:
            return False 

        for move in priority_list:
            new_seat = self.available[move]
            # check if new position is occupied
            if self.seating[new_seat] == 90:
                # move player from old position to new position
                self.seating[curr_seat] = 90 
                self.seating[new_seat] = aid

                # update player
                self.pos[aid] = new_seat 

                return True

        return False 

if __name__ == "__main__":
    env = WeddingGossipEnvironment()
    parallel_api_test(env, num_cycles=1_000)
