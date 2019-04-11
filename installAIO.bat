@echo off
title Installing.
setlocal EnableDelayedExpansion
::AIO-Installer for all deps for Windows
::Files needed: requirements.txt


:checkPrivileges
::Check if we have admin
NET FILE 1>NUL 2>NUL
if '%errorlevel%' == '0' ( goto gotPrivileges 
) else (echo Please give this program admin access. & powershell "saps -filepath %0 -verb runas" >nul 2>&1)
exit /b 


:gotPrivileges
:: set starting path, we will be using requirements.txt
SET starting=%~dp0

::get start time
set "startTime=%time: =0%"

::download ffmpeg
cd %temp%
echo [%time%] Downloading ffmpeg.
certutil.exe -urlcache -split -f "https://ffmpeg.zeranoe.com/builds/win32/static/ffmpeg-20190410-4d2f621-win32-static.zip" ffmpeg.zip

::unzip downloaded file
echo [%time%] Unzipping ffmpeg.
unzip -o ffmpeg.zip -d "ffmpeg-extracted"
cd ffmpeg-extracted
cd ffmpeg-20190410-4d2f621-win32-static
cd bin

:: install ffmpeg
echo [%time%] Installing ffmpeg.
copy *.* "C:\Windows\system32\"

:: get end time
set "endTime=%time: =0%"

:: get elapsed time
set "end=!endTime:%time:~8,1%=%%100)*100+1!"  &  set "start=!startTime:%time:~8,1%=%%100)*100+1!"
set /A "elap=((((10!end:%time:~2,1%=%%100)*60+1!%%100)-((((10!start:%time:~2,1%=%%100)*60+1!%%100)"

:: convert it to a more "human readable" format
set /A "cc=elap%%100+100,elap/=100,ss=elap%%60+100,elap/=60,mm=elap%%60+100,hh=elap/60+100"


echo [%time%] Done in %hh:~1%%time:~2,1%%mm:~1%%time:~2,1%%ss:~1%%time:~8,1%%cc:~1%.
goto python

:python
echo [%time%] Installing Python modules.
:: WE'VE INSTALLED FFMPEG. INSTALL PYTHON DEPS NOW.
FOR /f %%p in ('where python') do SET PYTHONPATH=%%p
if %errorlevel%==1 goto missingPython

cd %starting%
call %PYTHONPATH% -m pip install -r requirements.txt
echo.


:: THE PROGRAM ENDS HERE!!!!!
echo ////////////////////////////////////
echo //             DONE!              //
echo //  You can now run jumpcutter.   //
echo ////////////////////////////////////
echo.
pause
exit


:missingPython
cd %temp%
::The user is missing the Python executable. Download the latest version.
echo [%time%] (WARNING) You are missing the Python executable!
echo [%time%] Downloading Python 3.7...
::get start time
set "startTime=%time: =0%"

certutil.exe -urlcache -split -f "https://www.python.org/ftp/python/3.7.3/python-3.7.3.exe" python3inst.exe
call python3inst.exe /quiet

:: get end time
set "endTime=%time: =0%"

:: get elapsed time
set "end=!endTime:%time:~8,1%=%%100)*100+1!"  &  set "start=!startTime:%time:~8,1%=%%100)*100+1!"
set /A "elap=((((10!end:%time:~2,1%=%%100)*60+1!%%100)-((((10!start:%time:~2,1%=%%100)*60+1!%%100)"

:: convert it to a more "human readable" format
set /A "cc=elap%%100+100,elap/=100,ss=elap%%60+100,elap/=60,mm=elap%%60+100,hh=elap/60+100"

echo [%time%] Done in %hh:~1%%time:~2,1%%mm:~1%%time:~2,1%%ss:~1%%time:~8,1%%cc:~1%.

goto python
