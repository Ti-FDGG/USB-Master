#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/functional.h>
#include "USBScanner.h"

namespace py = pybind11;

// 将USBDeviceInfo结构体绑定到Python
PYBIND11_MODULE(usb_scanner, m) {
    m.doc() = "USB Scanner C++ binding module";

    // 绑定USBDeviceInfo结构体
    py::class_<USBDeviceInfo>(m, "USBDeviceInfo")
        .def(py::init<>())
        .def_readwrite("devicePath", &USBDeviceInfo::devicePath)
        .def_readwrite("serialNumber", &USBDeviceInfo::serialNumber)
        .def_readwrite("deviceGUID", &USBDeviceInfo::deviceGUID)
        .def_readwrite("description", &USBDeviceInfo::description)
        .def_readwrite("manufacturer", &USBDeviceInfo::manufacturer)
        .def_readwrite("product", &USBDeviceInfo::product)
        .def_readwrite("deviceClass", &USBDeviceInfo::deviceClass)
        .def_readwrite("deviceInstanceId", &USBDeviceInfo::deviceInstanceId)
        .def_readwrite("vendorId", &USBDeviceInfo::vendorId)
        .def_readwrite("productId", &USBDeviceInfo::productId)
        .def_readwrite("busNumber", &USBDeviceInfo::busNumber)
        .def_readwrite("portNumber", &USBDeviceInfo::portNumber)
        .def_readwrite("speed", &USBDeviceInfo::speed)
        .def_readwrite("version", &USBDeviceInfo::version)
        .def("__repr__", [](const USBDeviceInfo &info) {
            return "<USBDeviceInfo devicePath='" + info.devicePath + "'>";
        });

    // 绑定USBScanner类
    py::class_<USBScanner>(m, "USBScanner")
        .def(py::init<>())
        .def("scanUSBDevices", &USBScanner::scanUSBDevices,
             "Scan all USB devices and return a list of USBDeviceInfo objects")
        .def_static("getCurrentUsername", &USBScanner::getCurrentUsername,
                    "Get current logged in username");
}

