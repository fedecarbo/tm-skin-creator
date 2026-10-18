const { contextBridge, ipcRenderer } = require("electron");
contextBridge.exposeInMainWorld("lab", {
  ready: () => ipcRenderer.invoke("lab:ready"),
  url: () => ipcRenderer.invoke("lab:url"),
});
contextBridge.exposeInMainWorld("term", {
  start: (size) => ipcRenderer.send("term:start", size),
  write: (d) => ipcRenderer.send("term:write", d),
  resize: (size) => ipcRenderer.send("term:resize", size),
  onData: (cb) => ipcRenderer.on("term:data", (_e, d) => cb(d)),
  onExit: (cb) => ipcRenderer.on("term:exit", (_e, code) => cb(code)),
});
