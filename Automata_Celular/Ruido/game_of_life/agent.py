# FixedAgent: Immobile agents permanently fixed to cells
from mesa.discrete_space import FixedAgent

class Cell(FixedAgent):
    """Represents a single ALIVE or DEAD cell in the simulation."""

    DEAD = 0
    ALIVE = 1 

    @property
    def x(self):
        return self.cell.coordinate[0]

    @property
    def y(self):
        return self.cell.coordinate[1]

    @property
    def is_alive(self):
        return self.state == self.ALIVE

    @property
    def neighbors(self):
        return self.cell.neighborhood.agents
    
    def __init__(self, model, cell, init_state=DEAD): # Constructor
        """Create a cell, in the given state, at the given x, y position."""
        super().__init__(model) # super = Constructor de la clase padre
        self.cell = cell
        self.pos = cell.coordinate
        self.state = init_state
        self._next_state = None

    def determine_state(self):
        """Compute if the cell will be dead or alive at the next tick based on
        the 3 neighbors above it."""
        
        # Get grid dimensions
        width, height = self.model.grid.dimensions
        
        # Calculate the row above (with wrap-around)
        target_y = (self.y + 1) % height
        
        # Get the 3 neighbors above: left, center, right
        top_neighbors = []
        
        for dx in [-1, 0, 1]:
            target_x = (self.x + dx) % width  # Wrap-around horizontally
            
            # Find the cell at this specific position
            target_cell = self.model.grid._cells[(target_x, target_y)]
            
            # Get the agent in that cell
            if target_cell.agents:
                neighbor = target_cell.agents[0]  # Should be only one agent per cell
                top_neighbors.append(neighbor)
            else:
                print(f"Error: No agent found at ({target_x}, {target_y})")
                return

        # Verify we found exactly 3 neighbors
        if len(top_neighbors) != 3:
            print(f"Error: Cell ({self.x}, {self.y}) has {len(top_neighbors)} top neighbors")
            return
        
        # Get the states of the 3 neighbors (left, center, right)
        states = [neighbor.state for neighbor in top_neighbors]
        
        # Apply the cellular automaton rule (Rule 30, 110, etc.)
        # Current implementation appears to be a custom rule
        if states == [1, 1, 1]:    # 111
            self._next_state = self.DEAD
        elif states == [1, 1, 0]:  # 110
            self._next_state = self.ALIVE
        elif states == [1, 0, 1]:  # 101
            self._next_state = self.DEAD
        elif states == [1, 0, 0]:  # 100
            self._next_state = self.ALIVE
        elif states == [0, 1, 1]:  # 011
            self._next_state = self.ALIVE
        elif states == [0, 1, 0]:  # 010
            self._next_state = self.DEAD
        elif states == [0, 0, 1]:  # 001
            self._next_state = self.ALIVE
        elif states == [0, 0, 0]:  # 000
            self._next_state = self.DEAD

    def assume_state(self):
        """Set the state to the new computed state."""
        self.state = self._next_state