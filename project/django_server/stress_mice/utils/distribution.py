#!/usr/bin/python
import glob
import os
import sys

data = {}

group_labels = {
    "group1": "+",
    "group2": "-"
}

dir = sys.argv[1]
mode = sys.argv[2]

if mode == "gene": index = -1
elif mode == "transcript": index = -5
else:
	sys.stderr.write("Please provide a mode between 'gene' and 'transcript'!\n")
	sys.exit()

files = glob.glob(dir + "*")
for file in files:
    separator = ""
    if file.endswith(".tsv"): separator = "\t"
    if file.endswith(".csv"): separator = ","
    
    id = os.path.splitext(os.path.basename(file))[0]
    
    met = set()
    
    with open(file, "r") as reader:
        reader.readline()
        for line in reader:
            line = line.rstrip('\n')
            fields = line.split(separator)

            if mode == "gene": fc = float(fields[3]) 
            elif mode == "transcript": fc = float(fields[2])
            
            group = "group1" if fc >= 0 else "group2"
            label = fields[index] if fields[index] != '"."' else fields[index-1]
            label = label.replace('"', "")
            
            if label in met: continue
            met.add(label)
            
            if label not in data:
                data[label] = {'group1': 0, 'group2': 0, 'who': []}

            datum = data[label]
                
            datum[group] += 1
            datum['who'].append(id)

# Let's sort
sorted_data = sorted(data, key=lambda x: data[x]['group1'] + data[x]['group2'], reverse=True)

for label in sorted_data:
        datum = data[label]
        g1 = datum['group1']
        g2 = datum['group2']
        sys.stdout.write(label + "\t" + str(g1)+group_labels["group1"] + str(g2)+group_labels["group2"] + "\t" + "|".join([str(x) for x in datum['who']]) + "\n")
