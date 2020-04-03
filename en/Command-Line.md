# Command Line

Usage: `chutbot [options…] [<file>]`

Option name|Short|Setting|Type (Default)|Description
---|---|---|---|--
`--config`| | |string|Configuration file to use. With INI format. See [example.ini](../example.ini). Cannot be used with any other parameter except `--verbose`.
`<file>`| |`resources.file`|string|Sound file to play when volume threshold is reached.
`--folder <folder>`|`-F <folder>`|`resources.folder`|string|Folder where sound files to play sequentially when threshold is reached are put.
`--random`| |`resources.random`|bool(False)|Activate playing the files randomly.
`--bipfile <bip>`|`-b <bip>`|`startup.bipfile`|string|Sound file played on startup.
`--warmup <wait>`|`-w <wait>`|`startup.warmup`|int(2000)|Duration in milliseconds at start in which the device is silent.
`--volume <dB>`|`-t <dB>`|`detection.volume`|float(-15)|Threshold volume in decibel, relative to max volume (0dB). Value is expected to be negative.
`--frequency <freq>`|`-f <freq>`|`detection.frequency`|int(10)|Frequency of threshold computation in Hz, between 1 and 55.
`--repeat <times>`|`-r <times>`|`detection.repeat`|int(10)|Number of times the threshold must be reached continuously before triggering the playback.
`--clear <ms>`|`-c <ms>`|`detection.clear`|int(5000)|Duration in milliseconds after the playback in which the device will be silent.
`--verbose`|`-v`|`global.verbose`|bool(False)|Display program state.

Setting is specified as `section`.`name` in INI file.
