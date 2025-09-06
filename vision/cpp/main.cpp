#include <pybind11/pybind11.h>
#include <pybind11/numpy.h> // 关键！用于处理numpy数组
#include <opencv2/opencv.hpp>

namespace py = pybind11;

// 这个函数将直接被Python调用
py::array_t<unsigned char> process_image(py::array_t<unsigned char> &input_array) {
    // 1. 获取Python传来的numpy数组的信息（只读缓冲区）
    py::buffer_info buf = input_array.request();

    // 2. 从缓冲区提取图像尺寸和通道数
    int height = buf.shape[0];
    int width = buf.shape[1];
    int channels = buf.shape[2];

    // 3. 创建一个指向numpy数组数据的OpenCV Mat（零拷贝）
    cv::Mat image(height, width, CV_8UC3, buf.ptr);

    // 4. 进行你的C++ OpenCV处理
    cv::Mat processed_image;
    cv::cvtColor(image, processed_image, cv::COLOR_BGR2GRAY);
    cv::Canny(processed_image, processed_image, 100, 200);
    // 注意：如果处理改变了图像尺寸或类型，就不能用零拷贝了，需要返回新的数组。

    // 5. 将结果CV::Mat转换回numpy数组并返回
    // pybind11::array_t会自动管理内存
    return py::array_t<unsigned char>(
        {processed_image.rows, processed_image.cols}, // Shape
        {processed_image.step, processed_image.elemSize()}, // Strides
        processed_image.data // Data pointer
    );
}

// 创建Python模块
PYBIND11_MODULE(cpp_processor, m) {
    m.doc() = "PyBind11 example plugin"; // 模块说明
    m.def("process_image", &process_image, "A function that processes an image"); // 暴露函数
}