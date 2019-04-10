@echo off
title Installing dependencies...

:pysearch
:: Search for specific Python command.
python --version >> nul
if %errorlevel%==0 (
set command="python"
goto pip
)

py --version >> nul
if %errorlevel%==0 (
set command="py"
goto pip
)

::We didn't found the Python executable! Ask the user for the path to the .exe file.
echo !!PYTHON NOT FOUND.!!
set/p path="Path to Python:"
cd path
goto pysearch
:pip
::Install the required modules.
echo Installing Pillow.
start %command% -m pip install pillow
echo Installing AudioTSM.
start %command% -m pip install audiotsm
echo Installing SciPy.
start %command% -m pip install scipy
echo Installing NumPy.
start %command% -m pip install numpy

:: We've completed the task.
:: Ask for user input and terminate the script.
pause
exit


