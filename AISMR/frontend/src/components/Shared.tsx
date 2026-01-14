import { useState, useEffect, useRef, ReactNode } from 'react';

export const THEME = {
  bg: 'bg-[#121214]',
  panel: 'bg-[#18181b]',
  sakura: '#E16B8C',
  sakuraLight: '#F596AA',
};

export const ICONS = {
  Video: () => <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>,
  Audio: () => <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" /></svg>,
  Import: () => <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" /></svg>,
  Play: () => <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" /></svg>,
  Trash: () => <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>,
  Clear: () => <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>,
  Settings: () => <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg>,
  Close: () => <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>,
  Min: () => <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" /></svg>,
  Back: () => <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" /></svg>,
  Cache: () => <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" /></svg>,
  ChevronDown: () => <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>,
  Check: () => <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>,
  Download: () => <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>,
  Missing: () => <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>,
};

export const Button = ({ onClick, disabled, primary, icon, label, className }: any) => (
  <button 
    onClick={onClick}
    disabled={disabled}
    className={`
      px-6 py-2.5 rounded-lg flex items-center gap-2 font-bold tracking-wide text-sm select-none transition-all duration-300 ease-out active:scale-95 justify-center
      ${disabled 
        ? 'bg-[#1e1e24] text-gray-600 border border-gray-800 cursor-not-allowed' 
        : primary 
          ? `bg-[#E16B8C] text-white hover:bg-[#d0597a] shadow-[0_0_20px_rgba(225,107,140,0.4)] hover:shadow-[0_0_25px_rgba(225,107,140,0.6)]` 
          : `bg-[#1e1e24] hover:bg-[#272730] text-[#F596AA] border border-[#E16B8C]/20 hover:border-[#E16B8C]/40 shadow-[0_0_0_1px_rgba(225,107,140,0.05)] hover:shadow-[0_0_15px_rgba(225,107,140,0.2)]`
      }
      ${className}
    `}
  >
    {icon}
    <span>{label}</span>
  </button>
);

export const CustomSelect = ({ value, onChange, options, label }: any) => {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const selectedLabel = options.find((o: any) => o.value === value)?.label || value;

  useEffect(() => {
    function handleClickOutside(event: any) {
      if (containerRef.current && !containerRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <div className="flex flex-col gap-2 w-full" ref={containerRef}>
      {label && <label className="text-[10px] uppercase tracking-wider text-gray-500 font-bold ml-1">{label}</label>}
      <div className="relative">
        <button
          onClick={() => setIsOpen(!isOpen)}
          className={`w-full flex items-center justify-between bg-[#1e1e24] border border-[#E16B8C]/20 text-gray-300 text-sm rounded-lg px-4 py-3 hover:border-[#E16B8C]/50 transition-all duration-300 ${isOpen ? 'border-[#E16B8C]/50 shadow-[0_0_10px_rgba(225,107,140,0.1)]' : ''}`}
        >
          <span>{selectedLabel}</span>
          <div className={`text-[#E16B8C] transition-transform duration-300 ${isOpen ? 'rotate-180' : ''}`}>
            <ICONS.ChevronDown />
          </div>
        </button>

        {isOpen && (
          <div className="absolute top-full left-0 right-0 mt-2 bg-[#1e1e24] border border-[#E16B8C]/20 rounded-lg shadow-xl overflow-hidden z-50 animate-scale-in origin-top">
            {options.map((opt: any) => (
              <button
                key={opt.value}
                onClick={() => { onChange(opt.value); setIsOpen(false); }}
                className={`w-full text-left px-4 py-3 text-sm flex items-center justify-between transition-colors ${value === opt.value ? 'bg-[#E16B8C]/10 text-[#F596AA]' : 'text-gray-300 hover:bg-white/5'}`}
              >
                <span>{opt.label}</span>
                {value === opt.value && <ICONS.Check />}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export const ProgressBar = ({ value, max, label }: any) => {
  const percent = Math.min(100, Math.max(0, (value / max) * 100));
  return (
    <div className="w-full">
        <div className="flex justify-between text-[10px] uppercase tracking-wider font-bold mb-2">
            <span className="text-gray-500">{label}</span>
            <span className="text-[#F596AA] font-mono">{value.toFixed(2)} GB / {max} GB</span>
        </div>
        <div className="h-2 w-full bg-[#1e1e24] rounded-full overflow-hidden border border-white/5">
            <div 
                className="h-full bg-[#E16B8C] shadow-[0_0_15px_rgba(225,107,140,0.5)] transition-all duration-700 ease-out" 
                style={{ width: `${percent}%` }}
            />
        </div>
    </div>
  )
}

export const ModelInitModal = ({ step, missing, progress, status, onDownload, onManualCheck }: any) => {
  if (step === 'idle') return null;

  return (
    <div className="absolute inset-0 z-100 bg-[#121214]/95 backdrop-blur-xl flex flex-col items-center justify-center animate-fade-in">
        <div className="w-full max-w-lg p-10 flex flex-col items-center gap-8 bg-[#18181b]/50 border border-[#E16B8C]/10 rounded-3xl shadow-2xl">
            
            {step === 'check' && (
                <>
                    <div className="p-6 rounded-full bg-[#E16B8C]/10 text-[#E16B8C] animate-pulse">
                        <ICONS.Cache />
                    </div>
                    <h2 className="text-xl font-bold text-white tracking-widest">CHECKING RESOURCES...</h2>
                </>
            )}

            {step === 'prompt' && (
                <>
                    <div className="p-6 rounded-full bg-yellow-500/10 text-yellow-500 shadow-[0_0_40px_rgba(234,179,8,0.2)]">
                        <ICONS.Missing />
                    </div>
                    <div className="text-center space-y-2">
                        <h2 className="text-xl font-bold text-white tracking-widest">MISSING MODELS DETECTED</h2>
                        <p className="text-gray-400 text-sm">The following AI models are required to run the application:</p>
                    </div>
                    <div className="w-full bg-[#1e1e24] rounded-xl p-4 border border-white/5">
                        <ul className="space-y-2">
                            {missing.map((m: string, i: number) => (
                                <li key={i} className="text-xs text-[#F596AA] font-mono flex items-center gap-2">
                                    <span className="text-[#E16B8C]">●</span> {m}
                                </li>
                            ))}
                        </ul>
                    </div>
                    <div className="flex flex-col gap-3 w-full pt-2">
                        <Button 
                            primary 
                            onClick={onDownload} 
                            label="DOWNLOAD AUTOMATICALLY" 
                            icon={<ICONS.Download />}
                            className="w-full py-4"
                        />
                        <button 
                            onClick={onManualCheck}
                            className="text-xs text-gray-500 hover:text-gray-300 transition-colors py-2"
                        >
                            I have placed them manually (Re-scan)
                        </button>
                    </div>
                </>
            )}

            {step === 'downloading' && (
                <>
                    <div className="p-6 rounded-full bg-[#E16B8C]/10 text-[#E16B8C] animate-bounce shadow-[0_0_40px_rgba(225,107,140,0.3)]">
                        <ICONS.Download />
                    </div>
                    <div className="text-center space-y-2">
                        <h2 className="text-2xl font-bold text-white tracking-widest">INSTALLING</h2>
                        <p className="text-[#F596AA] font-mono text-sm">{status || "Initializing..."}</p>
                    </div>
                    <div className="w-full space-y-2">
                        <div className="h-2 w-full bg-[#1e1e24] rounded-full overflow-hidden border border-white/10">
                            <div 
                                className="h-full bg-[#E16B8C] shadow-[0_0_15px_rgba(225,107,140,0.8)] transition-all duration-300 ease-out" 
                                style={{ width: `${progress}%` }}
                            />
                        </div>
                        <div className="flex justify-end text-[10px] font-mono text-gray-500">
                            {progress}% COMPLETE
                        </div>
                    </div>
                </>
            )}
        </div>
    </div>
  );
};

export type ProcessStatus = 'pending' | 'preparing' | 'normalizing' | 'analyzing' | 'whispering' | 'correcting' | 'translating' | 'exporting' | 'done' | 'error';

export const StatusBadge = ({ status }: { status: ProcessStatus }) => {
    const colors: Record<ProcessStatus, string> = {
        'pending': 'text-gray-400 border-gray-800 bg-gray-800/40',
        'preparing': 'text-[#F596AA] border-[#E16B8C]/30 bg-[#E16B8C]/10 shadow-[0_0_10px_rgba(225,107,140,0.2)]',
        'normalizing': 'text-[#F596AA] border-[#E16B8C]/30 bg-[#E16B8C]/10 shadow-[0_0_10px_rgba(225,107,140,0.2)]',
        'analyzing': 'text-[#F596AA] border-[#E16B8C]/30 bg-[#E16B8C]/10 shadow-[0_0_10px_rgba(225,107,140,0.2)]',
        'whispering': 'text-blue-200 border-blue-500/30 bg-blue-500/10 shadow-[0_0_10px_rgba(59,130,246,0.1)]',
        'correcting': 'text-purple-200 border-purple-500/30 bg-purple-500/10 shadow-[0_0_10px_rgba(168,85,247,0.1)]',
        'translating': 'text-indigo-200 border-indigo-500/30 bg-indigo-500/10 shadow-[0_0_10px_rgba(99,102,241,0.1)]',
        'exporting': 'text-cyan-200 border-cyan-500/30 bg-cyan-500/10 shadow-[0_0_10px_rgba(6,182,212,0.1)]',
        'done': 'text-emerald-300 border-emerald-500/20 bg-emerald-500/5',
        'error': 'text-red-400 border-red-500/30 bg-red-500/10',
    };
    const StatusText: Record<ProcessStatus, string> = {
      'pending': 'WAITING', 'preparing': 'PREPARE', 'normalizing': 'NORMALIZING', 'analyzing': 'ANALYZING', 'whispering': 'WHISPER',
      'correcting': 'CORRECT', 'translating': 'TRANSLATE', 'exporting': 'EXPORT',
      'done': 'FINISHED', 'error': 'ERROR'
    };
    return (
        <div className={`px-2 py-1 rounded text-[10px] font-bold tracking-wider border transition-all duration-500 ${colors[status]}`}>
            {StatusText[status]}
        </div>
    );
}