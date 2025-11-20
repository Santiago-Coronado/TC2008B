from mesa.discrete_space import CellAgent, FixedAgent
import heapq
from collections import deque

class RandomAgent(CellAgent):
    """
    Agent that moves randomly.
    Attributes:
        unique_id: Agent's ID 
    """

    def __init__(self, model, cell):
        """
        Creates a new random agent.
        Args:
            model: Model reference for the agent
            cell: Reference to its position within the grid
        """
        super().__init__(model)
        self.cell = cell
        self._battery = 100
        self.path_to_station = []  # Store of path to recharge station
        self.in_crisis = False  # If battery is low
        self.visited_cells = set()  # To keep track of visited cells
        self.path_to_trash = []  # Store of path to nearest trash
        self.dead = False

        # Metrics to collect
        self.cleaned_trash = 0  # Count of trash cleaned
        self.recharges = 0  # Count of recharges
        self.steps_taken = 0  # Count of steps taken

    def explore(self):
        """
        Determines the next empty cell in its neighborhood, and moves to it
        """
        # If we have a path to trash, follow it
        if self.path_to_trash:
            next_cell = self.path_to_trash.pop(0)
            # Check if the next cell is occupied by another agent
            if not any(isinstance(a, RandomAgent) for a in next_cell.agents):
                self.cell = next_cell
                self.visited_cells.add(self.cell.coordinate)
                self._battery -= 1
                self.steps_taken += 1
            else:
                # If occupied, clear the path and find alternative
                self.path_to_trash = []
                self._battery -= 1
                self.steps_taken += 1
            return
        
        # Try to find nearby trash using BFS
        self.path_to_trash = self.find_nearest_trash(max_distance=5)
        
        if self.path_to_trash:
            # Move towards nearest trash
            next_cell = self.path_to_trash.pop(0)
            if not any(isinstance(a, RandomAgent) for a in next_cell.agents):
                self.cell = next_cell
                self.visited_cells.add(self.cell.coordinate)
            else:
                self.path_to_trash = []
        else:
            # Check if there's trash in immediate neighborhood
            trash_neighbors = self.cell.neighborhood.select(
                lambda cell: any(isinstance(a, TrashAgent) for a in cell.agents) and
                not any(isinstance(a, RandomAgent) for a in cell.agents)
            )

            if len(trash_neighbors.cells) > 0:
                # Move towards trash
                self.cell = trash_neighbors.select_random_cell()
            else:
                # Prefer unvisited cells
                next_moves = self.cell.neighborhood.select(
                    lambda cell: (cell.is_empty or
                    any(isinstance(a, RechargeStationAgent) for a in cell.agents)) and
                    cell.coordinate not in self.visited_cells and 
                    not any(isinstance(a, RandomAgent) for a in cell.agents)
                )
                
                # If all neighbors are visited, go to any valid cell
                if len(next_moves.cells) == 0:
                    next_moves = self.cell.neighborhood.select(
                        lambda cell: (cell.is_empty or
                        any(isinstance(a, RechargeStationAgent) for a in cell.agents)) and
                        not any(isinstance(a, RandomAgent) for a in cell.agents)
                    )
                
                if len(next_moves.cells) > 0:
                    self.cell = next_moves.select_random_cell()
                    self.visited_cells.add(self.cell.coordinate)
    
        self._battery -= 1
        self.steps_taken += 1


    def recharge(self):
        """
        Recharges the agent
        """
        # Check if there's another RandomAgent in this station
        other_agents = [a for a in self.cell.agents 
                    if isinstance(a, RandomAgent) and a != self]
        
        if other_agents:
        # If there's another agent, only the one with less battery charges
            if self._battery >= 100:
                # If fully charged, leave
                self.in_crisis = False
                self.path_to_station = []
                self.path_to_trash = []
                return
            elif self._battery > other_agents[0]._battery:
                # If I have more battery than the other agent, don't charge (wait)
                return
        
        # Only charge if alone in the station
        if self._battery < 100:
            self._battery = min(100, self._battery + 5)
            self.recharges += 1
        
        # Only leave when fully charged
        if self._battery >= 100:
            self.in_crisis = False
            self.path_to_station = []
            self.path_to_trash = []


    def clean(self):
        """
        Cleans the cell the agent is on
        """
        # Find trash in current cell
        trash_agents = [a for a in self.cell.agents if isinstance(a, TrashAgent)] 
        if trash_agents:
            self._battery -= 1
            self.cleaned_trash += 1
            self.steps_taken += 1
            trash_agents[0].disappear()
            # Clear the path since we reached our destination
            self.path_to_trash = []
    
    def crisis(self):
        """
        Happens when battery is low
        """
        # If there is no path, calculate it
        if not self.path_to_station:
            self.path_to_station = self.dijkstra(self.cell, RechargeStationAgent)
        
        # If there is a path, follow it
        if self.path_to_station:
            next_cell = self.path_to_station[0]  # Peek at next cell
            
            # Check if next cell is occupied by another RandomAgent
            if any(isinstance(a, RandomAgent) for a in next_cell.agents):
                # If the next cell or destination is occupied, find alternative station
                destination = self.path_to_station[-1] if self.path_to_station else None
                if destination and any(isinstance(a, RandomAgent) for a in destination.agents):
                    # Find an unoccupied station
                    alternative_path = self.find_unoccupied_station()
                    if alternative_path:
                        self.path_to_station = alternative_path
                        next_cell = self.path_to_station.pop(0)
                        self.cell = next_cell
                    else:
                        # Wait if no alternative found
                        self.path_to_station = []
                else:
                    # Just wait this turn
                    pass
                self._battery -= 1
                self.steps_taken += 1
            else:
                # Move to next cell
                self.cell = self.path_to_station.pop(0)
                self._battery -= 1
                self.steps_taken += 1
        else:
            # If there is no path, the agent dies
            self.die()

    def find_unoccupied_station(self):
        """
        Find the nearest unoccupied recharge station
        Returns: path to nearest unoccupied station or None
        """
        counter = 0
        pq = [(0, counter, self.cell)]
        distances = {self.cell: 0}
        previous = {self.cell: None}
        visited = set()
        
        while pq:
            current_dist, _, current_cell = heapq.heappop(pq)
            
            if current_cell in visited:
                continue
                
            visited.add(current_cell)
            
            # Check if this is an unoccupied recharge station
            if any(isinstance(a, RechargeStationAgent) for a in current_cell.agents):
                # Check if it's not occupied by another RandomAgent
                if not any(isinstance(a, RandomAgent) for a in current_cell.agents):
                    # Reconstruct path
                    path = []
                    while current_cell is not None:
                        path.append(current_cell)
                        current_cell = previous[current_cell]
                    path.reverse()
                    return path[1:]  # Exclude current cell
            
            # Explore neighbors
            for neighbor in current_cell.neighborhood.cells:
                if neighbor not in visited:
                    if neighbor.is_empty or any(isinstance(a, RechargeStationAgent) for a in neighbor.agents):
                        new_dist = current_dist + 1
                        
                        if neighbor not in distances or new_dist < distances[neighbor]:
                            distances[neighbor] = new_dist
                            previous[neighbor] = current_cell
                            counter += 1
                            heapq.heappush(pq, (new_dist, counter, neighbor))
        
        return None

    def die(self):
        """
        Removes the agent from the grid and from the model
        """
        self.dead = True
        self._battery = 0

        alive_agents = [a for a in self.model.agents if isinstance(a, RandomAgent) and not a.dead]

        if len(alive_agents) == 0:
            self.model.running = False

    def step(self):
        """
        Determines the new action it will take, and then moves
        """
        if self.dead:
            return
        
        if self._battery > 0:
            # Check if on trash
            if any(isinstance(a, TrashAgent) for a in self.cell.agents):
                self.clean()
            # Check if on recharge station
            elif any(isinstance(a, RechargeStationAgent) for a in self.cell.agents):
                if self.in_crisis or self._battery < 100:
                    self.recharge()
                else:
                    self.explore()
            # Check if battery is low
            elif self._battery <= 35:
                self.in_crisis = True
                self.crisis()
            else:
                self.explore()
        else:
            self.die()

    def dijkstra(self, start_cell, goal_type):  
        """
        Dijkstra Algorithm to find path to recharge station
        Args:
            start_cell: Initial cell
            goal_type: Target agent type (RechargeStationAgent)
        Returns:
            List of cells forming the shortest path
        """
        # Counter for tie breaking
        counter = 0
        # Priority Queue: (distance, counter, cell)
        pq = [(0, counter ,start_cell)]
        # Distance dictionary
        distances = {start_cell: 0}
        # Dictionary to reconstruct the path
        previous = {start_cell: None}
        # Set of visited cells
        visited = set()
        
        while pq:
            current_dist, _, current_cell = heapq.heappop(pq)
            
            if current_cell in visited:
                continue
                
            visited.add(current_cell)
            
            # If recharge station is found, reconstruct the path
            if any(isinstance(a, goal_type) for a in current_cell.agents):
                path = []
                while current_cell is not None:
                    path.append(current_cell)
                    current_cell = previous[current_cell]
                path.reverse()
                return path[1:]  # Exclude the current cell
            
            # Explore neighbors
            for neighbor in current_cell.neighborhood.cells:
                # Only consider empty cells or recharge stations
                if neighbor not in visited:
                    # Check that the cell does not have obstacles
                    if neighbor.is_empty or any(isinstance(a, RechargeStationAgent) for a in neighbor.agents):
                        # Distance = 1 for each step
                        new_dist = current_dist + 1
                        
                        if neighbor not in distances or new_dist < distances[neighbor]:
                            distances[neighbor] = new_dist
                            previous[neighbor] = current_cell
                            counter += 1
                            heapq.heappush(pq, (new_dist, counter, neighbor))
        
        # If there is no path to recharge station, return empty list
        return []
    
    def find_nearest_trash(self, max_distance=5):
        """
        Find the nearest trash within max_distance using BFS
        Returns: path to nearest trash or None
        """
        queue = deque([(self.cell, 0)])
        visited = {self.cell}
        
        while queue:
            current_cell, distance = queue.popleft()
            
            if distance > max_distance:
                continue
            
            # Check if current cell has trash
            if any(isinstance(a, TrashAgent) for a in current_cell.agents):
                # Return path to this trash using dijkstra
                return self.dijkstra_to_cell(current_cell)
            
            # Explore neighbors
            for neighbor in current_cell.neighborhood.cells:
                if neighbor not in visited:
                    # Only explore empty cells, trash cells, or recharge stations
                    if (neighbor.is_empty or 
                        any(isinstance(a, (TrashAgent, RechargeStationAgent)) for a in neighbor.agents)):
                        visited.add(neighbor)
                        queue.append((neighbor, distance + 1))
        
        return None
    
    def dijkstra_to_cell(self, target_cell):
        """
        Find path to a specific cell using Dijkstra
        Args:
            target_cell: The destination cell
        Returns:
            List of cells forming the shortest path
        """
        counter = 0
        pq = [(0, counter, self.cell)]
        distances = {self.cell: 0}
        previous = {self.cell: None}
        visited = set()
        
        while pq:
            current_dist, _, current_cell = heapq.heappop(pq)
            
            if current_cell in visited:
                continue
            
            visited.add(current_cell)
            
            # If we reach the target cell
            if current_cell == target_cell:
                path = []
                while current_cell is not None:
                    path.append(current_cell)
                    current_cell = previous[current_cell]
                path.reverse()
                return path[1:]  # Exclude the starting cell
            
            # Explore neighbors
            for neighbor in current_cell.neighborhood.cells:
                if neighbor not in visited:
                    # Can move through empty cells, trash, or recharge stations
                    if (neighbor.is_empty or 
                        any(isinstance(a, (TrashAgent, RechargeStationAgent)) for a in neighbor.agents)):
                        new_dist = current_dist + 1
                        
                        if neighbor not in distances or new_dist < distances[neighbor]:
                            distances[neighbor] = new_dist
                            previous[neighbor] = current_cell
                            counter += 1
                            heapq.heappush(pq, (new_dist, counter, neighbor))
        
        return []
    
class ObstacleAgent(FixedAgent):
    """
    Obstacle agent. Just to add obstacles to the grid.
    """
    def __init__(self, model, cell):
        super().__init__(model)
        self.cell=cell

    def step(self):
        pass

class TrashAgent(FixedAgent):
    """
    Trash agent. Just to add trash to the grid.
    """
    def __init__(self, model, cell):
        super().__init__(model)
        self.cell=cell

    def disappear(self):
        self.remove()

    def step(self):
        pass

class RechargeStationAgent(FixedAgent):
    """
    Recharge Station agent. Just to add recharge stations to the grid.
    """
    def __init__(self, model, cell):
        super().__init__(model)
        self.cell=cell 
    
    def step(self):
        pass