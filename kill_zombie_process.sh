#/bin/bash

# REF: https://ex1.m-yabe.com/archives/3490
PName=defunct
PID=$$

for i in `ps -ef | grep $PName | grep -v $PID | grep -v grep | awk '{print $2,$3}'`
do
    TIME=`ps -o lstart --noheader -p $i`

    if [ -n "$TIME" ]; then
        StartupTime=`date +%s -d "$TIME"`
        CurrentTime=`date +%s`
        ElapsedTime=`expr $CurrentTime - $StartupTime`
    else
        ElapsedTime=1
    fi

    kill -9 $i

done