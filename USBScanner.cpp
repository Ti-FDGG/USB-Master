#ifndef UNICODE
#define UNICODE
#endif
#ifndef _UNICODE
#define _UNICODE
#endif

#include <initguid.h>
#include <windows.h>
#include <setupapi.h>
#include <usbiodef.h>
#include <usbioctl.h>
#include <devguid.h>
#include <regstr.h>
#include <lmcons.h>
#include <iostream>
#include <sstream>
#include <iomanip>
#include <algorithm>
#include <cctype>
#include <cstdio>
#include "USBScanner.h"

// USB速度常量定义（如果未定义）
#ifndef UsbSuperSpeedPlus
#define UsbSuperSpeedPlus 5
#endif

USBScanner::USBScanner() {
}

USBScanner::~USBScanner() {
}

// 获取当前登录用户名
std::string USBScanner::getCurrentUsername() {
    char username[UNLEN + 1];
    DWORD usernameLen = UNLEN + 1;
    
    if (GetUserNameA(username, &usernameLen)) {
        return std::string(username);
    }
    return "Unknown";
}

// 字符串转换：wstring -> string
std::string USBScanner::wstringToString(const std::wstring& wstr) {
    if (wstr.empty()) return std::string();
    
    int size_needed = WideCharToMultiByte(CP_UTF8, 0, &wstr[0], (int)wstr.size(), NULL, 0, NULL, NULL);
    std::string strTo(size_needed, 0);
    WideCharToMultiByte(CP_UTF8, 0, &wstr[0], (int)wstr.size(), &strTo[0], size_needed, NULL, NULL);
    return strTo;
}

// 字符串转换：string -> wstring
std::wstring USBScanner::stringToWstring(const std::string& str) {
    if (str.empty()) return std::wstring();
    
    int size_needed = MultiByteToWideChar(CP_UTF8, 0, &str[0], (int)str.size(), NULL, 0);
    std::wstring wstrTo(size_needed, 0);
    MultiByteToWideChar(CP_UTF8, 0, &str[0], (int)str.size(), &wstrTo[0], size_needed);
    return wstrTo;
}

// 从注册表获取设备属性
std::string USBScanner::getRegistryProperty(HDEVINFO deviceInfoSet, PSP_DEVINFO_DATA deviceInfoData, DWORD property) {
    DWORD dataType;
    DWORD requiredSize = 0;
    
    // 获取所需缓冲区大小
    SetupDiGetDeviceRegistryProperty(deviceInfoSet, deviceInfoData, property, 
                                     &dataType, NULL, 0, &requiredSize);
    
    if (requiredSize == 0) {
        return "";
    }
    
    std::vector<BYTE> buffer(requiredSize);
    if (SetupDiGetDeviceRegistryProperty(deviceInfoSet, deviceInfoData, property,
                                         &dataType, buffer.data(), requiredSize, NULL)) {
        return wstringToString(std::wstring((wchar_t*)buffer.data()));
    }
    
    return "";
}

// 从设备路径提取serialNumber和deviceGUID
void USBScanner::extractSerialNumberAndDeviceGUIDFromDevicePath(const std::string& devicePath, std::string& serialNumber, std::string& deviceGUID) {
    // 1. 查找最后一个 '#' 的位置
    size_t lastHashPos = devicePath.find_last_of('#');
    if (lastHashPos == std::string::npos) return;

    // 2. 提取 deviceGUID (大括号内)
    // 查找最后一个 '#' 之后的 '{' 和 '}'
    size_t openBracePos = devicePath.find('{', lastHashPos);
    size_t closeBracePos = devicePath.find('}', openBracePos);

    if (openBracePos != std::string::npos && closeBracePos != std::string::npos) {
        // 截取大括号中间的内容
        deviceGUID = devicePath.substr(openBracePos + 1, closeBracePos - openBracePos - 1);
    }

    // 3. 查找倒数第二个 '#' 的位置
    size_t secondLastHashPos = devicePath.find_last_of('#', lastHashPos - 1);
    if (secondLastHashPos != std::string::npos) {
        // 提取两个 '#' 之间的部分作为 serialNumber
        serialNumber = devicePath.substr(secondLastHashPos + 1, lastHashPos - secondLastHashPos - 1);
    }
}

// 从实例ID提取VID和PID
void USBScanner::extractVidPidFromInstanceId(const std::string& instanceId, std::string& vid, std::string& pid) {
    vid.clear();
    pid.clear();
    
    size_t vidPos = instanceId.find("VID_");
    if (vidPos != std::string::npos) {
        vid = instanceId.substr(vidPos + 4, 4);
    }
    
    size_t pidPos = instanceId.find("PID_");
    if (pidPos != std::string::npos) {
        pid = instanceId.substr(pidPos + 4, 4);
    }
}

// 通过USB Hub查询设备速度并获取总线/端口信息
bool USBScanner::getUSBSpeedViaHubWithPortInfo(const std::string& targetVid, const std::string& targetPid, 
                                                      std::string& busNumber, std::string& portNumber, std::string& speed, std::string& version) {
    busNumber.clear();
    portNumber.clear();    
    speed = "Unknown";
    version = "Unknown"; 
    // 查找所有USB Hub设备
    HDEVINFO deviceInfoSet = SetupDiGetClassDevs(&GUID_DEVINTERFACE_USB_HUB, NULL, NULL,
                                                 DIGCF_PRESENT | DIGCF_DEVICEINTERFACE);
    
    if (deviceInfoSet == INVALID_HANDLE_VALUE) {
        return false;
    }
    
    SP_DEVINFO_DATA deviceInfoData;
    deviceInfoData.cbSize = sizeof(SP_DEVINFO_DATA);
    
    SP_DEVICE_INTERFACE_DATA interfaceData;
    interfaceData.cbSize = sizeof(SP_DEVICE_INTERFACE_DATA);
    

    // 转换目标VID/PID为大写以便比较
    std::string upperTargetVid = targetVid;
    std::string upperTargetPid = targetPid;
    std::transform(upperTargetVid.begin(), upperTargetVid.end(), upperTargetVid.begin(), ::toupper);
    std::transform(upperTargetPid.begin(), upperTargetPid.end(), upperTargetPid.begin(), ::toupper);
    
    // 遍历所有USB Hub
    int hubIndex = 0;
    for (DWORD i = 0; SetupDiEnumDeviceInfo(deviceInfoSet, i, &deviceInfoData); i++) {
        if (SetupDiEnumDeviceInterfaces(deviceInfoSet, &deviceInfoData,
                                       &GUID_DEVINTERFACE_USB_HUB, 0, &interfaceData)) {
            DWORD requiredSize = 0;
            SetupDiGetDeviceInterfaceDetail(deviceInfoSet, &interfaceData, NULL, 0, &requiredSize, NULL);
            
            if (requiredSize > 0) {
                std::vector<BYTE> buffer(requiredSize);
                PSP_DEVICE_INTERFACE_DETAIL_DATA detailData = 
                    (PSP_DEVICE_INTERFACE_DETAIL_DATA)buffer.data();
                detailData->cbSize = sizeof(SP_DEVICE_INTERFACE_DETAIL_DATA);
                
                if (SetupDiGetDeviceInterfaceDetail(deviceInfoSet, &interfaceData, detailData,
                                                   requiredSize, NULL, NULL)) {
                    std::string hubPath = wstringToString(std::wstring(detailData->DevicePath));
                    hubIndex++;
                    // 获取Hub的总线编号
                    std::string hubBusNumber = getBusNumberFromHubPath(hubPath);
                    
                    // 打开USB Hub设备
                    HANDLE hHub = CreateFileA(hubPath.c_str(), GENERIC_WRITE, 
                                             FILE_SHARE_WRITE, NULL, OPEN_EXISTING, 0, NULL);
                    
                    if (hHub != INVALID_HANDLE_VALUE) {
                        // 查询所有端口的连接信息
                        int connectedPorts = 0;
                        for (ULONG portNum = 1; portNum <= 256; portNum++) {
                            USB_NODE_CONNECTION_INFORMATION_EX connectionInfo;
                            DWORD bytesReturned = 0;
                            
                            ZeroMemory(&connectionInfo, sizeof(USB_NODE_CONNECTION_INFORMATION_EX));
                            
                            // 使用IOCTL_USB_GET_NODE_CONNECTION_INFORMATION_EX查询端口信息
                            BOOL result = DeviceIoControl(
                                hHub,
                                IOCTL_USB_GET_NODE_CONNECTION_INFORMATION_EX,
                                &portNum,
                                sizeof(ULONG),
                                &connectionInfo,
                                sizeof(USB_NODE_CONNECTION_INFORMATION_EX),
                                &bytesReturned,
                                NULL
                            );
                            
                            if (result) {
                                if (connectionInfo.ConnectionStatus == DeviceConnected) {
                                    connectedPorts++;
                                    // 尝试从端口获取设备描述符以匹配VID/PID
                                    bool matched = false;
                                    if (getAndMatchDeviceDescriptor(hHub, portNum, upperTargetVid, upperTargetPid, matched)) {
                                        if (matched) {
                                            // 设置总线编号
                                            busNumber = hubBusNumber;
                                            
                                            // 设置端口编号
                                            std::ostringstream portOss;
                                            portOss << portNum;
                                            portNumber = portOss.str();
                                            
                                            // 设置传输速度和版本
                                            speed = speedValueToString(connectionInfo.Speed);
                                            version = versionValueToString(connectionInfo.DeviceDescriptor.bcdUSB);

                                            CloseHandle(hHub);
                                            SetupDiDestroyDeviceInfoList(deviceInfoSet);
                                            return true;
                                        }
                                    }
                                }
                            }
                        }
                        
                        CloseHandle(hHub);
                    }
                }
            }
        }
    }
    
    SetupDiDestroyDeviceInfoList(deviceInfoSet);
    return false;
}

// 获取并匹配设备描述符
bool USBScanner::getAndMatchDeviceDescriptor(HANDLE hHub, ULONG portNum, const std::string& targetVid, const std::string& targetPid, bool& matched) {
    matched = false;
    
    const DWORD requestSize = sizeof(USB_DESCRIPTOR_REQUEST);
    const DWORD descriptorSize = sizeof(USB_DEVICE_DESCRIPTOR);
    const DWORD totalBufferSize = requestSize + descriptorSize;
    
    std::vector<BYTE> descBuffer(totalBufferSize);
    USB_DESCRIPTOR_REQUEST* descriptorRequest = (USB_DESCRIPTOR_REQUEST*)descBuffer.data();
    USB_DEVICE_DESCRIPTOR* deviceDescriptor = NULL;
    DWORD descBytesReturned = 0;
    
    ZeroMemory(descriptorRequest, requestSize);
    
    descriptorRequest->ConnectionIndex = portNum;
    descriptorRequest->SetupPacket.bmRequest = 0x80;
    descriptorRequest->SetupPacket.bRequest = 0x06;
    descriptorRequest->SetupPacket.wValue = (USB_DEVICE_DESCRIPTOR_TYPE << 8) | 0;
    descriptorRequest->SetupPacket.wIndex = 0;
    descriptorRequest->SetupPacket.wLength = descriptorSize;
    
    BOOL descResult = DeviceIoControl(
        hHub,
        IOCTL_USB_GET_DESCRIPTOR_FROM_NODE_CONNECTION,
        descriptorRequest,
        requestSize,
        descBuffer.data(),
        totalBufferSize,
        &descBytesReturned,
        NULL
    );
    
    if (descResult && descBytesReturned >= requestSize + descriptorSize) {
        deviceDescriptor = (USB_DEVICE_DESCRIPTOR*)(descBuffer.data() + requestSize);
        
        if (deviceDescriptor->bLength >= 18 && 
            deviceDescriptor->bDescriptorType == USB_DEVICE_DESCRIPTOR_TYPE &&
            deviceDescriptor->idVendor != 0) {
            char vidStr[5], pidStr[5];
            sprintf_s(vidStr, sizeof(vidStr), "%04X", deviceDescriptor->idVendor);
            sprintf_s(pidStr, sizeof(pidStr), "%04X", deviceDescriptor->idProduct);
            
            std::string upperTargetVid = targetVid;
            std::string upperTargetPid = targetPid;
            std::transform(upperTargetVid.begin(), upperTargetVid.end(), upperTargetVid.begin(), ::toupper);
            std::transform(upperTargetPid.begin(), upperTargetPid.end(), upperTargetPid.begin(), ::toupper);
            
            bool vidMatch = (vidStr == upperTargetVid);
            bool pidMatch = (pidStr == upperTargetPid);
            
            if (vidMatch && pidMatch) {
                matched = true;
                return true;
            }
        }
    } else {
        DWORD error = GetLastError();
        std::cout << "Error: " << error << std::endl;
    }
    
    return false;
}

// 从Hub路径获取总线编号
std::string USBScanner::getBusNumberFromHubPath(const std::string& hubPath) {
    // Hub路径格式: \\?\usb#root_hub30#4&309c7bfa&0&0#{f18a0e88-c30c-11d0-8815-00a0c906bed8}
    // 或者: \\?\usb#vid_xxxx&pid_xxxx#...
    // 尝试从Hub路径中提取总线信息
    
    std::string upperPath = hubPath;
    std::transform(upperPath.begin(), upperPath.end(), upperPath.begin(), ::toupper);
    
    // 查找root_hub或hub标识
    size_t hubPos = upperPath.find("ROOT_HUB");
    if (hubPos != std::string::npos) {
        // 查找Hub编号后的#号
        size_t hashPos = upperPath.find("#", hubPos);
        if (hashPos != std::string::npos) {
            // 查找下一个&或#，这之间可能是Hub编号
            size_t start = hashPos + 1;
            size_t end = upperPath.find("&", start);
            if (end == std::string::npos) {
                end = upperPath.find("#", start);
            }
            if (end != std::string::npos && end > start) {
                return hubPath.substr(start, end - start);
            }
        }
    }
    
    // 如果找不到，尝试从Hub索引生成（作为备用）
    return "";
}

// 将USB速度值转换为字符串
std::string USBScanner::speedValueToString(UCHAR speed) {
    switch (speed) {
        case UsbLowSpeed:
            return "Low Speed";
        case UsbFullSpeed:
            return "Full Speed";
        case UsbHighSpeed:
            return "High Speed";
        case UsbSuperSpeed:
            return "Super Speed";
        case 5:  // UsbSuperSpeedPlus
            return "Super Speed+";
        default:
            {
                std::ostringstream oss;
                oss << "Unknown Speed" << std::hex << speed;
                return oss.str();
            }
    }
}

// 将USB版本值转换为字符串
std::string USBScanner::versionValueToString(USHORT version) {
    switch (version) {
        case 0x0100:
            return "USB 1.0";
        case 0x0110:
            return "USB 1.1";
        case 0x0200:
            return "USB 2.0";
        case 0x0201:
            return "USB 2.0.1";
        case 0x0300:
            return "USB 3.0";
        default:
            {
                std::ostringstream oss;
                oss << "Unknown Version" << std::hex << version;
                return oss.str();
            }
    }
}

// 扫描所有USB设备
std::vector<USBDeviceInfo> USBScanner::scanUSBDevices() {
    std::vector<USBDeviceInfo> devices;
    
    // 获取所有USB设备接口
    HDEVINFO deviceInfoSet = SetupDiGetClassDevs(&GUID_DEVINTERFACE_USB_DEVICE, NULL, NULL,
                                                  DIGCF_PRESENT | DIGCF_DEVICEINTERFACE);
    
    if (deviceInfoSet == INVALID_HANDLE_VALUE) {
        return devices;
    }
    
    SP_DEVINFO_DATA deviceInfoData;
    deviceInfoData.cbSize = sizeof(SP_DEVINFO_DATA);
    
    SP_DEVICE_INTERFACE_DATA interfaceData;
    interfaceData.cbSize = sizeof(SP_DEVICE_INTERFACE_DATA);
    
    for (DWORD i = 0; SetupDiEnumDeviceInfo(deviceInfoSet, i, &deviceInfoData); i++) {
        // 枚举设备接口
        for (DWORD j = 0; SetupDiEnumDeviceInterfaces(deviceInfoSet, &deviceInfoData,
                                                      &GUID_DEVINTERFACE_USB_DEVICE, j, &interfaceData); j++) {
            USBDeviceInfo info;
            
            // 获取设备接口详细信息
            DWORD requiredSize = 0;
            SetupDiGetDeviceInterfaceDetail(deviceInfoSet, &interfaceData, NULL, 0, &requiredSize, NULL);
            
            if (requiredSize > 0) {
                std::vector<BYTE> buffer(requiredSize);
                PSP_DEVICE_INTERFACE_DETAIL_DATA detailData = 
                    (PSP_DEVICE_INTERFACE_DETAIL_DATA)buffer.data(); //detailData仅包含设备路径和cbSize
                detailData->cbSize = sizeof(SP_DEVICE_INTERFACE_DETAIL_DATA);
                
                if (SetupDiGetDeviceInterfaceDetail(deviceInfoSet, &interfaceData, detailData,
                                                   requiredSize, NULL, NULL)) {
                    // 来源于 SetupDiGetDeviceInterfaceDetail
                    info.devicePath = wstringToString(std::wstring(detailData->DevicePath));
                    // 设备路径：VID、PID、序列号、GUID。VID、PID由设备实例ID中提取
                    extractSerialNumberAndDeviceGUIDFromDevicePath(info.devicePath, info.serialNumber, info.deviceGUID);
                    
                    // getRegistryProperty系列，来源于 SetupDiGetDeviceRegistryProperty
                    // 获取设备详细信息
                    info.description = getRegistryProperty(deviceInfoSet, &deviceInfoData, SPDRP_DEVICEDESC);
                    info.manufacturer = getRegistryProperty(deviceInfoSet, &deviceInfoData, SPDRP_MFG);
                    info.product = getRegistryProperty(deviceInfoSet, &deviceInfoData, SPDRP_FRIENDLYNAME);
                    if (info.product.empty()) {
                        info.product = info.description;
                    }
                    // 获取设备实例ID
                    info.deviceInstanceId = getRegistryProperty(deviceInfoSet, &deviceInfoData, SPDRP_HARDWAREID);
                    // 获取设备类
                    info.deviceClass = getRegistryProperty(deviceInfoSet, &deviceInfoData, SPDRP_CLASS);

                    // 从实例ID中提取VID和PID
                    extractVidPidFromInstanceId(info.deviceInstanceId, info.vendorId, info.productId);
                    
                    // 获取设备速度和总线/端口信息
                    getUSBSpeedViaHubWithPortInfo(info.vendorId, info.productId, info.busNumber, info.portNumber, info.speed, info.version);
                    
                    devices.push_back(info);
                }
            }
        }
    }
    
    SetupDiDestroyDeviceInfoList(deviceInfoSet);
    
    return devices;
}

