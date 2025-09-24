s = r"\"../../../build/./tsclient -i shm:%s -o tcp://*:5556\""
print("Original:", s)

# Strip the first and last backslash
cleaned = s[1:-1]
print("Cleaned:", cleaned)
