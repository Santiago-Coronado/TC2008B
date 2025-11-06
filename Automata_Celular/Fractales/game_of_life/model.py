from mesa import Model
from mesa.discrete_space import OrthogonalMooreGrid
from .agent import Cell

 
class ConwaysGameOfLife(Model):
    """Represents the 2-dimensional array of cells in Conway's Game of Life."""

    def __init__(self, width=50, height=50, initial_fraction_alive=0.2, seed=None):
        """Create a new playing area of (width, height) cells."""
        super().__init__(seed=seed)

        """Grid where cells are connected to their 8 neighbors.

        Example for two dimensions:
        directions = [
            (-1, -1), (-1, 0), (-1, 1),
            ( 0, -1),          ( 0, 1),
            ( 1, -1), ( 1, 0), ( 1, 1),
        ]
        """
        self.grid = OrthogonalMooreGrid((width, height), capacity=1, torus=True) # torus = True means the grid wraps around at edges

        # Place a cell at each location, with some initialized to
        # ALIVE and some to DEAD.
        for cell in self.grid.all_cells:
            y = cell.coordinate[1]
            #x = cell.coordinate[0]
            if y == 49:
                Cell(
                    self,
                    cell,
                    init_state=(
                        Cell.ALIVE
                        if self.random.random() < initial_fraction_alive
                        else Cell.DEAD
                    ),
                )
            else:
                Cell(self, cell, init_state=Cell.DEAD)

        self.current_row = 48
        self.running = True

    def step(self):
        """Perform the model step for one row only."""
        # See if there are rows to process
        if self.current_row < 0:
            self.running = False
            return

        # Process only the current row
        y = self.current_row
        agents_in_row = [agent for agent in self.agents if agent.y == y]

        # Determine state for all agents in this row
        for agent in agents_in_row:
            agent.determine_state()

        # Assume state for all agents in this row
        for agent in agents_in_row:
            agent.assume_state()
        
        #print(f"Procesando fila y={y}")

        # Move to next row (downward)
        self.current_row -= 1
