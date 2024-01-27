from minizinc import Solver, Model, Instance
import numpy as np
import pandas as pd
import datetime
import matplotlib.pyplot as plt

gold = pd.read_csv("GLD.csv")
stock = pd.read_csv("^IXIC.csv")

budget = 50000
stockAmount = 0.0
goldAmount = 0
bondAmount = []
startTime = datetime.datetime.strptime("2022-05-02", "%Y-%m-%d")
endTime = datetime.datetime.strptime("2023-11-29", "%Y-%m-%d")

# functions


def saleBond(value):
    for d in range(1, 28):
        for bond in bondAmount:
            if value == 0:
                break
            if (startTime - bond[1]).days % 28 == d and (startTime - bond[1]).days > 28:
                if bond[0] > value:
                    bond[0] -= value
                    value = 0
                    break
                else:
                    value -= bond[0]
                    bond[0] = 0
        if value <= 0:
            break


def dateToNumber(dates):
    datesInNumber = []
    for d in dates:
        tempTime = datetime.datetime.strptime(d, "%Y-%m-%d")
        datesInNumber.append((tempTime - startTime).days)

    return datesInNumber


def getLastData(decisionDate, dataFrame, week=1):
    dates = (dataFrame[(dataFrame["Date"] <= decisionDate.strftime("%Y-%m-%d")) & (dataFrame["Date"]
             >= (decisionDate - datetime.timedelta(weeks=week)).strftime("%Y-%m-%d"))]["Date"].to_list())
    prices = (dataFrame[(dataFrame["Date"] <= decisionDate.strftime("%Y-%m-%d")) & (dataFrame["Date"]
              >= (decisionDate - datetime.timedelta(weeks=week)).strftime("%Y-%m-%d"))]["Close"].to_list())

    return dates, prices
# functions end


while startTime <= endTime:
    # gold close price
    dates, goldClosedPrice = getLastData(startTime, gold, 1)
    dates2, goldClosedPrice2 = getLastData(
        startTime, gold, 2)
    # stock close price
    dates, stockClosedPrice = getLastData(startTime, stock, 1)
    dates2, stockClosedPrice2 = getLastData(
        startTime, stock, 2)

    solver = Solver.lookup("cbc")
    model = Model("./Prediction.mzn")
    # week - 1
    instance_gold = Instance(solver, model)
    instance_gold["numberOfDays"] = len(dates)
    instance_gold["days"] = [float(i) for i in dateToNumber(dates)]
    instance_gold["price"] = goldClosedPrice
    result_gold = instance_gold.solve()
    # week - 2
    instance_gold2 = Instance(solver, model)
    instance_gold2["numberOfDays"] = len(dates2)
    instance_gold2["days"] = [float(i) for i in dateToNumber(dates2)]
    instance_gold2["price"] = goldClosedPrice2
    result_gold2 = instance_gold2.solve()

    # week - 1
    instance_stock = Instance(solver, model)
    instance_stock["numberOfDays"] = len(dates)
    instance_stock["days"] = [float(i) for i in dateToNumber(dates)]
    instance_stock["price"] = stockClosedPrice
    result_stock = instance_stock.solve()
    # week - 2
    instance_stock2 = Instance(solver, model)
    instance_stock2["numberOfDays"] = len(dates2)
    instance_stock2["days"] = [float(i) for i in dateToNumber(dates2)]
    instance_stock2["price"] = stockClosedPrice2
    result_stock2 = instance_stock2.solve()

    # plotting
    # plt.plot(dates, goldClosedPrice, dates, [
    #     float(result_gold["a"]) * d + float(result_gold["b"]) for d in dateToNumber(dates)])

    # plt.show()
    # plt.plot(dates, stockClosedPrice, dates, [
    #     float(result_stock["a"]) * d + float(result_stock["b"]) for d in dateToNumber(dates)])
    # plt.show()
    # Convert dates to numbers
    # date_numbers = dateToNumber(dates)

    # Set the width of the figure
    # Adjust the width (10 inches) and height (6 inches) as needed
    # fig, axs = plt.subplots(2, 1, figsize=(10, 6))

    # 1st subplot
    # axs[0].plot(dates, goldClosedPrice, label='Gold Closed Price')
    # axs[0].plot(dates, [float(result_gold["a"]) * d + float(result_gold["b"])
    #             for d in date_numbers], label='Regression Line')
    # axs[0].legend()

    # # 2nd subplot
    # axs[1].plot(dates, stockClosedPrice, label='Stock Closed Price')
    # axs[1].plot(dates, [float(result_stock["a"]) * d + float(result_stock["b"])
    #             for d in date_numbers], label='Regression Line')
    # axs[1].legend()

    # # Adjust layout to prevent clipping of labels
    # plt.tight_layout()

    # Show the plot
    # plt.show()

    model_decision = Model("./main.mzn")
    instance_decision = Instance(solver, model_decision)
    instance_decision["budget"] = budget
    instance_decision["goldAmount"] = goldAmount
    instance_decision["stockAmount"] = stockAmount
    instance_decision["saleableBondAmount"] = sum([
        i[0] for i in bondAmount if i[1] < startTime - datetime.timedelta(weeks=4)
    ])
    instance_decision["goldCurrentPrice"] = goldClosedPrice[-1]
    instance_decision["goldPredictedPrice"] = ((2 * result_gold["a"] + result_gold2["a"])/3) * \
        (dateToNumber(dates)[-1]+7) + result_gold["b"]
    instance_decision["stockCurrentPrice"] = stockClosedPrice[-1]
    instance_decision["stockPredictedPrice"] = ((2 * result_stock["a"] + result_stock2["a"])/3) * \
        (dateToNumber(dates)[-1]+7) + result_stock["b"]
    result_decision = instance_decision.solve()

    print(result_decision)

    goldAmount += result_decision["goldDiff"]
    stockAmount += result_decision["stockDiff"]
    if result_decision["bondDiff"] > 0:
        bondAmount.append([result_decision["bondDiff"], startTime])
    elif result_decision["bondDiff"] < 0:
        saleBond(abs(result_decision["bondDiff"]))

    budget = budget - (result_decision["goldDiff"] * instance_decision["goldCurrentPrice"] +
                       result_decision["stockDiff"] * instance_decision["stockCurrentPrice"] + result_decision["bondDiff"])

    for i in bondAmount:
        if (startTime - i[1]).days % 28 == 0 and (i[1] - startTime).days != 0:
            budget += i[0] * 0.0054

    print(
        f"date:{startTime.strftime('%Y-%m-%d')}, total : {budget + goldAmount * goldClosedPrice[-1] + stockAmount * stockClosedPrice[-1] + sum([i[0] for i in bondAmount])}, budget: {budget}, goldAmount: {goldAmount}, stockAmount: {stockAmount}, bondAmount: {sum([i[0] for i in bondAmount])}")
    print()
    startTime += datetime.timedelta(weeks=1)
