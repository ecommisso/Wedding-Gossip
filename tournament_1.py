import argparse
from wedding_gossip import WeddingGossip
import pandas as pd

if __name__ == '__main__':
    
    seeds = [2, 3]
    turns = [10, 30, 60, 120, 180, 360]

    parser = argparse.ArgumentParser()
    parser.add_argument("--teams", "-teams", default=[1,2], nargs="+", help="Helper Text")
    parser.add_argument("--seed", "-s", default=2, help="Seed")
    parser.add_argument("--scale", "-sc", default=9, help="Scale")
    parser.add_argument("--turns", "-T", default=1440, help="Number of turns")
    parser.add_argument("--gui", "-g", default="False", help="GUI")
    parser.add_argument("--interval", "-i", default=1, help="GUI")
    args = parser.parse_args()

    # configuration 1
    # 21 runs
    # df = pd.DataFrame(columns=["Run", "Seed", "Turns", "Team 1", "Team 2", "Team 3", "Team 4", "Team 5", "Team 6", "Group Score"])
    # df.to_csv("config_1.csv")
    # run = 1
    # for seed in seeds:
    #     for turn in turns:
    #         try:
    #             print(run, seed, turn)
    #             args.teams=[1, 2, 3, 4, 5, 6]
    #             args.seed=seed
    #             args.turns=turn
    #             args.scale=10
    #             args.gui="False"
    #             args.interval=1
    #             args.run=run
    #             wedding_game = WeddingGossip(args)

    #             row = [run, seed, turn]

    #             results = wedding_game.get_results()
    #             print(results)
    #             team_scores = list(results["team_scores"].values())
    #             print(team_scores)
    #             row.extend(team_scores)
    #             group_score = results["group_score"]
    #             row.append(group_score)
    #             df = pd.DataFrame([row], columns=["Run", "Seed", "Turns", "Team 1", "Team 2", "Team 3", "Team 4", "Team 5", "Team 6", "Group Score"])
    #             df.to_csv("config_1.csv", mode='a', header=False)
    #         except:
    #             row = [run, seed, turn, 'Error', 'Error', 'Error', 'Error', 'Error', 'Error', 'Error']
    #             df = pd.DataFrame([row], columns=["Run", "Seed", "Turns", "Team 1", "Team 2", "Team 3", "Team 4", "Team 5", "Team 6", "Group Score"])
    #             df.to_csv("config_1.csv", mode='a', header=False)
    #         run += 1

    turns = [1440]

    # configuration 4
    # 105 runs
    run = 1
    groups = [[1, 2], [1, 3], [1, 4], [1, 6],
              [2, 3], [2, 4], [2, 6],
              [3, 4], [3, 6], [4, 6]]
    run = 1
    df = pd.DataFrame(columns=["Run", "Seed", "Turns", "Team Number", "Team Score", "Group Score"])
    df.to_csv("config_4.csv")
    for seed in [3]:
        for turn in turns:
            for group in groups:
                try:
                    print(run, seed, turn, group)
                    args.teams=group
                    args.seed=seed
                    args.turns=turn
                    args.scale=10
                    args.gui="False"
                    args.interval=1
                    args.run=run
                    wedding_game = WeddingGossip(args)

                    results = wedding_game.get_results()
                    team_scores = list(results["team_scores"].values())
                    group_score = results["group_score"]
                    print(team_scores)
                    row1 = [run, seed, turn, group[0], team_scores[0], group_score]
                    row2 = [run, seed, turn, group[1], team_scores[1], group_score]
                    df = pd.DataFrame([row1, row2], columns=["Run", "Seed", "Turns", "Team Number", "Team Score", "Group Score"])
                    df.to_csv("config_4.csv", mode='a', header=False)
                except:
                    row = [run, seed, turn, 'Error', 'Error', 'Error']
                    df = pd.DataFrame([row], columns=["Run", "Seed", "Turns", "Team Number", "Team Score", "Group Score"])
                    df.to_csv("config_4.csv", mode='a', header=False)
                run += 1