import shelve

d = shelve.open("userstats", writeback=False)

for k,v in d.items():
    print("{} : {}".format(k, v))

d.close()
