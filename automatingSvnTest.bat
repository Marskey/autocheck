cd /d %~dp0

REM svn log -v -r 45130:head "https://10.0.3.3/svn/Star/01. Develop/05. Source/02. Server/Star2" --xml --incremental > test.xml
REM svn export -r 45131 "https://10.0.3.3/svn/Star//01. Develop/05. Source/02. Server/Star2/source/main/GameServer/CommandService.cpp" "./"

REM pvs-studio_cmd.exe --target "E:\IGG\Star2\Source\star2 - 2017.sln" --output "results.plog" --configuration "Release" -f "sor.xml"
PlogConverter.exe E:\MyProjects\AutoCheck\result_45131.plog --renderTypes=FullHtml

pause
