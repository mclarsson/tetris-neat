import board
import pickle
from pyswarm import pso

def min_func(w):
    b = board.Board(20, 10)
    b.start();
    result = b.play_with_network(net=None, weights=w)
    return 1 / result

if __name__ == '__main__':
    # Lower and upper bounds, last value is bias
    lb = [-5, -5, -5, -5, -5, -5, -5]
    ub = [ 5,  5,  5,  5,  5,  5,  5]
    xopt, fopt = pso(min_func, lb, ub, debug=True, swarmsize=15, maxiter=5)

    print("Winner found:")
    print("Max score: " + str(round(1 / fopt)))
    print(xopt)

    with open("winner_swarm", "wb") as f:
        pickle.dump(xopt, f)
