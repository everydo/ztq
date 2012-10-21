function show_detail(obj){
    pre = obj.firstChild
    content = pre.innerHTML
    openwindow=window.open ("", "详细信息", "height=300, width=600, toolbar=no, menubar=no, scrollbars=yes, resizable=no, location=no, status=no")
    openwindow.document.write('<pre style="font-size:13px;">' + content + '</pre>') 
    openwindow.document.close()
    return null;
}
