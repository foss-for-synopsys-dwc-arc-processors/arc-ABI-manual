import re, fileinput

for line in fileinput.input(inplace=True):
    if re.search(r'release = u', line):
        line = re.sub(r"-(\d+)", lambda x: "-{:03}".format(int(x.group(1)) + 1), line)
    print(line.rstrip())
