% Data
int: numberOfDays;
array[1..numberOfDays] of float: days;
array[1..numberOfDays] of float: price;

% Coefficients
var float: a;
var float: b;
array[1..numberOfDays] of var float: err;  

constraint forall(i in 1..numberOfDays) (err[i] >= a * days[i] + b - price[i]);
constraint forall(i in 1..numberOfDays) (err[i] >= price[i] - a * days[i] - b);

solve minimize sum(i in 1..numberOfDays) (err[i]);

output ["a=", show(a), " b=", show(b), " error=", show(err)];