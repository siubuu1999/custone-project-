from flask import Flask, render_template, request, jsonify
import os
import json
import time
from gpiozero import LED
from max6675 import read_max6675
# Cấu hình chân GPIO cho các LED
blue = LED(17)  # LED động cơ
red = LED(27)   # LED thanh nhiệt
yellow = LED(18) # LED thanh nhiệt
# Biến toàn cục kiểm soát chương trình
program_running = True
# Biến toàn cục để lưu trạng thái
# Hàm bắt đầu chương trình
def start_program():
    global program_running
    program_running = True
# Hàm dừng chương trình
def stop_program():
    global program_running
    program_running = False
# Hàm cập nhật nhiệt độ
def update_temperature():
    return read_max6675()
# Hàm chạy logic chính của chương trình
def run_program(temperatures, times):
    global program_running
    num_stages = len(temperatures)  # Tổng số giai đoạn
    stage = 0  # Giai đoạn hiện tại
    start_time = time.monotonic()  # Thời gian bắt đầu giai đoạn đầu tiên
    # Hàm kiểm tra thời gian đã trôi qua và quản lý chuyển giai đoạn
    def check_stage():
        nonlocal stage, start_time
        elapsed_time = time.monotonic() - start_time
        if elapsed_time >= times[stage]:  # Chuyển sang giai đoạn tiếp theo nếu hết thời gian
            stage += 1
            if stage < num_stages:
                start_time = time.monotonic()  # Đặt lại thời gian bắt đầu cho giai đoạn tiếp theo
        return stage
    # Vòng lặp chính
    try:
        print("Chương trình bắt đầu...")
        while program_running:
            current_stage = check_stage()
            # Thoát vòng lặp nếu tất cả các giai đoạn đã hoàn thành
            if current_stage >= num_stages:
                print("Tất cả các giai đoạn đã hoàn thành. Thoát chương trình...")
                blue.off()
                red.off()
                yellow.off()
                break
            # Lấy nhiệt độ hiện tại từ cảm biến MAX6675
            current_temp = read_max6675()
            print(f"Nhiệt độ hiện tại: {current_temp:.2f}C")
            print(f"Giai đoạn hiện tại: {current_stage + 1}")
            # Điều khiển LED đỏ dựa trên nhiệt độ
            if current_temp <= temperatures[current_stage]:
                yellow.on()
                red.on()  # Bật thanh nhiệt 
                blue.on()
                print("Thanh nhiệt Bật.")
            else:
                yellow.off()
                red.off()  # Đảm bảo tắt thanh nhiệt
                blue.on()
                print("Thanh nhiệt tắt.")
            time.sleep(1)  # Chờ 1 giây trước khi lặp lại
    except KeyboardInterrupt:
        print("\nChương trình bị ngắt bởi người dùng.")
    finally:
        # Đảm bảo tất cả các LED tắt trước khi kết thúc
        blue.off()
        red.off()
        yellow.off()
        print("Chương trình đã dừng. Đèn LED đã tắt.")
app = Flask(__name__)
# Tạo thư mục "Recipe" nếu chưa tồn tại
if not os.path.exists("Desktop/Recipe"):
    os.makedirs("Desktop/Recipe")
@app.route("/")
def index():
    return render_template("index.html")
# Endpoint trả về nhiệt độ
@app.route("/temperature", methods=["GET"])
def get_temperature():
    return jsonify({"temperature": update_temperature()})
# Endpoint lưu dữ liệu
@app.route("/save", methods=["POST"])
def save_data():
    try:
        data = request.json
        file_name = data.get("file_name", "recipe.json").strip()
        stages = data.get("stages", [])
        # Kiểm tra nếu tên tệp chứa ký tự '/'
        if '/' in file_name:
            return jsonify({"error": "Tên tệp không được chứa ký tự '/'. Vui lòng nhập lại tên tệp."}), 400

        # Kiểm tra dữ liệu đầu vào
        if not file_name.endswith(".json"):
            file_name += ".json"  # Tự động thêm .json nếu không có phần mở rộng
        if not stages or len(stages) == 0:
            return jsonify({"error": "Không có giai đoạn nào được cung cấp."}), 400
        # Kiểm tra các giai đoạn
        for stage in stages:
            if not isinstance(stage.get("temperature"), (int, float)) or not isinstance(stage.get("time"), int):
                return jsonify({"error": "Dữ liệu giai đoạn không hợp lệ."}), 400
        # Lưu dữ liệu vào tệp JSON
        file_path = os.path.join("Desktop/Recipe", file_name)
        with open(file_path, "w") as file:
            json.dump(stages, file, indent=4)        
        return jsonify({"message": f"Dữ liệu đã được lưu vào {file_path}."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
#hàm endpoint chạy chương trình với dữ liệu
@app.route("/run", methods=["POST"])
def run_program_with_data():
    try:
        data = request.json
        stages = data.get("stages", [])
        # Kiểm tra dữ liệu
        if not stages or len(stages) == 0:
            return jsonify({"error": "Không có dữ liệu để chạy chương trình."}), 400
        temperatures = [stage["temperature"] for stage in stages]
        times = [stage["time"] for stage in stages]
        # Chạy chương trình với dữ liệu đã cung cấp
        start_program()
        run_program(temperatures, times)
        return jsonify({"message": "Chương trình đã chạy với dữ liệu được cung cấp."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
# hàm endpoint tải file
@app.route("/list_recipes", methods=["GET"])
def list_recipes():
    try:
        # Lấy danh sách tất cả các tệp JSON trong thư mục "Recipe"
        recipes = [f.replace(".json", "") for f in os.listdir("Desktop/Recipe") if f.endswith(".json")]
        return jsonify({"recipes": recipes}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
# hàm endpoint xuất dữ liệu từ server
@app.route("/export_data", methods=["POST"])
def export_data():
    try:
        # Lấy dữ liệu từ request (tên file)
        data = request.json
        print("Dữ liệu nhận được từ client:", data)  # Kiểm tra dữ liệu nhận từ client
        file_name = data.get("file_name", "").strip()
        # Kiểm tra nếu tên tệp hợp lệ
        if not file_name.endswith(".json"):
            file_name += ".json"
        file_path = os.path.join("Desktop/Recipe", file_name)
        # Kiểm tra nếu tệp tồn tại
        if not os.path.exists(file_path):
            return jsonify({"error": f"Tệp {file_name} không tồn tại."}), 400 
        # Đọc dữ liệu từ tệp JSON đã lưu
        with open(file_path, "r") as file:
            stages = json.load(file)
        if not stages or len(stages) == 0:
            return jsonify({"error": "Tệp không có giai đoạn nào."}), 400      
        # Trả lại dữ liệu giai đoạn cho client
        return jsonify({"message": "Dữ liệu xuất thành công!","stages": stages})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
# Endpoint để dừng chương trình
@app.route("/stop", methods=["POST"])
def stop_program_endpoint():
    try:
        stop_program()  # Gọi hàm dừng chương trình
        return jsonify({"message": "Chương trình đã dừng thành công."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # Thay đổi host thành '0.0.0.0' để Flask có thể truy cập từ mọi địa chỉ IP
    app.run(host='0.0.0.0', port=5000, debug=False)
