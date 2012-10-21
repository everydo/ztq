set objWMI = GetObject("winmgmts:\\.\root\cimv2")
set colOS = objWMI.InstancesOf("Win32_OperatingSystem")
for each objOS in colOS
strReturn = round(objOS.TotalVisibleMemorySize / 1024) & vbCrLf & round(objOS.FreePhysicalMemory / 1024) & vbCrLf & Round(((objOS.TotalVisibleMemorySize-objOS.FreePhysicalMemory)/objOS.TotalVisibleMemorySize)*100) & "%"
Wscript.Echo strReturn
next
