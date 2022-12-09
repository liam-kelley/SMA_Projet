# SMA_Projet

Implementing the game of PILLARS as a Multi-Agent System, and implementing MANUAL (human-controlled), RANDOM, REACTIVE, and UTILITY AI for the agents.

# The game of PILLARS

The game plays on a square Grid space of uneven side length (5, 7, 9...).

There is a pillar in every cell. 
There are multiple GamerAgents per team initialized on the grid at random. They cannot share a cell.

GamerAgents for each team try and build up pillars to climb onto, to eventually reach the top of the center pillar.
The center pillar is always the tallest. All other pillars are initialized at height 0.
The first team to have a GamerAgent reach the top of the center pillar wins.

## How to play

GamerAgents of a team have access to hand of Cards which is shared amongst all GamerAgents of a Team.
This hand will have a (num_gamers_per_team) of cards in it. These can be MOVE or a BUILD_PILLAR cards.
So for 3 players, a hand can look like any of these options:
- Card.MOVE * 3
- Card.MOVE * 2 + Card.BUILD_PILLAR
- Card.MOVE + Card.BUILD_PILLAR * 2
- Card.BUILD_PILLAR * 3

An agent playing one of these cards can either:
- USE the corresponding MOVE or BUILD_PILLAR action.
- or NOT use the corresponding action and become first initiative (more on that later).
Whatever option the GamerAGent chooses to do with his card, he sends this chosen card to his team's discard pile.

When the team's hand is empty, more cards can be drawn from the team's draw pile.
When the draw pile is empty, we shuffle the discard pile back into the draw pile.

## MOVE action and BUILD_PILLAR action.

**MOVE action**
A GamerAgent can only MOVE to adjacent unoccupied cells, and only to a pillar of height +1, +0 or -1 than the pillar he is leaving.
So an agent on pillar height 0 can move to a pillar of height 1, but not 2.
And an agent wanting to get on the center pillar of height 5, must MOVE from a pillar of height 4.

**BUILD_PILLAR**
A GamerAgent can BUILD_PILLAR on ANY unoccupied cell. This increments the cell's pillar height by 1.
So a GamerAgent can change a pillar's height from across the grid from height 2 to 3.
A pillar's height can never be more than the center pillar's height - 1.
So if the center Pillar's height is 5, than any other pillar cannot be taller than 4.

## Initiative

Each team has x number of GamerAgents. They each have a unique initiative ranging from "0" to "number_of_GamerAgents - 1".
On a turn, each team firstly has their GamerAgent which has initiative 0 act.
Then each team has their GamerAgent which has initiative 1 act, and so on.

When a GamerAgent acts, they MAY want to become to become first initiative.
Say steveAgent wants to become first initiative. Here's what happens

Initial state:
Team Blue's Initiative Pile =
- catherineAgent
- liamAgent
- steveAgent
- florianAgent

The new state after steve becomes first initiative:
Team Blue's Initiative Pile =
- steveAgent
- catherineAgent
- liamAgent
- florianAgent

Steve moves first, the others before him move 1 back in the initiative pile.
The remainder of the turn isn't influenced by this, but on the NEXT turn, steve will act first.
Just as long as florian doesn't want to act first too...

**Why would an agent want to play first?** Maybe an agent acts last and DOESN'T have a certain card accessible.
Acting first next turn will give him the most options to choose from. Also, if it CAN'T use the available cards it has, it MUST switch its initiative.

## A generic "Turn":

An agent's turn is divised as such :
- Update the agent's height;
- Update the agent's initiative;
- Clear the agent's own messages; (useless in the end because the messaging function ended up being used for no AI behaviour);
- Draw a new hand for the team if it is empty (the first agent to play in the round should be the one to do that because size_hand == num_agents)
- Choose a card from the hand according to the agent's behaviour and discard it to use its action (or don't use it to play first in the next round);
- Check if this action is a game-winning action.
AI behaviours are described later in this file.

## Setup and running the model

Clone the repository.

**Libraries needed** : Python=3.7, mesa, numpy

**Possible model options** : Mesa's interface can be used to select different options on the board. The number of players in a team, the height of the central pillar, the behaviour used for any of the two AIs and whether or not there is a human playing the game.

**How to change grid_size** : Because the size of the grid cannot be passed as a user settable argument to the game model we need to find another way. The size is thus initialised at the launch of the script after calling the main file, and it will only work if the argument is an odd number that is superior to 5. Passing no argument will initialise size_grid to 5.

# Code Architechture

We use the mesa architecture. The GamerAgents interact within the Model each step according to a specific initiative pattern.

## Enums:

**Color** : Corresponds to team colors. Can be RED or BLUE.

**AI** : Corresponds to what drives each team's agents. Can be RANDOM, REACTIVE, UTILITY.

**Card** : These are the cards that can be in a team's hand, deck, or discard pile. Can be MOVE, or BUILD_PILLAR.

## Classes:

**Message** :
Messages are sent by gamer agents to the team.message_pile.
They can then be read by other agents for them to have their desires accomodated.
There are two possible types of desires:
- an agent can desire to obtain a card.
- or an agent can desire to stay as first initiave.

**Team** :
The Team class manages the decks which are common to all agents of a given team.
The team class also manages team messages and team initiative.
The agents belonging to a team are all represented in its initiative queue.
    
The team class has the following methods:
- shuffle_deck_from_discard(self)
- draw_new_hand(self)
- add_new_card_to_deck(self, card) # this function is currently unused.
- discard_cards()
- clear_messages_from_pile(self, agent_id)
- move_agent_to_first_initiative(self, agent)

**PillarAgent** :
Pillar "agent".
Has a height ranging from 0 to self.model.max_pillar_height -1.
The center pillar is an exception, it has a height of max_pillar_height.

Pillars aren't scheduled in the scheduler because they aren't an agent in an SMA approach.
(This class does inherit mes.Agent, but they aren't agents They must inherit the mesa.Agent class to be visualized in mesa when we aren't changing the javascript visualization library, which we didn't do.)

Their height is converted to a corresponding lightness value for visualizing purposes.

**GamerAgent** :
This represents the main type of agent in the game, the one that is scheduled in the scheduler. Some basic methods are implemented for all AI's behaviours :
- This < sign is overriden to compare two GamerAgents based on their initiative;
- The get_allies() method is used to access the members of an agent's team;
- The get_foes() method is used to access the members of the agent's ennemy team;
- The update_height() method (straightfoward);
- The update_initiative() method (straightfoward);
- The move_action(cell, test, raise_errors) method tests is the target cell is accessible and gets the agent to that cell there if test==False;
- The build_pillar_action(cell, test, raise_errors) method tests if the pillar in the target cell can be upgraded, and upgrades it of test==False;
- The debuild_pillar(cell) method downgrades a pillar, and doesn't require a test because it is always used after upgrading the target pillar;
- The use_card_as_initiative_setter() method calls the move_agent_to_first_initiative(agent) method from the Team class;
- The print_current_status() method prints the team of the current agent, its id and its hand;
- The clear_own_previous_messages() method calls the clear_messages_from_pile(agent_id) method from the Team class;
- The ask_for_card(desired_card,importance=0) method sends a message to the pile with a desired card (not used eventually);
- The ask_for_first_initiative(importance=0) method sends a message to the pile to ask for initiative (not used eventually);
- The check_win_condition() method (straightfoward).

Four specific behaviours are then implemented using their own methods, to determine which action to play for each agent at each turn.

## Different AI implemented:

Here are presented the four behaviours implemented.

**RANDOM AI** : This AI acts totally at random, randomly picking a card from the hand and selecting one of its the agent's nearby cells which it can the card onto. If no cell is available for the chosen card, it will discard it and use it to set its initiative to first for the next round.
This AI usually gets stuck by itself, but sometimes reaches the central pillar, with a little bit of luck.

**REACTIVE AI** : This AI follows this plan :
- If there is a nearby cell which the agent can climb upon and a MOVE card is in the agent's team, the agent will choose this action;
- Else if there is nearby cell of same height as the agent's that can be upgraded and a BUILD_PILLAR card is in the agent's team, the agent will choose it;
- Else if there is a nearby cell of a height lower than the agent's that can be upgraded and a BUILD_PILLAR card is in the agent's team, the agent will choose it;
- Else if there is a nearby cell of same height as the agent's that is reachable and a MOVE card is in the agent's team, the agent will choose this action;
- Else the AI will choose a card at random from the hand and use it to set the agent's initiative to first for the next round.

This AI usually performs well, always reaching the central pillar even if it has to build many unnecessary pillars to the maximum height. It very usually wins against the random behaviour.

**UTILITY AI** : This AI chooses the action according to a utility function which it will maximise. To do so, it determines which actions are possible to do, it  realises them and calculates the utility score from this position. It then reverts back to the initial state and tests the following actions until everything has been tested. It eventually chooses the action that had the best utility score, and realises it if the corresponding card is available in the agent's team's hand. If the best score is too low or if the card is not available, it will discard a card at random to set its initiative to first for the next round.

The utility function is based on the following criteria :
- Maximise the heights of the allies, and minimise those of the ennemies;
- Maximise the number of pillars which an ally can climb upon, and minimise this type of cells for the ennemies;
- Maximise the number of pillars which are the same level as an ally agent, and minimse this type of cells for the ennemies;
- Minimise the number of cells which an ally cannot access, and maximise this type of cell for the ennemies;
- Minimise the ally distance to the central pillar.

Every one of these criteria has its own weight in the utility function, so that it is a linear combination of all these criteria. Unfortunately, because of a lack of time, no batch has been run to test the best weights. As a result, the final behaviour is unsatisfying, unable to access the central pillar and usually ending up doing the same two movements for eternity, or having the agent get stuck by itself. Also the weights are probably not linear, for example we would like the "minimising distance to the center" have more and more impact as the agent climbs up and up.

**PLAYER** : Finally, the behaviour can be controlled by a human player via a command line. One just needs to pass the desired action as (move/build) + (up/down/left/right), or (no action) if one wants to set initiative to first for the next round. The script should check if the desired action is doable and ask until a valid command is given.
**IMPORTANT NOTE: BECAUSE OF THE WHILE TRUE LOOP, THE CTRL+C COMMAND DOESN'T WORK TO KILL THE SCRIPT, BUT ONE CAN DO IT BY ENTERING "KILL LOOP" WHILE ENTERING THE DESIRED ACTION**
