@echo off
title Jumpcutter
cd Videos
:Menu
cls
echo Hello and welcom to jumpcutter
echo This tool is a quick way to shorten long videos by removing the silence
echo.
echo.
echo.
echo What would you like to do?
echo [1] help
echo [2] presets
echo [3] custom
echo [4] credits
echo [5] exit
set /p answer=Enter the number to navigate the menus: 
if %answer% == 1 goto Help
if %answer% == 2 goto Presets
if %answer% == 3 goto Custom
if %answer% == 4 goto Credits
if %answer% == 5 goto Exit
goto Menu_Error_Trap
:Help
cls
echo This program is a more simple way of changing the settings for jumpcutter.py
pause >nul
cls
echo Using this program is optional but is much more straight forwards as it takes out most of the work for you
pause >nul
cls
echo Just follow the on screen prompts and they will tell you what to do
pause >nul
goto Menu
:Presets
cls
echo This is yet to be set up but you will be able to load saved settings for quicker use of the program
pause >nul
goto Menu
:Custom
cls
set preset_name=Custom
set /p input_file=State the video you want to shorten (remeber to add .mp4): 
echo.
set /p output_file=Name the output file (remember to add .mp4): 
echo.
set /p sounded_speed=Speed of spoken parts: 
echo.
set /p silent_speed=Speed of silent parts: 
echo.
set /p frame_rate=Enter the frame rate of the video: 
echo.
goto Settings_Check
:Settings_Check
cls
echo -Your Settings-
echo preset name: %preset_name%
echo input file: %input_file%
echo output file: %output_file%
echo silent threshold: 0.2
echo sounded speed: %sounded_speed%
echo silent speed: %silent_speed%
echo frame margin: 60
echo frame rate: %frame_rate%
echo frame quality: 1
set /p answer=Are these correct? [Y/N/B]
if %answer% == Y goto Start_Edit
if %answer% == N goto Custom
if %answer% == B goto Menu
:Custom_Error_Trap
cls
Echo Invalid Input
pause >nul
goto Settings_Check
:Credits
cls
echo The jumpcutter.py was made by Craykh
echo.
echo The jumpcutter.bat was made by Steveycat
pause >nul
goto Menu
:Exit
exit
:Menu_Error_Trap
cls
echo Invalid Input
pause >nul
goto Menu
:Start_Edit
echo.
python jumpcutter.py --input_file %input_file% --output_file %output_file% --silent_threshold 0.2 --sounded_speed %sounded_speed% --silent_speed %silent_speed% --frame_margin 60 --frame_rate %frame_rate% --frame_quality 1
echo.
echo Finished
pause >nul
goto Menu