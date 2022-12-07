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

def tuple_dist(tuple_a,tuple_b):
    return(diff(tuple_a[0],tuple_b[0]) + diff(tuple_a[1],tuple_b[1]))

def closest_cells_to_target(cell_list, target_cell):
    '''
    from list of tuples and target, returns list closest tuples to target tuple.
    Warning! pops first element of original cell_list.
    '''
    try:
        assert(cell_list)
    except(AssertionError):
        return None
    closest_cells=[cell_list.pop(0)]
    min_dist= tuple_dist(closest_cells[0],target_cell)
    for cell in cell_list:
        dist= tuple_dist(cell,target_cell)
        if dist < min_dist :
            closest_cells = [cell]
            min_dist = dist
        elif dist == min_dist:
            closest_cells.append(cell)
    return(closest_cells)

class Color(Enum):
    RED = enum.auto(),
    BLUE = enum.auto()

class AI(Enum):
    RANDOM = enum.auto()
    REACTIVE = enum.auto()
    UTILITY = enum.auto()

class Card(Enum):
    MOVE = enum.auto(),
    BUILD_PILLAR = enum.auto()

class Message:
    """
    Messages are sent by gamer agents to the team.message_pile.
    They can then be read by other agents for them to have their desires accomodated.
    There are two possible types of desires:
    - an agent can desire to obtain a card.
    - or an agent can desire to stay as first initiave.
    """
    def __init__(self, sender_id, desire_card=None, desire_first_initiative=False, importance=1):
        self.sender_id=sender_id
        self.desire_card=desire_card
        self.desire_first_initiative=desire_first_initiative
        self.importance=importance
        # self.intention=


class Team:
    """
    The Team class manages the decks which are common to all agents of a given team.
    The team class also manages team messages and team initiative.
    The agents belonging to a team are all represented in its initiative queue.
    """
    def __init__(self,color=Color.RED,hand_size=3,ai="RANDOM", player=False):
        self.color=color
        self.hand_size=hand_size
        self.deck=[] #list of cards
        self.hand=[] #list of cards
        self.discard=[] #list of cards
        if ai == "RANDOM" : self.ai = AI.RANDOM
        if ai == "REACTIVE" : self.ai = AI.REACTIVE
        if ai == "UTILITY" : self.ai = AI.UTILITY
        self.player = player
        self.message_pile=[] #pile of Messages
        self.initiative_queue=[] # Queue of agents
    
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

    def discard_card(self,card):
        self.discard.append(card)
        self.hand.remove(card)

    def clear_messages_from_pile(self, agent_id=None):
        if agent_id!=None:
            messages_to_remove=[]
            for message in self.message_pile:
                if message.sender_id == agent_id :
                    messages_to_remove.append(message)
            for message in messages_to_remove:
                self.message_pile.remove(message)
        else:
            self.message_pile=[]
    
    def move_agent_to_first_initiative(self,agent):
        self.initiative_queue.remove(agent)
        self.initiative_queue.insert(0,agent)


class PillarAgent(mesa.Agent):
    """
    A pillar "agent".
    Has a height ranging from 0 to self.model.max_pillar_height -1 except the center pillar which has a height of max_pillar_height.
    A pillar must be an agent to be visualized in mesa.
    Pillars aren't scheduled in the scheduler.
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
    """
    A gamer agent. There are multiple GamerAgents per team.
    They each act in turn according to their (unique) initiative.
    Initiave 0 acts first, then initiative 1, then 2 ...
    A gamer agent stands on pillars of varying heights.

    A GamerAgent must stand on top on the highest center pillar for his team to win.
    To do that, it can take move_actions, build_pillar_actions, change its initiative, and send intention and desire messages to its teammates.
    It can't just choose which action it takes though.

    Each team has a deck of cards. This deck is initialized with (num_gamers_per_team) MOVE cards and (num_gamers_per_team) BUILD_PILLAR cards.
    The team will draw a hand of (num_gamers_per_team) cards.
    So for 3 players, a hand can look like: Card.MOVE * 3, or Card.MOVE * 2 + Card.BUILD_PILLAR, or Card.MOVE + Card.BUILD_PILLAR * 2, or Card.BUILD_PILLAR * 3

    When each GamerAgent takes his step, he must choose a card from the remaining cards in the hand.
    So in our example, the 1st acting gamerAgent has 3 cards to choose from, the 2nd acting gamerAgent has 2 cards to choose from,
    and the 3rd only has one card to choose from.

    With his chosen_card, the GamerAgent can either:
    -use the card's corresponding action (move_action to a nearby cell, build_pillar_action on a nearby cell)
    -or NOT use the corresponding action and instead change his initiative to 0 (first) to play first on the next "turn".
    
    Whatever he does with his card, the agent can then send out messages on his team's message_pile.
    Maybe next turn he needs a specific card so the others shouldn't use them, or maybe he really wants to go
    first next turn and would rather no one else NOT use their card after him, robbing him of his first/0 initiave.

    As of right now, two possible AI's are coded, neither of them making use of messages or using initiative intelligently, or trying to block the enemy team.

    AI.RANDOM uses a random card, and uses the corresponding action randomly.
    If the corresponding card cannot be played (no space to build or move), it changes its initiative.

    AI.REACTIVE always tries to get higher, or builds to get higher, and avoids moving lower.
    Changes its initiative only to avoid getting lower or blocking itself by building.
    """

    def __init__(self, unique_id, model,team=Team(Color.RED)):
        super().__init__(unique_id, model)
        self.team = team
        self.height = 0
        self.initiative = 0

    def __lt__(self, other):
        '''
        Overloading/Creating a less than operator between two gamer agents.
        This is to sort them according to their initiave using python's sort().
        This isn't currently used.
        '''
        return(self.initiative < other.initiative)
    
    def get_allies(self):
        allies = [agent for agent in self.model.schedule.agents if agent.team == self.team]
        return (allies)
    
    def get_foes(self):
        foes = [agent for agent in self.model.schedule.agents if agent.team != self.team]
        return (foes)

    def update_height(self):
        '''Updates current height from the pillar the agent is standing on.'''
        self.height = self.model.pillars[self.pos[0]][self.pos[1]].height

    def update_initiative(self):
        '''Updates current initiative from the team's initiative queue'''
        self.initiative=self.team.initiative_queue.index(self)

    def move_action(self, cell, test=False, raise_errors=False):
        '''
        Basic agent action which corresponds to moving the agent to a cell.
        Usually, an agent cannot move into a cell if there already is an agent in the cell,
        or if the vertical (height) distance to the cell is higher than 1.

        cell is a (x,y) tuple.
        You can set the 'test' parameter to True to test if this action can be made or not.
        You can set the 'raise_errors' parameter to True to raise_errors.
        '''
        cell_content=self.model.grid.grid[cell[0]][cell[1]]
        if not any(isinstance(agent,GamerAgent) for agent in cell_content): # Si il n'y a pas un agent dans la cell
            if diff(self.height, self.model.pillars[cell[0]][cell[1]].height) <= 1: # et si le pillier correspondant est à une distance inférieure à 1
                if not test : self.model.grid.move_agent(self, cell)
                return(True)
            if raise_errors: raise(Exception("Pillar is too far away."))
        if raise_errors: raise(Exception("There is already an agent in this cell."))
        return(False)
    
    def build_pillar_action(self, cell, test=False, raise_errors=False):
        '''
        Basic agent action which corresponds to building up a pillar in a cell.
        Usually, an agent cannot build up a pillar in a cell if there already is an agent in the cell,
        or if the pillar would be built higher than self.model.max_pillar_height-1.
        (Only the center pillar is of max_pillar height.)
        
        cell is a (x,y) tuple.
        You can set the 'test' parameter to True to test if this action can be made or not.
        You can set the 'raise_errors' parameter to True to raise_errors
        '''
        cell_content=self.model.grid.grid[cell[0]][cell[1]]
        if not any(isinstance(agent,GamerAgent) for agent in cell_content): # Si il n'y a pas un agent dans la cell
            if self.model.pillars[cell[0]][cell[1]].height<self.model.max_pillar_height-1: #On ne peut pas construire un pillier plus haut que max_pillar_height-1
                if not test : self.model.pillars[cell[0]][cell[1]].height+=1
                return(True)
            if raise_errors: raise(Exception("Pillar is too tall to build up."))
        if raise_errors: raise(Exception("There is an agent in this cell."))
        return(False)
    
    def debuild_pillar(self, cell):
        self.model.pillars[cell[0]][cell[1]].height-=1

    def use_card_as_initiative_setter(self):
        self.team.move_agent_to_first_initiative(self)

    def print_current_status(self):
        print("STATUS - ", end="")
        print("Team: ", self.team.color, end=" ")
        print("Agent: " + str(self.unique_id), end=" ")
        print("Current hand: ", end=" ")
        for card in self.team.hand:
            print(card, end=" , ")
        print("")

    def clear_own_previous_messages(self):
        '''To not read own messages before reading messages.'''
        self.team.clear_messages_from_pile(self.unique_id)

    def ask_for_card(self,desired_card,importance=0):
        message=Message(sender_id=self.unique_id, desire_card=desired_card, importance=importance)
        self.team.message_pile.append(message)

    def ask_for_first_initiative(self,importance=0):
        message=Message(sender_id=self.unique_id, desire_first_initiative=True, importance=importance)
        self.team.message_pile.append(message)

    def check_win_condition(self):
        self.update_height()
        if self.height==self.model.max_pillar_height:
            self.model.running=False

    def random_move(self):
        '''
        This function finds the neighboring available cells where the player can move
        aka where (no other agents and pillar height distance <=1) 
        and then moves there if there is an available option.

        If there are no available options, it sets initiative to 0 instead.
        '''
        neighborhood_cells = self.model.grid.get_neighborhood(self.pos,moore=False, include_center=False) # Moore = avec diagonales. 
        available_moves = []
        for cell in neighborhood_cells: # Les "cell" retournées sont des tuples de pos.
            if self.move_action(cell, test=True):
                available_moves.append(cell)
        try:
            cell = self.random.choice(available_moves)
            self.move_action(cell)
        except IndexError:
            print("I can't move! No available cells.")
            self.use_card_as_initiative_setter()

    def random_build_pillar(self):
        '''
        This function finds the neighboring available cells where a pillar can be built
        aka where (no other agents + not too high) 
        and then builds there if there is an available option.

        If there are no available options, it sets initiative to 0 instead.
        '''
        neighborhood_cells = self.model.grid.get_neighborhood(self.pos,moore=False, include_center=False) # Moore = avec diagonales. 
        available_cells = []
        for cell in neighborhood_cells: # Les "cell" retournées sont des tuples de pos.
            if self.build_pillar_action(cell, test=True):
                available_cells.append(cell)
        try:
            cell = self.random.choice(available_cells)
            self.build_pillar_action(cell)
        except(IndexError):
            print("I can't build! No available cells.")
            self.use_card_as_initiative_setter()

    def random_AI(self):
        '''
        Random AI.
        Chooses a random card to play, and plays it randomly.
        If the card cannot be played, it sets its initiave to 0.
        '''
        chosen_card=self.random.choice(self.team.hand)
        if chosen_card==Card.MOVE:
            self.random_move()
        elif chosen_card==Card.BUILD_PILLAR:
            self.random_build_pillar()
        return(chosen_card)
    
    def player(self):
        '''
        Human player.
        Overrides second blue AI if player option is active.
        Chooses an action between move and build, as well as the intended cell.
        If no card can be played, set initiative to 0.
        '''
        nb_build = self.team.hand.count(Card.BUILD_PILLAR)
        nb_move = self.team.hand.count(Card.MOVE)
        
        blocked = True
        
        neighborhood_cells = self.model.grid.get_neighborhood(self.pos,moore=False, include_center=False)
        for cell in neighborhood_cells:
            if ((Card.BUILD_PILLAR in self.team.hand and self.build_pillar_action(cell, test=True)) or 
                    (Card.MOVE in self.team.hand and self.move_action(cell, test=True))):
                blocked = False
        
        if blocked == False:
        # get the command from the player
            while True:
                    
                print("There are {} move cards and {} build cards left in your hand".format(nb_move, nb_build))
                print("Your current pawn is on column", self.pos[0]+1, "and line", self.model.grid.height - self.pos[1],".")
                # get the command from user
                try:
                    action, direction = str(input("Enter your action with format (move/build) + (up/down/left/right), or (no action) to play first in the next round: ")).split()
                except :
                    print("Invalid command, enter a chain of characters.\n")
                    continue
                else:
                    # command kill loop to exit the program
                    if (action.lower() == "kill" and direction.lower() == "loop") : exit()
                    # choose to set initiative to zero
                    if (action.lower() == "no" and direction.lower() == "action") : 
                        self.use_card_as_initiative_setter()
                        while True:
                            try:
                                print("There are {} move cards and {} build cards left in your hand".format(nb_move, nb_build))
                                to_discard = str(input("Choose which action to discard (move or build) :"))
                            except :
                                print("Invalid command, enter a chain of characters.\n")
                                continue
                            else:
                                if to_discard.lower() == "move" and nb_move > 0:
                                    return Card.MOVE
                                elif to_discard.lower() == "build" and nb_build > 0:
                                    return Card.BUILD_PILLAR
                                print("Invalid command, you must choose between available cards.\n")
                        
                    # if invalid set of commands
                    if(not action.lower() in ["move", "build"] or not direction.lower() in ["up", "down", "left", "right"]):
                        print("Invalid command, enter command with the given format.\n")
                        continue
                    if direction.lower() == "up": intended_cell = (self.pos[0], self.pos[1]+1)
                    elif direction.lower() == "down": intended_cell = (self.pos[0], self.pos[1]-1)
                    elif direction.lower() == "left": intended_cell = (self.pos[0]-1, self.pos[1])
                    else : intended_cell = (self.pos[0]+1, self.pos[1])
                    
                    # if given cell out of bounds
                    if self.model.grid.out_of_bounds(intended_cell) :
                        print("Invalid command, cell out of bounds.\n")
                        continue
                    
                    # check that the action is a possible card in the team's hand and that the action is doable
                    if action.lower() == "build" and Card.BUILD_PILLAR in self.team.hand and self.build_pillar_action(intended_cell, test=True) :
                        self.build_pillar_action(intended_cell, test=False)
                        return Card.BUILD_PILLAR
                    elif action.lower() == "move" and Card.MOVE in self.team.hand and self.move_action(intended_cell, test=True) :
                        self.move_action(intended_cell, test=False)
                        return Card.MOVE
                    print("Invalid command, you can't do this action !\n")
                    
        print("You pawn can't do anything for this turn and must play first in the next round.\n")
        self.use_card_as_initiative_setter()
        return(self.random.choice(self.team.hand))

    def count_height(self, t="default"):
        if t == "foes" : team = self.get_foes()
        else : team = self.get_allies()
        return (sum([agent.height for agent in team]))
    
    def count_advantageaous_cells(self, t="default"):
        advantageous_cells=[]
        if t == "foes" : team = self.get_foes()
        else : team = self.get_allies()
        for agent in team:
            neighborhood_cells = self.model.grid.get_neighborhood(agent.pos,moore=False, include_center=False)
            for cell in neighborhood_cells:
                if agent.move_action(cell, test=True) and self.model.pillars[cell[0]][cell[1]].height - agent.height == 1 and cell not in advantageous_cells: 
                    advantageous_cells.append(cell)
        return len(advantageous_cells)
    
    def count_upgradable_cells(self, t="default"):
        upgradable_cells=[]
        if t == "foes" : team = self.get_foes()
        else : team = self.get_allies()
        for agent in team:
            neighborhood_cells = self.model.grid.get_neighborhood(agent.pos,moore=False, include_center=False)
            for cell in neighborhood_cells:
                if agent.build_pillar_action(cell, test=True) and self.model.pillars[cell[0]][cell[1]].height - agent.height == 0 and cell not in upgradable_cells: 
                    upgradable_cells.append(cell)
        return len(upgradable_cells)    
    
    def distance_center(self):
        return (abs(self.pos[0] - self.model.grid.width//2) + abs(self.pos[1] - self.model.grid.height//2))
    
    def count_blocking_cells(self, t="default"):
        blocking_cells=[]
        if t == "foes" : team = self.get_foes()
        else : team = self.get_allies()
        for agent in team:
            neighborhood_cells = self.model.grid.get_neighborhood(agent.pos,moore=False, include_center=False)
            for cell in neighborhood_cells:
                if not agent.move_action(cell, test=True) and cell not in blocking_cells: 
                    blocking_cells.append(cell)
        return len(blocking_cells)        
    
    def utility(self, w_height_A=3, w_height_F=1, w_adv_A=3, w_adv_F=1, w_upgrade_A=3, w_upgrade_F=1,
                    w_center_A=1, w_block_A=1, w_block_F=1):
        return (w_height_A * self.count_height() - w_height_F * self.count_height(t = "foes")
                + w_adv_A * self.count_advantageaous_cells() - w_adv_F * self.count_advantageaous_cells(t = "foes")
                + w_upgrade_A * self.count_upgradable_cells() - w_upgrade_F * self.count_upgradable_cells(t = "foes")
                - w_center_A * self.distance_center()
                - w_block_A * self.count_blocking_cells() + w_block_F * self.count_blocking_cells(t = "foes")
                )
    
    def utility_AI(self):
        '''
        Reacts according to a utility function, designed to maximise allies' height, the number of cells that
        enable to move up, the number of cells that can be upgraded, minimise the number of unreachable cells and
        the distance to the center (vice-versa with these features for the opponents)
        '''
        
        neighborhood_cells = self.model.grid.get_neighborhood(self.pos,moore=False, include_center=False)
        best_utility = float('-inf')
        best_cell = neighborhood_cells[0]
        best_action = "move"
        
        for cell in neighborhood_cells:
            cell_tmp = (self.pos[0], self.pos[1])
            print("CURR CELL:", cell_tmp)
            print("NEIG CELL:", cell)
            if self.move_action(cell, test=True):
                self.move_action(cell, raise_errors=True)
                utility = self.utility()
                if utility > best_utility : 
                    best_utility = utility
                    best_cell = cell
                    best_action = "move"
                print("JE SUIS EN ", cell , "ET JAI UNE HAUTEUR", self.height)
                print("CA BOUGE EN :", cell_tmp)
                self.move_action(cell_tmp, raise_errors=True)
            if self.build_pillar_action(cell, test=True):
                self.build_pillar_action(cell, raise_errors=True)
                utility = self.utility()
                if utility > best_utility : 
                    best_utility = utility
                    best_cell = cell
                    best_action = "build"
                self.debuild_pillar(cell)
                
        if best_utility < -10:
            chosen_card = self.random.choice(self.team.hand)
            self.use_card_as_initiative_setter()
        elif best_action == "move" and Card.MOVE in self.team.hand:
            chosen_card = Card.MOVE
            self.move_action(best_cell, raise_errors=True)
        elif best_action =="build" and Card.BUILD_PILLAR in self.team.hand:
            chosen_card = Card.BUILD_PILLAR
            self.build_pillar_action(best_cell, raise_errors=True)
        else :
            chosen_card = self.random.choice(self.team.hand)
            self.use_card_as_initiative_setter() 
            
        return(chosen_card)       
                
    def reactive_AI(self):
        '''
        Always tries to get higher, or builds to get higher, and avoids moving lower.
        Doesn't necessarily try to get to the middle of the board.
        '''
        chosen_card=None

        neighborhood_cells = self.model.grid.get_neighborhood(self.pos,moore=False, include_center=False)
        center_cell = (self.model.grid.width//2, self.model.grid.height//2)

        advantageous_cells=[]
        for cell in neighborhood_cells:
            if self.move_action(cell, test=True) and self.model.pillars[cell[0]][cell[1]].height - self.height == 1: 
                advantageous_cells.append(cell)

        upgradable_cells=[]
        for cell in neighborhood_cells:
            if self.build_pillar_action(cell, test=True) and (self.model.pillars[cell[0]][cell[1]].height - self.height == 0): 
                upgradable_cells.append(cell)

        lower_cells=[]
        for cell in neighborhood_cells:
            if self.build_pillar_action(cell, test=True) and (self.model.pillars[cell[0]][cell[1]].height - self.height < 0): 
                lower_cells.append(cell)

        same_level_cells=[]
        for cell in neighborhood_cells:
            if self.move_action(cell, test=True) and (self.model.pillars[cell[0]][cell[1]].height - self.height == 0): 
                same_level_cells.append(cell)

        try:
            if advantageous_cells and Card.MOVE in self.team.hand : # First check if there is any pillar you can move up upon.
                chosen_card = Card.MOVE
                cell = self.random.choice(closest_cells_to_target(advantageous_cells, center_cell))
                self.move_action(cell,raise_errors=True)
            elif upgradable_cells and Card.BUILD_PILLAR in self.team.hand : # Then check if you can make a pillar to move up upon.
                chosen_card = Card.BUILD_PILLAR
                cell = self.random.choice(closest_cells_to_target(upgradable_cells, center_cell))
                self.build_pillar_action(cell,raise_errors=True)
            elif lower_cells and Card.BUILD_PILLAR in self.team.hand : # Then check if there are any pillars to build which won't block you.
                chosen_card = Card.BUILD_PILLAR
                cell = self.random.choice(closest_cells_to_target(lower_cells, center_cell))
                self.build_pillar_action(cell,raise_errors=True)
            elif same_level_cells and Card.MOVE in self.team.hand : # Then check if you can move horizontally to another pillar.
                chosen_card = Card.MOVE
                cell = self.random.choice(closest_cells_to_target(same_level_cells, center_cell))
                self.move_action(cell,raise_errors=True)
            else: # Then instead of moving down, or building anywhere that would block the agent, choose to use card as an initiative_setter.
                chosen_card = self.random.choice(self.team.hand)
                self.use_card_as_initiative_setter()
        except Exception as e:
            print("EXCEPTION! ", e)
        
        return(chosen_card)

    def step(self):
        self.update_height()
        self.update_initiative() #initiative has no practical purpose, but it could be used by an AI as additionnal info idk.
        self.clear_own_previous_messages()

        if len(self.team.hand) ==0 : self.team.draw_new_hand()

        self.print_current_status()

        chosen_card=None
        if self.team.player == True : chosen_card=self.player()
        elif self.team.ai==AI.RANDOM: chosen_card=self.random_AI()        
        elif self.team.ai==AI.REACTIVE: chosen_card=self.reactive_AI()
        elif self.team.ai==AI.UTILITY: chosen_card=self.utility_AI()

        self.team.discard_card(chosen_card)
        self.check_win_condition()

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

    def __init__(self, num_gamers_per_team, width, height, player, AI1_behaviour, AI2_behaviour, max_pillar_height=7):
        self.grid = mesa.space.MultiGrid(width, height, False)
        self.schedule = mesa.time.BaseScheduler(self) # Sequential scheduler.
        self.running = True
        self.player = player
        self.AI1_behaviour = AI1_behaviour
        self.AI2_behaviour = AI2_behaviour
        self.num_gamers_per_team = num_gamers_per_team
        self.max_pillar_height=max_pillar_height
        self.teams=self.init_teams(AIs=[AI1_behaviour, AI2_behaviour], player=player)
        self.pillars=self.init_pillars()
        self.init_gamerAgents()
        
        self.datacollector = mesa.DataCollector(
            model_reporters={},
            agent_reporters={}
        )

    def init_teams(self, player, AIs=["RANDOM", "REACTIVE"]):
        '''Initialize Teams, team decks, and team hands.'''
        if player :
            teams=[Team(Color.RED , hand_size=self.num_gamers_per_team, ai=AIs[0]),
                Team(Color.BLUE, hand_size=self.num_gamers_per_team, ai=None, player = True)]
        else :
            teams=[Team(Color.RED , hand_size=self.num_gamers_per_team, ai=AIs[0]),
               Team(Color.BLUE, hand_size=self.num_gamers_per_team, ai=AIs[1])]
        for team in teams:
            #Initialize team decks
            for _ in range(team.hand_size):
                team.deck.append(Card.MOVE)
                team.deck.append(Card.BUILD_PILLAR)
            random.shuffle(team.deck)
            #Initialize team hands
            for _ in range(team.hand_size): #hand size is equal to the number of players per team.
                team.hand.append(team.deck.pop())
        return(teams)

    def init_pillars(self):
        '''
        Initialize Pillars as agents and initialize pillar list.
        There is one pillar per cell.
        All pillars are of height 0, except the central pillar which is of max height.
        '''
        pillars=np.zeros((self.grid.width,self.grid.height),dtype=int).tolist()
        grid_length=self.grid.width*self.grid.height
        for unique_id in range(grid_length): # In mesa, we must add each pillar as agents to the grid to visualize them.
            pillar = PillarAgent(unique_id, self,height=0)
            # Pillars aren't activated, they don't do anything, so they aren't scheduled.

            # Add the Pillar Agent to each grid cell
            x = unique_id%self.grid.width
            y = unique_id//self.grid.width
            self.grid.place_agent(pillar, (x,y))
            pillars[x][y]=pillar
        # Init central pillar    
        pillars[self.grid.width//2][self.grid.height//2].height=self.max_pillar_height
        return(pillars)

    def init_gamerAgents(self):
        '''Initialize gamers and team initiave_queues'''
        grid_length=self.grid.width*self.grid.height
        for i in range(self.num_gamers_per_team*2):
            unique_id=i+grid_length # each pillar already has a unique id, so we must give different unique ids to the gamer agents.
            
            team=self.teams[i%2] # un agent est ajouté à chaque équipe tour à tour.

            agent = GamerAgent(unique_id, self,team)
            team.initiative_queue.append(agent)
            self.schedule.add(agent)

            # Add the GamerAgent to a random unoccupied grid cell
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            while len(self.grid.grid[x][y])!=1 or self.grid.grid[x][y][0].height != 0: #Check that only a pillar is there and that that pillar is of height 0
                x = self.random.randrange(self.grid.width)
                y = self.random.randrange(self.grid.height)
            self.grid.place_agent(agent, (x, y))

    def update_initiatives(self):
        '''
        Firstly remove all agents from the scheduler.
        Then add them back in the order the initiative queue dictates.
        So that way, the first agent in each team's initiative queue will act first in turn,
        then the second, then the third...
        '''
        for team in self.teams:
            for agent in team.initiative_queue:
                self.schedule.remove(agent)
        for i in range(self.num_gamers_per_team):
            for team in self.teams: # un agent est ajouté à chaque équipe tour à tour.
                agent=team.initiative_queue[i]
                self.schedule.add(agent)
    
    def step(self):
        """Advance the model by one step."""
        self.datacollector.collect(self)
        self.update_initiatives()
        self.schedule.step()
