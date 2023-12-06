import argparse
from wedding_gossip import WeddingGossip

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--teams", "-teams", default=[1, 5], nargs="+", help="Helper Text")
    parser.add_argument("--seed", "-s", default=2, help="Seed")
    parser.add_argument("--scale", "-sc", default=9, help="Scale")
    parser.add_argument("--turns", "-T", default=60, help="Number of turns")
    parser.add_argument("--gui", "-g", default="True", help="GUI")
    parser.add_argument("--interval", "-i", default=1, help="GUI")
    args = parser.parse_args()
    # dodgem_game = WeddingGossip(args)

    # dodgem_game = WeddingGossip(args, 2)
    num_seeds = 5
    all_scores = list()
    for random_talk_prob in range(0, 101, 5):  # Adjust the range as needed
        avg_score = 0
        for seed in range(num_seeds):
            # Set the RANDOM_TALK_PROB to the current probability value
            dodgem_game = WeddingGossip(args, seed, random_talk_prob)
            avg_score += dodgem_game.team_1_score

        avg_score /= num_seeds
        all_scores.append((avg_score, random_talk_prob))

    with open("all_turns_60_prob.txt", "w") as f:
        for score in all_scores:
            f.write(f"{score[1]} {score[0]}\n")

    print("Final scores: \n")
    # f.close()