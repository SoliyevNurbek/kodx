import sys

counts = {}
for word in sys.stdin.read().lower().split():
    counts[word] = counts.get(word, 0) + 1
for word, count in sorted(counts.items(), key=lambda item: (-item[1], item[0])):
    print(word, count)
