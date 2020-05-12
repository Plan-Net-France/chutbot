# ChutBot

[En Français](fr/README.md)
[Look at the wiki to find how we have build to ChutBot](https://github.com/Plan-Net-France/chutbot/wiki)

## Dependencies

Python dependencies:

* pydub: For computing sample volume
* pyalsaaudio (python-alsaaudio): For capturing sound
* scandir (python-scandir): For listing files (python 2.7 only)

## Installation

1. Install dependencies
2. Execute `install.sh` as `root`

Installation process executes these operations:

* Create system user `chutbot` with home `/var/local/lib/chutbot` and add it to `audio` group;
* Copy source file in `/usr/local/bin` with name `chutbot`;
* Copy settings example file in `/usr/local/lib/chutbot`;
* Copy and activate systemd service unit `chutbot.service` in `/etc/systemd`;

## Usage

The application can be executed in two way: service or manual.

### Service

Service mode execution is done using systemd. The application can also
be executed without parameters to obtain a similar behaviour.

The service runnign user is `chutbot`. Priority settings file is 
`/etc/chutbot/chutbot.ini`. User home file `.chutbot.ini` is used as second
settings source.

If no settings file is found, startup fail. It also fails if the settings
are invalid.

### Manual

Manual execution is considered when parameters are passed in the command line.

Command line parameters are explained on [this page](en/Command-Line.md).
