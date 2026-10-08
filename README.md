# **Analyses de biofeedback EMG**

Auteure: Dorothée Morand-Grondin  
Contact: dorothee.morand-grondin@mail.mcgill.ca  
Répertoire: https\://github.com/dorotheemorandgrondin/EMG\_biofeedback

# **Avant le premier démarrage**

## Installer Python

* Téléchargez Python ≥3.10 (https\://www\.python.org/downloads/)  
* Sur Windows : Cochez “Add python.exe to PATH” avant de cliquer “Installer”  
* Sur Mac OS : Installez normalement

## Librairies Python

Ce workflow utilise certaines librairies Python; Vous n’avez pas besoin de les télécharger vous-même. Elles seront installées automatiquement, donc le premier lancement pourrait prendre quelques minutes supplémentaires pour l’installation. 

## Nommer les fichiers

Les numéros de participants et de sessions sont lus à partir du nom du fichier BioGraph. SVP assurez-vous que les fichiers sont nommés de manière conforme. P. ex. Données brutes client XX session XX.txt

# **Démarrage rapide**

1) Téléchargez le répertoire sur l’ordinateur: sur GitHub, cliquez sur le bouton vert “Code”, téléchargez en format ZIP, et dé-ZIPper sur l’ordinateur.   
2) Ajouter localement le dossier input/ avec les fichiers de données (.txt)  
3) Double-cliquez RUN\_ME (windows \= .bat; mac \= .command)  
4) Lorsque la fenêtre indique “terminé”, cliquez n’importe quelle touche pour fermer

# **Ce que chaque script construit**

## 1\_organize.py

Ce script utilise les fichiers de données .txt ajoutés au dossier input/ et trouve les informations suivantes : 

- Le numéro de participant  
- Le numéro de la session  
- La date de la session  
- Les données EMG pour les mains gauche et droite à travers le temps

Ensuite, le script sauvegarde les colonnes de données EMG dans un nouveau dossier organised\_data/. Donc, il n’y a à cette étape aucune transformation de données, seulement un “copié-collé” plus propre et donc plus facile à utiliser pour la suite des choses. 

# **Détails concernant les autres fichiers et dossiers**

## input/

Placez ici les fichiers de données .txt

## organised\_data/

Ce dossier est créé par le script 1\_organize.py et ajoute 1 fichier par participant par session, p. ex. PXX\_sessionXX\_YYYY-MM-DD.csv (participant, session, date). Voici ce que les différentes colonnes de ces fichiers représentent : 

| Colonne | Interprétation |
| :---- | :---- |
| time\_s | Temps écoulé depuis le début de l’enregistrement EMG (en secondes) |
| left\_raw | Le signal EMG brut de la main gauche (MyoScan 1C, en μV) |
| right\_raw | Le signal EMG brut de la main droite (MyoScan 1D, en μV) |
| left\_smoothed | Le signal EMG “smooth” de la main gauche (“Smoothing Average” colonne 1, en μV) |
| right\_smoothed | Le signal EMG “smooth” de la main droite (“Smoothing Average” colonne 2, en μV) |
