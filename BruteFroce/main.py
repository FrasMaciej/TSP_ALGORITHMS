from pathlib import Path
import itertools
import sys
import time
import csv

configPath = "config.ini"
resultPath = ""
measuresAmount = 0

# Wczytanie danych wejściowych z pliku tekstowego


def readIni(configPath):
    with open(configPath) as file:
        fileContent = csv.reader(file, delimiter=' ')
        next(fileContent)
        fileContent = list(fileContent)
    output_path = fileContent.pop()[0]
    return fileContent, output_path


def readGraph(graphPath):
    f = open(graphPath, "r")  # otwarcie pliku
    size = int(f.readline())
    graphStr = []
    for line in f.readlines():
        graphStr.append(line.split())
    graphInt = []
    for i in range(0, len(graphStr)):
        graphInt.append([])
        for j in range(0, len(graphStr[i])):
            graphInt[i].append(int(graphStr[i][j]))
    return graphInt, size


def findBestPath(graph, size):
    paths = []
    bestPath = []
    bestCost = sys.maxsize
    nodes = []
    for i in range(1, size):
        nodes.append(i)
        # Znajdź wszystkie permutacje zbioru wierzchołków
    paths = itertools.permutations(nodes)
    for p in paths:
        newCost = 0
        for i in range(0, size-2):
            # Oblicz koszt ścieżki
            newCost += graph[p[i]][p[i+1]]
        newCost += graph[0][p[0]]
        newCost += graph[p[len(p)-1]][0]
        # Sprawdzenie czy znaleziono naniższy koszt ścieżki
        if (newCost < bestCost):
            bestPath = list(p)
            bestCost = newCost
    bestPath.append(0)
    bestPath.insert(0, 0)
    return bestPath, bestCost


def main():
    fileContent, resultPath = readIni(configPath)
    print(resultPath)
    print('Wczytano pliki:')
    for file in fileContent:
        print(file[0])
    print('Nazwa pliku z wynikami: ' + resultPath)
    print('-------------------------------------------------------------')
    f = open(resultPath, "x")
    for file in fileContent:
        print(file)
        graph, graphSize = readGraph(file[0])
        measuresAmount = int(file[1])
        timeSum = 0
        f.write(str(file) + '\n')
        f.write('---\n')
        for i in range(1, measuresAmount+1):
            t1 = time.time()
            t2 = t1
            bestPath, bestCost = findBestPath(graph, graphSize)
            while t1 == t2:
                t2 = time.time()
            t2 = time.time()
            t = t2 - t1
            f.write(str(t) + ' ' + str(bestCost) + ' ' + str(bestPath) + '\n')
            timeSum += t
            print('Wykonano pomiar nr ' + str(i) + ', wynik: ' + str(t))
        averageResult = timeSum/measuresAmount
        print("Usredniony wynik pomiaru dla " + str(measuresAmount) +
              " instancji: " + str(averageResult))
        # Zapisanie wyniku średniego do pliku
        f.write('---\n')
        f.write("Usredniony wynik pomiaru dla " + str(measuresAmount) +
                " instancji: " + str(averageResult) + '\n')
        f.write(
            '------------------------------------------------------------------------------' + '\n')
        print('-------------------------------------------------------------')


if __name__ == "__main__":
    main()
