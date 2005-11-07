def DFS2(graph, start, rlevel=0, seen = None):
    if seen is None: seen = {}
    seen[start] = 1 # allow for jumping into arbitrary subtrees with
                    # same seen dict in new generator ?
    for v in graph[start]:
        is_back = v in seen
        seen[v] = True # ok if redundant
        yield (start, v), is_back, rlevel
        if not is_back:
            if v in graph:
                for e in DFS2(graph, v, rlevel+1, seen):
                    yield e

if __name__ == '__main__':
    G = {
            1:      (2,3),
            2:      (3,5),
            3:      (4,),
            4:      (6,),
            5:      (2,6),
            6:      (1,),
            }
    for e, is_back, level in DFS2(G, 1):
        print '%s%s -> %s%s' %(level*'     ',e[0], e[1], ('',' (back)')[is_back])
