import React, { useState, useRef, useEffect } from 'react';
import { FolderOpen, FileText, HardDrive, Trash2, Plus, Upload, RefreshCw, File } from 'lucide-react';
import { FileEntry, UsbDeviceLog, DriveInfo } from '../types';
import { formatBytes, formatSpeed } from '../utils/formatters';
import api from '../utils/api';

interface FileManagerProps {
  addLog: (type: UsbDeviceLog['type'], message: string) => void;
}

const FileManager: React.FC<FileManagerProps> = ({ addLog }) => {
  const [currentDrive, setCurrentDrive] = useState<string | null>(null);
  const [drives, setDrives] = useState<DriveInfo[]>([]);
  const [files, setFiles] = useState<FileEntry[]>([]);
  const [isScanning, setIsScanning] = useState(false);
  const [showHidden, setShowHidden] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // 加载可移动驱动器列表
  const loadDrives = async () => {
    try {
      const driveList: any = await api.get('/files/drives');
      const drivesArray: DriveInfo[] = Array.isArray(driveList) ? driveList : [];
      setDrives(drivesArray);
      if (drivesArray.length > 0 && !currentDrive) {
        // 自动选择第一个驱动器
        selectDrive(drivesArray[0].path);
      }
    } catch (error: any) {
      addLog('error', `Failed to load drives: ${error.message || 'Unknown error'}`);
    }
  };

  // 选择驱动器
  const selectDrive = async (drivePath: string) => {
    setCurrentDrive(drivePath);
    addLog('connect', `Mounted drive: ${drivePath}`);
    await scanDirectory(drivePath);
  };

  // 扫描目录
  const scanDirectory = async (drivePath: string) => {
    if (!drivePath) return;
    setIsScanning(true);
    try {
      const fileList: FileEntry[] = await api.get('/files/list', {
        params: {
          path: drivePath,
          show_hidden: showHidden
        }
      });
      setFiles(fileList || []);
    } catch (e: any) {
      addLog('error', `Failed to list files: ${e.message || 'Unknown error'}`);
    } finally {
      setIsScanning(false);
    }
  };

  // 初始化：加载驱动器列表
  useEffect(() => {
    loadDrives();
    // 定期刷新驱动器列表（检测新插入的U盘）
    const interval = setInterval(loadDrives, 3000);
    return () => clearInterval(interval);
  }, []);

  // 当 showHidden 改变时重新扫描
  useEffect(() => {
    if (currentDrive) {
      scanDirectory(currentDrive);
    }
  }, [showHidden]);

  const createTextFile = async () => {
    if (!currentDrive) return;
    const fileName = prompt("Enter file name (e.g., test.txt):", "test.txt");
    if (!fileName) return;

    const content = prompt("Enter text content:", "Hello USB World!");
    if (content === null) return;

    try {
      const startTime = performance.now();
      const filePath = currentDrive.endsWith('\\') || currentDrive.endsWith('/') 
        ? `${currentDrive}${fileName}` 
        : `${currentDrive}/${fileName}`;
      
      const result: any = await api.post('/files/create', null, {
        params: {
          path: filePath,
          content: content
        }
      });
      
      const endTime = performance.now();
      
      if (result && result.status === 'success') {
        const size = result.size || new Blob([content]).size;
        const speed = formatSpeed(size, endTime - startTime);
        addLog('transfer', `Created ${fileName} (${size} bytes) at ${speed}`);
        await scanDirectory(currentDrive);
      } else {
        addLog('error', `Write failed: ${result?.message || 'Unknown error'}`);
      }
    } catch (e: any) {
      addLog('error', `Write failed: ${e.message || 'Unknown error'}`);
    }
  };

  const deleteFile = async (filePath: string) => {
    if (!currentDrive) return;
    const fileName = filePath.split(/[/\\]/).pop() || filePath;
    if (!confirm(`Are you sure you want to delete "${fileName}"?`)) return;

    try {
      const result: any = await api.delete('/files/delete', {
        params: { path: filePath }
      });
      
      if (result && result.status === 'success') {
        addLog('info', `Deleted: ${fileName}`);
        await scanDirectory(currentDrive);
      } else {
        addLog('error', `Delete failed: ${result?.message || 'Unknown error'}`);
      }
    } catch (e: any) {
      addLog('error', `Delete failed: ${e.message || 'Unknown error'}`);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!currentDrive || !e.target.files || e.target.files.length === 0) return;
    
    const fileToUpload = e.target.files[0];
    
    try {
      addLog('info', `Starting upload: ${fileToUpload.name}...`);
      const startTime = performance.now();
      
      // 使用 FormData 上传文件
      const formData = new FormData();
      formData.append('file', fileToUpload);
      
      const result: any = await api.post('/files/upload', formData, {
        params: {
          target_path: currentDrive
        },
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      
      const endTime = performance.now();
      
      if (result && result.status === 'success') {
        const size = result.size || fileToUpload.size;
        const speed = formatSpeed(size, endTime - startTime);
        addLog('transfer', `Uploaded ${fileToUpload.name} (${formatBytes(size)}) at ${speed}`);
        await scanDirectory(currentDrive);
      } else {
        addLog('error', `Upload failed: ${result?.message || 'Unknown error'}`);
      }
    } catch (err: any) {
      addLog('error', `Upload failed: ${err.message || 'Unknown error'}`);
    } finally {
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  return (
    <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden flex flex-col h-full shadow-lg">
      <div className="p-4 bg-slate-900 border-b border-slate-700 flex justify-between items-center">
        <h2 className="text-lg font-semibold flex items-center text-emerald-400">
          <HardDrive className="w-5 h-5 mr-2" />
          File Manager
        </h2>
        
        {currentDrive ? (
          <div className="flex gap-2">
            <button 
              onClick={() => currentDrive && scanDirectory(currentDrive)} 
              className="p-2 hover:bg-slate-700 rounded-lg text-slate-400 hover:text-white transition-colors" 
              title="Refresh"
            >
               <RefreshCw className={`w-4 h-4 ${isScanning ? 'animate-spin' : ''}`} />
            </button>
            <div className="h-8 w-px bg-slate-700 mx-1"></div>
            <label className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-white text-xs font-medium rounded-lg transition-colors flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={showHidden}
                onChange={(e) => {
                  setShowHidden(e.target.checked);
                  if (currentDrive) scanDirectory(currentDrive);
                }}
                className="mr-1"
              />
              Hidden
            </label>
            <button onClick={createTextFile} className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-white text-xs font-medium rounded-lg transition-colors flex items-center gap-2">
              <Plus className="w-3 h-3" />
              New File
            </button>
            <button onClick={() => fileInputRef.current?.click()} className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-medium rounded-lg transition-colors flex items-center gap-2">
              <Upload className="w-3 h-3" />
              Upload
            </button>
            <input 
              type="file" 
              ref={fileInputRef} 
              className="hidden" 
              onChange={handleFileUpload}
            />
          </div>
        ) : (
          <button
            onClick={loadDrives}
            className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium rounded-lg transition-colors flex items-center gap-2"
          >
            <FolderOpen className="w-3 h-3" />
            Load Drives
          </button>
        )}
      </div>

      <div className="flex-1 overflow-y-auto bg-slate-900/30">
        {!currentDrive ? (
          <div className="h-full flex flex-col items-center justify-center text-slate-500">
            <HardDrive className="w-16 h-16 mb-4 opacity-20" />
            <p>No drive mounted.</p>
            <p className="text-sm mt-2 opacity-60">Click "Load Drives" to detect USB drives.</p>
            {drives.length > 0 && (
              <div className="mt-4 space-y-2 max-w-md w-full px-4">
                <p className="text-xs text-slate-400 text-center">Available drives:</p>
                {drives.map((drive, idx) => (
                  <button
                    key={idx}
                    onClick={() => selectDrive(drive.path)}
                    className="block w-full px-4 py-2 bg-slate-800 hover:bg-slate-700 rounded-lg text-sm transition-colors text-left"
                  >
                    <div className="font-medium text-slate-200">{drive.label}</div>
                    <div className="text-xs text-slate-400 mt-1">
                      {drive.path} - {formatBytes(drive.free_space)} free / {formatBytes(drive.total_space)} total
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        ) : (
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-800/50 text-slate-400 uppercase text-[10px] tracking-wider sticky top-0 backdrop-blur-sm">
              <tr>
                <th className="px-4 py-3 font-medium">Name</th>
                <th className="px-4 py-3 font-medium w-24">Type</th>
                <th className="px-4 py-3 font-medium w-32">Size</th>
                <th className="px-4 py-3 font-medium w-16 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/50">
              {files.length === 0 && (
                 <tr>
                    <td colSpan={4} className="px-4 py-8 text-center text-slate-500 italic">
                      Folder is empty
                    </td>
                 </tr>
              )}
              {files.map((file, idx) => (
                <tr key={idx} className="hover:bg-slate-800/50 transition-colors group">
                  <td className="px-4 py-3 font-medium text-slate-200 flex items-center gap-2">
                    {file.is_directory ? <FolderOpen className="w-4 h-4 text-blue-400" /> : <File className="w-4 h-4 text-slate-400" />}
                    {file.isHidden && <span className="text-xs text-slate-500">[H]</span>}
                    {file.name}
                  </td>
                  <td className="px-4 py-3 text-slate-400 text-xs uppercase">{file.is_directory ? 'directory' : 'file'}</td>
                  <td className="px-4 py-3 text-slate-400 font-mono text-xs">
                    {file.size !== undefined ? formatBytes(file.size) : '--'}
                  </td>
                  <td className="px-4 py-3 text-right">
                    {!file.is_directory && (
                      <button 
                        onClick={() => deleteFile(file.path)}
                        className="p-1.5 text-slate-500 hover:text-red-400 hover:bg-red-400/10 rounded transition-colors opacity-0 group-hover:opacity-100"
                        title="Delete"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

export default FileManager;