import React, { useEffect, useState, useRef } from 'react';
import { Usb, Cpu, Zap, AlertCircle, ShieldCheck } from 'lucide-react';
import { UsbDeviceLog } from '../types';
import api, { WebSocketClient } from '../utils/api';

interface USBDeviceInfo {
  device_id: string;
  vendor_id: string;
  product_id: string;
  manufacturer: string;
  product: string;
  serial_number: string;
  bus_number: number;
  address: number;
  speed: string;
  usb_version: string;
}

interface UsbMonitorProps {
  addLog: (type: UsbDeviceLog['type'], message: string) => void;
}

const UsbMonitor: React.FC<UsbMonitorProps> = ({ addLog }) => {
  const [devices, setDevices] = useState<USBDeviceInfo[]>([]);
  const [isSupported, setIsSupported] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const wsClientRef = useRef<WebSocketClient | null>(null);

  const refreshDevices = async () => {
    setIsLoading(true);
    try {
      const devicesList: USBDeviceInfo[] = await api.get('/usb/devices');
      setDevices(devicesList || []);
      addLog('info', `Found ${devicesList?.length || 0} USB device(s)`);
    } catch (error: any) {
      console.error('Failed to get USB devices:', error);
      addLog('error', `Failed to get USB devices: ${error.message || 'Unknown error'}`);
      setIsSupported(false);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    // 初始加载设备列表
    refreshDevices();

    // 连接 WebSocket 监控设备变化
    const wsClient = new WebSocketClient('/api/usb/ws/monitor');
    wsClientRef.current = wsClient;

    wsClient.connect()
      .then(() => {
        addLog('info', 'USB device monitoring started.');
        
        // 监听初始设备列表
        wsClient.on('initial', (data: any) => {
          if (data.devices) {
            setDevices(data.devices);
          }
        });

        // 监听设备连接
        wsClient.on('device_connected', (data: any) => {
          if (data.devices) {
            setDevices(data.devices);
            const newDevices = data.devices.filter((d: USBDeviceInfo) => 
              !devices.some(existing => existing.device_id === d.device_id)
            );
            if (newDevices.length > 0) {
              newDevices.forEach((device: USBDeviceInfo) => {
                addLog('connect', `Device connected: ${device.product || device.manufacturer || 'Unknown Device'}`);
              });
            }
          }
        });

        // 监听设备断开
        wsClient.on('device_disconnected', (data: any) => {
          if (data.devices) {
            const oldDevices = devices.filter(d => 
              !data.devices.some((newD: USBDeviceInfo) => newD.device_id === d.device_id)
            );
            oldDevices.forEach(device => {
              addLog('disconnect', `Device disconnected: ${device.product || device.manufacturer || 'Unknown Device'}`);
            });
            setDevices(data.devices);
          }
        });
      })
      .catch((error) => {
        console.error('Failed to connect WebSocket:', error);
        addLog('error', 'Failed to connect to USB monitoring service. Device changes may not be detected in real-time.');
      });

    return () => {
      if (wsClientRef.current) {
        wsClientRef.current.disconnect();
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const requestDevice = async () => {
    try {
      await api.post('/usb/scan');
      await refreshDevices();
      addLog('info', 'USB device scan completed.');
    } catch (error: any) {
      addLog('error', `Scan failed: ${error.message || 'Unknown error'}`);
    }
  };

  return (
    <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden flex flex-col h-full min-h-0 shadow-lg">
      <div className="p-4 bg-slate-900 border-b border-slate-700 flex justify-between items-center">
        <h2 className="text-lg font-semibold flex items-center text-blue-400">
          <Usb className="w-5 h-5 mr-2" />
          USB Bus Monitor
        </h2>
        {isSupported && (
          <button
            onClick={requestDevice}
            className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white text-xs font-medium rounded-lg transition-colors flex items-center gap-2"
          >
            <Zap className="w-3 h-3" />
            Scan / Add Device
          </button>
        )}
      </div>

      <div className="p-4 overflow-y-auto flex-1 space-y-3">
        {!isSupported && (
          <div className="bg-red-900/20 border border-red-500/50 text-red-200 p-4 rounded-lg flex items-start gap-3">
            <AlertCircle className="w-5 h-5 mt-0.5 flex-shrink-0" />
            <div className="text-sm">
              <p className="font-bold">Backend API Not Available</p>
              <p>Please ensure the backend server is running on http://localhost:8000</p>
            </div>
          </div>
        )}

        {isLoading && (
          <div className="text-center text-slate-500 py-8">
            <Cpu className="w-12 h-12 mx-auto mb-3 opacity-20 animate-pulse" />
            <p className="text-sm">Loading USB devices...</p>
          </div>
        )}

        {!isLoading && devices.length === 0 && isSupported && (
          <div className="text-center text-slate-500 py-8">
            <Cpu className="w-12 h-12 mx-auto mb-3 opacity-20" />
            <p className="text-sm">No USB devices detected.</p>
            <p className="text-xs mt-1">Click "Scan" to refresh device list.</p>
          </div>
        )}

        {devices.map((device) => (
          <div key={device.device_id} className="bg-slate-700/50 rounded-lg p-3 border border-slate-600 hover:border-blue-500/50 transition-colors group">
            <div className="flex justify-between items-start mb-2">
              <div>
                <h3 className="font-semibold text-slate-200">{device.product || 'Unknown Device'}</h3>
                <p className="text-xs text-slate-400">{device.manufacturer || 'Unknown Manufacturer'}</p>
              </div>
              <div className="bg-emerald-500/10 text-emerald-400 px-2 py-0.5 rounded text-[10px] border border-emerald-500/20 flex items-center gap-1">
                <ShieldCheck className="w-3 h-3" />
                Connected
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-2 text-xs text-slate-400 mt-3">
              <div className="bg-slate-800 p-1.5 rounded">
                <span className="block text-slate-500 text-[10px] uppercase">Vendor ID</span>
                <span className="font-mono text-slate-300">{device.vendor_id || 'N/A'}</span>
              </div>
              <div className="bg-slate-800 p-1.5 rounded">
                <span className="block text-slate-500 text-[10px] uppercase">Product ID</span>
                <span className="font-mono text-slate-300">{device.product_id || 'N/A'}</span>
              </div>
              <div className="bg-slate-800 p-1.5 rounded">
                <span className="block text-slate-500 text-[10px] uppercase">Bus Number</span>
                <span className="font-mono text-slate-300">{device.bus_number}</span>
              </div>
              <div className="bg-slate-800 p-1.5 rounded">
                <span className="block text-slate-500 text-[10px] uppercase">Speed</span>
                <span className="font-mono text-slate-300">{device.speed || 'N/A'}</span>
              </div>
              <div className="bg-slate-800 p-1.5 rounded">
                <span className="block text-slate-500 text-[10px] uppercase">USB Version</span>
                <span className="font-mono text-slate-300">{device.usb_version || 'N/A'}</span>
              </div>
              <div className="bg-slate-800 p-1.5 rounded">
                <span className="block text-slate-500 text-[10px] uppercase">Serial</span>
                <span className="font-mono text-slate-300 truncate" title={device.serial_number}>{device.serial_number || 'N/A'}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
      
      <div className="bg-slate-900/50 p-2 border-t border-slate-700 text-[10px] text-slate-500 text-center">
        Monitoring USB devices via WebSocket. Found {devices.length} device(s).
      </div>
    </div>
  );
};

export default UsbMonitor;