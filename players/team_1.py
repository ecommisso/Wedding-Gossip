import random

# RANDOM_TALK_PROB = 60
class Player():
    def __init__(self, id, team_num, table_num, seat_num, unique_gossip, color, turns, seed, prob):
        self.id = id
        self.team_num = team_num
        self.table_num = table_num
        self.seat_num = seat_num
        self.color = color
        self.unique_gossip = unique_gossip
        self.gossip_list = [unique_gossip]
        self.group_score = 0
        self.individual_score = 0
        self.turns = turns

        # player to knowledge map
        self.player_gossip_map = {}
        for i in range(90):
            self.player_gossip_map[i] = []

        self.gossip_retire_map = {}
        for i in range(91):
            self.gossip_retire_map[i] = 3

        self.cut_off = 60

        self.turn_counter = 0

        # open seats
        self.open_seats = []

        # game map - (table number, seat number) = player number #-> -1 inserted in place of empty seat
        self.seating_arrangement = {}
        self.recent_gossip_shared = 0

        # record the actions each player is taking at your table
        self.action_counts = {}
        # record the action each player took -- ONLY FOR CURRENT TABLE
        self.previous_action = {}

        self.talk_actions = ['left', 'right']
        self.listen_actions = ['right', 'left']

        self.talk_count = 0
        self.listen_count = 0
        self.move_count = 0

        self.RANDOM_TALK_PROB = prob
        # print("RANDOM TALK PROB: ", self.RANDOM_TALK_PROB)


    # At the beginning of a turn, players should be told who is sitting where, so that they can use that info to decide if/where to move
    # list of thruples: player number, table num, seat num
    def observe_before_turn(self, player_positions):
        # print("JUST UPDATED")
        self.open_seats = []
        self.seating_arrangement = {}
        # populate seating arrangement
        for position in player_positions:
            self.seating_arrangement[(position[1], position[2])] = position[0]

        # update seat_num, table_num
        self.table_num = player_positions[self.id][1]
        self.seat_num = player_positions[self.id][2]

        # find empty seats
        for i in range(10):
            for j in range(10):
                if (i, j) not in self.seating_arrangement.keys():
                    self.seating_arrangement[(i, j)] = -1
                    self.open_seats.append((i, j))

        # print("open seats", self.open_seats)

    # At the end of a turn, players should be told what everybody at their current table (who was there at the start of the turn)
    # did (i.e., talked/listened in what direction, or moved)
    def observe_after_turn(self, player_actions):

        # I think action counts should count the past 3 turns and then be reset

        # we DECREMENT the counter -- so if we see a player's action, we decrement the count

        for player_action in player_actions:
            player, action = player_action

            # if player == 34:
            #     print("player", player, "action", action)

            self.previous_action[player] = action

            act, direction = action

            # dict of dicts
            if player not in self.action_counts:

                count_dict = {"talk": {"right": 2, "left": 2}, "listen": {"right": 2, "left": 2}}

                count_dict[act][direction] -= 1

                self.action_counts[player] = count_dict

            else:
                self.action_counts[player][act][direction] -= 1
        # print("ACTION COUNTS", self.action_counts)
        pass

    def __check_actions_all_zeroes(self):
        # if 22 in self.action_counts.keys():
            # print("CAAZ!!! actions_counts of ", self.id, ": ", self.action_counts[22])
        if self.id in self.action_counts.keys():
            for action in self.action_counts[self.id].keys():
                for direction in self.action_counts[self.id][action].keys():
                    if self.action_counts[self.id][action][direction] > 0:
                        # print("player: ", player, "action: ", action, "direction: ", direction)
                        # print("NAURRRRR: ", self.action_counts[player][action][direction])
                        return False
        # print("AYYYYYUYUYYYYYYYYYYYYYYYYYYYYYYY")
        return True

    def __move_to_empty_seat(self):
        # sort open seats by how crowded they are 3 seats in each direction
        seat_count = {}
        for seat in self.open_seats:
            seat_count[seat] = 0
            for i in range(1, 4):
                target_player = self.seating_arrangement[(seat[0], (seat[1] - i) % 10)]
                if target_player != -1:
                    seat_count[seat] += 1
                target_player = self.seating_arrangement[(seat[0], (seat[1] + i) % 10)]
                if target_player != -1:
                    seat_count[seat] += 1

        sorted_seats = sorted(seat_count.items(), key=lambda x: x[1], reverse=True)

        waitlist = []
        for seat in sorted_seats:
            if seat[0][0] != self.table_num:  # move to a different table
                waitlist.append([seat[0][0], seat[0][1]])

        # print("open seats", self.open_seats)
        # print("waitlist", waitlist)

        return 'move', waitlist

    def get_action(self):
        self.turn_counter += 1

        # direction depends on odd or even turn (see talk/listen dict for mapping)
        direction = self.turn_counter % 2

        # gossip to share if talking this turn
        gossip = self.get_gossip_to_share(direction)

        # if self.turn_counter == self.turns:
        #     print("=======================================")
        #     print("talk count", self.talk_count/self.turns)
        #     print("listen count", self.listen_count/self.turns)
        #     print("move count", self.move_count/self.turns)

        # on the first turn of game, players with high gossip should talk
        if self.turn_counter == 1:

            # at this point, they should only have 1 piece of gossip
            if gossip:
                self.recent_gossip_shared = gossip
                self.talk_count += 1
                return 'talk', self.talk_actions[direction], gossip
            self.listen_count += 1
            return 'listen', self.listen_actions[direction]

        else:
            # need to check the prev actions of the 3 players both to the left and right of me

            # Calculate the range for the seats to the left and right
            left_seats = [(self.seat_num - i) % 10 for i in range(1, 4)]
            right_seats = [(self.seat_num + i) % 10 for i in range(1, 4)]

            # need to map player versus seat versus action!

            players_by_seat = {}
            for table,seat in self.seating_arrangement.keys():
                player = self.seating_arrangement[(table, seat)]
                # print("seating arr player", player)

                # -1 = empty seat at that table
                if player != -1:
                    if table == self.table_num:
                        # print("player", player)
                        # print("self.previous_action[player]", self.previous_action[player])
                        if player in self.previous_action.keys():
                            players_by_seat[seat] = {"id": player, "action": self.previous_action[player]}
                        else:
                            players_by_seat[seat] = {"id": player, "action": ("move", None)}


            # process people to the right
            my_prev_action, my_prev_direction = self.previous_action[self.id]
            opposite_direction = "left" if my_prev_direction == "right" else "right"

            # if self.id == 34:
            #     print("my_prev_action", my_prev_action)
            #     print("my_prev_direction", my_prev_direction)
            #     print(self.action_counts[self.id])

            if my_prev_action == "talk":
                #look in opposite direction
                relevant_seats = right_seats if my_prev_direction == "left" else left_seats
                neighbor_action_counts = self.get_neighbor_action_counts(players_by_seat, relevant_seats)
                listen_count = neighbor_action_counts[0]
                talk_count = neighbor_action_counts[1]

                # print("listen count", listen_count)
                # print("talk count", talk_count)
                # update our dicts based on the actions we saw
                if listen_count == 3:
                    self.action_counts[self.id]["talk"][my_prev_direction] = 0
                # elif self.action_counts[self.id]["talk"]["left"] != 0:
                #     self.action_counts[self.id]["talk"]["left"] -= 1

                # MOVE
                # now check if we should move based on if all actions in self.action_counts go to 0
                if self.__check_actions_all_zeroes():
                    # reset the actions counts to 2
                    self.action_counts[self.id] = {"talk": {"right": 2, "left": 2}, "listen": {"right": 2, "left": 2}}

                    self.move_count += 1
                    return self.__move_to_empty_seat()

                # check the OTHER side because we will have to talk to the RIGHT next turn for this condition
                if (listen_count > 1 and self.action_counts[self.id]["talk"][opposite_direction] > 0) or self.action_counts[self.id]["listen"][my_prev_direction] == 0:

                    rand_prob = random.randint(0, 100)
                    if rand_prob < self.RANDOM_TALK_PROB:
                        self.recent_gossip_shared = gossip
                        self.talk_count += 1
                        return 'talk', self.talk_actions[direction], gossip
                self.listen_count += 1
                return 'listen', self.listen_actions[direction]
            elif my_prev_action == "listen":
                relevant_seats = left_seats if my_prev_direction == "left" else right_seats
                # if self.id == 34:
                #     print("was listen left")
                # look at SAME side
                neighbor_action_counts = self.get_neighbor_action_counts(players_by_seat, relevant_seats)
                listen_count = neighbor_action_counts[0]
                talk_count = neighbor_action_counts[1]

                # update our dicts based on the actions we saw
                if talk_count == 3:
                    self.action_counts[self.id]["listen"][my_prev_direction] = 0
                # elif self.action_counts[self.id]["listen"]["left"] != 0:
                #     self.action_counts[self.id]["listen"]["left"] -= 1

                # MOVE
                # now check if we should move based on if all actions in self.action_counts go to 0
                # print(self.__check_actions_all_zeroes())
                if self.__check_actions_all_zeroes():
                    # reset the actions counts to 2
                    self.action_counts[self.id] = {"talk": {"right": 2, "left": 2}, "listen": {"right": 2, "left": 2}}
                    self.move_count += 1
                    return self.__move_to_empty_seat()
                
                # if self.id == 34:
                #     print("was def listen left")
                # check the SAME side because we will have to talk to the LEFT next turn for this condition
                if (listen_count > 1 and self.action_counts[self.id]["talk"][my_prev_direction] > 0) or self.action_counts[self.id]["listen"][opposite_direction] <= 0:
                    # if self.id == 34:
                    #     print("is now talking in direction: ", self.talk_actions[direction])

                    rand_prob = random.randint(0, 100)
                    if rand_prob < self.RANDOM_TALK_PROB:
                        self.recent_gossip_shared = gossip
                        self.talk_count += 1
                        return 'talk', self.talk_actions[direction], gossip

                # if self.id == 34:
                #     print("is now listening in direction: ", self.listen_actions[direction])
                self.listen_count += 1
                return 'listen', self.listen_actions[direction]
               
    # returns tuple of (listen_count, talk_count) based on neighbors seats
    def get_neighbor_action_counts(self, players_by_seat, seats):
        listen_count = 0
        talk_count = 0

        for seat in seats:
            if seat in players_by_seat.keys():
                their_prev_action, their_prev_direction = players_by_seat[seat]["action"]
                if their_prev_action == "talk":
                    talk_count += 1
                elif their_prev_action == "listen":
                    listen_count += 1

        return listen_count, talk_count

    # random probability code
    # def get_action(self):
    #     if random.random() <= 0.11: # 1/9 (if 10 out of 90 players move)
    #         return self.__move_to_empty_seat()
    #     direction = self.turn_counter % 2
    #     gossip = self.get_gossip_to_share(direction)
    #     if gossip and random.random() <= 0.50:
    #         return 'talk', self.talk_actions[direction], gossip
    #     else:
    #         return 'listen', self.listen_actions[direction]




    # add shared feedback to those player's knowledge base that received it 'Nod Head 12'
    def feedback(self, feedback):
        # feedback of form String + String + player number
        for feed in feedback:
            result = feed.split(' ')
            if result[0] == "Nod" or result[0] == "Shake":
                self.player_gossip_map[int(result[2])].append(self.recent_gossip_shared)
                self.gossip_retire_map[self.recent_gossip_shared] -= 1

    # add learned gossip to our gossip list and to the gossip list of the player we received it from... to be used later
    def get_gossip(self, gossip_item, gossip_talker):
        self.gossip_list.append(gossip_item)
        self.player_gossip_map[gossip_talker].append(gossip_item)

    # share gossip value above threshold value determined by turn count
    # if gossip is not known by at least 2 neighboring players, talk with high value, else talk with max gossip
    # TODO: maybe mess around with how amount of times shared affects distribution instead of random selection
    def get_gossip_to_share(self, direction):
        dif = 27 + ((self.turn_counter // self.cut_off) * 9)
        #ceiling = (1 - ((self.turn_counter // self.cut_off) * .1)) * 90  # start at 100% of 90, then drops to 90% of 90, etc. for top of range
        floor = 90 - dif  # 30% of 90 is 27
        gossip_in_range = [x for x in self.gossip_list if x >= floor]
        gossip_in_range.sort(reverse=True)
        neigh_dir = 1 if direction == 0 else -1
        final_gos_list = list()
        for gos in gossip_in_range:
            known_count = 0
            for i in range(1, 4):
                target_player = self.seating_arrangement[(self.table_num, (self.seat_num - (neigh_dir * i)) % 10)]
                if target_player != -1:
                    if gos in self.player_gossip_map[target_player]:
                        known_count += 1
            if known_count < 3:
                final_gos_list.append(gos)

        # Currently select random gossip within desired range
        if len(final_gos_list) > 0:
            return random.choice(final_gos_list)

        # return max(self.gossip_list)
        return random.choice(self.gossip_list) # GET BETTER SCORES WITH THIS??? test

    # def get_gossip_to_share(self, direction):
    #     potential_gossip = [x for x in self.gossip_list if self.gossip_retire_map[x] > 0]
    #     potential_gossip.sort(reverse=True)
    #     neigh_dir = 1 if direction == 0 else -1
    #     for gos in potential_gossip:
    #         known_count = 0
    #         for i in range(1, 4):
    #             target_player = self.seating_arrangement[(self.table_num, (self.seat_num - (neigh_dir * i)) % 10)]
    #             if target_player != -1:
    #                 if gos in self.player_gossip_map[target_player]:
    #                     known_count += 1
    #         if known_count < 3:
    #             return gos
    #
    #     return max(self.gossip_list)


