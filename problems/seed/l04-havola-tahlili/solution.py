url = input().strip()
prefix = "git@github.com:"
rest = url[len(prefix):] if url.startswith(prefix) else url.split("github.com/", 1)[1]
rest = rest.strip("/")
if rest.endswith(".git"):
    rest = rest[:-4]
owner, repo = rest.split("/")[:2]
print(owner)
print(repo)
