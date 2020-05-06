"""
2-input XOR example -- this is most likely the simplest possible example.
"""

from __future__ import print_function
import os
import neat
import visualize
import board
import itertools
import pickle
import random

# 2-input XOR inputs and expected outputs.
xor_inputs = [(0.0, 0.0), (0.0, 1.0), (1.0, 0.0), (1.0, 1.0)]
xor_outputs = [   (0.0,),     (1.0,),     (1.0,),     (0.0,)]


def eval_genomes(genome, config):
    net = neat.nn.FeedForwardNetwork.create(genome, config)
    # r = random.Random(12)
    b = board.Board(20, 10)
    fit = 0
    for _ in range(1):
        b.start()
        fit += float(b.play_with_network(net))
    return fit / 1

def run(config_file):
    # Load configuration.
    config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                         neat.DefaultSpeciesSet, neat.DefaultStagnation,
                         config_file)

    # Create the population, which is the top-level object for a NEAT run.
    p = neat.Population(config)

    # Add a stdout reporter to show progress in the terminal.
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)
    # p.add_reporter(neat.Checkpointer(5))

    # Run for up to 300 generations.
    para = neat.parallel.ParallelEvaluator(6, eval_genomes)
    winner = p.run(para.evaluate, 25)

    # with open("winner", "rb") as f:
    #     winner = pickle.load(f)

    # Display the winning genome.
    print('\nBest genome:\n{!s}'.format(winner))

    with open("winner", "wb") as f:
        pickle.dump(winner, f)

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
    visualize.plot_stats(stats, ylog=False, view=True)
    visualize.plot_species(stats, view=True)

if __name__ == '__main__':
    # Determine path to configuration file. This path manipulation is
    # here so that the script will run successfully regardless of the
    # current working directory.
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'config-feedforward')
    run(config_path)
