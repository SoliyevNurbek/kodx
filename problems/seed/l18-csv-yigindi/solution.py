import csv
import sys

reader = csv.reader(sys.stdin)
next(reader)
print(sum(int(row[1]) for row in reader if row))
