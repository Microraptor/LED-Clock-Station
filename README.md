# Clock Station for the Raspberry Pi

## Install prerequisites

See **[README_driver_libraries.md](README_driver_libraries.md)** for instructions to install dependencies.

Python libraries needed:

```sh
sudo apt-get install python-daemon python-pip
```

## Usage

```sh
sudo python clock_station_daemon.py start
sudo python clock_station_daemon.py stop
```

To start the daemon at system start via init.d script, save the file
_clock_station.py_ as _/share/clockstation/clock_station.py_ on the RPI and
_clockstation.sh_ as _/etc/init.d/clockstation.sh_.
Then install an pyhton virtaul enviroment:

```sh
sudo pip install virtualenv
sudo virtualenv --system-site-packages /usr/share/clockstation/python_venv
sudo chmod u+x /etc/init.d/clockstation.sh
sudo chkconfig clockstation.sh on
chkconfig --list
```

The last command should confirm that 3 and 5 of the service are turned on.
Now the service starts at boot and can be also controlled with the commands:

```sh
sudo service clockstation.sh start
sudo service clockstation.sh restart
sudo service clockstation.sh stop
```

### Sync script

A batch sync script is included, which syncs a file directly to the
_/usr/share/clockstation/_ folder of the RPI. Before it can be used
_winscp.com_ has to be in the folder _%USERPROFILE%\SSH\_ and a session named
_syncRPI_ has to be saved in WinSCP or the script has to be adjusted.

Create folder and give write permissions for syncing:  
(Note: This gives the system a small security vulnerability, if all users have
  write permissions and the script starts at boot)

```sh
sudo mkdir /usr/share/clockstation/
sudo +w /usr/share/clockstation/
```

Usage

```sh
sync [filename] [optional-subdirectory]
```

for Powershell:

```sh
cmd /c sync [filename] [subdirectory]
```

Or just used the Build package, if you are using the Atom Editor.

## Notes

I am using a Raspberry Pi Revision 1 (early preordered RPI) for this projects
and the pins and ports are slightly different than the later Revisions.

## License

The MIT License (MIT)  
Copyright (c) 2016 Till
