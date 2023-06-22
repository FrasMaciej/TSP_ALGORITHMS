import time
import csv
import tsplib95
import networkx
import random
import math
import sys

configPath = "config.ini"
resultPath = ""
Q = 10
# Wczytanie danych wejściowych z pliku tekstowego


def readIni(configPath):
    global _initialTemp, _finishTemp, _alpha
    with open(configPath) as file:
        fileContent = csv.reader(file, delimiter=' ')
        next(fileContent)
        next(fileContent)
        fileContent = list(fileContent)
    output_path = fileContent.pop()[0]
    return fileContent, output_path

# Wczytanie grafu z wybranego wcześniej pliku


def expectedCost(graphSize, matrix):
    sumCost = 0
    vert = 0
    tabu = [0] * graphSize

    tabu[0] = 1
    for i in range(0, graphSize):
        singleCost = sys.maxsize
        for j in range(0, graphSize):
            if matrix[vert][j] < singleCost and tabu[j] == 0:
                singleCost = matrix[vert][j]
                tabu[j] = 1
                vert = j
        if singleCost != sys.maxsize:
            sumCost += singleCost
    sumCost += matrix[vert][0]
    return sumCost


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

def distance(city1: dict, city2: dict):
    return math.sqrt((city1['x'] - city2['x']) ** 2 + (city1['y'] - city2['y']) ** 2)


class Graph(object):
    def __init__(self, cost_matrix: list, rank: int, expCost):
        self.matrix = cost_matrix
        self.rank = rank
        self.pheromone = [[rank / expCost
                           for j in range(rank)] for i in range(rank)]


class ACO(object):
    def __init__(self, ant_count: int, generations: int, alpha: float, beta: float, rho: float, q: int,
                 strategy: int):
        self.Q = q
        self.rho = rho
        self.beta = beta
        self.alpha = alpha
        self.ant_count = ant_count
        self.generations = generations
        self.update_strategy = strategy

    def _update_pheromone(self, graph: Graph, ants: list):
        for i, row in enumerate(graph.pheromone):
            for j, col in enumerate(row):
                # Aktualizacja stężenia feromonu
                graph.pheromone[i][j] *= self.rho
                for ant in ants:
                    # Obliczenie delty
                    graph.pheromone[i][j] += ant.pheromone_delta[i][j]

    def solve(self, graph: Graph):
        best_cost = float('inf')
        best_solution = []
        for gen in range(self.generations):
            ants = [_Ant(self, graph) for i in range(self.ant_count)]
            for ant in ants:
                for i in range(graph.rank - 1):
                    ant._select_next()
                ant.total_cost += graph.matrix[ant.tabu[-1]][ant.tabu[0]]
                if ant.total_cost < best_cost:
                    best_cost = ant.total_cost
                    best_solution = [] + ant.tabu
                # aktualizacja stężenia feromonu
                ant._update_pheromone_delta()
            self._update_pheromone(graph, ants)
        return best_solution, best_cost


class _Ant(object):
    def __init__(self, aco: ACO, graph: Graph):
        self.colony = aco
        self.graph = graph
        self.total_cost = 0.0
        self.tabu = []  # lista tabu
        self.pheromone_delta = []  # lokalne stężenie feromonu
        # Węzły dozwolone do wyboru
        self.allowed = [i for i in range(graph.rank)]
        self.eta = [[0 if i == j else 1 / graph.matrix[i][j] for j in range(graph.rank)] for i in
                    range(graph.rank)]
        # wybranie początkowego węzła w sposób losowy
        start = random.randint(0, graph.rank - 1)
        self.tabu.append(start)
        self.current = start
        self.allowed.remove(start)

    def _select_next(self):
        denominator = 0
        for i in self.allowed:
            # Obliczenie mianownika do operacji obliczania prawdopodobieństwa
            denominator += self.graph.pheromone[self.current][i] ** self.colony.alpha * self.eta[self.current][
                i] ** self.colony.beta
        # Obliczenie prawdopodobieństwa wyboru miasta przez mrówkę
        probabilities = [0 for i in range(self.graph.rank)]
        # sprawdzenie wszystkich wierzchołków
        for i in range(self.graph.rank):
            try:
                self.allowed.index(i)
                probabilities[i] = self.graph.pheromone[self.current][i] ** self.colony.alpha * \
                    self.eta[self.current][i] ** self.colony.beta / denominator
            except ValueError:
                pass
        # Wybór następnego miasta
        selected = 0
        rand = random.random()
        for i, probability in enumerate(probabilities):
            rand -= probability
            if rand <= 0:
                selected = i
                break
        self.allowed.remove(selected)
        self.tabu.append(selected)
        self.total_cost += self.graph.matrix[self.current][selected]
        self.current = selected

    def _update_pheromone_delta(self):
        self.pheromone_delta = [
            [0 for j in range(self.graph.rank)] for i in range(self.graph.rank)]
        for _ in range(1, len(self.tabu)):
            i = self.tabu[_ - 1]
            j = self.tabu[_]
            # ant-quantity system (DAS) - algorytm ilościowy - algorytm gęstościowy - Ilość feromonu na jednostkę długości jest zawsze stała; niezależna od długości krawędzi
            if self.colony.update_strategy == 1:
                self.pheromone_delta[i][j] = self.colony.Q
            # ant-density system (QAS) - stała ilosć feromonu jest dzielona przez długość krawędzi
            elif self.colony.update_strategy == 2:
                self.pheromone_delta[i][j] = self.colony.Q / \
                    self.graph.matrix[i][j]


# Algorytm ---------------------------------------------------------------------------------------------------------


def main():
    global matrix, cities, weightMatrix, Q
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
        graphSize = 0
        if (file[0].endswith('.txt') or file[0].endswith('.csv')):
            matrix, graphSize = readGraph(file[0])
        else:
            problem = tsplib95.load(file[0])
            graph = problem.get_graph()
            weightMatrix = networkx.to_numpy_array(graph)
            cities = list(problem.get_nodes())
            matrix = weightMatrix.tolist()
            graphSize = len(cities)

        print(matrix)
        aco = ACO(int(file[4]), int(file[5]), float(file[6]), float(
            file[7]), float(file[8]), Q, float(file[9]))
        rank = graphSize

        # Obliczenie szacowanej długości trasy
        expCost = expectedCost(graphSize, matrix)

        graph = Graph(matrix, rank, expCost)
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

        strategy = ''
        if int(file[9]) == 1:
            strategy = 'DAS'
        elif int(file[9]) == 2:
            strategy = 'QAS'

        f.write(str(file[0:4]) + '\n')
        f.write('m: ' + str(file[4]) + ' iteracje: ' + str(file[5]) + ' alpha: ' + str(file[6]) + ' beta: ' + str(
            file[7]) + ' rho: ' + str(file[8]) + ' strategia: ' + strategy + '\n')
        f.write('---\n')
        percentageSum = 0
        for i in range(1, measuresAmount+1):

            t1 = time.time()
            t2 = t1
            bestPath, bestCost = aco.solve(graph)
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
