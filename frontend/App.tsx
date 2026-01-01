import React, { useState, useEffect, useRef, useCallback } from 'react';
import { User, Activity, Terminal, Clock, Settings, LayoutDashboard, ChevronDown, ChevronUp } from 'lucide-react';
import UsbMonitor from './components/UsbMonitor';
import FileManager from './components/FileManager';
import { UsbDeviceLog } from './types';
import api from './utils/api';

function App() {
  const [logs, setLogs] = useState<UsbDeviceLog[]>([]);
  const [currentUser, setCurrentUser] = useState<string>('Unknown');
  const [systemUptime, setSystemUptime] = useState(0);
  const [isLogExpanded, setIsLogExpanded] = useState(false);
  const isInitializedRef = useRef(false);

  const addLog = useCallback((type: UsbDeviceLog['type'], message: string) => {
    const newLog: UsbDeviceLog = {
      id: Math.random().toString(36).substr(2, 9),
      timestamp: new Date(),
      type,
      message,
    };
    setLogs((prev) => [newLog, ...prev]);
  }, []);

  useEffect(() => {
    // 防止重复初始化（React StrictMode 在开发模式下会执行两次）
    if (isInitializedRef.current) {
      return;
    }
    isInitializedRef.current = true;

    // 获取系统用户信息
    const fetchUserInfo = async () => {
      try {
        const userInfo: any = await api.get('/system/user');
        if (userInfo && userInfo.username) {
          setCurrentUser(userInfo.username);
        }
      } catch (error) {
        console.error('Failed to fetch user info:', error);
        setCurrentUser('Unknown');
      }
    };

    // 获取系统运行时间
    const fetchUptime = async () => {
      try {
        const uptimeInfo: any = await api.get('/system/uptime');
        if (uptimeInfo && uptimeInfo.uptime_seconds) {
          setSystemUptime(uptimeInfo.uptime_seconds);
        }
      } catch (error) {
        console.error('Failed to fetch uptime:', error);
      }
    };

    fetchUserInfo();
    fetchUptime();

    // 每秒更新运行时间（基于初始值）
    const interval = setInterval(() => {
      setSystemUptime(prev => prev + 1);
    }, 1000);

    // 每30秒同步一次运行时间
    const syncInterval = setInterval(() => {
      fetchUptime();
    }, 30000);

    // Initial Welcome Log
    addLog('info', 'System initialized. Ready to scan USB buses.');

    return () => {
      isInitializedRef.current = false;
      clearInterval(interval);
      clearInterval(syncInterval);
    };
  }, [addLog]);


  const formatUptime = (seconds: number) => {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  return (
    <div className="h-screen bg-slate-950 text-slate-200 flex flex-col font-sans selection:bg-blue-500/30 overflow-hidden">
      {/* Header */}
      <header className="bg-slate-900 border-b border-slate-800 h-16 flex items-center px-6 justify-between sticky top-0 z-50">
        <div className="flex items-center gap-3">
          <div className="bg-blue-600 p-2 rounded-lg shadow-lg shadow-blue-900/20">
            <LayoutDashboard className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="font-bold text-lg leading-tight tracking-tight text-white">USB Master</h1>
            <p className="text-[10px] text-slate-400 uppercase tracking-widest font-semibold">Bus Analysis & Device Control</p>
          </div>
        </div>

        <div className="flex items-center gap-6 text-sm">
          <div className="flex items-center gap-2 text-slate-400 bg-slate-800/50 py-1.5 px-3 rounded-full border border-slate-700/50">
            <Clock className="w-3 h-3" />
            <span className="font-mono text-xs">{formatUptime(systemUptime)}</span>
          </div>
          <div className="flex items-center gap-2 text-slate-300">
            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
            System Active
          </div>
          <div className="flex items-center gap-3 pl-6 border-l border-slate-800">
            <div className="text-right hidden sm:block">
              <p className="text-xs font-semibold text-white">{currentUser}</p>
              <p className="text-[10px] text-slate-500">Administrator</p>
            </div>
            <div className="bg-slate-800 p-2 rounded-full border border-slate-700">
              <User className="w-4 h-4 text-slate-400" />
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 p-6 grid grid-cols-1 lg:grid-cols-12 grid-rows-[1fr_auto] gap-6 max-w-[1600px] mx-auto w-full overflow-y-auto min-h-0">
        {/* Left Column: USB Bus Monitor */}
        <div className="lg:col-span-4 min-h-[600px] lg:h-full lg:min-h-0 flex flex-col">
          <UsbMonitor addLog={addLog} />
        </div>

        {/* Right Column: File Manager */}
        <div className="lg:col-span-8 min-h-[600px] lg:h-full lg:min-h-0 flex flex-col">
          <FileManager addLog={addLog} />
        </div>

        {/* Bottom Row: System Logs */}
        <div className={`lg:col-span-12 bg-slate-900 rounded-xl border border-slate-800 flex flex-col overflow-hidden shadow-inner transition-all duration-300 ${isLogExpanded ? 'h-64' : 'min-h-[48px]'}`}>
          <div 
            onClick={() => setIsLogExpanded(!isLogExpanded)}
            className={`px-4 py-2 bg-slate-950 flex items-center justify-between cursor-pointer hover:bg-slate-900 transition-colors ${isLogExpanded ? 'border-b border-slate-800' : ''}`}
          >
            <div className="flex items-center gap-2">
              <Terminal className="w-4 h-4 text-slate-500" />
              <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-500">System Event Log</h3>
            </div>
            <button
              // onClick={(e) => {
              //   e.stopPropagation();
              //   setIsLogExpanded(!isLogExpanded);
              // }}
              className="p-1.5 hover:bg-slate-800 rounded-lg transition-colors text-slate-400 hover:text-slate-200"
              aria-label={isLogExpanded ? '收起日志' : '展开日志'}
            >
              {isLogExpanded ? (
                <ChevronDown className="w-4 h-4" />
              ) : (
                <ChevronUp className="w-4 h-4" />
              )}
            </button>
          </div>
          {isLogExpanded && (
            <div className="flex-1 overflow-y-auto p-4 font-mono text-xs space-y-1 min-h-[200px]">
              {logs.length === 0 && (
                <span className="text-slate-600 italic">No events recorded...</span>
              )}
              {logs.map((log) => (
                <div key={log.id} className="flex gap-3 animate-fadeIn">
                  <span className="text-slate-600 shrink-0">
                    [{log.timestamp.toLocaleTimeString()}]
                  </span>
                  <span className={`
                    ${log.type === 'error' ? 'text-red-400' : ''}
                    ${log.type === 'connect' ? 'text-emerald-400' : ''}
                    ${log.type === 'disconnect' ? 'text-orange-400' : ''}
                    ${log.type === 'transfer' ? 'text-blue-400' : ''}
                    ${log.type === 'info' ? 'text-slate-300' : ''}
                  `}>
                    {log.type.toUpperCase()}:
                  </span>
                  <span className="text-slate-400">{log.message}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800 py-4 px-6 text-center text-xs text-slate-600">
        <p>USB Master &copy; 2025. Python Backend API with React Frontend.</p>
      </footer>
    </div>
  );
}

export default App;