@echo off
title Installing dependencies...

:pysearch
:: Search for specific Python command.
python --version >> nul
if %errorlevel%==0 goto pippython

py --version >> nul
if %errorlevel%==0 goto pippy

::We didn't found the Python executable! Ask the user for the path to the .exe file.
echo !!PYTHON NOT FOUND.!!
set/p path="Path to Python:"
cd path
goto pysearch
:pippy
::Install the required modules.
echo Installing Pillow.
call py -m pip install pillow
echo Installing AudioTSM.
call py -m pip install audiotsm
echo Installing SciPy.
call py -m pip install scipy
echo Installing NumPy.
call py -m pip install numpy


:pippython
::Install the required modules.
echo Installing Pillow.
call python -m pip install pillow
echo Installing AudioTSM.
call python -m pip install audiotsm
echo Installing SciPy.
call python -m pip install scipy
echo Installing NumPy.
call python -m pip install numpy

:: We've completed the task.
:: Ask for user input and terminate the script.
pause
exit


