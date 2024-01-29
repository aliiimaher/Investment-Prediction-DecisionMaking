from minizinc import Solver, Model, Instance
import numpy as np
import pandas as pd
import datetime
import matplotlib.pyplot as plt
import streamlit as st

gold = pd.read_csv("GLD.csv")
stock = pd.read_csv("^IXIC.csv")

if 'budget' not in st.session_state:
    st.session_state.budget = 50000
    st.session_state.stockAmount = 0.0
    st.session_state.goldAmount = 0
    st.session_state.bondAmount = []
    st.session_state.startTime = datetime.datetime.strptime(
        "2023-05-01", "%Y-%m-%d")
endTime = datetime.datetime.strptime("2023-11-29", "%Y-%m-%d")

placeholder = st.empty()
if st.button("Next Week"):
    st.session_state.startTime += datetime.timedelta(weeks=1)

# functions


def saleBond(value):
    for d in range(1, 28):
        for bond in st.session_state.bondAmount:
            if value == 0:
                break
            if (st.session_state.startTime - bond[1]).days % 28 == d and (st.session_state.startTime - bond[1]).days > 28:
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
        datesInNumber.append((tempTime - st.session_state.startTime).days)

    return datesInNumber


def getLastMonthData(decisionDate, dataFrame):
    dates = (dataFrame[(dataFrame["Date"] <= decisionDate.strftime("%Y-%m-%d")) & (dataFrame["Date"]
             >= (decisionDate - datetime.timedelta(days=4)).strftime("%Y-%m-%d"))]["Date"].to_list())
    prices = (dataFrame[(dataFrame["Date"] <= decisionDate.strftime("%Y-%m-%d")) & (dataFrame["Date"]
              >= (decisionDate - datetime.timedelta(days=4)).strftime("%Y-%m-%d"))]["Close"].to_list())

    return dates, prices
# functions end


if st.session_state.startTime <= endTime:
    # gold close price
    dates, goldClosedPrice = getLastMonthData(st.session_state.startTime, gold)
    # stock close price
    dates, stockClosedPrice = getLastMonthData(
        st.session_state.startTime, stock)

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

    plt.tight_layout()

    plt.show()

    model_decision = Model("./main.mzn")
    instance_decision = Instance(solver, model_decision)
    instance_decision["budget"] = st.session_state.budget
    instance_decision["goldAmount"] = st.session_state.goldAmount
    instance_decision["stockAmount"] = st.session_state.stockAmount
    instance_decision["saleableBondAmount"] = sum([
        i[0] for i in st.session_state.bondAmount if i[1] < st.session_state.startTime - datetime.timedelta(weeks=4)
    ])
    instance_decision["bondAmount"] = sum([
        i[0] for i in st.session_state.bondAmount
    ])
    instance_decision["goldCurrentPrice"] = goldClosedPrice[-1]
    instance_decision["goldPredictedPrice"] = result_gold["a"] * \
        (dateToNumber(dates)[-1]+7) + result_gold["b"]
    instance_decision["stockCurrentPrice"] = stockClosedPrice[-1]
    instance_decision["stockPredictedPrice"] = result_stock["a"] * \
        (dateToNumber(dates)[-1]+7) + result_stock["b"]
    result_decision = instance_decision.solve()

    print(result_decision)

    st.session_state.goldAmount += result_decision["goldDiff"]
    st.session_state.stockAmount += result_decision["stockDiff"]
    if result_decision["bondDiff"] > 0:
        st.session_state.bondAmount.append(
            [result_decision["bondDiff"], st.session_state.startTime])
    elif result_decision["bondDiff"] < 0:
        saleBond(abs(result_decision["bondDiff"]))

    st.session_state.budget = st.session_state.budget - (result_decision["goldDiff"] * instance_decision["goldCurrentPrice"] +
                                                         result_decision["stockDiff"] * instance_decision["stockCurrentPrice"] + result_decision["bondDiff"])

    for i in st.session_state.bondAmount:
        if (st.session_state.startTime - i[1]).days % 28 == 0 and (i[1] - st.session_state.startTime).days != 0:
            st.session_state.budget += i[0] * 0.0054

    print(
        f"date:{st.session_state.startTime.strftime('%Y-%m-%d')}, total : {st.session_state.budget + st.session_state.goldAmount * goldClosedPrice[-1] + st.session_state.stockAmount * stockClosedPrice[-1] + sum([i[0] for i in st.session_state.bondAmount])}, budget: {st.session_state.budget}, goldAmount: {st.session_state.goldAmount}, stockAmount: {st.session_state.stockAmount}, bondAmount: {sum([i[0] for i in st.session_state.bondAmount])}")
    print()

    with placeholder.container():
        st.title(st.session_state.startTime.strftime('%Y-%m-%d'))
        st.metric(label="Total", value=st.session_state.budget, delta=st.session_state.goldAmount *
                        goldClosedPrice[-1] + st.session_state.stockAmount * stockClosedPrice[-1] + sum([i[0] for i in st.session_state.bondAmount]))
        st.metric(label="Gold Amount: ", value=st.session_state.goldAmount,
                        delta=result_decision["goldDiff"])
        st.metric(label="Stock Amount: ", value=st.session_state.stockAmount,
                        delta=result_decision["stockDiff"])
        st.metric(label="Bond Amount: ", value=sum(
            [i[0] for i in st.session_state.bondAmount]), delta=result_decision["bondDiff"])
        st.metric(label="Total Budget: ", value=st.session_state.budget + st.session_state.goldAmount *
                        goldClosedPrice[-1] + st.session_state.stockAmount * stockClosedPrice[-1] + sum([i[0] for i in st.session_state.bondAmount]), delta=result_decision["goldDiff"] * goldClosedPrice[-1] + result_decision["stockDiff"] * stockClosedPrice[-1] + result_decision["bondDiff"])
        st.pyplot(fig)
