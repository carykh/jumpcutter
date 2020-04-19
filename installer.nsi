!include "MUI2.nsh"
;General
Name "Jumpcutter"
OutFile "jumpcutter-installer.exe"
InstallDir "$PROGRAMFILES\Jumpcutter"
RequestExecutionLevel admin

;Interface Settings
!define MUI_ABORTWARNING

;Pages

  !insertmacro MUI_PAGE_WELCOME
  !insertmacro MUI_PAGE_LICENSE "LICENSE"
  !insertmacro MUI_PAGE_COMPONENTS
  !insertmacro MUI_PAGE_DIRECTORY
  !insertmacro MUI_PAGE_INSTFILES
  !insertmacro MUI_PAGE_FINISH

  !insertmacro MUI_UNPAGE_WELCOME
  !insertmacro MUI_UNPAGE_CONFIRM
  !insertmacro MUI_UNPAGE_INSTFILES
  !insertmacro MUI_UNPAGE_FINISH
  

;Languages

  !insertmacro MUI_LANGUAGE "English"


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