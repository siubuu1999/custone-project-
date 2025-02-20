import time
import spidev

# Khởi tạo giao thức SPI
spi = spidev.SpiDev()
spi.open(0, 0)  # Bus 0, Device 0 (GPIO 8 là CS, GPIO 11 là SCK, GPIO 9 là MISO)
spi.max_speed_hz = 50000

# Định nghĩa hàm đọc nhiệt độ từ MAX6675
def read_temp():
    # MAX6675 yêu cầu một lệnh đọc để lấy dữ liệu (2 byte)
    # Đọc 2 byte từ MAX6675
    response = spi.xfer2([0x00, 0x00])  # Lệnh đọc mặc định
    
    # MAX6675 gửi dữ liệu nhiệt độ trong 16 bit, 12 bit đầu tiên là giá trị nhiệt độ
    high_byte = response[0]
    low_byte = response[1]
    
    # Kết hợp 2 byte và dịch để lấy giá trị 12 bit
    raw_temp = ((high_byte << 8) | low_byte) >> 3
    
    # Chuyển đổi giá trị nhiệt độ (độ phân giải 0.25°C cho mỗi bit)
    temperature = raw_temp * 0.25
    
    return temperature

# Đọc và in nhiệt độ liên tục
try:
    while True:
        temperature = read_temp()
        print(f"Temperature: {temperature:.2f} °C")
        time.sleep(1)
except KeyboardInterrupt:
    print("Program exited.")
    spi.close()
