#! /bin/bash
echo "ENV $ENV"
echo "DB $STAGING_DB"
echo "HOST $STAGING_DB_HOST"

touch $HOME/gunicorn-access-log.txt
if pgrep -x gunicorn > /dev/null
then
    echo 'Gunicorn restarting...' | tee gunicorn-log.txt -a
    kill -HUP "$(cat $HOME/gunicorn.pid)"
    EXIT_CODE=$?
    echo "Gunicorn executed with code $EXIT_CODE." | tee gunicorn-log.txt -a
else
    echo 'Gunicorn starting...' | tee gunicorn-log.txt -a
    gunicorn wsgi \
        --bind 0.0.0.0:5000 \
        --pid $HOME/gunicorn.pid \
        --log-file $HOME/gunicorn-log.txt \
        --access-logfile $HOME/gunicorn-access-log.txt \
        --timeout 60 \
        --capture-output \
        --enable-stdio-inheritance \
        --daemon

    EXIT_CODE=$?
    echo "Gunicorn executed with code $EXIT_CODE." | tee gunicorn-log.txt -a
    if [ $EXIT_CODE -ne 0 ]
    then
        exit $EXIT_CODE
    fi
fi

