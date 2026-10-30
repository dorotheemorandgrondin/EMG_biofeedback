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

Ce script lit les fichiers de données .txt ajoutés au dossier input/ et trouve les informations suivantes : 

- Le numéro de participant  
- Le numéro de la session  
- La date de la session  
- Les données EMG pour les mains gauche et droite à travers le temps

Le script sauvegarde les colonnes de données EMG dans un nouveau dossier organised\_data/. Donc, il n’y a à cette étape aucune transformation de données, seulement un “copié-collé” plus propre et donc plus facile à utiliser pour la suite des choses. 

## 2\_clean.py

Pour chaque fichier de données dans le dossier organised\_data/, ce script nettoie les données à travers plusieurs étapes : 

1) Le script identifie les trois sections principales de la session, soit (i) la partie de biofeedback de la main gauche, (ii) la partie de biofeedback de la main droite, et (iii) la partie de biofeedback combinant les deux mains. Ces sections sont identifiées à partir des données elles-mêmes de la manière suivante :   
- Le début et la fin de la tâche : le début de la tâche est considéré comme étant le moment où les signaux EMG des deux mains sont au-dessus de 0 μV (sauf sur indication contraire indiquée dans le document criteria.txt à la section “secondes rejetées au début du signal”). La fin de la tâche est considérée comme étant le dernier moment où les signaux EMG changent encore (n’est pas “flat”) (sauf sur indication contraire indiquée dans le document criteria.txt à la section “secondes rejetées à la fin du signal”). Les données qui se trouvent en dehors de ces intervalles sont considérées comme ne faisant pas partie de la tâche d’intérêt.   
- Les deux changements principaux (gauche→droite, droite→deux mains) : le script test chaque échantillon (1/256s) comme point de changement possible et garde l’échantillon qui divise la tâche en deux segments les plus homogènes (variance la plus faible sur une échelle logarithmique pour que les deux mains aient un poids égal). On répète ensuite l’opération dans chaque moitié et garde le meilleur second changement (*binary segmentation*, une méthode de *change point detection* ; https\://www\.sciencedirect.com/science/article/pii/S0165168419303494).   
- J’ai utilisé cette technique en m’assurant que chaque partie ait une durée d’au moins 4 minutes, pour que des stretchs de bruits (surtout au début ou à la fin de la série de données) ne puissent pas être détectés comme un changement d’instruction. Ce critère peut être changé dans le fichier criteria.txt  
2) Le script détecte les points de données artéfactuels. Ainsi, il identifie les points de données qui tombent dans l’une ou plusieurs des catégories suivantes :   
- Les données dont le signal EMG (en μV) est en dehors de l’intervalle 0-50μV  
- Les données qui sont au-delà de 3 écarts-types de la moyenne des données dans une fenêtre déroulante de 20s centrée sur la donnée   
- Ces critères peuvent être changés dans le fichier criteria.txt  
3) Le script remplace les données artéfactuelles identifiées par la moyenne des données considérées “valides” dans une fenêtre de 20s centrée sur la donnée (ce critère peut être changé dans le fichier criteria.txt)  
4) Le script sauvegarde ce fichier de données “propres” dans le dossier clean\_data/ et génère un graphique par session (pour vérification manuelle) et un fichier résumé cleaning\_summary.csv dans le dossier cleaning\_check/. Le fichier section\_durations.csv est également sauvegardé et contient le nombre de secondes identifiées dans chaque section du signal pour fins de vérifications. 

   \*\*\* À noter que tous les critères mentionnés dans cette section peuvent être modifiés directement dans le fichier criteria.txt 

## 3\_compute.py

Pour chaque fichier de données dans le dossier clean\_data/, et pour chaque signal EMG (gauche ou droite) et chaque section de la tâche (biofeedback main gauche, biofeedback main droite, biofeedback à deux mains), le script calcule les métriques suivantes : 

- La moyenne du signal EMG (en μV)  
- L’écart-type du signal EMG (en μV)  
- Le root mean square du signal EMG (en μV)   
- Le pourcentage de temps passé dans l’intervalle de biofeedback, soit   
  - Entre 20-30 μV pour la main “entraînée” (p. ex. pour la main gauche lors de la section de biofeedback de la main gauche)  
  - Entre 0-10 μV pour l’autre main

Ces métriques sont enregistrées dans le dossier results/ et un graphique pour chaque session est généré en conséquence. \*\*\* À noter que les intervalles considérés en “biofeedback” peuvent être modifiés dans le fichier criteria.txt

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

## cleaning\_check/

Ce dossier est créé par le script 2\_clean.py. Ceci n’est pas une étape cruciale dans le pipeline d’analyse mais plutôt un “checkpoint” qui permet de visualiser manuellement les données qui seront nettoyées. Il y a donc un graphique par participant par session qui montre le signal EMG au fil du temps de l’enregistrement pour la main gauche (bleu; en haut) et la main droite (orange; en bas). 

- En rouge se trouvent les données ayant été considérées comme artéfactuelles et qui seront remplacées.   
- Les changements de sections dans la tâche (biofeedback gauche→droite, droite→deux mains) sont identifiés par une ligne noire pointillée verticale. 

Dans ce dossier se trouve également le fichier cleaning\_summary.csv : 

| Colonne | Interprétation |
| :---- | :---- |
| session | Étiquette de la session (participant, session, date) |
| biofeedback | Indique la section de la tâche (biofeedback gauche, droite, deux mains) |
| pct\_left\_replaced | Pourcentage de données EMG de la main gauche considéré artefactuel et remplacé |
| pct\_right\_replaced | Pourcentage de données EMG de la main droite considéré artefactuel et remplacé |

Dans ce dossier se trouve également le fichier section\_durations.csv : 

| Colonne | Interprétation |
| :---- | :---- |
| session | Étiquette de la session (participant, session, date) |
| left\_s | Indique le temps en secondes détecté dans la section de biofeedback de la main gauche |
| right\_s | Indique le temps en secondes détecté dans la section de biofeedback de la main droite  |
| both\_s | Indique le temps en secondes détecté dans la section de biofeedback des deux mains |

## clean\_data/

Dossier crée par le script 2\_clean.py. Il y a un fichier par participant par session (mêmes noms que dans organised\_data/). 

| Colonne | Interprétation |
| :---- | :---- |
| time\_s | Temps écoulé depuis le début de l’enregistrement EMG (en secondes) |
| biofeedback | Section de la tâche (biofeedback gauche, droite, deux mains, ou “outside” qui ne fait pas partie de la tâche) |
| left\_clean | Données EMG nettoyées pour la main gauche |
| right\_clean | Données EMG nettoyées pour la main droite |
| left\_replaced | TRUE si la donnée gauche a été nettoyée et remplacée |
| right\_replaced | TRUE si la donnée droite a été nettoyée et remplacée |

## results/

Dossier créé par le script 3\_compute.py et contient les outputs finaux. Le fichier metrics\_long.csv contient toutes les métriques descriptives, avec une rangée par participant par session par section par main. Le fichier est aussi créé en format large, soit une seule ligne par participant. Dans le format large, chaque métrique est étiquetée selon la session, la main, et la section de biofeedback. Les sessions 1-10 sont incluses pour chaque participant, et les sessions dont les fichiers de données n’ayant pas été incluses en input indiquent “NA” pour les résultats. Voici les colonnes en format long: 

| Colonne | Interprétation |
| :---- | :---- |
| participant | Participant ID |
| session | \# de session |
| date | Date de la session YYYY-MM-DD |
| hand | Gauche ou droite |
| biofeedback | Section de la session (droite, gauche, deux mains) |
| avg\_uV | Moyenne de l’amplitude du signal EMG (μV) |
| sd\_uV | Écart-type du signal EMG (μV) |
| rms\_uV | Root mean square du signal EMG (μV) |
| target\_range\_uV | Intervalle μV utilisé comme cible |
| pct\_time\_bfb | Pourcentage de temps passé dans l’intervalle de biofeedback |

session\_graphs/: un graphique par participant par session est généré dans ce sous-dossier illustrant le signal EMG gauche (bleu) et droit (orange) au fil du temps en trois panels : 

- Haut : section de biofeedback main gauche  
- Milieu : section de biofeedback main droite  
- Bas : section de biofeedback à deux mains
