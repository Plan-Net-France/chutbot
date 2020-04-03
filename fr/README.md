# ChutBot

[In English](../README.md)

## Dépendances

Dépendances Python :

* pydub : Pour déterminer le volume d'un échantillon
* pyalsaaudio (python-alsaaudio) : Pour capturer le son
* scandir (python-scandir) : Pour lister les fichiers (python 2.7 seulement)

## Installation

1. Installer les dépendances
2. Exécuter `install.sh` en tant que `root`

Opérations effectuées par l'installation :

* Création de l'utilisateur système `chutbot` avec pour accueil 
  `/var/local/lib/chutbot` et ajout au groupe `audio` ;
* Copie du fichier source dans `/usr/local/bin` avec le nom `chutbot` ;
* Copie du fichier d'exemple de configuration dans `/usr/local/lib/chutbot` ;
* Copie et activation de l'unité de service systemd `chutbot.service` dans `/etc/systemd` ;

## Utilisation

Il est possible d'exécuter l'application de deux manières : service ou manuel.

### Service

L'exécution en mode service se fait avec systemd. Il est aussi possible 
d'exécuter l'application sans paramètres pour obtenir un comportement
similaire.

L'utilisateur exécutant le service est `chutbot`. Le fichier de configuration utilisé en priorité est `/etc/chutbot/chutbot.ini`. Le fichier de configuration
`.chutbot.ini` dans l'accueil de l'utilisateur est utilisé en second.

Si aucun fichier de configuration n'est trouvé, le démarrage échoue. De même
si la configuration n'est pas valide.

### Manuel

L'exécution est considérée manuelle lorsque des paramètres sont passés dans la ligne de commande.

Les paramètres de la ligne de commande sont documentés sur
[cette page](Command-Line.md).
