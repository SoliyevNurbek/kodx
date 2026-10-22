import sys

data = sys.stdin.read().split()
n = int(data[0])
print("/" + "/".join(data[1:1 + n]))
