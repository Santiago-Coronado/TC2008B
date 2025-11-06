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
        """Compute if the cell will be dead or alive at the next tick.  This is
        based on the number of alive or dead neighbors.  The state is not
        changed here, but is just computed and stored in self._nextState,
        because our current state may still be necessary for our neighbors
        to calculate their next state.
        """
        if self.y == 49:
            return  # Top row isnt affected

        # Search 3 top neighbors
        target_y = self.y + 1
        top_neighbors = []

        # Search in specific order: left, center, right
        for dx in [-1, 0, 1]:
            target_x = (self.x + dx) % 50  # % wrap-around

            # Search for the neighbor at the specific position
            neighbor = None
            for n in self.neighbors:
                if n.x == target_x and n.y == target_y:
                    neighbor = n
                    break
            
            if neighbor:
                top_neighbors.append(neighbor)
            else:
                print(f"Error: No se encontró vecino en ({target_x}, {target_y}) para celda ({self.x}, {self.y})")
                return

        # Check that there are exactly 3 neighbors
        if len(top_neighbors) != 3:
            print(f"Error: Celda ({self.x}, {self.y}) tiene {len(top_neighbors)} vecinos superiores")
            return
        
        # States 0 or 1
        states = [neighbor.state for neighbor in top_neighbors]
        
        #print(f"Celda ({self.x}, {self.y}): vecinos superiores {[(n.x, n.y, n.state) for n in top_neighbors]} -> estados {states}")
        
        # Determine next state based on the 3 neighbor states
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
        else:
            print(f"Estado no reconocido: {states}")
            self._next_state = self.DEAD

        

    def assume_state(self):
        """Set the state to the new computed state -- computed in step()."""
        if self._next_state is not None:
            self.state = self._next_state
