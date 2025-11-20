import math
import random
import mesa
from mesa.discrete_space import OrthogonalMooreGrid

from .agent import RandomAgent, ObstacleAgent, TrashAgent, RechargeStationAgent

class RandomModel(mesa.Model):
    """
    Creates a new model with random agents.
    Args:
        num_agents: Number of agents in the simulation
        height, width: The size of the grid to model
    """
    def __init__(self, num_agents=10, width=8, height=8, seed=42, percentage_dirty=20, percentage_obstacles=10, max_time=500):

        super().__init__(seed=seed)
        self.num_agents = num_agents
        self.seed = seed
        self.width = width
        self.height = height 
        self.steps = 0
        self.max_time = max_time
        self.running = True

        self.grid = OrthogonalMooreGrid([width, height], capacity = math.inf, torus=False)

        self.datacollector = mesa.DataCollector(
            {
                "Battery": lambda m: m.average_battery(),
                "Percentage Clean": lambda m: m.percentage_clean(),
                "Time": lambda m: m.max_time - m.steps,
                "Total Movements": lambda m: sum(a.steps_taken for a in m.agents if isinstance(a, RandomAgent))
            }
        )
        
        # Identify the coordinates of the border of the grid
        border = [(x,y)
                  for y in range(height)
                  for x in range(width)
                  if y in [0, height-1] or x in [0, width - 1]]

         # Create the border cells
        for x, y in border:
            ObstacleAgent(self, cell=self.grid[x, y])

        # Calculate number of obstacles and trash based on percentages
        total_cells = width * height
        border_cells = len(border)
        available_cells = total_cells - border_cells
        
        num_obstacles = int(available_cells * (percentage_obstacles / 100))
        num_trash = int(available_cells * (percentage_dirty / 100))

        # Initialize random obstacles (excluding border cells)
        empty_cells = [cell for cell in self.grid.empties.cells if cell.coordinate not in border]
        obstacle_cells = random.sample(empty_cells, min(num_obstacles, len(empty_cells)))
        for cell in obstacle_cells:
            ObstacleAgent(self, cell=cell)

        # Initialize random trash cells
        empty_cells = [cell for cell in self.grid.empties.cells]
        trash_cells = random.sample(empty_cells, min(num_trash, len(empty_cells)))
        for cell in trash_cells:
            TrashAgent(self, cell=cell)

        # Initialize recharge stations at specific or random positions
        if self.num_agents == 1:
            # For single agent, start at position (1, 1)
            start_cell = self.grid[1, 1]
            # If cell is occupied, remove occupants (except border)
            if not start_cell.is_empty:
                agents_to_remove = [a for a in start_cell.agents if not isinstance(a, ObstacleAgent)]
                for agent in agents_to_remove:
                    agent.remove()
            recharge_positions = [start_cell]
            RechargeStationAgent(self, cell=start_cell)
        else:
            # For multiple agents, random positions
            empty_cells = [cell for cell in self.grid.empties.cells]
            recharge_positions = random.sample(empty_cells, min(self.num_agents, len(empty_cells)))
            for cell in recharge_positions:
                RechargeStationAgent(self, cell=cell)

        # Initialize random agents at the recharge station positions
        for i, cell in enumerate(recharge_positions):
            RandomAgent(self, cell=cell)

        self.datacollector.collect(self)

    def step(self):
        '''Advance the model by one step.'''
        self.steps += 1
        self.agents.shuffle_do("step")
        
        # Check if we should stop
        if self.steps >= self.max_time or self.all_clean():
            self.running = False
            
        self.datacollector.collect(self)
    
    def count_clean_cells(self):
        """Count cells that don't have trash."""
        trash_cells = len([a for a in self.agents if isinstance(a, TrashAgent)])
        total_cells = self.grid.width * self.grid.height
        all_obstacles = len([a for a in self.agents if isinstance(a, ObstacleAgent)])
        cleanable_cells = total_cells - all_obstacles  
        clean_cells = cleanable_cells - trash_cells
        return clean_cells
    
    def percentage_clean(self):
        """Calculate the percentage of clean cells."""
        total_cells = self.grid.width * self.grid.height
        border_cells = 2 * (self.width + self.height) - 4
        obstacle_cells = len([a for a in self.agents if isinstance(a, ObstacleAgent)]) - border_cells
        cleanable_cells = total_cells - border_cells - obstacle_cells
        
        if cleanable_cells == 0:
            return 100

            
        clean_cells = self.count_clean_cells()
        clean_percentage = (clean_cells / cleanable_cells) * 100
        #print( f"Clean Cells: {clean_cells}, Cleanable Cells: {cleanable_cells}, Percentage Clean: {clean_percentage}%")
        return clean_percentage
    
    def all_clean(self):
        """Check if all cells are clean."""
        return len([a for a in self.agents if isinstance(a, TrashAgent)]) == 0
    
    def average_battery(self):
        """Calculate the average battery level of all agents."""
        batteries = [a._battery for a in self.agents if isinstance(a, RandomAgent)]
        if batteries:
            return sum(batteries) / len(batteries)
        return 0