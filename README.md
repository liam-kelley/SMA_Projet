# SMA_Projet

Implementing the game of PILLARS as a Multi-Agent System, and implementing MANUAL (human-controlled), RANDOM, REACTIVE, and UTILITARIAN AI for the agents.

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
Acting first next turn will give him the most options to choose from.

## A generic "Turn":

TODO

## Setup and running the model

Clone the repository.

Libraries needed: TODO

Possible model options: TODO

How to change grid_size: TODO

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

## Different AI implemented:
