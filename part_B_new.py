#!/usr/bin/env python
# coding: utf-8

# In[7]:


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
        K = int(row['K'])
        leaves = row['leaves']
    return N, D, N_s, N_g, m, a, e, T, days, K, leaves

def solve_part_b(N, D, N_s, N_g, m, a, e, T, days, K, leaves_str):
    start_time = time.time()
    time_limit = max(0.5, T - 1.5)

    # Parse leave matrix
    leave_matrix = [[False] * D for _ in range(N)]
    for n in range(N):
        for d in range(D):
            if leaves_str[n * D + d] == 'L':
                leave_matrix[n][d] = True

    grid = [["R"] * D for _ in range(N)]
    shifts_worked = [0] * N
    m_counts = [0] * N
    a_counts = [0] * N
    e_counts = [0] * N

    best_solution = None
    best_cost = float('inf')

    def calc_nurse_cost(cm, ca, ce):
        tot = cm + ca + ce
        return 3 * (cm**2 + ca**2 + ce**2) - tot**2

    def get_valid_shifts_for_nurse(n, d):
        if leave_matrix[n][d]:
            return ['R']
        
        can_work_1 = (shifts_worked[n] + 1 <= K)
        can_work_2 = (shifts_worked[n] + 2 <= K)
        
        consec = 0
        for prev_d in range(d - 1, -1, -1):
            if grid[n][prev_d] != 'R':
                consec += 1
            else:
                break
        can_work = (consec + 1 < 6)
        prev_shift = grid[n][d - 1] if d > 0 else None
        
        valid = ['R']
        if can_work and can_work_1:
            if prev_shift not in ('M', 'B', 'E'):  # H2 & H3
                valid.append('M')
            if prev_shift != 'B':                   # H6
                valid.append('A')
            valid.append('E')
        
        if n < N_s and days[d] == 'S' and can_work and can_work_2:
            if prev_shift not in ('M', 'B', 'E'):  # H2 & H3 for B
                valid.append('B')
                
        return valid

    def solve_day(d):
        nonlocal best_solution, best_cost
        if time.time() - start_time > time_limit:
            return
        if d == D:
            cur_cost = sum(calc_nurse_cost(m_counts[i], a_counts[i], e_counts[i]) for i in range(N))
            if cur_cost < best_cost:
                best_cost = cur_cost
                best_solution = {f"N{n}_{day}": grid[n][day] for n in range(N) for day in range(D)}
            return

        day_type = days[d]
        b_choices = list(range(1, min(m, a, N_s) + 1)) if day_type == 'S' else [0]

        for b in b_choices:
            req_M = m - b
            req_A = a - b
            req_E = e

            # Sort available surgical nurses by balance delta
            avail_B = [n for n in range(N_s) if 'B' in get_valid_shifts_for_nurse(n, d)]
            avail_B.sort(key=lambda n: calc_nurse_cost(m_counts[n] + 1, a_counts[n] + 1, e_counts[n]) - calc_nurse_cost(m_counts[n], a_counts[n], e_counts[n]))
            if len(avail_B) < b:
                continue

            chosen_today = {}

            def choose_nurses(slot_type, needed, available, next_step):
                nonlocal best_cost
                if time.time() - start_time > time_limit:
                    return
                if needed == 0:
                    next_step()
                    return
                
                for i, nurse in enumerate(available):
                    if nurse in chosen_today:
                        continue
                    chosen_today[nurse] = slot_type
                    rem_avail = available[i + 1:]
                    if len(rem_avail) >= needed - 1:
                        choose_nurses(slot_type, needed - 1, rem_avail, next_step)
                        if best_cost == 0:
                            return
                    del chosen_today[nurse]

            def step_M():
                avail_M = [n for n in range(N) if n not in chosen_today and 'M' in get_valid_shifts_for_nurse(n, d)]
                avail_M.sort(key=lambda n: calc_nurse_cost(m_counts[n] + 1, a_counts[n], e_counts[n]) - calc_nurse_cost(m_counts[n], a_counts[n], e_counts[n]))
                if len(avail_M) < req_M:
                    return
                choose_nurses('M', req_M, avail_M, step_A)

            def step_A():
                avail_A = [n for n in range(N) if n not in chosen_today and 'A' in get_valid_shifts_for_nurse(n, d)]
                avail_A.sort(key=lambda n: calc_nurse_cost(m_counts[n], a_counts[n] + 1, e_counts[n]) - calc_nurse_cost(m_counts[n], a_counts[n], e_counts[n]))
                if len(avail_A) < req_A:
                    return
                choose_nurses('A', req_A, avail_A, step_E)

            def step_E():
                avail_E = [n for n in range(N) if n not in chosen_today and 'E' in get_valid_shifts_for_nurse(n, d)]
                avail_E.sort(key=lambda n: calc_nurse_cost(m_counts[n], a_counts[n], e_counts[n] + 1) - calc_nurse_cost(m_counts[n], a_counts[n], e_counts[n]))
                if len(avail_E) < req_E:
                    return
                choose_nurses('E', req_E, avail_E, finalize_day)

            def finalize_day():
                for n in range(N):
                    sh = chosen_today.get(n, 'R')
                    grid[n][d] = sh
                    if sh == 'B':
                        shifts_worked[n] += 2
                        m_counts[n] += 1
                        a_counts[n] += 1
                    elif sh == 'M':
                        shifts_worked[n] += 1
                        m_counts[n] += 1
                    elif sh == 'A':
                        shifts_worked[n] += 1
                        a_counts[n] += 1
                    elif sh == 'E':
                        shifts_worked[n] += 1
                        e_counts[n] += 1

                solve_day(d + 1)

                for n in range(N):
                    sh = chosen_today.get(n, 'R')
                    if sh == 'B':
                        shifts_worked[n] -= 2
                        m_counts[n] -= 1
                        a_counts[n] -= 1
                    elif sh == 'M':
                        shifts_worked[n] -= 1
                        m_counts[n] -= 1
                    elif sh == 'A':
                        shifts_worked[n] -= 1
                        a_counts[n] -= 1
                    elif sh == 'E':
                        shifts_worked[n] -= 1
                        e_counts[n] -= 1
                    grid[n][d] = 'R'

            if b > 0:
                choose_nurses('B', b, avail_B, step_M)
            else:
                step_M()
            
            if best_cost == 0:
                return

    solve_day(0)
    return best_solution if best_solution is not None else {}

if __name__ == '__main__':
    if len(sys.argv) >= 3 and not sys.argv[1].startswith('-'):
        input_csv = sys.argv[1]
        output_json = sys.argv[2]
    else:
        input_csv = "test2.csv"
        output_json = "solution_b2_new.json"

    N, D, N_s, N_g, m, a, e, T, days, K, leaves = parse_input(input_csv)
    sol = solve_part_b(N, D, N_s, N_g, m, a, e, T, days, K, leaves)
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(sol, f, indent=4)


# In[8]:


from verifier import read_input, read_solution, verify_solution, calculate_objective

# Load files
instance = read_input("test2.csv")
solution = read_solution("solution_b2_new.json")

# Verify constraints
if verify_solution(instance, solution):
    score = calculate_objective(instance, solution)
    print(f"VALID {score}")
else:
    print("INVALID")


# In[ ]:




