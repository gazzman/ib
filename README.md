ib
==

A jython implementation of the Interactive Brokers API


Prerequisites
-------------

This was written in jython 2.5.3. It requires the JYTHONPATH to include the 
folder where the java IBJts API is located, as well as the path to the repo. An 
example of the appropriate .bash_profile entries would be

    JYTHONPATH=$JYTHONPATH:[path to IBJts/java]:[path to ib repo]
    export JYTHONPATH


client.py
---------

A module with callbacks for EClientSocket. The Client class contains wrappers
for the EClientSocket methods that assist in keeping track of contracts, 
orders, and requests.


reversal.py
-----------

A module for automating reversal positions. The Revesal class' enter_position
method automatically enters a revesal postion based on the ticker symbol,
expiry, and strike. The user can also specify the quantity and which side to
take, long or short.


reversal_server.py
------------------

This module implements revesal.py and starts  a TCP socket server that listens
for messages. Once the appropriately formatted message is recevied, it enters 
an order for a reversal position. This presupposes a TWS session has been 
started and is listening on the default TWS API port.

The following is an example of a simple bash script to help ensure the TWS has
been started prior to the reversal_server. It also will continue to restart the 
reversal_server if it's shutdown while the TWS is still running.

start_reversal_server.bash:

    #!/bin/bash
    H=[the listening host]
    RPORT=[the listening TCP port]
    TWSLOG=[the TWS logfile]
    RSERVERLOG=[a log file to catch stuff not caught by the logger]

    cd [the path to the IBJts directory]
    pgrep start_TWS # a custom bash script to start the TWS
    if [ $? = 1 ]
    then
        ./start_TWS &>$TWSLOG&
        echo 'Once you have logged into TWS, press enter to continue.'
        read
    fi    

    cd [the path from which you want to start the server]
    pgrep start_TWS
    RC=$?
    while [ $RC = 0 ]
    do
        echo "" 2>&1 | tee -a $RSERVERLOG
        echo "*** Server restart at" `date` "***" 2>&1 | tee -a $RSERVERLOG
        echo "Server will continue to restart until TWS is shutdown"
        echo "Press ctl-C to restart server"
        ./reversal_server.py $H $RPORT 2>&1 | tee -a $RSERVERLOG
        echo "*** Server stop at" `date` "***" 2>&1 | tee -a $RSERVERLOG
        echo "" 2>&1 | tee -a $RSERVERLOG
        pgrep start_TWS
        RC=$?
    done
