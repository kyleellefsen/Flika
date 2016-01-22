## Flika ##

**Flika** is an interactive image processing program for biologists written in Python.
### Website ###
[brettjsettle.pythonanywhere.com](http://brettjsettle.pythonanywhere.com/)

### Documentation ###
[brettjsettle.pythonanywhere.com/documentation.html](http://brettjsettle.pythonanywhere.com/documentation.html)

### Installation Instructions ###
Flika works in both Python 2 and Python 3.
#### Windows ####
Download the FLIKA zipped folder from Github and extract the folder to a location on your computer (Desktop or Program Files preferredly). After the folder has been extracted, you can double click the 'Flika.bat' file inside of the Flika-master folder. Or follow these steps to create an executable on the desktop:

Right click 'Flika.bat' and choose 'Create Shortcut', a shortcut icon should show up. Rename the 'Flika.bat - Shortcut' to just 'Flika', then right click it and select Properties. Click the button that says 'Change Icon' at the bottom of the window. (If a window pops up, press ok). Select 'Browse' to locate the FLIKA icon, located in the '/Flika-master/images/' folder under the name 'favicon.ico'. Once the icon is selected, you can move the shortcut to your desktop. Double click it to run Flika!

#### Ubuntu ####
Open a terminal and run the following commands:
```
sudo apt-get install python-pip python-numpy python-scipy build-essential cython python-matplotlib python-qt4-gl
sudo pip install scikit-image
sudo pip install future
```
Download the FLIKA zipped folder from Github and extract the folder to a location on your computer.  Navigate to the directory Flika was downloaded into.  Run Flika with the command
```python FLIKA.py```

#### Mac OSX ####

Install [https://www.continuum.io/downloads](Anaconda) by Continuum. This will install Python along with most of Flika's dependencies.  Any libraries not included in Anaconda will be installed the first time Flika is run.

Download the FLIKA zipped folder from Github and extract the folder to a location on your computer.  Navigate to the directory Flika was downloaded into.  Run Flika with the command
```python FLIKA.py```