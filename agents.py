import random
import math

class Firm:
    def __init__(self, x, y, wage=15.0, budget=1000.0, capacity=10, is_shock_zone=False,
                 automation_prob=0.0, revenue_per_step=30.0):
        self.x = x
        self.y = y
        self.wage = wage
        self.budget = budget
        self.capacity = capacity
        self.workers = []  # list of Worker objects
        self.is_shock_zone = is_shock_zone
        self.automation_prob = automation_prob  # chance to automate instead of lay off
        self.automated_roles = 0  # number of jobs replaced by automation
        self.revenue_per_step = revenue_per_step  # NEW

    def update_wage(self, new_wage):
        self.wage = new_wage

    def hire_worker(self, worker):
        if len(self.workers) < self.capacity:
            self.workers.append(worker)
            return True
        return False

    def layoff_or_automate(self):
        # NEW: decide affordability based on per-step revenue, not stockpile
        payroll = self.wage * len(self.workers)
        if payroll <= self.revenue_per_step:
            return

        # number of roles to cut to get payroll <= revenue
        needed_reduction = math.ceil((payroll - self.revenue_per_step) / max(self.wage, 1e-9))

        for _ in range(min(needed_reduction, len(self.workers))):
            if random.random() < self.automation_prob and self.capacity > 0:
                # Automation replaces a role: reduce capacity and remove one worker
                self.automated_roles += 1
                self.capacity -= 1
            # In both cases we free one worker spot to reduce payroll
            if self.workers:
                worker = self.workers.pop()
                worker.layoff()

    def pay_workers(self):
        total_pay = self.wage * len(self.workers)
        self.budget -= total_pay


class Worker:
    def __init__(self, id, firm=None):
        self.id = id
        self.current_firm = firm  # None if unemployed
        self.unemployed = False
        self.failed_moves = 0
        self.max_failed_attempts = 3  # After this, may exit labor force
        self.exited_labor_force = False
        self.search_cooldown = 0  # rounds to wait before looking again after layoff
        self.job_search_success_prob = 0.5  # 50% chance per opportunity

    def consider_move(self, neighbors):
        if self.exited_labor_force:
            return

        if self.search_cooldown > 0:
            self.search_cooldown -= 1
            return

        if self.exited_labor_force:
            return

        better_firms = [
            f for f in neighbors
            if f.wage > (self.current_firm.wage if self.current_firm else 0)
            and len(f.workers) < f.capacity
        ]

        if better_firms and random.random() < self.job_search_success_prob:
            best = max(better_firms, key=lambda f: f.wage)
            if self.current_firm:
                self.current_firm.workers.remove(self)
            best.hire_worker(self)
            self.current_firm = best
            self.unemployed = False
            self.failed_moves = 0
        else:
            self.failed_moves += 1
            if self.failed_moves >= self.max_failed_attempts:
                self.exit_labor_force()

    def layoff(self):
        self.current_firm = None
        self.unemployed = True
        self.search_cooldown = 1  # wait one step before job search
        print(f"DEBUG: Worker {self.id} marked as unemployed.")

    def exit_labor_force(self):
        self.exited_labor_force = True
        self.unemployed = False
        self.current_firm = None