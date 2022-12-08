import mesa
from mesa.visualization.ModularVisualization import VisualizationElement, ModularServer, UserSettableParameter
from mesa.visualization.modules import ChartModule
from mesa.datacollection import DataCollector
import matplotlib.pyplot as plt
import numpy as np
import sys

from game_model import GameModel

def get_object_portrayal(agent):
    '''Gets each agent's portrayal method.'''
    return (agent.portrayal_method())

def run_single_server(grid_size=5):
    '''Setup and run server'''
    chart = ChartModule([{"Label": ""}])
    
    grid = mesa.visualization.CanvasGrid(get_object_portrayal, grid_size, grid_size, 500, 500)
    # chart = mesa.visualization.ChartModule([{}],
    #                     data_collector_name='datacollector')
    server = mesa.visualization.ModularServer(
        GameModel, [grid], "Game Model",
        {"num_gamers_per_team": UserSettableParameter('slider', "Number of mates per team", 2, 1, 5, 1),
         "max_pillar_height": UserSettableParameter('slider', "Height of the central pillar", 7, 4, 10, 1),
         "width": grid_size,
         "height": grid_size,
         "AI1_behaviour" : UserSettableParameter('choice', 'Red AI behaviour', value='RANDOM',
                                          choices=["RANDOM", "REACTIVE", "UTILITY"]),
         "AI2_behaviour" : UserSettableParameter('choice', 'Blue AI behaviour', value='RANDOM',
                                          choices=['RANDOM', 'REACTIVE', 'UTILITY']),
         "player" : UserSettableParameter('checkbox', 'Human player ? (BLUE)', value=False),
         } # Model parameters
    )
    server.port = 8521  # The default
    server.launch()

if __name__ == "__main__":
    # run_single_server(grid_size = [7,7], num_gamers_per_team=3, max_pillar_height=7)
    try:
        if int(sys.argv[1]) % 2 == 1 and int(sys.argv[1]) >= 5 : run_single_server(int(sys.argv[1]))
        else : print("Grid size must be >= 5 and an even number. Try again.")
    except:
        print("Either no grid size given or incorrect call of the main function.")
        print("Script will me launched with grid size 5.")
        run_single_server()