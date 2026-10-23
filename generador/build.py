import json, random, re, unicodedata, sys
from collections import defaultdict
sys.path.insert(0, '.')
from authors import clean as clean_authors

BAD = {"AZUZ", "BANDOLEON", "MALEVO", "OTRA", "ALAR", "ORE", "POSA", "ESTOLA", "TESTA", "ALI"}

def norm(s):
    s = s.upper().replace('Ñ', '\0')
    s = ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
    return s.replace('\0', 'Ñ')

def load_words():
    W = {}
    for fn in ['words1.txt', 'words2.txt', 'words3.txt', 'words4.txt']:
        for line in open(fn, encoding='utf-8'):
            line = line.strip()
            if not line: continue
            w, clue, d = line.split('|')
            w = norm(w)
            if ' ' in w or w in BAD or not re.fullmatch('[A-ZÑ]+', w): continue
            d = int(d)
            if d > 3: continue
            if w in norm(clue).replace(' ', '') and len(w) > 2: continue
            if w not in W:
                W[w] = {'w': w, 'clues': [], 'd': d}
            if clue not in W[w]['clues']:
                W[w]['clues'].append(clue)
            W[w]['d'] = min(W[w]['d'], d)
    return W

WORDS = load_words()

# ---------------- syllabification ----------------
V = set('AEIOU')
STRONG = set('AEO')
INSEP = {'PR','PL','BR','BL','FR','FL','TR','DR','CR','CL','GR','GL','CH','LL','RR','KR'}

def tokens(w):
    out = []; i = 0
    while i < len(w):
        if w[i:i+2] in ('CH','LL','RR'):
            out.append(w[i:i+2]); i += 2
        elif w[i:i+2] in ('QU','GU') and i+2 < len(w) and w[i+2] in 'EI':
            out.append(w[i:i+2]); i += 2   # treat qu/gu as consonant unit
        else:
            out.append(w[i]); i += 1
    return out

def isv(t): return t in V or t == 'Y_V'

def syllables(w):
    t = tokens(w)
    # mark Y as vowel when final or between consonants
    kinds = []
    for i, x in enumerate(t):
        if x in V: kinds.append('V')
        elif x == 'Y' and (i == len(t)-1 or (i+1 < len(t) and t[i+1] not in V)): kinds.append('V')
        else: kinds.append('C')
    # find nuclei: group consecutive vowels, split strong-strong (hiatus)
    groups = []  # list of (start,end) vowel nuclei
    i = 0
    while i < len(t):
        if kinds[i] == 'V':
            j = i
            while j+1 < len(t) and kinds[j+1] == 'V':
                a, b = t[j], t[j+1]
                if a in STRONG and b in STRONG: break
                j += 1
            groups.append((i, j)); i = j+1
        else:
            i += 1
    if len(groups) <= 1: return [w]
    cuts = []
    for g in range(len(groups)-1):
        e = groups[g][1]; s = groups[g+1][0]
        cons = t[e+1:s]
        n = len(cons)
        if n == 0: cut = s
        elif n == 1: cut = e+1
        elif n == 2:
            cut = e+1 if (cons[0]+cons[1]) in INSEP else e+2
        elif n == 3:
            cut = e+2 if (cons[1]+cons[2]) in INSEP else e+3
        else:
            cut = e+3
        cuts.append(cut)
    out = []; prev = 0
    for c in cuts:
        out.append(''.join(t[prev:c])); prev = c
    out.append(''.join(t[prev:]))
    return out

# ---------------- helpers ----------------
def clue_for(word, rng):
    return rng.choice(WORDS[word]['clues'])

def pool(maxd, minlen=3, maxlen=99):
    return [w for w, e in WORDS.items() if e['d'] <= maxd and minlen <= len(w) <= maxlen]

# ---------------- claringrilla ----------------
def _pick(cands, used, rng, maxd):
    c = [w for w in cands if w not in used and WORDS[w]['d'] <= maxd]
    if not c: return None
    c.sort(key=lambda w: (WORDS[w]['d'], rng.random()))
    return c[min(len(c)-1, int(rng.random()**1.5 * min(len(c), 6)))]

def _pack(author, work, answers, rng, mode):
    sy = []
    for w in answers: sy += syllables(w)
    sy.sort()
    return {'mode': mode, 'author': author, 'work': work,
            'rows': [{'a': w, 'c': clue_for(w, rng)} for w in answers], 'syl': sy}

def make_claringrillas():
    by_ends = defaultdict(list); by_start = defaultdict(list)
    for w, e in WORDS.items():
        if 4 <= len(w) <= 9:
            by_ends[(w[0], w[-1])].append(w); by_start[w[0]].append(w)
    res = {1: [], 2: [], 3: []}
    seen = set()
    rng = random.Random(7)
    authors = clean_authors()
    # modo clasico: iniciales = autor, finales = obra
    for author, works in authors:
        A = norm(author).replace(' ', '')
        for work in works:
            Wk = norm(work).replace(' ', '')
            if len(A) != len(Wk) or (A, Wk) in seen: continue
            for v in range(2):
                used = set(); answers = []
                for i in range(len(A)):
                    p = _pick(by_ends[(A[i], Wk[i])], used, rng, 3)
                    if not p: break
                    used.add(p); answers.append(p)
                if len(answers) != len(A): break
                if tuple(answers) in seen: continue
                seen.add(tuple(answers)); seen.add((A, Wk))
                res[3].append(_pack(author, work, answers, rng, 'clasica'))
    # modo iniciales: las iniciales forman autor + obra
    for author, works in authors:
        A = norm(author).replace(' ', '')
        for work in works:
            Wk = norm(work).replace(' ', '')
            key = A + Wk
            n = len(key)
            if n < 7 or n > 18 or key in seen: continue
            seen.add(key)
            diff = 1 if n <= 12 else (2 if n <= 15 else 3)
            maxd = {1: 1, 2: 2, 3: 3}[diff]
            used = set(); answers = []
            for ch in key:
                p = _pick(by_start[ch], used, rng, maxd) or _pick(by_start[ch], used, rng, 3)
                if not p: break
                used.add(p); answers.append(p)
            if len(answers) != n: continue
            res[diff].append(_pack(author, work, answers, rng, 'iniciales'))
    for d in res: rng.shuffle(res[d])
    return res

# ---------------- freeform crossword engine ----------------
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

def make_crosswords(count_per):
    cfg = {1: (9, 9, 14, 1, 7), 2: (11, 11, 18, 2, 9), 3: (13, 13, 25, 3, 11)}
    out = {}
    for diff, (R, C, target, maxd, maxlen) in cfg.items():
        rng = random.Random(100 + diff)
        p = pool(maxd)
        lst = []; sigs = set()
        while len(lst) < count_per:
            sc, grid, _, placed = build_grid(p, R, C, target, rng, tries=20, maxlen=maxlen)
            if len(placed) < target * 0.8: continue
            sig = tuple(sorted(x['w'] for x in placed))
            if sig in sigs: continue
            sigs.add(sig)
            num = number_grid(grid, placed)
            words = []
            for x in placed:
                cl = WORDS[x['w']]['clues']
                # harder level prefers later (more cultured) clue when there are several
                c = cl[-1] if diff == 3 else rng.choice(cl)
                words.append({'n': num[(x['r'], x['c'])], 'd': x['d'], 'r': x['r'], 'c': x['c'], 'a': x['w'], 'q': c})
            words.sort(key=lambda x: (x['d'], x['n']))
            lst.append({'R': R, 'C': C, 'grid': [''.join(ch or '#' for ch in row) for row in grid], 'words': words})
            print('cw', diff, len(lst), len(placed), file=sys.stderr)
        out[diff] = lst
    return out

def make_autodef(count_per):
    cfg = {1: (8, 8, 10, 1, 7), 2: (9, 9, 12, 2, 8), 3: (10, 10, 14, 3, 9)}
    out = {}
    for diff, (R, C, target, maxd, maxlen) in cfg.items():
        rng = random.Random(200 + diff)
        p = pool(maxd)
        lst = []; sigs = set()
        while len(lst) < count_per:
            sc, grid, clue, placed = build_grid(p, R, C, target, rng, autodef=True, tries=20, maxlen=maxlen)
            if len(placed) < target * 0.8: continue
            sig = tuple(sorted(x['w'] for x in placed))
            if sig in sigs: continue
            sigs.add(sig)
            words = []
            for x in placed:
                cl = WORDS[x['w']]['clues']
                c = cl[-1] if diff == 3 else rng.choice(cl)
                dr, dc = (0, 1) if x['d'] == 'A' else (1, 0)
                words.append({'d': x['d'], 'r': x['r'], 'c': x['c'], 'cr': x['r']-dr, 'cc': x['c']-dc, 'a': x['w'], 'q': c})
            lst.append({'R': R, 'C': C, 'grid': [''.join(ch or '#' for ch in row) for row in grid], 'words': words})
            print('ad', diff, len(lst), len(placed), file=sys.stderr)
        out[diff] = lst
    return out

# ---------------- word search ----------------
ALPH = 'AAAAABCDEEEEEFGHIIIIJLLMNNÑOOOOOPQRRRSSSTTTUUVZ'
def make_sopas(count_per):
    cfg = {1: (9, 9, 8, [(0,1),(1,0)]),
           2: (11, 11, 11, [(0,1),(1,0),(1,1),(-1,1)]),
           3: (13, 13, 15, [(0,1),(1,0),(1,1),(-1,1),(0,-1),(-1,0),(-1,-1),(1,-1)])}
    themes = {}
    out = {}
    for diff, (R, C, nwords, dirs) in cfg.items():
        rng = random.Random(300 + diff)
        p = [w for w in pool(min(diff+1, 3), 4, R)]
        lst = []
        while len(lst) < count_per:
            grid = [[None]*C for _ in range(R)]
            words = []
            cand = rng.sample(p, len(p))
            for w in cand:
                if len(words) >= nwords: break
                opts = []
                for r in range(R):
                    for c in range(C):
                        for dr, dc in dirs:
                            er, ec = r+dr*(len(w)-1), c+dc*(len(w)-1)
                            if not (0 <= er < R and 0 <= ec < C): continue
                            ov = 0; ok = True
                            for k, ch in enumerate(w):
                                g = grid[r+dr*k][c+dc*k]
                                if g is not None and g != ch: ok = False; break
                                if g == ch: ov += 1
                            if ok and ov < len(w): opts.append((ov, rng.random(), r, c, dr, dc))
                if not opts: continue
                opts.sort(reverse=True)
                ov, _, r, c, dr, dc = opts[0] if rng.random() < .5 else rng.choice(opts)
                for k, ch in enumerate(w): grid[r+dr*k][c+dc*k] = ch
                words.append({'a': w, 'r': r, 'c': c, 'dr': dr, 'dc': dc})
            if len(words) < nwords: continue
            for r in range(R):
                for c in range(C):
                    if grid[r][c] is None: grid[r][c] = rng.choice(ALPH)
            # ensure each word appears exactly once in all 8 dirs
            text = [''.join(row) for row in grid]
            def count(w):
                n = 0
                for r in range(R):
                    for c in range(C):
                        for dr, dc in [(0,1),(1,0),(1,1),(-1,1),(0,-1),(-1,0),(-1,-1),(1,-1)]:
                            er, ec = r+dr*(len(w)-1), c+dc*(len(w)-1)
                            if 0 <= er < R and 0 <= ec < C and all(grid[r+dr*k][c+dc*k] == w[k] for k in range(len(w))):
                                n += 1
                return n
            if any(count(x['a']) != 1 for x in words): continue
            lst.append({'R': R, 'C': C, 'grid': text, 'words': words})
        out[diff] = lst
        print('sopa', diff, len(lst), file=sys.stderr)
    return out

if __name__ == '__main__':
    print('palabras:', len(WORDS), file=sys.stderr)
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    cl = make_claringrillas()
    print('claringrillas', {k: len(v) for k, v in cl.items()}, file=sys.stderr)
    data = {
        'claringrilla': cl,
        'crucigrama': make_crosswords(N),
        'autodefinido': make_autodef(N),
        'sopa': make_sopas(N),
    }
    json.dump(data, open('games.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
