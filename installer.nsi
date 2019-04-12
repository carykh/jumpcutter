OutFile "jumpcutter-installer.exe"
InstallDir "$PROGRAMFILES\Jumpcutter"
Section
SetOutPath $INSTDIR
File /r dist\jumpcutter-gui\*.*
WriteUninstaller $INSTDIR\uninstaller.exe
SectionEnd
Section "Desktop Shortcuts" SHORTCUT
     SetOutPath "$INSTDIR"
     CreateShortCut "$Desktop\Jumpcutter.lnk" "$INSTDIR\jumpcutter-gui.exe"
	 CreateShortCut "$Desktop\Uninstall Jumpcutter.lnk" "$INSTDIR\uninstaller.exe"
SectionEnd
Section "Uninstall"
Delete $INSTDIR\uninstaller.exe
rmdir /r $INSTDIR
Delete "$Desktop\Jumpcutter.lnk"
Delete "$Desktop\Uninstall Jumpcutter.lnk"
SectionEnd