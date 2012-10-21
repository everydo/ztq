Set objProc = GetObject("winmgmts:\\.\root\cimv2:win32_processor='cpu0'")
Wscript.Echo objProc.Name  ' 得到cpu型号
