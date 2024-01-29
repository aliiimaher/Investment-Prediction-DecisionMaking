% Data Define
float: budget;
float: stockAmount;
int: goldAmount;
float: saleableBondAmount;
float: bondAmount;

float: goldCurrentPrice;
float: goldPredictedPrice;
float: stockCurrentPrice;
float: stockPredictedPrice;

% Decision Vars.
var int: goldDiff;
var float: stockDiff;
var float: bondDiff;

% Constraints of Gold
constraint goldDiff >= -1*goldAmount;
constraint stockDiff >= -1 * stockAmount;
constraint bondDiff >= -1 * saleableBondAmount;
constraint goldDiff*goldCurrentPrice + stockDiff*stockCurrentPrice + bondDiff <= budget;
constraint bondDiff <= 0.5 * budget;

% added const.
var float: A1;
constraint A1 >= 0;
% float: totalBudget = budget + (goldAmount * goldCurrentPrice + stockAmount * stockCurrentPrice + bondAmount);
% constraint (goldAmount + goldDiff) * goldCurrentPrice + A1 >= 0.05 * budget;
% constraint (stockAmount + stockDiff) * stockCurrentPrice >= 0.10 * budget;
% constraint bondAmount + bondDiff >= 0.15 * budget;

% Solve
solve maximize (goldPredictedPrice - goldCurrentPrice) * goldDiff + (stockPredictedPrice - stockCurrentPrice) * stockDiff + 0.0054 * bondDiff - A1*10000000;
