% Program for a nest


% total number of ant + detection of ant absence.
ant_count(C):- C=#sum{N,T:ant_count(T,N)}.
ant_count(0):- not ant_count(_,_).
no_ant:- ant_count(0).
turn(T):- memory(_,T,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_).   % slot 1 of memory is time counter


do(ant_new,1):- no_ant ; turn(0).
do(ant_new,2):- no_ant ; turn(1..2).  % faire jusqu'à 10 scavenger
% do(ant_new,1):- no_ant ; turn(11..12). % d'autres explorateurs
% do(ant_new,2):- no_ant ; turn(1..10).  % faire jusqu'à 10 scavenger

% Can't build ant without needed stocks.
:- do(ant_new,_) ; stock(N) ; N<5.

% Send ants out of the nest.
do(ant_out,1,0,0,0):- ant_count(1,_).
do(ant_out,2,0,0,0):- ant_count(2,_).

% Increase counter on ant_new
inc_memory(0,1):- do(ant_new,_).
% Increase turn counter
inc_memory(1,1):- do(ant_new,_).


#show.
#show inc_memory/2.
#show do/2.
#show do/5.
