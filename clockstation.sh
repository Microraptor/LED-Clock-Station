#! /bin/sh
### BEGIN INIT INFO
# Provides:          clockstation
# Required-Start:
# Required-Stop:
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Clock-Station daemon
# Description:       Starts the daemon of the Clock-Station
### END INIT INFO

PATH_SCRIPT=/usr/share/clockstation/clock_station.py
PATH_VENV=/usr/share/clockstation/python_venv
DESC="Clock-Station daemon"

# Activate the python virtual environment
. $PATH_VENV/bin/activate

case "$1" in
  start)
    echo "Starting $DESC"
    # Start the daemon
    python $PATH_SCRIPT start
    ;;

  stop)
    echo "Stopping $DESC"
    # Stop the daemon
    python $PATH_SCRIPT stop
    ;;

  restart)
    echo "Restarting $DESC"
    # Restart the daemon
    python $PATH_SCRIPT restart
    ;;

  *)
    # Define function
    echo "Usage: /etc/init.d/clockstation.sh {start|stop|restart}"
    exit 1
    ;;
esac

:
