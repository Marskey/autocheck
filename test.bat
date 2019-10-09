cd %~dp0
cppcheck --file-list=temp\r45263 --language=c++ -q --xml 2>err.xml
