
echo "
BEGIN NEST
STOCK 100
MEMORY 9 2 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
ANT_IN 0
END

BEGIN NEST
STOCK 100
MEMORY 9 2 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
ANT_COUNT 1 1
ANT_IN 0
END

BEGIN ANT
TYPE 1
MEMORY 0 0
STAMINA 1000
STOCK 10
SEE_NEST 1 NEAR 0 FRIEND
END
" | ./start.sh
