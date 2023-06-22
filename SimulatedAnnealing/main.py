import time
import csv
import tsplib95
import networkx
import random
import math
import copy

configPath = "config.ini"
resultPath = ""
measuresAmount = 0
_initialTemp = 0.0
_finishTemp = 0.0
_alpha = 0.0
cities = list()
matrix = []
weightMatrix = []
_cooling = 1
_neighbourSolution = 1
_iterations = 1
_eraIterations = 1
_finishTemp = 1

# Wczytanie danych wejściowych z pliku tekstowego


def readIni(configPath):
    global _initialTemp, _finishTemp, _alpha
    with open(configPath) as file:
        fileContent = csv.reader(file, delimiter=' ')
        next(fileContent)
        fileContent = list(fileContent)
    output_path = fileContent.pop()[0]
    return fileContent, output_path

# Wczytanie grafu z pliku o danej nazwie


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


# Algorytm ---------------------------------------------------------------------------------------------------------

def simulatedAnnealing(citiesList):
    global _initialTemp, _alpha, weightMatrix, _cooling, _eraIterations, _finishTemp

    initial_temp = _initialTemp
    alpha = _alpha
    current_temp = initial_temp
    finishTemp = _finishTemp

    random.shuffle(citiesList)
    solution = citiesList

    same_solution = 0
    same_cost_diff = 0

    eraIterations = _eraIterations
    iterations = _iterations

    iteration = 1
    while current_temp > finishTemp and same_solution < 10000 and same_cost_diff < 100000:
        for i in range(eraIterations):
            neighbor = get_neighbors(solution)
            cost_diff = get_cost(neighbor) - get_cost(solution)
            if cost_diff > 0:
                solution = neighbor
                same_solution = 0
                same_cost_diff = 0
            elif cost_diff == 0:
                solution = neighbor
                same_solution = 0
                same_cost_diff += 1
            else:
                # Określenie prawdopodobieństwa ruchu z x0 do x
                if random.uniform(0, 1) <= math.exp(float(cost_diff) / float(current_temp)):
                    solution = neighbor
                    same_solution = 0
                    same_cost_diff = 0
                else:
                    same_solution += 1
                    same_cost_diff += 1
        # Zmniejszanie temperatury
        if _cooling == 1:
            # Schemat geometryczny
            current_temp = initial_temp * (alpha ** iteration)
        elif _cooling == 2:
            # Schemat liniowy
            current_temp = initial_temp/(1.0 + (alpha*iteration))
        iteration += 1
    return solution, 1/get_cost(solution)


def get_cost(state):
    global matrix
    distance = 0

    for i in range(len(state)):
        from_city = state[i]
        to_city = None
        if i+1 < len(state):
            to_city = state[i+1]
        else:
            to_city = state[0]
        distance += matrix.get_weight(from_city, to_city)
    fitness = 1/float(distance)
    return fitness


def get_neighbors(state):
    global _neighbourSolution
    neighbor = copy.deepcopy(state)
    func = _neighbourSolution
    if func == 1:
        swap(neighbor)      # 2-zamiana
    elif func == 2:
        inverse(neighbor)
    return neighbor


def inverse(state):
    node_one = random.choice(state)
    new_list = list(filter(lambda city: city != node_one, state))
    node_two = random.choice(new_list)
    state[min(node_one, node_two):max(node_one, node_two)] = state[min(
        node_one, node_two):max(node_one, node_two)][::-1]

    return state


def swap(state):
    pos_one = random.choice(range(len(state)))
    pos_two = random.choice(range(len(state)))
    state[pos_one], state[pos_two] = state[pos_two], state[pos_one]

    return state
# Algorytm ---------------------------------------------------------------------------------------------------------


def main():
    global matrix, cities, weightMatrix
    global _initialTemp, _finishTemp, _alpha, _neighbourSolution, _cooling, _iterations, _eraIterations

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
        global matrix
        if (file[0].endswith('.txt') or file[0].endswith('.csv')):
            inputFile = readGraph(file[0])
        else:
            matrix = tsplib95.load(file[0])
            graph = matrix.get_graph()
            weightMatrix = networkx.to_numpy_array(graph)
            cities = list(matrix.get_nodes())
        print(matrix)
        measuresAmount = int(file[1])
        optimalCost = float(file[2])
        timeSum = 0
        lowestResult = 999999999999999999999999999999
        lowestResultPath = []
        lowestResultError = 0
        biggestResult = 0
        biggestResultPath = []
        biggestResultError = 0

        bestFoundResult = 0
        bestFoundResultPath = []
        bestFoundResultError = 999999999999999999999999999999

        f.write(str(file[0]) + ', optymalny koszt: ' + str(file[2]) + ', temp. poczatkowa: ' + str(
            file[4]) + ', temp. koncowa:' + str(file[5]) + ', wsp. schladzania: ' + str(file[7]) + '\n')
        f.write('---\n')
        percentageSum = 0
        for i in range(1, measuresAmount+1):
            _initialTemp = float(file[4])
            _finishTemp = float(file[5])
            _eraIterations = int(file[6])
            _alpha = float(file[7])
            _neighbourSolution = int(file[8])
            _cooling = int(file[9])

            t1 = time.time()
            t2 = t1
            bestPath, bestCost = simulatedAnnealing(cities)
            while t1 == t2:
                t2 = time.time()

            t2 = time.time()
            t = t2 - t1

            percentageError = round(
                (abs(optimalCost - bestCost)*100)/optimalCost, 2)
            percentageSum += percentageError

            if bestCost > biggestResult:
                biggestResult = bestCost
                biggestResultPath = bestPath
                biggestResultError = percentageError
            if bestCost < lowestResult:
                lowestResult = bestCost
                lowestResultPath = bestPath
                lowestResultError = percentageError
            if percentageError < bestFoundResultError:
                bestFoundResult = bestCost
                bestFoundResultPath = bestPath
                bestFoundResultError = percentageError

            f.write(str(t) + ' ' + str(bestCost) + ' ' +
                    str(percentageError) + '% ' + str(bestPath) + '\n')
            timeSum += t
            print('Wykonano pomiar nr ' + str(i) + ', wynik: ' + str(t))
        averageResult = timeSum/measuresAmount
        averageError = round(percentageSum/measuresAmount, 2)
        print("Usredniony wynik pomiaru dla " + str(measuresAmount) +
              " instancji: " + str(averageResult))
        # Zapisanie wyniku średniego do pliku
        f.write('---\n')
        f.write("Usredniony wynik pomiaru dla " + str(measuresAmount) +
                " instancji: " + str(averageResult) + '\n')
        f.write("Sredni blad: " + str(averageError) + '% \n')
        f.write("Najwiekszy znaleziony koszt: " + str(biggestResult) + ', blad: ' + str(biggestResultError) + '%, sciezka: ' +
                str(biggestResultPath) + '\n')
        f.write("Najmniejszy znaleziony koszt: " + str(lowestResult) + ', blad: ' + str(lowestResultError) + '%, sciezka: ' +
                str(lowestResultPath) + '\n')
        f.write("Najbardziej dokladny znaleziony koszt: " + str(bestFoundResult) + ', blad: ' + str(bestFoundResultError) + '%, sciezka: ' +
                str(bestFoundResultPath) + '%' + '\n')
        f.write(
            '------------------------------------------------------------------------------' + '\n')
        print('-------------------------------------------------------------')


if __name__ == "__main__":
    main()
