@echo off
set file=%1
set subdirectory=%2
if "%file%" == "" (goto print_help)
if %file% == --help (goto print_help)

if "%subdirectory%" == "" (
    %USERPROFILE%\SSH\winscp.com /script=sync_script.txt /parameter %file% %file%
) else (
    %USERPROFILE%\SSH\winscp.com /script=sync_script.txt /parameter %file% %subdirectory%
)
echo.
echo.
echo DONE!
echo.
goto end

:print_help
echo Syntax: sync [filename] [optional-subdirectory]

:end
