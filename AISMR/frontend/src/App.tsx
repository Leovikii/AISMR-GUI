import { useState, useEffect, useRef } from 'react';
import { SelectFile, SelectFolder, RunScript, ProcessPaths, GetCacheInfo, ClearCache, GetSettings, SetSettings, CheckModels } from "../wailsjs/go/main/App";
import { WindowMinimise, Quit, EventsOn, EventsOff, OnFileDrop } from "../wailsjs/runtime/runtime";
import { THEME, ICONS, Button, CustomSelect, ProgressBar, StatusBadge, ProcessStatus, DownloadModal } from "./components/Shared";

interface FileItem {
  id: string;
  path: string;
  relativePath: string;
  name: string;
  type: string;
  status: ProcessStatus;
}

const SettingsView = ({ onBack, cacheSize, cacheStrategy, onStrategyChange, onClearCache }: any) => {
    return (
        <div className="flex-1 p-10 flex flex-col gap-8 animate-slide-up w-full">
            <div className="flex items-center gap-4 border-b border-white/5 pb-6">
                <div className="p-3 bg-[#E16B8C]/10 rounded-xl text-[#E16B8C]">
                    <ICONS.Settings />
                </div>
                <div>
                    <h2 className="text-2xl font-bold text-white tracking-wide">SETTINGS</h2>
                    <p className="text-gray-500 text-sm mt-1">Configure application preferences and storage.</p>
                </div>
            </div>

            <div className="grid grid-cols-1 gap-8 w-full max-w-none">
                <div className="bg-[#18181b] border border-[#E16B8C]/10 rounded-2xl p-6 space-y-6 hover:border-[#E16B8C]/30 transition-colors duration-300 w-full">
                    <div className="flex items-center gap-3 mb-2">
                        <ICONS.Cache />
                        <h3 className="text-sm font-bold text-[#E16B8C] tracking-widest">STORAGE & CACHE</h3>
                    </div>
                    
                    <ProgressBar value={cacheSize} max={10} label="Current Cache Usage" />
                    
                    <div className="flex items-end justify-between gap-6">
                        <div className="flex-1">
                            <CustomSelect 
                                label="AUTO-CLEANUP STRATEGY"
                                value={cacheStrategy}
                                onChange={onStrategyChange}
                                options={[
                                    { value: "off", label: "Manual Only (Default)" },
                                    { value: "immediate", label: "Clean After Completion" },
                                    { value: "3days", label: "Keep for 3 Days" },
                                    { value: "7days", label: "Keep for 7 Days" },
                                ]}
                            />
                        </div>
                        <Button 
                            onClick={onClearCache}
                            label="CLEAR NOW"
                            icon={<ICONS.Clear />}
                            className="bg-red-500/10 text-red-400 border-red-500/20 hover:bg-red-500/20 hover:border-red-500/40 hover:text-red-300 h-11.5"
                        />
                    </div>
                    <p className="text-[10px] text-gray-600 font-mono pt-2 border-t border-white/5">
                        Cache Path: ./core/cache
                    </p>
                </div>
            </div>
        </div>
    )
}

const DashboardView = ({ 
    files, isRunning, importMenuRef, showImportMenu, setShowImportMenu, 
    handleImportFile, handleImportFolder, runQueue, removeFile, clearList,
    logs, setLogs, logEndRef
}: any) => {
    return (
        <div className="flex-1 flex flex-col overflow-hidden animate-slide-up">
            <div className="h-24 flex items-center px-8 gap-6 bg-[#141417]/60 backdrop-blur-sm relative z-20 shrink-0">
                <div className="relative" ref={importMenuRef}>
                    <Button 
                        onClick={() => setShowImportMenu(!showImportMenu)} 
                        icon={<ICONS.Import />} 
                        label="IMPORT MEDIA" 
                    />
                    {showImportMenu && (
                        <div className="absolute top-full left-0 mt-3 w-56 bg-[#1e1e24] border border-[#E16B8C]/20 rounded-xl shadow-2xl overflow-hidden z-50 animate-scale-in origin-top-left p-1.5">
                            <button onClick={handleImportFile} className="w-full text-left px-4 py-3 text-sm text-gray-300 hover:bg-[#E16B8C]/10 hover:text-[#F596AA] rounded-lg transition-colors flex items-center gap-3 mb-1">
                                <span>📄</span> Import File
                            </button>
                            <button onClick={handleImportFolder} className="w-full text-left px-4 py-3 text-sm text-gray-300 hover:bg-[#E16B8C]/10 hover:text-[#F596AA] rounded-lg transition-colors flex items-center gap-3">
                                <span>📂</span> Import Folder
                            </button>
                        </div>
                    )}
                </div>
                
                <div className="h-8 w-px bg-white/5"></div>
                
                <div className="flex-1 flex flex-col justify-center">
                    <div className="text-[10px] text-gray-500 font-bold tracking-widest mb-1">QUEUE STATUS</div>
                    <div className="text-gray-300 text-sm flex items-center gap-2">
                        <span className={isRunning ? "text-[#E16B8C]" : "text-gray-500"}>●</span>
                        {isRunning ? "PROCESSING ACTIVE" : "READY TO START"}
                    </div>
                </div>

                <Button 
                    primary 
                    onClick={runQueue} 
                    disabled={isRunning || files.length === 0}
                    icon={isRunning ? <span className="animate-spin">🌸</span> : <ICONS.Play />}
                    label={isRunning ? 'PROCESSING...' : 'START QUEUE'}
                    className="px-8 py-3 text-base"
                />
            </div>

            <div className="flex-1 overflow-hidden p-8 pt-2 flex flex-col gap-6">
                <div className="flex-1 bg-[#0c0c0e] rounded-2xl border border-gray-800/60 overflow-hidden flex flex-col shadow-inner relative transition-colors duration-500 hover:border-gray-700/50">
                    <div className="h-12 border-b border-gray-800/60 flex items-center justify-between px-6 bg-[#141417] select-none">
                        <div className="text-[10px] font-bold text-gray-500 uppercase tracking-widest flex items-center gap-2">
                            <span className="text-[#E16B8C]/50">●</span> FILE QUEUE ({files.length})
                        </div>
                        {files.length > 0 && !isRunning && (
                        <button onClick={clearList} className="flex items-center gap-1.5 text-[10px] text-gray-500 hover:text-[#F596AA] px-3 py-1.5 rounded-lg hover:bg-[#E16B8C]/10 transition-colors">
                            <ICONS.Clear /> <span>CLEAR ALL</span>
                        </button>
                        )}
                    </div>

                    <div className="flex-1 overflow-y-auto p-3 space-y-2 custom-scrollbar">
                        {files.length === 0 ? (
                        <div className="h-full flex flex-col items-center justify-center opacity-30 select-none pointer-events-none">
                            <div className="w-24 h-24 text-gray-600 mb-6 scale-125 opacity-20"><ICONS.Import /></div>
                            <p className="text-sm font-mono tracking-[0.2em] text-gray-500">DROP FILES HERE</p>
                        </div>
                        ) : (
                        files.map((file: any) => {
                            const isDone = file.status === 'done';
                            return (
                            <div key={file.id} className={`relative group flex items-center gap-5 px-5 py-4 rounded-xl border transition-all duration-300 ${isDone ? 'opacity-40 grayscale bg-transparent border-transparent' : 'bg-[#18181b] border-[#E16B8C]/10 hover:border-[#E16B8C]/40 shadow-sm'}`}>
                                <div className="p-3 rounded-xl bg-[#E16B8C]/10 text-[#F596AA]">
                                    {file.type === 'video' ? <ICONS.Video /> : <ICONS.Audio />}
                                </div>
                                <div className="flex-1 min-w-0 flex flex-col justify-center">
                                    <div className={`font-medium text-sm truncate ${isDone ? 'text-gray-500' : 'text-gray-200'}`}>{file.name}</div>
                                    <div className="text-[10px] text-gray-600 font-mono truncate opacity-60 mt-1">{file.relativePath}</div>
                                </div>
                                <StatusBadge status={file.status} />
                                {!isRunning && (
                                <button onClick={(e) => removeFile(e, file.id)} className="absolute right-4 p-2 rounded-lg bg-[#18181b] text-gray-500 hover:text-red-400 hover:bg-red-500/10 border border-gray-700 hover:border-red-500/30 opacity-0 group-hover:opacity-100 shadow-xl translate-x-4 group-hover:translate-x-0 transition-all duration-300">
                                    <ICONS.Trash />
                                </button>
                                )}
                            </div>
                            );
                        })
                        )}
                    </div>
                </div>

                <div className="h-40 bg-[#0c0c0e] rounded-2xl border border-gray-800/60 overflow-hidden flex flex-col shadow-inner relative transition-colors duration-500 hover:border-gray-700/50 shrink-0">
                    <div className="h-10 border-b border-gray-800/60 flex items-center justify-between px-6 bg-[#141417] select-none">
                        <div className="text-[10px] font-bold text-gray-500 uppercase tracking-widest flex items-center gap-2">
                            <div className={`w-1.5 h-1.5 rounded-full ${isRunning ? 'bg-[#E16B8C] animate-pulse' : 'bg-gray-700'}`}></div>
                            SYSTEM OUTPUT
                        </div>
                        <button onClick={() => setLogs([])} className="text-[10px] text-gray-600 hover:text-gray-400 px-2 py-1 rounded hover:bg-white/5 transition-colors">
                            CLEAR LOGS
                        </button>
                    </div>
                    <div className="flex-1 overflow-y-auto p-4 space-y-1 text-gray-500 custom-scrollbar font-mono text-[11px]">
                        {logs.map((log: string, i: number) => (
                            <div key={i} className="wrap-break-word border-l-2 border-transparent pl-2 hover:bg-white/5 opacity-80 hover:opacity-100 hover:border-gray-800 transition-colors">
                                {log}
                            </div>
                        ))}
                        <div ref={logEndRef} />
                    </div>
                </div>

            </div>
        </div>
    )
}

function App() {
  const [files, setFiles] = useState<FileItem[]>([]);
  const [logs, setLogs] = useState<string[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [currentIndex, setCurrentIndex] = useState<number | null>(null);
  const [showImportMenu, setShowImportMenu] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  
  const [currentView, setCurrentView] = useState<'dashboard' | 'settings'>('dashboard');
  const [cacheSize, setCacheSize] = useState<number>(0);
  const [cacheStrategy, setCacheStrategy] = useState<string>("off");
  
  const [isDownloading, setIsDownloading] = useState(false);
  const [downloadProgress, setDownloadProgress] = useState(0);
  const [downloadStatus, setDownloadStatus] = useState("");

  const logEndRef = useRef<HTMLDivElement>(null);
  const currentIndexRef = useRef<number | null>(null);
  const importMenuRef = useRef<HTMLDivElement>(null);
  const filesRef = useRef(files);

  useEffect(() => { currentIndexRef.current = currentIndex; }, [currentIndex]);
  useEffect(() => { filesRef.current = files; }, [files]);

  useEffect(() => {
    function handleClickOutside(event: any) {
      if (importMenuRef.current && !importMenuRef.current.contains(event.target)) setShowImportMenu(false);
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  useEffect(() => {
    OnFileDrop((x, y, paths) => { setIsDragging(false); handleNewPaths(paths); }, false);
    const handleDragEnter = () => setIsDragging(true);
    const handleDragLeave = (e: MouseEvent) => {
        if (e.clientX <= 0 || e.clientY <= 0 || e.clientX >= window.innerWidth || e.clientY >= window.innerHeight) setIsDragging(false);
    };
    window.addEventListener('dragenter', handleDragEnter);
    window.addEventListener('dragleave', handleDragLeave);
    return () => {
        window.removeEventListener('dragenter', handleDragEnter);
        window.removeEventListener('dragleave', handleDragLeave);
    };
  }, []);

  useEffect(() => {
    const logHandler = (msg: string) => {
      setLogs((prev) => [...prev, msg]);
      const idx = currentIndexRef.current;
      if (idx === null) return;
      if (msg.includes("RUNNING: _0_prepare.py")) updateStatus(idx, 'preparing');
      else if (msg.includes("RUNNING: _1_whisper.py")) updateStatus(idx, 'whispering');
      else if (msg.includes("RUNNING: _2_correct.py")) updateStatus(idx, 'correcting');
      else if (msg.includes("RUNNING: _3_translate.py")) updateStatus(idx, 'translating');
      else if (msg.includes("RUNNING: _4_output.py")) updateStatus(idx, 'exporting');
    };
    
    // Model Download Events
    const dlProgress = (msg: string) => {
        setIsDownloading(true);
        const p = parseInt(msg.replace("PROGRESS: ", ""));
        if (!isNaN(p)) setDownloadProgress(p);
    };
    const dlStatus = (msg: string) => {
        setIsDownloading(true);
        setDownloadStatus(msg.replace("STATUS: ", ""));
    };
    const dlDone = () => {
        setIsDownloading(false);
        setDownloadStatus("Ready");
    };

    EventsOn("log-message", logHandler);
    EventsOn("model-download-progress", dlProgress);
    EventsOn("model-download-status", dlStatus);
    EventsOn("model-download-done", dlDone);
    
    return () => {
        EventsOff("log-message");
        EventsOff("model-download-progress");
        EventsOff("model-download-status");
        EventsOff("model-download-done");
    };
  }, []);

  useEffect(() => { logEndRef.current?.scrollIntoView({ behavior: "smooth" }); }, [logs]);

  useEffect(() => {
    refreshCacheInfo();
    GetSettings().then(cfg => { if(cfg && cfg.cacheStrategy) setCacheStrategy(cfg.cacheStrategy); });
    
    // Check models on startup
    CheckModels().catch(err => {
        addLog(`[System] Model check failed: ${err}`);
    });
  }, []);

  const refreshCacheInfo = async () => {
    const info = await GetCacheInfo();
    setCacheSize(Number(info.size) / (1024 * 1024 * 1024));
  };

  const handleStrategyChange = (val: string) => { setCacheStrategy(val); SetSettings({ cacheStrategy: val }); };
  const handleClearCache = async () => { await ClearCache(); refreshCacheInfo(); addLog("[System] Cache cleared manually."); };

  const updateStatus = (index: number, status: ProcessStatus) => {
    setFiles(prev => { const newFiles = [...prev]; if (newFiles[index]) newFiles[index].status = status; return newFiles; });
  };

  const handleNewPaths = async (paths: string[]) => {
    if (!paths || paths.length === 0) return;
    if (currentView === 'settings') setCurrentView('dashboard');
    
    const processedItems = await ProcessPaths(paths);
    if (!processedItems || processedItems.length === 0) { addLog("[System] No valid media files found."); return; }
    setFiles(prev => {
        const newItems = processedItems.filter((item: any) => !prev.some(f => f.path === item.path)).map((item: any) => ({ ...item, status: 'pending' }));
        if (newItems.length > 0) { addLog(`[System] Added ${newItems.length} files.`); return [...prev, ...newItems]; }
        return prev;
    });
    setShowImportMenu(false);
  };

  const handleImportFile = async () => { const path = await SelectFile(); if (path) handleNewPaths([path]); };
  const handleImportFolder = async () => { const dir = await SelectFolder(); if (dir) handleNewPaths([dir]); };
  const removeFile = (e: React.MouseEvent, id: string) => { e.stopPropagation(); if (isRunning) return; setFiles(prev => prev.filter(f => f.id !== id)); };
  const clearList = () => { if (isRunning) return; setFiles([]); addLog("[System] List cleared."); };
  const addLog = (msg: string) => { setLogs((prev) => [...prev, msg]); };

  const runQueue = async () => {
    if (isRunning) return;
    setIsRunning(true);
    for (let i = 0; i < files.length; i++) {
        if (files[i].status === 'done') continue;
        setCurrentIndex(i);
        updateStatus(i, 'preparing'); 
        addLog(`=== Processing [${i+1}/${files.length}]: ${files[i].name} ===`);
        try { await RunScript(files[i].path); updateStatus(i, 'done'); } catch (e: any) { updateStatus(i, 'error'); addLog(`=== Error: ${e} ===`); }
    }
    setCurrentIndex(null);
    setIsRunning(false);
    refreshCacheInfo();
    addLog("=== Queue Finished ===");
  };

  return (
    <div className={`h-screen flex flex-col ${THEME.bg} text-gray-200 font-sans overflow-hidden border border-gray-800/50 relative`}>
      
      <DownloadModal isOpen={isDownloading} progress={downloadProgress} status={downloadStatus} />

      {isDragging && (
        <div className="absolute inset-0 z-50 bg-[#121214]/90 backdrop-blur-md flex flex-col items-center justify-center border-4 border-[#E16B8C]/30 border-dashed rounded-lg animate-fade-in pointer-events-none">
            <div className="p-6 rounded-full bg-[#E16B8C]/10 mb-4 animate-bounce shadow-[0_0_30px_rgba(225,107,140,0.3)]"><ICONS.Import /></div>
            <h2 className="text-2xl font-bold text-[#F596AA] tracking-widest drop-shadow-md">RELEASE TO IMPORT</h2>
        </div>
      )}

      <div className="h-10 flex items-center justify-between bg-[#18181b] select-none border-b border-white/5 shrink-0" style={{ widows: '100%', '--wails-draggable': 'drag' } as any}>
        <div className="flex items-center gap-3 px-4 w-full h-full">
          <div className="w-3 h-3 rounded-full bg-[#E16B8C] shadow-[0_0_10px_rgba(225,107,140,0.6)]"></div>
          <span className="text-xs font-bold tracking-[0.2em] text-gray-400">AISMR STUDIO</span>
        </div>
        <div className="flex h-full no-drag items-center" style={{ '--wails-draggable': 'no-drag' } as any}>
          {currentView === 'dashboard' ? (
             <button onClick={() => { refreshCacheInfo(); setCurrentView('settings'); }} className="w-10 h-full flex items-center justify-center hover:bg-white/5 text-gray-500 hover:text-[#E16B8C] transition-colors">
                <ICONS.Settings />
             </button>
          ) : (
             <button onClick={() => setCurrentView('dashboard')} className="w-10 h-full flex items-center justify-center hover:bg-white/5 text-[#E16B8C] bg-[#E16B8C]/5 transition-colors">
                <ICONS.Back />
             </button>
          )}
          <div className="w-px h-3 bg-white/10 mx-1"></div>
          <button onClick={WindowMinimise} className="w-12 h-full flex items-center justify-center hover:bg-white/5 text-gray-500 hover:text-gray-200"><ICONS.Min /></button>
          <button onClick={Quit} className="w-12 h-full flex items-center justify-center hover:bg-[#E16B8C]/80 hover:text-white text-gray-500"><ICONS.Close /></button>
        </div>
      </div>

      {currentView === 'settings' ? (
          <SettingsView 
            onBack={() => setCurrentView('dashboard')}
            cacheSize={cacheSize}
            cacheStrategy={cacheStrategy}
            onStrategyChange={handleStrategyChange}
            onClearCache={handleClearCache}
          />
      ) : (
          <DashboardView 
            files={files}
            isRunning={isRunning}
            importMenuRef={importMenuRef}
            showImportMenu={showImportMenu}
            setShowImportMenu={setShowImportMenu}
            handleImportFile={handleImportFile}
            handleImportFolder={handleImportFolder}
            runQueue={runQueue}
            removeFile={removeFile}
            clearList={clearList}
            logs={logs}
            setLogs={setLogs}
            logEndRef={logEndRef}
          />
      )}

      <style>{`
        .custom-scrollbar::-webkit-scrollbar { width: 5px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: #27272a; border-radius: 3px; }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: #3f3f46; }
      `}</style>
    </div>
  );
}

export default App;