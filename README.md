# AutoHome

AutoHome is a personal server that is designed to run in the background of a laptop or desktop computer.
It is built for modules to be added, where the modules are run on certain intervals while also supplying them with useful tools such as easy logging and notifications to your phone (via [Pushover](https://pushover.net/)).

The main server adds modules to a queue in the form of tasks every given multiple of 30 seconds. Then a variable number of worker threads will act to complete these tasks.
The worker threads are very robust; If one runs into an error, it is discarded and another worker is initialised.

There is very detailed logging, both from the main server, but also minor loggers given down as parameters to each of the modules. All logs are found in the root folder in logs/ where the `current.log` can easily be switched out for archiving purposes.

While the tasks are running, the server can also be accessed through a telnet socket. This socket can get information regarding the application processes and also control the server, such as telling it to shutdown.
