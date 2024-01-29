from minizinc import Solver, Model, Instance
import numpy as np
import pandas as pd
import datetime
import matplotlib.pyplot as plt
import streamlit as st

gold = pd.read_csv("GLD.csv")
stock = pd.read_csv("^IXIC.csv")

budget = 50000
stockAmount = 0.0
goldAmount = 0
bondAmount = []
startTime = datetime.datetime.strptime("2023-05-01", "%Y-%m-%d")
endTime = datetime.datetime.strptime("2023-11-29", "%Y-%m-%d")

placeholder = st.empty()

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


def getLastMonthData(decisionDate, dataFrame):
    dates = (dataFrame[(dataFrame["Date"] <= decisionDate.strftime("%Y-%m-%d")) & (dataFrame["Date"]
             >= (decisionDate - datetime.timedelta(days=4)).strftime("%Y-%m-%d"))]["Date"].to_list())
    prices = (dataFrame[(dataFrame["Date"] <= decisionDate.strftime("%Y-%m-%d")) & (dataFrame["Date"]
              >= (decisionDate - datetime.timedelta(days=4)).strftime("%Y-%m-%d"))]["Close"].to_list())

    return dates, prices
# functions end


while startTime <= endTime:
    # gold close price
    dates, goldClosedPrice = getLastMonthData(startTime, gold)
    # stock close price
    dates, stockClosedPrice = getLastMonthData(startTime, stock)

    solver = Solver.lookup("cbc")
    model = Model("./Prediction.mzn")
    instance_gold = Instance(solver, model)
    instance_gold["numberOfDays"] = len(dates)
    instance_gold["days"] = [float(i) for i in dateToNumber(dates)]
    instance_gold["price"] = goldClosedPrice
    result_gold = instance_gold.solve()

    instance_stock = Instance(solver, model)
    instance_stock["numberOfDays"] = len(dates)
    instance_stock["days"] = [float(i) for i in dateToNumber(dates)]
    instance_stock["price"] = stockClosedPrice
    result_stock = instance_stock.solve()

    # plotting
    # plt.plot(dates, goldClosedPrice, dates, [
    #     float(result_gold["a"]) * d + float(result_gold["b"]) for d in dateToNumber(dates)])

    # plt.show()
    # plt.plot(dates, stockClosedPrice, dates, [
    #     float(result_stock["a"]) * d + float(result_stock["b"]) for d in dateToNumber(dates)])
    # plt.show()
    # Convert dates to numbers
    date_numbers = dateToNumber(dates)

    # Set the width of the figure
    # Adjust the width (10 inches) and height (6 inches) as needed
    fig, axs = plt.subplots(2, 1, figsize=(10, 6))

    # 1st subplot
    axs[0].plot(dates, goldClosedPrice, label='Gold Closed Price')
    axs[0].plot(dates, [float(result_gold["a"]) * d + float(result_gold["b"])
                for d in date_numbers], label='Regression Line')
    axs[0].legend()

    # 2nd subplot
    axs[1].plot(dates, stockClosedPrice, label='Stock Closed Price')
    axs[1].plot(dates, [float(result_stock["a"]) * d + float(result_stock["b"])
                for d in date_numbers], label='Regression Line')
    axs[1].legend()

    # # Adjust layout to prevent clipping of labels
    plt.tight_layout()

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
    instance_decision["bondAmount"] = sum([
        i[0] for i in bondAmount
    ])
    instance_decision["goldCurrentPrice"] = goldClosedPrice[-1]
    instance_decision["goldPredictedPrice"] = result_gold["a"] * \
        (dateToNumber(dates)[-1]+7) + result_gold["b"]
    instance_decision["stockCurrentPrice"] = stockClosedPrice[-1]
    instance_decision["stockPredictedPrice"] = result_stock["a"] * \
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

    with placeholder.container():
        st.title(startTime.strftime('%Y-%m-%d'))
        st.metric(label="Total", value=budget, delta=goldAmount *
                        goldClosedPrice[-1] + stockAmount * stockClosedPrice[-1] + sum([i[0] for i in bondAmount]))
        st.metric(label="Gold Amount: ", value=goldAmount,
                        delta=result_decision["goldDiff"])
        st.metric(label="Stock Amount: ", value=stockAmount,
                        delta=result_decision["stockDiff"])
        st.metric(label="Bond Amount: ", value=sum(
            [i[0] for i in bondAmount]), delta=result_decision["bondDiff"])
        st.metric(label="Total Budget: ", value=budget + goldAmount *
                        goldClosedPrice[-1] + stockAmount * stockClosedPrice[-1] + sum([i[0] for i in bondAmount]), delta=result_decision["goldDiff"] * goldClosedPrice[-1] + result_decision["stockDiff"] * stockClosedPrice[-1] + result_decision["bondDiff"])
        st.pyplot(fig)

    startTime += datetime.timedelta(weeks=1)
