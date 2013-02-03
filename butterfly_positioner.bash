#!/bin/bash
OFILE="butterflies.mkt"
TFILE="tmp.mkt"
for d in `ls -l | grep dr | awk '{print $9}'`
do
    COUNT=0
    SYMBOL=`echo $d | awk -F'_' '{print $1}'`
    cd $d
    touch $OFILE
    touch $TFILE
    rm $OFILE
    rm $TFILE
    for f in `ls *_*_*.mkt`
    do
        cat $f | awk "{print \"$COUNT \"\$0}" >> $TFILE
        COUNT=$(($COUNT + 1))
    done
    cat ../$SYMBOL.mkt | awk "{print \"$COUNT \"\$0}" >> $TFILE
    sort -k2 $TFILE >> $OFILE
    rm $TFILE
    cd ..
done    
