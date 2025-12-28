export interface UsbDeviceLog {
  id: string;
  timestamp: Date;
  type: 'connect' | 'disconnect' | 'info' | 'error' | 'transfer';
  message: string;
}

export interface FileEntry {
  name: string;
  path: string;
  is_directory: boolean;
  size?: number;
  modified_time?: number;
  isHidden?: boolean;
}

export interface DriveInfo {
  path: string;
  label: string;
  total_space: number;
  free_space: number;
  type: string;
}

// Partial typing for WebUSB API
export interface USBDevice {
  usbVersionMajor: number;
  usbVersionMinor: number;
  usbVersionSubminor: number;
  deviceClass: number;
  deviceSubclass: number;
  deviceProtocol: number;
  vendorId: number;
  productId: number;
  deviceVersionMajor: number;
  deviceVersionMinor: number;
  deviceVersionSubminor: number;
  manufacturerName?: string;
  productName?: string;
  serialNumber?: string;
  opened: boolean;
  open(): Promise<void>;
  close(): Promise<void>;
  selectConfiguration(configurationValue: number): Promise<void>;
  claimInterface(interfaceNumber: number): Promise<void>;
}

export interface NavigatorWithUSB extends Navigator {
  usb: {
    getDevices(): Promise<USBDevice[]>;
    requestDevice(options: { filters: any[] }): Promise<USBDevice>;
    addEventListener(type: string, listener: (event: any) => void): void;
    removeEventListener(type: string, listener: (event: any) => void): void;
  };
}