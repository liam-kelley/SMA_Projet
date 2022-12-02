import mesa
import matplotlib.pyplot as plt
import numpy as np

from game_model import GameModel

def get_object_portrayal(agent):
    '''Gets each agent's portrayal method.'''
    return (agent.portrayal_method())

def run_single_server(grid_size, num_gamers_per_team, max_pillar_height):
    '''Setup and run server'''
    grid = mesa.visualization.CanvasGrid(get_object_portrayal, grid_size[0], grid_size[1], 500, 500)
    # chart = mesa.visualization.ChartModule([{}],
    #                     data_collector_name='datacollector')
    server = mesa.visualization.ModularServer(
        GameModel, [grid], "Game Model",
        {"num_gamers_per_team": num_gamers_per_team, "width": grid_size[0], "height": grid_size[1], "max_pillar_height": max_pillar_height} # Model parameters
    )
    server.port = 8521  # The default
    server.launch()

if __name__ == "__main__":
    # run_single_server(grid_size = [7,7], num_gamers_per_team=3, max_pillar_height=7)
    run_single_server(grid_size = [5,5], num_gamers_per_team=2, max_pillar_height=7)