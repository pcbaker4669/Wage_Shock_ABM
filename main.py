import numpy as np
import random
from agents import Firm, Worker
import csv

# Simulation parameters
GRID_SIZE = 10
NUM_WORKERS = 180
WAGE_HIKE = 22.0

STEPS = 20
SHOCK_AT = 3  # number of pre steps before policy turns on

# Statewide treated region: all rows, left half of columns
SHOCK_ZONE = (slice(0, GRID_SIZE), slice(0, GRID_SIZE // 2))

# Initialize grid of firms
def create_firm_grid(size, shock_zone, default_wage=15.0, automation_prob=0.3, p_fast=0.30,
                     capacity=2, base_revenue=30):
    grid = np.empty((size, size), dtype=object)
    for i in range(size):
        for j in range(size):
            is_shock = (i in range(*shock_zone[0].indices(size)) and
                        j in range(*shock_zone[1].indices(size)))

            revenue = 50

            sector = "fast_food" if random.random() < p_fast else "other"

            firm = Firm(i, j,
                        wage=default_wage,
                        is_shock_zone=is_shock,
                        automation_prob=automation_prob,
                        revenue_per_step=base_revenue,  # was 50
                        sector=sector,
                        capacity=capacity)              # pass capacity
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

def apply_sectoral_wage_shock(grid, shock_zone, new_wage, target_sector="fast_food"):
    # Apply only to firms in the zone *and* with the target sector (CA-style)
    for i in range(*shock_zone[0].indices(grid.shape[0])):
        for j in range(*shock_zone[1].indices(grid.shape[1])):
            f = grid[i, j]
            if f.sector == target_sector:
                f.update_wage(new_wage)

def apply_broad_wage_shock(grid, shock_zone, delta):
    # Apply a modest raise to all firms in zone (NY-style)
    for i in range(*shock_zone[0].indices(grid.shape[0])):
        for j in range(*shock_zone[1].indices(grid.shape[1])):
            f = grid[i, j]
            f.update_wage(f.wage + delta)

def did_from_series(treated_series, control_series, pre_steps=(0,2), post_steps=(3,10)):
    # pre_steps and post_steps are inclusive index ranges in step space (0-based)
    pre_slice  = slice(pre_steps[0],  pre_steps[1] + 1)
    post_slice = slice(post_steps[0], post_steps[1] + 1)
    pre_t  = np.mean(treated_series[pre_slice])
    post_t = np.mean(treated_series[post_slice])
    pre_c  = np.mean(control_series[pre_slice])
    post_c = np.mean(control_series[post_slice])
    return (post_t - pre_t) - (post_c - pre_c)

# Run simulation steps
def run_simulation():
    grid = create_firm_grid(GRID_SIZE, SHOCK_ZONE, capacity=2, base_revenue=30)
    workers = create_workers(NUM_WORKERS)
    assign_workers_to_firms(grid, workers)


    # fixed counts by region
    n_shock = sum(1 for row in grid for f in row if f.is_shock_zone)
    n_non   = sum(1 for row in grid for f in row if not f.is_shock_zone)

    # Metrics tracking
    metrics = {
        'shock_stress_share': [], 'nonshock_stress_share': [],
        'unemployed': [], 'exited': [], 'automated_jobs': [], 'total_employment': [],
        'shock_employment': [], 'nonshock_employment': [],
        'shock_firms_stressed': [], 'nonshock_firms_stressed': [],
        'vacancies': [], 'wage_bill': [],
        'treated_emp': [], 'control_emp': [], 'event_diff': [],
        'treated_ff_emp': [], 'control_ff_emp': [], 'event_diff_ff': [],
        'policy_on': [], 'avg_w_treated': [], 'avg_w_control': [],
        'shock_firms_stressed_ff': []  # <<< add this
    }

    for step in range(STEPS):
        print(f"Step {step+1}")

        # inside the loop, after step prints:
        metrics['policy_on'].append(1 if step >= SHOCK_AT else 0)

        if step == SHOCK_AT:
            # CA-style (sector-targeted) shock:
            apply_sectoral_wage_shock(grid, SHOCK_ZONE, new_wage=WAGE_HIKE, target_sector="fast_food")

            # OR NY-style (broad) shock:
            # apply_broad_wage_shock(grid, SHOCK_ZONE, delta=2.00)

        # Firm actions
        for row in grid:
            for firm in row:
                firm.layoff_or_automate()
                firm.pay_workers()

        # Worker actions
        for worker in workers.values():
            if worker.unemployed and not worker.exited_labor_force:
                # Use a random firm if worker has no current firm
                i = random.randrange(grid.shape[0])
                j = random.randrange(grid.shape[1])
                reference_firm = worker.current_firm or grid[i, j]
                neighbors = get_neighbors(grid, reference_firm)
                worker.consider_move(neighbors)

        # Collect metrics
        exited = sum(w.exited_labor_force for w in workers.values())
        unemployed = sum(w.unemployed for w in workers.values())
        automated = sum(f.automated_roles for row in grid for f in row)
        employed = sum(len(f.workers) for row in grid for f in row)
        metrics['unemployed'].append(unemployed)
        metrics['exited'].append(exited)
        metrics['automated_jobs'].append(automated)
        metrics['total_employment'].append(employed)


        # State-level employment (treated vs control) each step
        treated_emp = sum(len(f.workers) for row in grid for f in row if f.y < GRID_SIZE // 2)
        control_emp = sum(len(f.workers) for row in grid for f in row if f.y >= GRID_SIZE // 2)
        metrics['treated_emp'].append(treated_emp)
        metrics['control_emp'].append(control_emp)
        metrics['event_diff'].append(treated_emp - control_emp)

        # Average wages by side (treatment intensity)
        avg_w_treated = np.mean([f.wage for row in grid for f in row if f.y < GRID_SIZE // 2])
        avg_w_control = np.mean([f.wage for row in grid for f in row if f.y >= GRID_SIZE // 2])
        metrics['avg_w_treated'].append(avg_w_treated)
        metrics['avg_w_control'].append(avg_w_control)

        treated_ff_emp = sum(len(f.workers) for row in grid for f in row
                             if f.y < GRID_SIZE // 2 and f.sector == "fast_food")
        control_ff_emp = sum(len(f.workers) for row in grid for f in row
                             if f.y >= GRID_SIZE // 2 and f.sector == "fast_food")

        metrics['treated_ff_emp'].append(treated_ff_emp)
        metrics['control_ff_emp'].append(control_ff_emp)
        metrics['event_diff_ff'].append(treated_ff_emp - control_ff_emp)

        # --- per-region metrics ---
        shock_emp = sum(len(f.workers) for row in grid for f in row if f.is_shock_zone)
        nonshock_emp = sum(len(f.workers) for row in grid for f in row if not f.is_shock_zone)
        stress_shock = sum((f.wage * len(f.workers)) > f.revenue_per_step
                           for row in grid for f in row if f.is_shock_zone)
        stress_non = sum((f.wage * len(f.workers)) > f.revenue_per_step
                         for row in grid for f in row if not f.is_shock_zone)

        # NEW: stress among treated-sector (fast_food) firms only
        stress_shock_ff = sum((f.wage * len(f.workers)) > f.revenue_per_step
                              for row in grid for f in row
                              if f.is_shock_zone and f.sector == "fast_food")

        metrics['shock_stress_share'].append(stress_shock / max(n_shock, 1))
        metrics['nonshock_stress_share'].append(stress_non / max(n_non, 1))

        # --- slack & cost metrics ---
        vacancies = sum(max(f.capacity - len(f.workers), 0) for row in grid for f in row)
        wage_bill = sum(f.wage * len(f.workers) for row in grid for f in row)

        metrics['shock_employment'].append(shock_emp)
        metrics['nonshock_employment'].append(nonshock_emp)
        metrics['shock_firms_stressed'].append(stress_shock)
        metrics['nonshock_firms_stressed'].append(stress_non)
        metrics['shock_firms_stressed_ff'].append(stress_shock_ff)  # <<< append here
        metrics['vacancies'].append(vacancies)
        metrics['wage_bill'].append(wage_bill)

        print(f"  Unemployed: {unemployed}, Exited: {exited}, Automated Roles: {automated}, Employed: {employed}")
        print(f"  Vacancies: {vacancies}, Wage bill: {wage_bill:.2f}")

    return metrics

# https://chatgpt.com/c/68927f9c-27cc-832f-b19f-3574f72c230b?model=o4-mini-high
if __name__ == "__main__":
    random.seed(42)
    np.random.seed(42)
    metrics = run_simulation()
    print("\nSimulation complete. Metrics:")
    for key, values in metrics.items():
        print(f"{key}: {values}")

    # Save metrics to CSV
    keys = list(metrics.keys())
    with open('metrics.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['step'] + keys)
        for t in range(STEPS):
            writer.writerow([t + 1] + [metrics[k][t] for k in keys])

    print("Saved metrics.csv")

    did_est = did_from_series(
        metrics['treated_emp'], metrics['control_emp'],
        pre_steps=(0, SHOCK_AT - 1),
        post_steps=(SHOCK_AT + 1, min(SHOCK_AT + 8, STEPS - 1))
    )
    print(f"DiD (treated vs control): {did_est:.2f}")

    did_est_ff = did_from_series(
        metrics['treated_ff_emp'], metrics['control_ff_emp'],
        pre_steps=(0, SHOCK_AT - 1),
        post_steps=(SHOCK_AT + 1, min(SHOCK_AT + 8, STEPS - 1))
    )
    print(f"DiD (fast-food, treated vs control): {did_est_ff:.2f}")

    # --- paper summary stats ---
    peak_u = max(metrics['unemployed'])
    cum_u = sum(metrics['unemployed'])
    # first step >= SHOCK_AT where total employment recovers to baseline
    try:
        rec_step = next(s for s, emp in enumerate(metrics['total_employment'])
                        if s >= SHOCK_AT and emp >= NUM_WORKERS)
        ttr = rec_step - SHOCK_AT
    except StopIteration:
        ttr = None  # never fully recovered within horizon

    print(f"Peak unemployment: {peak_u}")
    print(f"Cumulative unemployment (sum over steps): {cum_u}")
    print(f"Time-to-recovery (steps after shock): {ttr}")
