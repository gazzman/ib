#!/bin/bash
TFILE="tmp.mkt"
for d in `ls -l | grep dr | awk '{print $9}'`
do
    COUNT=0
    SYMBOL=`echo $d | awk -F'_' '{print $1}'`
    cd $d
    touch $TFILE
    rm $TFILE
    for f in `ls *_*_*.mkt`
    do
        if [ $COUNT -eq 0 ]
        then
            START=`echo $f | awk -F'_' '{print $1}'`
        fi
        cat $f | awk "{print \"$COUNT \"\$0}" >> $TFILE
        COUNT=$(($COUNT + 1))
    done
    END=`echo $f | awk -F '_' '{print $3}' | awk -F'.mkt' '{print $1}'`
    INTERVAL=`echo "scale = 1; ($END-$START-1)/$COUNT" | bc`
    cat ../$SYMBOL.mkt | awk "{print \"$COUNT \"\$0}" >> $TFILE
    OFILE=$START'_'$END'_'$INTERVAL'.mkt'
    touch $OFILE
    rm $OFILE
    sort -k2 $TFILE >> $OFILE
    rm $TFILE
    cd ..
done
