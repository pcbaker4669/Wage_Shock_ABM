import numpy as np
import random
from agents import Firm, Worker

# Simulation parameters
GRID_SIZE = 10
NUM_WORKERS = 80
WAGE_HIKE = 20.0
SHOCK_ZONE = (slice(0, 5), slice(0, 5))  # top-left 5x5
STEPS = 20

# Initialize grid of firms
def create_firm_grid(size, shock_zone, default_wage=15.0, automation_prob=0.2):
    grid = np.empty((size, size), dtype=object)
    for i in range(size):
        for j in range(size):
            is_shock = (i in range(*shock_zone[0].indices(size)) and
                        j in range(*shock_zone[1].indices(size)))
            firm = Firm(i, j, wage=default_wage, is_shock_zone=is_shock, automation_prob=automation_prob)
            grid[i, j] = firm
    return grid

def create_workers(num_workers):
    return {wid: Worker(wid) for wid in range(num_workers)}

def assign_workers_to_firms(grid, workers):
    for worker in workers.values():
        assigned = False
        while not assigned:
            i, j = random.randint(0, grid.shape[0] - 1), random.randint(0, grid.shape[1] - 1)
            firm = grid[i, j]
            if firm.hire_worker(worker):
                worker.current_firm = firm
                assigned = True

# Get neighboring firms for a worker
def get_neighbors(grid, firm, radius=1):
    neighbors = []
    x, y = firm.x, firm.y
    for dx in range(-radius, radius+1):
        for dy in range(-radius, radius+1):
            if 0 <= x+dx < grid.shape[0] and 0 <= y+dy < grid.shape[1]:
                neighbor = grid[x+dx, y+dy]
                if neighbor != firm:
                    neighbors.append(neighbor)
    return neighbors

# Apply a wage hike to shock zone
def apply_wage_shock(grid, shock_zone, new_wage):
    for i in range(*shock_zone[0].indices(grid.shape[0])):
        for j in range(*shock_zone[1].indices(grid.shape[1])):
            grid[i, j].update_wage(new_wage)

# Run simulation steps
def run_simulation():
    grid = create_firm_grid(GRID_SIZE, SHOCK_ZONE)
    workers = create_workers(NUM_WORKERS)
    assign_workers_to_firms(grid, workers)
    apply_wage_shock(grid, SHOCK_ZONE, WAGE_HIKE)

    for step in range(STEPS):
        print(f"Step {step+1}")
        # Firm actions
        for row in grid:
            for firm in row:
                firm.layoff_or_automate()
                firm.pay_workers()

        # Worker actions
        for worker in workers.values():
            if worker.unemployed and not worker.exited_labor_force:
                # Use a random firm if worker has no current firm
                reference_firm = worker.current_firm or random.choice(random.choice(grid))
                neighbors = get_neighbors(grid, reference_firm)
                worker.consider_move(neighbors)

        for w in workers.values():
            if w.unemployed:
                print(f"DEBUG: Worker {w.id} is unemployed")
        # Metrics (to expand)
        exited = sum(w.exited_labor_force for w in workers.values())
        unemployed = sum(w.unemployed for w in workers.values())
        print(f"  Unemployed: {unemployed}, Exited: {exited}")

if __name__ == "__main__":
    run_simulation()