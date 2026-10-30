import random
from collections import defaultdict

def build_grid(words_pool, R, C, target, rng, autodef=False, tries=40, minlen=3, maxlen=None):
    maxlen = maxlen or max(R, C)
    best = None
    pool_ok = [w for w in words_pool if minlen <= len(w) <= maxlen]
    for t in range(tries):
        grid = [[None]*C for _ in range(R)]
        dirs = [[set() for _ in range(C)] for _ in range(R)]
        clue = [[False]*C for _ in range(R)]
        where = defaultdict(list)
        placed = []; used = set()

        def can(w, r, c, d):
            dr, dc = (0, 1) if d == 'A' else (1, 0)
            er, ec = r + dr*(len(w)-1), c + dc*(len(w)-1)
            if not (0 <= r and 0 <= c and er < R and ec < C): return -1
            pr, pc = r-dr, c-dc
            if autodef:
                if pr < 0 or pc < 0: return -1
                if grid[pr][pc] is not None: return -1
            elif pr >= 0 and pc >= 0 and grid[pr][pc] is not None: return -1
            nr, nc = er+dr, ec+dc
            if nr < R and nc < C and grid[nr][nc] is not None: return -1
            if autodef and nr < R and nc < C and False: return -1
            cross = 0
            for k, ch in enumerate(w):
                rr, cc = r+dr*k, c+dc*k
                if clue[rr][cc]: return -1
                g = grid[rr][cc]
                if g is not None:
                    if g != ch or d in dirs[rr][cc]: return -1
                    cross += 1
                else:
                    for ar, ac in ((rr+dc, cc+dr), (rr-dc, cc-dr)):
                        if 0 <= ar < R and 0 <= ac < C and grid[ar][ac] is not None: return -1
            if cross == len(w): return -1
            return cross

        def put(w, r, c, d):
            dr, dc = (0, 1) if d == 'A' else (1, 0)
            for k, ch in enumerate(w):
                rr, cc = r+dr*k, c+dc*k
                if grid[rr][cc] is None: where[ch].append((rr, cc))
                grid[rr][cc] = ch; dirs[rr][cc].add(d)
            if autodef: clue[r-dr][c-dc] = True
            placed.append({'w': w, 'r': r, 'c': c, 'd': d}); used.add(w)

        cand = rng.sample(pool_ok, len(pool_ok))
        first = next((w for w in cand if len(w) >= min(C-2, 7)), cand[0])
        if autodef:
            put(first, rng.randrange(1, R), 1, 'A')
        else:
            put(first, R//2, (C-len(first))//2, 'A')
        fails = 0
        idx = 0
        while len(placed) < target and fails < 2:
            batch = [w for w in (rng.sample(pool_ok, min(len(pool_ok), 260)) if fails == 0 else pool_ok) if w not in used]
            bestopt = None
            for w in batch:
                for k, ch in enumerate(w):
                    for (rr, cc) in where.get(ch, ()):
                        for d in 'AD':
                            if d in dirs[rr][cc]: continue
                            dr, dc = (0, 1) if d == 'A' else (1, 0)
                            r0, c0 = rr-dr*k, cc-dc*k
                            sc = can(w, r0, c0, d)
                            if sc > 0:
                                val = sc*2 + len(w)*0.3 + rng.random()
                                if bestopt is None or val > bestopt[0]:
                                    bestopt = (val, w, r0, c0, d)
            if bestopt:
                put(*bestopt[1:]); fails = 0
            else:
                fails += 1
        filled = sum(1 for r in range(R) for c in range(C) if grid[r][c])
        score = len(placed)*3 + filled
        if best is None or score > best[0]:
            best = (score, [row[:] for row in grid], [row[:] for row in clue], list(placed))
    return best

def number_grid(grid, placed):
    R, C = len(grid), len(grid[0])
    starts = {}
    for p in placed:
        starts.setdefault((p['r'], p['c']), []).append(p)
    num = {}; n = 1
    for r in range(R):
        for c in range(C):
            if (r, c) in starts:
                num[(r, c)] = n; n += 1
    return num

