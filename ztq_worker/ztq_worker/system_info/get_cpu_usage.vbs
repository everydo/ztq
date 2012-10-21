Set objProc = GetObject("winmgmts:\\.\root\cimv2:win32_processor='cpu0'")
Wscript.Echo Round(objProc.LoadPercentage , 2)  ' 得到cpu使用率
