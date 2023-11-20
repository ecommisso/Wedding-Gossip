import random


class Player():
    def __init__(self, id, team_num, table_num, seat_num, unique_gossip, color):
        self.id = id
        self.team_num = team_num
        self.table_num = table_num
        self.seat_num = seat_num
        self.color = color
        self.unique_gossip = unique_gossip
        self.gossip_list = [unique_gossip]
        self.group_score = 0
        self.individual_score = 0

    # At the beginning of a turn, players should be told who is sitting where, so that they can use that info to decide if/where to move

    def observe_before_turn(self, player_positions):
        # TODO: does not seem to have any data?
        pass

    # At the end of a turn, players should be told what everybody at their current table (who was there at the start of the turn)
    # did (i.e., talked/listened in what direction, or moved)

    def observe_after_turn(self, player_actions):
        pass

    def get_action(self):
        # Check if the player has any high-value gossip
        # likelihood of choosing to talk is increased to 60% (compared to 20% for listening and 20% for moving)
        has_high_value_gossip = any(gossip > 70 for gossip in self.gossip_list)

        # If the player has high-value gossip, increase the chance of talking
        if has_high_value_gossip:
            action_type = random.choices(
                population=[0, 1, 2],
                weights=[0.6, 0.2, 0.2],
                k=1
            )[0]
        else:
            action_type = random.randint(0, 2)

        # talk
        if action_type == 0:
            direction = random.choice(['left', 'right'])
            gossip = random.choice(self.gossip_list)
            return 'talk', direction, gossip

        # listen
        elif action_type == 1:
            direction = random.choice(['left', 'right'])
            return 'listen', direction

        # move
        else:
            table1 = random.randint(0, 9)
            seat1 = random.randint(0, 9)

            table2 = random.randint(0, 9)
            while table2 == table1:
                table2 = random.randint(0, 9)

            seat2 = random.randint(0, 9)

            return 'move', [[table1, seat1], [table2, seat2]]

    def feedback(self, feedback):
        pass

    def get_gossip(self, gossip_item, gossip_talker):
        pass
