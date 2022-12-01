import mesa
import enum
from enum import Enum
import numpy as np
import random

def rgb_to_hex(r,g,b):
    return('#%02x%02x%02x' % (r,g,b))

def clamp(x, minimum, maximum ):
    return(min(max(x,minimum), maximum))

def diff(a,b):
    return(abs(a-b))

class Color(Enum):
    RED = enum.auto(),
    BLUE = enum.auto()

class AI(Enum):
    RANDOM = enum.auto()
    REACTIVE = enum.auto()

class Card(Enum):
    MOVE = enum.auto(),
    BUILD_PILLAR = enum.auto()

class Team:
    """
    The Team class manages the decks which are common to all agents of a given team.
    The team class currently has no information on which agents are on which team.
    """
    def __init__(self,color=Color.RED,hand_size=3,ai=AI.RANDOM):
        self.color=color
        self.hand_size=hand_size
        self.deck=[] #list of cards
        self.hand=[] #list of cards
        self.discard=[] #list of cards
        self.ai=ai #can be : [AI.RANDOM]
    
    def shuffle_deck_from_discard(self):
        print("Team ", self.color, " is shuffling their deck from their discard pile!")
        while len(self.discard) != 0:
            self.deck.append(self.discard.pop())
        random.shuffle(self.deck)

    def draw_new_hand(self):
        print("Team ", self.color, " is drawing a new hand from their deck!")
        while len(self.hand) < self.hand_size:
            if len(self.deck) == 0:
                self.shuffle_deck_from_discard()
            else:
                self.hand.append(self.deck.pop())

    def add_new_card_to_deck(self,card):
        self.deck.append(card)
    
    def get_unique_cards_from_hand(self):
        unique_cards=[]
        for card in self.hand:
            if card not in unique_cards:
                unique_cards.append(card)
        return(unique_cards)

class PillarAgent(mesa.Agent):
    """
    A pillar agent. Has a height ranging from 0 to self.model.max_pillar_height
    A pillar must be an agent to be visualized in mesa.
    Pillars aren't scheduled.
    """

    def __init__(self, unique_id, model,height):
        super().__init__(unique_id, model)
        self.height=height

    def step(self):
        print("Hi, I am pillar " + str(self.unique_id) + ".")

    def height_to_hex(self):
        max_pillar_height=self.model.max_pillar_height
        clamped_height=clamp(self.height, 0, max_pillar_height)
        reverse_height=max_pillar_height-clamped_height
        shade=(reverse_height*255)//max_pillar_height
        return(rgb_to_hex(shade,shade,shade))

    def portrayal_method(self):
        portrayal = {"Shape": "rect",
                     "Filled": "true",
                     "w": 0.7,
                     "h": 0.7,
                     "Layer": 0,
                     "Color": self.height_to_hex()}

        return portrayal

class GamerAgent(mesa.Agent):
    """A game agent. Has a team."""

    def __init__(self, unique_id, model,team=Team(Color.RED),initiative=0):
        super().__init__(unique_id, model)
        self.team = team
        self.height = 0
        self.initiative = initiative

    def update_height(self):
        self.height = self.model.pillars[self.pos[0]][self.pos[1]].height

    def move(self, cell, test=False, raise_errors=False):
        '''
        Action which corresponds to the basic Card.MOVE card.
        You can set the 'test' variable to True to test if this action can be made or not.
        '''
        cell_content=self.model.grid.grid[cell[0]][cell[1]]
        if not any(isinstance(agent,GamerAgent) for agent in cell_content): # Si il n'y a pas un agent dans la cell
            if diff(self.height, self.model.pillars[cell[0]][cell[1]].height) <= 1: # et si le pillier correspondant est à une distance inférieure à 1
                if not test : self.model.grid.move_agent(self, cell)
                return(True)
            if raise_errors: raise(Exception("Pillar is too far away."))
        if raise_errors: raise(Exception("There is already an agent in this cell."))
        return(False)
    
    def build_pillar(self, cell, test=False, raise_errors=False):
        '''
        Action which corresponds to the basic Card.BUILD_PILLAR card.
        You can set the 'test' variable to True to test if this action can be made or not.
        '''
        cell_content=self.model.grid.grid[cell[0]][cell[1]]
        if not any(isinstance(agent,GamerAgent) for agent in cell_content): # Si il n'y a pas un agent dans la cell
            if self.model.pillars[cell[0]][cell[1]].height<self.model.max_pillar_height-1: #On ne peut pas construire un pillier plus haut que max_pillar_height-1
                if not test : self.model.pillars[cell[0]][cell[1]].height+=1
                return(True)
            if raise_errors: raise(Exception("Pillar is too tall to build up."))
        if raise_errors: raise(Exception("There is an agent in this cell."))
        return(False)

    def random_move(self):
        '''
        This function finds the neighboring available cells (no other agents and pillar height distance <=1) where the player can move,
        and then moves there if there is an available option.
        '''
        neighborhood_cells = self.model.grid.get_neighborhood(self.pos,moore=False, include_center=False) # Moore = avec diagonales. 
        available_moves = []
        for cell in neighborhood_cells: # Les "cell" retournées sont des tuples de pos.
            if self.move(cell, test=True):
                available_moves.append(cell)
        try:
            cell = self.random.choice(available_moves)
            self.move(cell)
        except IndexError: print("I can't move! No available cells.")

    def random_build_pillar(self):
        '''
        This function finds the neighboring available cells (no other agents + not too high) where a pillar can be built,
        and then builds there if there is an available option.
        '''
        neighborhood_cells = self.model.grid.get_neighborhood(self.pos,moore=False, include_center=False) # Moore = avec diagonales. 
        available_cells = []
        for cell in neighborhood_cells: # Les "cell" retournées sont des tuples de pos.
            if self.build_pillar(cell, test=True):
                available_cells.append(cell)
        try:
            cell = self.random.choice(available_cells)
            self.build_pillar(cell)
        except(IndexError): print("I can't build! No available cells.")
       
    def get_nearby_empty_cells_with_a_x_higher_pillar(self,x):
        neighborhood_cells = self.model.grid.get_neighborhood(self.pos,moore=False, include_center=False) # Moore = avec diagonales. 
        available_cells = []
        for cell in neighborhood_cells: # Les "cell" retournées sont des tuples de pos. 
            cell_content=self.model.grid.grid[cell[0]][cell[1]] # On lit leur contenu.
            if not any(isinstance(agent,GamerAgent) for agent in cell_content): # Si il n'y a pas un agent dans la cell à coté
                if self.model.pillars[cell[0]][cell[1]].height - self.height == x: # et Si le pillier d'à coté est à une distance inférieure 
                    available_cells.append(cell)
        return(available_cells)

    def step(self):
        print("GamerAgent: " + str(self.unique_id) + "| Team: ", self.team.color , end="| ")

        self.update_height()
        if len(self.team.hand) ==0 : self.team.draw_new_hand()
        
        print("Current hand | ", end="")
        for card in self.team.hand:
            print(card, end=" | ")
        print("\n")
        
        # AI START
        chosen_card=None

        if self.team.ai==AI.RANDOM:
            '''
            Random AI.
            Chooses a random card to play, and plays it. (This will sometime make the player do nothing.)
            '''
            chosen_card=self.random.choice(self.team.hand)
            if chosen_card==Card.MOVE:
                self.random_move()
            elif chosen_card==Card.BUILD_PILLAR:
                self.random_build_pillar()
                
        if self.team.ai==AI.REACTIVE:
            '''
            Purely Reactive AI. Previously known as AI.GOTTA_STAY_HIGH.
            Always tries to get higher, or builds to get higher, and avoids moving lower.
            '''
            neighborhood_cells = self.model.grid.get_neighborhood(self.pos,moore=False, include_center=False)

            advantageous_cells=[]
            for cell in neighborhood_cells:
                if self.move(cell, test=True) and self.model.pillars[cell[0]][cell[1]].height - self.height == 1: 
                    advantageous_cells.append(cell)

            upgradable_cells=[]
            for cell in neighborhood_cells:
                if self.build_pillar(cell, test=True) and (self.model.pillars[cell[0]][cell[1]].height - self.height == 0): 
                    upgradable_cells.append(cell)

            lower_cells=[]
            for cell in neighborhood_cells:
                if self.build_pillar(cell, test=True) and (self.model.pillars[cell[0]][cell[1]].height - self.height < 0): 
                    lower_cells.append(cell)

            same_level_cells=[]
            for cell in neighborhood_cells:
                if self.move(cell, test=True) and (self.model.pillars[cell[0]][cell[1]].height - self.height == 0): 
                    same_level_cells.append(cell)

            try:
                if advantageous_cells and Card.MOVE in self.team.hand : # First check if there is any pillar you can move up upon.
                    chosen_card = Card.MOVE
                    cell = self.random.choice(advantageous_cells)
                    self.move(cell,raise_errors=True)
                elif upgradable_cells and Card.BUILD_PILLAR in self.team.hand : # Then check if you can make a pillar to move up upon.
                    chosen_card = Card.BUILD_PILLAR
                    cell = self.random.choice(upgradable_cells)
                    self.build_pillar(cell,raise_errors=True)
                elif lower_cells and Card.BUILD_PILLAR in self.team.hand : # Then check if there are any pillars to build which won't block you.
                    chosen_card = Card.BUILD_PILLAR
                    cell = self.random.choice(lower_cells)
                    self.build_pillar(cell,raise_errors=True)
                elif same_level_cells and Card.MOVE in self.team.hand : # Then check if you can move horizontally to another pillar.
                    chosen_card = Card.MOVE
                    cell = self.random.choice(same_level_cells)
                    self.move(cell,raise_errors=True)
                elif Card.MOVE in self.team.hand : # Then try moving anywhere (down).
                    chosen_card = Card.MOVE
                    self.random_move()
                elif Card.BUILD_PILLAR in self.team.hand : # Then try building anywhere (blocking yourself).
                    chosen_card = Card.BUILD_PILLAR
                    self.random_build_pillar()
            except Exception as e:
                print("EXCEPTION! ", e)
        # AI END

        self.team.discard.append(chosen_card)
        self.team.hand.remove(chosen_card)

        self.update_height()
        if self.height==self.model.max_pillar_height:
            self.model.running=False

    def portrayal_method(self):
        portrayal = {"Shape": "circle",
                     "Filled": "true",
                     "r": 0.2,
                     "Layer": 1}
        if self.team.color == Color.RED: portrayal["Color"] = "red"
        else: portrayal["Color"] = "blue"
        return portrayal

class GameModel(mesa.Model):
    """
    The model for the pillar game.
    The game plays on a Grid space.
    Players/"GamerAgents" for each team try and build pillars to reach the top of the center pillar.
    By default the center pillar is of height 7. All other pillars are initialized at height 0.

    Players of a team have access to hand which is shared amongst all team members.
    This hand will have a certain amount of cards in it. These can currently be MOVE or a BUILD_PILLAR cards.
    If a player from the team uses up a card, then that card will become unavailable to the other players until the hand is re-drawn.
    Additionnal cards can be added to each team's deck.

    You can access grid cell content using self.grid.grid[x][y].
    A grid cell will contain a pillar and a certain amount of players (0-1)
    A pillar in a cell will generally be self.grid.grid[x][y][0], but you can directly access the pillar info using self.pillars[x][y].
    """

    def __init__(self, num_gamers_per_team, width, height, max_pillar_height=7):
        self.num_gamers_per_team = num_gamers_per_team
        self.grid = mesa.space.MultiGrid(width, height, False)
        self.schedule = mesa.time.BaseScheduler(self) #Each player will play turn by turn
        self.running = True # This variable enables conditional shut off of the model once a condition is met. (usually for batch run, or win condition)
        self.max_pillar_height=max_pillar_height
        self.pillars=np.zeros((width,height),dtype=int).tolist()

        '''Initialize Teams'''
        self.teams=[Team(Color.RED,hand_size=num_gamers_per_team,ai=AI.RANDOM),
                    # Team(Color.BLUE,hand_size=num_gamers_per_team,ai=AI.RANDOM)]
                    Team(Color.BLUE,hand_size=num_gamers_per_team,ai=AI.REACTIVE)]
        for team in self.teams:
            '''Initialize team decks'''
            for _ in range(team.hand_size):
                team.deck.append(Card.MOVE)
                team.deck.append(Card.BUILD_PILLAR)
            self.random.shuffle(team.deck)
            '''Initialize team hands'''
            for _ in range(team.hand_size): #hand size is equal to the number of players per team.
                team.hand.append(team.deck.pop())

        '''Initialize Pillar list.'''
        grid_length=self.grid.width*self.grid.height
        for unique_id in range(grid_length): # In mesa, we must add each pillar as agents to the grid to visualize them.
            pillar = PillarAgent(unique_id, self,height=0)
            # self.schedule.add(pillar) # Pillars aren't activated, they don't do anything.

            # Add the Pillar Agent to each grid cell
            x = unique_id%self.grid.width
            y = unique_id//self.grid.width
            self.grid.place_agent(pillar, (x,y))
            self.pillars[x][y]=pillar

        self.pillars[width//2][height//2].height=self.max_pillar_height

        '''Initialize gamers'''
        for i in range(self.num_gamers_per_team*2):
            unique_id=i+grid_length
            
            team=self.teams[i%2] # un agent est ajouté à chaque équipe tour à tour.
            initiative=i

            agent = GamerAgent(unique_id, self,team,initiative=initiative)
            self.schedule.add(agent)

            # Add the GamerAgent to a random unoccupied grid cell
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            while len(self.grid.grid[x][y])!=1 or self.grid.grid[x][y][0].height != 0: #Check that only a pillar is there and that that pillar is of height 0
                x = self.random.randrange(self.grid.width)
                y = self.random.randrange(self.grid.height)
            self.grid.place_agent(agent, (x, y))
        
        self.datacollector = mesa.DataCollector(
            model_reporters={},
            agent_reporters={}
        )
    
    def step(self):
        """Advance the model by one step."""
        self.datacollector.collect(self)
        self.schedule.step()