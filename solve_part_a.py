#!/usr/bin/env python
# coding: utf-8

# In[20]:


#!/usr/bin/env python3
import sys
import csv
import json
import time

def parse_input(input_csv):
    with open(input_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        row = next(reader)
        N = int(row['N'])
        D = int(row['D'])
        N_s = int(row['N_s'])
        N_g = int(row['N_g'])
        m = int(row['m'])
        a = int(row['a'])
        e = int(row['e'])
        T = float(row['T'])
        days = row['days']
        max_shifts = int(row['K'])
        leaves = row['leaves']
    return N, D, N_s, N_g, m, a, e, T, days, max_shifts, leaves

def solve_part_a(N, D, N_s, N_g, m, a, e, T, days, max_shifts, leaves):
    start_time = time.time()
    
    # Parse leave matrix: leave_grid[nurse][day] == True if on leave
    leave_grid = [[leaves[i * D + d] == 'L' for d in range(D)] for i in range(N)]
    
    # State tracking across days for each nurse
    grid = [[None for _ in range(D)] for _ in range(N)]
    shifts_worked = [0] * N
    consec_work = [0] * N

    def get_valid_shifts(nurse, day):
        if leave_grid[nurse][day]:
            return ['R']
        
        is_surgical = (nurse < N_s)
        prev_shift = grid[nurse][day - 1] if day > 0 else None
        
        # Max shifts check (B costs 2 shifts, standard shifts cost 1)
        remaining_shifts = max_shifts - shifts_worked[nurse]
        if remaining_shifts <= 0:
            return ['R']

        # Max consecutive working days check (H5: 5 max work days in a row)
        if consec_work[nurse] == 5:
            return ['R']

        candidates = ['R']
        
        # Determine allowed working shifts based on previous day's shift
        possible = []
        if is_surgical and days[day] == 'S' and remaining_shifts >= 2:
            if prev_shift not in ['M', 'B', 'E']:  # H2 & H3 for B (starts with M)
                possible.append('B')
        
        if prev_shift not in ['M', 'B', 'E']:  # H2 & H3
            possible.append('M')
            
        if prev_shift != 'B':  # H6
            possible.append('A')
            
        possible.append('E')

        if prev_shift == 'B':
            # H6: B can only be followed by R or E
            possible = [s for s in possible if s in ['R', 'E']]

        candidates.extend(possible)
        return candidates

    def search_day(day, nurse_idx, current_day_assignments, counts):
        if time.time() - start_time > T - 1.0:
            return False

        if nurse_idx == N:
            # Check exact daily cover constraints (H4)
            if counts['M'] + counts['B'] != m:
                return False
            if counts['A'] + counts['B'] != a:
                return False
            if counts['E'] != e:
                return False
            # Check surgical requirement (H7)
            if days[day] == 'S' and counts['B'] < 1:
                return False

            # Recurse to next day
            if day + 1 == D:
                return True
            return search_day(day + 1, 0, {}, {'M': 0, 'A': 0, 'E': 0, 'B': 0, 'R': 0})

        # Pruning check: Can we still meet required shift counts?
        nurses_left = N - nurse_idx
        needed_m = max(0, m - (counts['M'] + counts['B']))
        needed_a = max(0, a - (counts['A'] + counts['B']))
        needed_e = max(0, e - counts['E'])
        
        # Minimum nurses needed to satisfy daily cover
        min_nurses_needed = max(needed_m, needed_a) + needed_e
        if min_nurses_needed > nurses_left:
            return False

        options = get_valid_shifts(nurse_idx, day)
        
        # Heuristic ordering for shifts
        def shift_priority(s):
            if s == 'B' and days[day] == 'S' and counts['B'] == 0:
                return 0
            if s == 'M' and counts['M'] + counts['B'] < m:
                return 1
            if s == 'A' and counts['A'] + counts['B'] < a:
                return 2
            if s == 'E' and counts['E'] < e:
                return 3
            if s == 'R':
                return 4
            return 5

        options.sort(key=shift_priority)

        for s in options:
            # Check capacity violations
            if s == 'M' and counts['M'] + counts['B'] >= m:
                continue
            if s == 'A' and counts['A'] + counts['B'] >= a:
                continue
            if s == 'E' and counts['E'] >= e:
                continue
            if s == 'B' and (counts['M'] + counts['B'] >= m or counts['A'] + counts['B'] >= a):
                continue

            # Apply move
            grid[nurse_idx][day] = s
            cost = 2 if s == 'B' else (0 if s == 'R' else 1)
            shifts_worked[nurse_idx] += cost
            old_consec = consec_work[nurse_idx]
            consec_work[nurse_idx] = 0 if s == 'R' else old_consec + 1
            counts[s] += 1

            if search_day(day, nurse_idx + 1, current_day_assignments, counts):
                return True

            # Backtrack
            counts[s] -= 1
            shifts_worked[nurse_idx] -= cost
            consec_work[nurse_idx] = old_consec
            grid[nurse_idx][day] = None

        return False

    initial_counts = {'M': 0, 'A': 0, 'E': 0, 'B': 0, 'R': 0}
    if search_day(0, 0, {}, initial_counts):
        solution = {}
        for i in range(N):
            for d in range(D):
                solution[f"N{i}_{d}"] = grid[i][d]
        return solution
    return {}

if __name__ == '__main__':
    input_csv = "test1.csv"       # Make sure test1.csv is in the same folder as this notebook
    output_json = "solutionA_1.json"

    N, D, N_s, N_g, m, a, e, T, days, max_shifts, leaves = parse_input(input_csv)
    result = solve_part_a(N, D, N_s, N_g, m, a, e, T, days, max_shifts, leaves)

    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=4)

    print("Solution generated successfully!")
    


# In[21]:


from verifier import read_input, read_solution, verify_solution, calculate_objective

# Load files
instance = read_input("test1.csv")
solution = read_solution("solutionA_1.json")

# Verify constraints
if verify_solution(instance, solution):
    score = calculate_objective(instance, solution)
    print(f"VALID {score}")
else:
    print("INVALID")


# In[ ]:





# In[ ]:




