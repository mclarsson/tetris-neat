import sys
import pickle
import visualize
import matplotlib.pyplot as plt
import matplotlib
import neat
import collections
import os
import re
from itertools import zip_longest

def pgfplotsplot(xs, ys, lab):
    coords = " ".join("({},{})".format(x, y) for x, y in zip(xs, ys))
    print(r"\addplot coordinates {{{}}}; \addlegendentry{{{}}}".format(coords, lab))

def main():
    try:
        ind = sys.argv.index("--", 1)
    except ValueError:
        ind = len(sys.argv)

    files = sys.argv[1:ind]
    names = sys.argv[ind+1:]
    colors = collections.deque(["b", "r", "g", "c", "m", "y", "k"])

    # full_frame(4.7747, 3.5)
    plt.figure(figsize=(4.7747, 3.5))

    for f, n in zip_longest(files, names):
        with open(f, "rb") as ff:
            _winner, stats = pickle.load(ff)

        generation = range(1, len(stats.most_fit_genomes) + 1)
        best_fitness = [c.fitness for c in stats.most_fit_genomes]
        avg_fitness = stats.get_fitness_mean()

        col = colors[0]
        colors.rotate(-1)

        if n is None:
            lab = os.path.basename(f)
            lab = ",".join(re.sub(r"[A-Z]", lambda x: "_" + x[0].lower(), s) for s in lab.split("_"))
        else:
            lab = n

        pgfplotsplot(generation, best_fitness, lab)
        # plt.plot(generation, best_fitness, col + '-', label=lab)
        # plt.plot(generation, avg_fitness, col + '--')

    # plt.title("Average and best fitnesses")
    plt.xlabel("Generations")
    plt.ylabel("Fitness")
    plt.grid()
    # plt.legend(loc="best")
    # plt.gca().set_yscale('symlog')
    # plt.axhline(y=1000000, color="r", linestyle=":")

    # plt.show()
    # plt.savefig("exported.pgf", transparent=True, pad_inches=0, bbox_inches="tight")

def main_plot_single():
    if len(sys.argv) != 2:
        print("invalid usage")
        exit(1)

    with open(sys.argv[1], "rb") as f:
        winner, stats = pickle.load(f)

    config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                         neat.DefaultSpeciesSet, neat.DefaultStagnation,
                         "config-feedforward")
    node_names = {
        -1: 'landing_height',
        -2: 'rows_eliminated',
        -3: 'row_trans',
        -4: 'col_trans',
        -5: 'holes',
        -6: 'wells',
        0:  'output'
    }
    visualize.draw_net(config, winner, True, node_names=node_names)
    # visualize.plot_stats(stats, ylog=False, view=True, filename=None)

if __name__ == "__main__":
   main_plot_single()
