import argparse
from wedding_gossip import WeddingGossip

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--teams", "-teams", default=[1, 2], nargs="+", help="Helper Text")
    parser.add_argument("--seed", "-s", default=1, help="Seed")
    parser.add_argument("--scale", "-sc", default=9, help="Scale")
    parser.add_argument("--turns", "-T", default=10, help="Number of turns")
    parser.add_argument("--gui", "-g", default="True", help="GUI")
    parser.add_argument("--interval", "-i", default=1, help="GUI")
    args = parser.parse_args()
    args.run = 1
    wedding_game = WeddingGossip(args)
