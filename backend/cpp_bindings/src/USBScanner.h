#ifndef USB_SCANNER_H
#define USB_SCANNER_H

#ifndef UNICODE
#define UNICODE
#endif
#ifndef _UNICODE
#define _UNICODE
#endif

#include <windows.h>
#include <setupapi.h>
#include <usbiodef.h>
#include <string>
#include <vector>

#pragma comment(lib, "setupapi.lib")

// USB设备信息结构
struct USBDeviceInfo {
    std::string devicePath;           // 设备路径
    std::string serialNumber;         // 序列号
    std::string deviceGUID;           // 设备GUID

    std::string description;          // 设备描述
    std::string manufacturer;         // 制造商
    std::string product;              // 产品名称
    std::string deviceClass;          // 设备类
    std::string deviceInstanceId;     // 设备实例ID
    std::string vendorId;             // 厂商ID
    std::string productId;            // 产品ID

    std::string busNumber;            // 总线编号
    std::string portNumber;           // 端口编号
    std::string speed;                // 传输速度
    std::string version;              // 版本
};

// USB扫描器类
class USBScanner {
public:
    USBScanner();
    ~USBScanner();

    // 扫描所有USB设备
    std::vector<USBDeviceInfo> scanUSBDevices();
    
    // 获取当前登录用户名
    static std::string getCurrentUsername();

private:
    // 字符串转换辅助函数
    std::string wstringToString(const std::wstring& wstr);
    std::wstring stringToWstring(const std::string& str);

    // 注册表相关函数
    // 从注册表获取设备属性
    std::string getRegistryProperty(HDEVINFO deviceInfoSet, PSP_DEVINFO_DATA deviceInfoData, DWORD property);

    // 从设备路径提取serialNumber和deviceGUID
    void extractSerialNumberAndDeviceGUIDFromDevicePath(const std::string& devicePath, std::string& serialNumber, std::string& deviceGUID);

    // 从实例ID提取VID和PID
    void extractVidPidFromInstanceId(const std::string& instanceId, std::string& vid, std::string& pid);

    // USB Hub相关函数
    // 通过USB Hub查询设备速度并获取总线/端口信息
    bool getUSBSpeedViaHubWithPortInfo(const std::string& targetVid, const std::string& targetPid, 
                                              std::string& busNumber, std::string& portNumber, std::string& speed, std::string& version);
    
    
    // 获取并匹配设备描述符
    bool getAndMatchDeviceDescriptor(HANDLE hHub, ULONG portNum, const std::string& targetVid, const std::string& targetPid, bool& matched);

    // 从Hub路径和端口号获取总线编号
    std::string getBusNumberFromHubPath(const std::string& hubPath);
    
    // 将USB速度值转换为字符串
    std::string speedValueToString(UCHAR speed);
    // 将USB版本值转换为字符串
    std::string versionValueToString(USHORT version);
    
};

#endif // USB_SCANNER_H

