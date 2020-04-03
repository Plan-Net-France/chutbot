# Ligne de commande

Utilisation : `chutbot [options…] [<fichier>]`

Nom d'option|Courte|Configuration|Type (Par défaut)|Description
---|---|---|---|--
`--config`| | |texte|Fichier de configuration à utiliser. Au format INI. Voir [example.ini](../example.ini). Ne peut pas être utilisé avec les autres paramètres excepté `--verbose`.
`<fichier>`| |`resources.file`|texte|Fichier son à lire lorsque le seuil de volume est atteint.
`--folder <dossier>`|`-F <dossier>`|`resources.folder`|texte|Dossier où sont placés les fichiers à lire en séquence lorsque le seuil est atteint.
`--random`| |`resources.random`|booléen(Faux)|Active la lecture aléatoire.
`--bipfile <bip>`|`-b <bip>`|`startup.bipfile`|texte|Fichier son à lire au démarrage.
`--warmup <attente>`|`-w <attente>`|`startup.warmup`|entier(2000)|Durée pendant laquelle l'appareil est silencieux au démarrage.
`--volume <dB>`|`-t <dB>`|`detection.volume`|réel(-15)|Seuil de volume en décibel, relative au volume maximum (0dB). La valeur est attendu négative.
`--frequency <freq>`|`-f <freq>`|`detection.frequency`|entier(10)|Fréquence de calcul du seuil en Hz, entre 1 et 55.
`--repeat <fois>`|`-r <fois>`|`detection.repeat`|entier(10)|Nombre de fois qu'il est nécessaire que le seuil soit atteint continuellement pour déclencher la lecture.
`--clear <ms>`|`-c <ms>`|`detection.clear`|entier(5000)|Durée pendant laquelle l'appareil est silencieux après la lecture.
`--verbose`|`-v`|`global.verbose`|booléen(Faux)|Afficher l'état du programme.

La configuration est spécifiée comme `section`.`name` dans le fichier INI.
