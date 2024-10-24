import csv
import matplotlib.pyplot as plt
import sys

"""
Warning: Since the path used in line 29 and 33 are relative paths, the program may fail depending on the directory you started it in. 
Thus it is recommended to start the program in the folder flesnet/app/memory_test, where it is currently saved.
"""

# reading of the csv-data
def read_csv(file_name):

    with open(file_name, newline='') as f:
        reader = csv.reader(f)
        data = list(reader)
    time = []
    memory_usage = []
    for elem in data:
        time += [int(elem[0])/1000]
        memory_usage += [int(elem[1])]
    return time,memory_usage

# plotting of the memory usage 
def plotting(time,data,title):
    plt.plot(time,data)
    plt.title(title)
    plt.xlabel("time in seconds")
    plt.ylabel("RAM usage in MB")
    plt.savefig("test_run/plots/" +title+".png")
    plt.close()

def main(file_name):
    time, memory_usage = read_csv("../../build/csv_data/"+file_name+'.csv')
    plotting(time, memory_usage,file_name)


if __name__ == "__main__":
    file_name = str(sys.argv[1])
    main(file_name)