# WageHikeGridModel

To simulate the diverse effects of localized minimum wage hikes on employment dynamics using a 2D grid of firms and mobile workers.
## https://chatgpt.com/c/68927f9c-27cc-832f-b19f-3574f72c230b

## 🧠 Purpose

This model investigates how localized wage hikes affect:
- Employment stability in surrounding firms
- Worker turnover, migration, unemployment, and labor force exit
- Firm-level budget stress, wage affordability, and layoffs
- Spatial wage diffusion and labor market ripple effects

**Key Dynamics to Include:**

- ✅ **Layoffs** due to budget constraints  
- ✅ **Worker migration** to nearby firms or regions  
- ✅ **Unemployment tracking** across time  
- ✅ **Automation as a substitution strategy**  
- ✅ **Hours reduction** as a middle-ground response  
- ✅ **Firm exits or shrinkage** under prolonged stress  
- ✅ **Spillover effects**: wage or unemployment spreading into non-shock zones

## 🗺️ Model Design

### Agents
- **Firm**:
  - Located on a 2D grid
  - Has attributes: wage, budget, capacity, workers
  - May be part of a "shock zone" where a wage floor is enforced
  - May lay off workers, reduce hours, or automate in response to wage pressures

- **Worker**:
  - Initially employed at a firm on the grid
  - Can become unemployed if laid off due to wage pressure
  - Attempts to find new employment locally; may migrate or exit the labor force if unsuccessful
  - Tracks employment status and job search history
 

### Environment
- A 2D NumPy grid where each cell is a firm
- Shocks can be applied to a region (e.g., top-left quadrant)

### Behavior
**Firms**
- Pay workers each round if budget allows
- Lay off workers if unable to meet the wage bill
- Adjust hiring or reduce headcount based on budget stress
- Attempt automation as a cost-saving alternative if layoffs are likely
  - Automation depends on a feasibility score or probability threshold
  - If automation succeeds, reduces the number of workers required

**Workers**
- Work at assigned firms if employed
- Become unemployed if laid off
- Search locally for new firms hiring
- If repeatedly unsuccessful, may migrate or exit the labor force


## 🔄 Simulation Flow

1. **Initialize grid of firms**
   - Set default wages, budgets, and capacities
2. **Randomly assign workers**
   - Distribute workers to firms based on available capacity
3. **Apply wage hike to selected region**
   - Raise minimum wage for firms in the designated shock zone
4. **Run simulation for N steps**
   - Firms evaluate whether they can afford current staff
   - If not, firms may:
     - Lay off workers
     - Automate roles to reduce headcount (if automation is enabled)
   - Workers who are laid off seek jobs locally
   - If jobs unavailable, they may migrate or exit the labor force
   - Update visualization and track metrics (e.g., unemployment, migration, automation usage)


## 📊 Visualization

- Grid color maps wage levels
- Optional overlays for worker movement and layoffs
- Matplotlib is used for rendering

## 📁 File Structure
.  
├── agents.py # Contains Firm and Worker classes  
├── simulation.py # Main simulation logic  
├── visualize.py # Grid rendering functions  
├── README.md # Project overview  
└── requirements.txt # Dependencies (NumPy, matplotlib)  

## 🧪 Example Output

![grid_sim_example](docs/grid_sim_example.png)

## 📚 References

- Baker, P. (2025). *How Minimum Wage Hikes Affect Food Service Employment...*  
- Journal of Artificial Societies and Social Simulation (planned submission)

## 🔧 Requirements

- Python 3.8+
- NumPy
- Matplotlib

```bash
pip install -r requirements.txt