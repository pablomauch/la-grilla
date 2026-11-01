"""Banco v4: cero repetición, también contra las tandas v1 y v2.

Cada palabra, cada definición y cada par autor/obra aparece una sola vez
en toda la versión. Los juegos se generan intercalados (tipo y nivel por
turnos) para repartir el vocabulario hasta agotarlo.

Uso: python3 build3.py  -> games3.json
"""
import json, os, random, sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build2 as B
from gridlib import build_grid, number_grid

B.FILES += ['r1.txt'] + ['n%d.txt' % i for i in range(1, 19)]
W = B.load()
B.W = W
# una definición pertenece a una sola palabra: si dos palabras comparten el mismo texto, se queda con la primera
_owner = {}
for k in list(W):
    for t in list(W[k]['clues']):
        keep = []
        for c in W[k]['clues'][t]:
            n = ' '.join(c.lower().split())
            if _owner.setdefault(n, k) == k: keep.append(c)
        if keep: W[k]['clues'][t] = keep
        else: del W[k]['clues'][t]
    if not W[k]['clues']: del W[k]

# Lo usado en las tandas v1 y v2 queda excluido de entrada
_prev = json.load(open(os.path.join(HERE, 'used_v1v2.json'), encoding='utf-8'))
USED_W = set(_prev['words'])      # palabras ya usadas
USED_C = set(_prev['clues'])      # definiciones ya usadas (texto normalizado)
cnorm = lambda s: ' '.join(s.lower().split())
PREF = {1: [1, 2], 2: [2, 3, 1], 3: [3, 2]}

def free_clues(k, L):
    for t in PREF[L]:
        cs = [c for c in W[k]['clues'].get(t, []) if cnorm(c) not in USED_C]
        if cs: return t, cs
    return None, []

def avail(k, L):
    return k not in USED_W and free_clues(k, L)[0] is not None

def take(k, L, rng):
    t, cs = free_clues(k, L)
    c = rng.choice(cs)
    USED_W.add(k); USED_C.add(cnorm(c))
    return c

def pool(L, lo, hi):
    return [k for k in W if lo <= len(k) <= hi and avail(k, L)]

# ---------------- claringrilla ----------------
COMBOS = []
from authors3 import AUTHORS3
_seen = set()
for a, works in B.AUTHORS + AUTHORS3:
    for w in works:
        key = B.norm(a) + B.norm(w)
        if key not in _seen: _seen.add(key); COMBOS.append((a, w, key))
CG = {1: dict(kmin=11, kmax=18, wmin=4, wmax=10), 2: dict(kmin=15, kmax=22, wmin=4, wmax=11), 3: dict(kmin=16, kmax=26, wmin=5, wmax=12)}
used_combo = set(_prev['combos'])

PREF_CG = {1: [1, 2, 3], 2: [2, 3, 1], 3: [3, 2, 1]}

def make_cg(L, rng):
    # en la claringrilla, si faltan palabras de un nivel se completa con las de otro
    saved = dict(PREF); PREF.update(PREF_CG)
    try:
        return _make_cg(L, rng)
    finally:
        PREF.clear(); PREF.update(saved)

def _make_cg(L, rng):
    c = CG[L]
    by_s = defaultdict(list)
    for k in pool(L, c['wmin'], c['wmax']): by_s[k[0]].append(k)
    cands = [x for x in COMBOS if x[2] not in used_combo and c['kmin'] <= len(x[2]) <= c['kmax']]
    rng.shuffle(cands)
    for a, w, key in cands[:400]:
        need = defaultdict(int)
        for ch in key: need[ch] += 1
        if any(len(by_s[ch]) < n for ch, n in need.items()): continue
        ans = []; chosen = set()
        for ch in key:
            lst = [k for k in by_s[ch] if k not in chosen]
            lst.sort(key=lambda k: (-(free_clues(k, L)[0] or 0) if L > 1 else 0, -len(k) if L == 3 else 0, rng.random()))
            k = rng.choice(lst[:max(2, len(lst) // 3)])
            chosen.add(k); ans.append(k)
        used_combo.add(key)
        rows = [{'a': k, 'c': take(k, L, rng)} for k in ans]
        sy = []
        for k in ans: sy += B.syllables(W[k]['acc'])
        sy.sort()
        return {'mode': 'iniciales', 'author': a, 'work': w, 'rows': rows, 'syl': sy}
    return None

# ---------------- grillas ----------------
GRID = {'cw': {1: (13, 13, 26, 20, 11), 2: (13, 13, 28, 21, 12), 3: (15, 15, 34, 26, 13)},
        'ad': {1: (10, 10, 16, 11, 9), 2: (11, 11, 18, 12, 10), 3: (12, 12, 22, 14, 11)}}

FLOOR = {'cw': {1: 14, 2: 14, 3: 18}, 'ad': {1: 9, 2: 10, 3: 11}}
MINW = {k: {L: v[L][3] for L in v} for k, v in GRID.items()}

def make_grid(kind, L, rng):
    R, C, target, _, maxlen = GRID[kind][L]
    minw = MINW[kind][L]
    p = pool(L, 3, maxlen)
    if len(p) < 3 * FLOOR[kind][L]: return None
    best = None
    for attempt in range(4):
        sc, grid, cl, placed = build_grid(p, R, C, target, rng, autodef=(kind == 'ad'), tries=10, maxlen=maxlen)
        if best is None or len(placed) > len(best[3]): best = (sc, grid, cl, placed)
        if len(placed) >= minw: break
    sc, grid, cl, placed = best
    if len(placed) < minw:
        if minw > FLOOR[kind][L]:
            MINW[kind][L] -= 1
            return make_grid(kind, L, rng)
        return None
    words = []
    if kind == 'cw':
        num = number_grid(grid, placed)
        for x in placed:
            words.append({'n': num[(x['r'], x['c'])], 'd': x['d'], 'r': x['r'], 'c': x['c'], 'a': x['w'], 'q': take(x['w'], L, rng)})
        words.sort(key=lambda x: (x['d'], x['n']))
    else:
        for x in placed:
            dr, dc = (0, 1) if x['d'] == 'A' else (1, 0)
            words.append({'d': x['d'], 'r': x['r'], 'c': x['c'], 'cr': x['r'] - dr, 'cc': x['c'] - dc, 'a': x['w'], 'q': take(x['w'], L, rng)})
    return {'R': R, 'C': C, 'grid': [''.join(ch or '#' for ch in row) for row in grid], 'words': words}

# ---------------- sopa ----------------
ALPH = B.ALPH; DIRS8 = B.DIRS8
SP = {1: (12, 12, 11), 2: (13, 13, 13), 3: (15, 15, 16)}

def make_sp(L, rng):
    R, C, nw = SP[L]
    p = pool(L, 4, R)
    if len(p) < 2 * nw: return None
    for attempt in range(30):
        grid = [[None] * C for _ in range(R)]
        words = []
        for w in rng.sample(p, len(p)):
            if len(words) >= nw: break
            if any(w in x['a'] or x['a'] in w for x in words): continue
            opts = []
            for r in range(R):
                for c in range(C):
                    for dr, dc in DIRS8:
                        er, ec = r + dr * (len(w) - 1), c + dc * (len(w) - 1)
                        if not (0 <= er < R and 0 <= ec < C): continue
                        ov = 0; ok = True
                        for k, ch in enumerate(w):
                            g = grid[r + dr * k][c + dc * k]
                            if g is not None and g != ch: ok = False; break
                            if g == ch: ov += 1
                        if ok and ov < len(w): opts.append((ov, rng.random(), r, c, dr, dc))
            if not opts: continue
            opts.sort(reverse=True)
            _, _, r, c, dr, dc = opts[0] if rng.random() < .6 else rng.choice(opts)
            for k, ch in enumerate(w): grid[r + dr * k][c + dc * k] = ch
            words.append({'a': w, 'r': r, 'c': c, 'dr': dr, 'dc': dc})
        if len(words) < nw: continue
        for _ in range(nw * (1 + L)):
            w = rng.choice(words)['a']; frag = w[:rng.randint(3, min(5, len(w) - 1))]
            r, c = rng.randrange(R), rng.randrange(C); dr, dc = rng.choice(DIRS8)
            cells = [(r + dr * k, c + dc * k) for k in range(len(frag))]
            if all(0 <= a < R and 0 <= b < C and grid[a][b] is None for a, b in cells):
                for (a, b), ch in zip(cells, frag): grid[a][b] = ch
        for r in range(R):
            for c in range(C):
                if grid[r][c] is None: grid[r][c] = rng.choice(ALPH)
        def count(w):
            n = 0
            for r in range(R):
                for c in range(C):
                    if grid[r][c] != w[0]: continue
                    for dr, dc in DIRS8:
                        er, ec = r + dr * (len(w) - 1), c + dc * (len(w) - 1)
                        if 0 <= er < R and 0 <= ec < C and all(grid[r + dr * k][c + dc * k] == w[k] for k in range(len(w))): n += 1
            return n
        if any(count(x['a']) != 1 for x in words): continue
        for x in words: x['q'] = take(x['a'], L, rng)
        return {'R': R, 'C': C, 'grid': [''.join(row) for row in grid], 'words': words}
    return None

if __name__ == '__main__':
    rng = random.Random(3033)
    out = {t: {1: [], 2: [], 3: []} for t in ('claringrilla', 'crucigrama', 'autodefinido', 'sopa')}
    makers = {'claringrilla': make_cg, 'crucigrama': lambda L, r: make_grid('cw', L, r),
              'autodefinido': lambda L, r: make_grid('ad', L, r), 'sopa': make_sp}
    # Primero las claringrillas (el juego favorito), hasta 40 por nivel: se quedan con las iniciales que necesitan
    CG_CAP = 40
    for rnd in range(CG_CAP):
        for L in (1, 2, 3):
            if len(out['claringrilla'][L]) > rnd: continue
            g = make_cg(L, rng)
            if g: out['claringrilla'][L].append(g)
        print('claringrillas', [len(out['claringrilla'][L]) for L in (1, 2, 3)], 'usadas', len(USED_W), file=sys.stderr, flush=True)
    alive = {(t, L) for t in out for L in (1, 2, 3) if t != 'claringrilla'}
    rnd = 0
    fails = {}
    while alive:
        rnd += 1
        for L in (1, 2, 3):
            for t in ('crucigrama', 'claringrilla', 'autodefinido', 'sopa'):
                if (t, L) not in alive: continue
                g = makers[t](L, rng)
                if g is None:
                    fails[(t, L)] = fails.get((t, L), 0) + 1
                    if fails[(t, L)] >= 3: alive.discard((t, L))
                    continue
                fails[(t, L)] = 0
                out[t][L].append(g)
        print('ronda', rnd, 'usadas', len(USED_W), 'de', len(W), {t: [len(out[t][L]) for L in (1, 2, 3)] for t in out}, file=sys.stderr, flush=True)
    json.dump(out, open(os.path.join(HERE, 'games4.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
