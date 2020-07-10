# AutoHome

AutoHome is a personal server that is designed to run in the background of a laptop or desktop computer.
It is built for modules to be added, where the modules are run on certain intervals while also supplying them with useful tools such as easy logging and notifications to your phone (via [Pushover](https://pushover.net/)).

There is very detailed logging, both from the main server, but also minor loggers given down as parameters to each of the modules. All logs are found in the root folder in logs/ where the `current.log` can easily be switched out for archiving purposes. Giving the program the *'-n' (or '--new')* flag upon lauch will cause the program to start the logging for this instance in a new file. If a `current.log` file already exists, it is archived automatically and given a name including the first timestamp in the file or a unique id if no timestamp is found.

## Mainloop
The Main class handles the main thread where every 30 seconds it checks through the installed modules and runs those meant to occur. Giving the program the *'-t' (or '--test')* flag upon lauch will cause the program to run a test mode. This will stop the programs running on 30 seconds intervals, but rather `input()` is called to act in place of `time.sleep()`. This means that time can be passed as slowly or quickly as you might need while debugging your modules.

A new thread is created for each module to be run on individualy to prevent them from interfering with the main program. A max thread count is defined to prevent too many threads from working, where if the program reaches it, the excess modules to be ran are added to a backlog queue. A separate thread is initialised at this point where it waits for module threads to finish, only then to take modules from the backlog and run them. Once the backlog is empty, the new separate thread closes.

This thread infrastructure is beneficial as it ensures that all open threads are active and threads are only opened once a task needs to be completed. This method also prevents errors in modules from affecting other modules or the greater server itself.

## Telnet Server

A separate thread runs independantly from the main and module threads which hosts a telnet server on **Port 23**. On connection, commands can be inputted in order to get information about and control the AutoHome server remotely.

|   Command      |                  Description                    |
|:--------------:|:-----------------------------------------------:|
|   ***help***   |   Get list of commands with brief descriptions  |
|   ***quit***   |              Close the telnet connection        |
| ***shutdown*** |  Closes the connection and closes the server    |
| ***modules***  |  Read/Run/Pause/Start modules running on server |
