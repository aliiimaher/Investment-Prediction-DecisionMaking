% Data Define
float: budget;
float: stockAmount;
int: goldAmount;
float: saleableBondAmount;

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
constraint goldDiff*goldCurrentPrice + stockDiff*stockCurrentPrice + bondDiff < budget;
constraint bondDiff <= 0.5 * budget;

% Solve
solve maximize (goldPredictedPrice - goldCurrentPrice) * goldDiff + (stockPredictedPrice - stockCurrentPrice) * stockDiff + 0.0054 * bondDiff;
