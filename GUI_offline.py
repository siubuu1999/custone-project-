import os
from tkinter import Tk, Button, Label, Entry, messagebox, filedialog, Frame
import json
import threading
import time
from gpiozero import LED
from max6675 import read_max6675
import tkinter as tk
# Phông chữ tùy chỉnh
custom_font = ("Arial",40)
mini_font = ("Arial", 23)
# Cấu hình pin GPIO cho các LED (Đã thay đổi pin thành GPIO17 và GPIO27)
blue = LED(17)  # LED động cơ
red = LED(27)   # LED thanh nhiệt
yellow = LED(18) # LED thanh nhiệt
# Biến điều khiển vòng lặp
program_running = True
# ham chay chuong tgrinh
def start_program():
    global program_running
    program_running = True
# Hàm dừng chương trình
def stop_program():
    global program_running
    program_running = False
# Hàm thực thi logic chính của chương trình
def run_program(temperatures, times):
    global program_running
    num_stages = len(temperatures)  # Tổng số giai đoạn
    stage = 0  # Giai đoạn hiện tại
    start_time = time.monotonic()  # Thời gian bắt đầu giai đoạn đầu tiên
    # Hàm kiểm tra thời gian đã trôi qua và quản lý chuyển giai đoạn
    def check_stage():
        nonlocal stage, start_time
        elapsed_time = time.monotonic() - start_time
        if elapsed_time >= times[stage]:  # Chuyển sang giai đoạn tiếp theo nếu thời gian đã vượt qua
            stage += 1
            if stage < num_stages:
                start_time = time.monotonic()  # Đặt lại thời gian bắt đầu cho giai đoạn tiếp theo
        return stage
    # Vòng lặp chính
    try:
        print("Chương trình bắt đầu...")
        while program_running:  # Vòng lặp sẽ dừng khi biến program_running được set thành False
            current_stage = check_stage()
            # Thoát vòng lặp nếu tất cả các giai đoạn đã hoàn thành
            if current_stage >= num_stages:
                print("Tất cả các giai đoạn đã hoàn thành. Thoát chương trình...")
                red.off()
                yellow.off()
                blue.off()
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
                print("Đèn đỏ BẬT: tạo nhiệt.")
            else:
                red.off()  # tắt thanh nhiệt
                yellow.off()
                blue.on()
                print("Đèn đỏ TẮT: ngưng nhiệt")
            time.sleep(1)  # Chờ 1 giây trước khi lặp lại
    except KeyboardInterrupt:
        print("\nChương trình bị ngắt bởi người dùng.")
    finally:
        # Đảm bảo tất cả các LED đều tắt trước khi thoát
        blue.off()
        red.off()
        yellow.off()
        print("Chương trình đã dừng. Thanh nhiệt và động cơ đã tắt.")
def update_temp(temperatures, times):
    global program_running
    root = tk.Toplevel()
    root.title("Chương trình thông báo nhiệt độ")
    temp_label = tk.Label(root, text="Nhiệt độ hiện tại: 0.00°C", font=mini_font)
    temp_label.pack(pady=10)
    stage_label = tk.Label(root, text="Giai đoạn hiện tại: 1", font=mini_font)
    stage_label.pack(pady=10)
    update_label = tk.Label(root, text="", font=mini_font)
    update_label.pack(pady=10)
    countdown_label = tk.Label(root, text="Thời gian còn lại: 0 giây", font=mini_font)
    countdown_label.pack(pady=10)
    tk.Button(root, text="Dừng chương trình", font=mini_font, command=lambda: [root.destroy(), stop_program()]).pack(pady=20)
    num_stages = len(temperatures)
    stage = 0
    start_time = time.monotonic()
    def check_stage():
        nonlocal stage, start_time
        elapsed_time = time.monotonic() - start_time
        if elapsed_time >= times[stage]:
            stage += 1
            if stage < num_stages:
                start_time = time.monotonic()
        return stage
    def get_remaining_time():
        elapsed_time = time.monotonic() - start_time
        remaining_time = max(0, times[stage] - elapsed_time)
        return remaining_time
    try:
        while program_running:
            current_stage = check_stage()
            if current_stage >= num_stages:
                update_label.config(text="Tất cả các giai đoạn đã hoàn thành.")
                root.after(2000, root.destroy) #đóng cửa sổ sau 2 giây
                break
            current_temp = read_max6675()
            temp_label.config(text=f"Nhiệt độ hiện tại: {current_temp:.2f}°C")
            stage_label.config(text=f"Giai đoạn hiện tại: {current_stage + 1}")
            remaining_time = get_remaining_time()
            if remaining_time >= 60:
                minutes = int(remaining_time // 60)
                seconds = int(remaining_time % 60)
                countdown_label.config(text=f"Thời gian còn lại: {minutes} phút {seconds} giây")
            else:
                countdown_label.config(text=f"Thời gian còn lại: {int(remaining_time)} giây")
            if current_temp <= temperatures[current_stage]:
                update_label.config(text="Tạo nhiệt.")
            else:
                update_label.config(text="Ngưng nhiệt.")
            root.update()
            time.sleep(1)
    except KeyboardInterrupt:
        update_label.config(text="Chương trình bị ngắt bởi người dùng.")
# Hàm render GUI trường nhập
def generate_input_fields(num_stages):
    try:
        num_stages = int(num_stages)
        if num_stages <= 0:
            raise ValueError("Số giai đoạn phải lớn hơn 0.")
        # Xóa các trường nhập cũ
        for widget in input_frame.winfo_children():
            widget.destroy()
        # Tạo Canvas và Scrollbar
        canvas = tk.Canvas(input_frame,width=600, height=200)  # Giới hạn chiều cao của canvas
        scrollbar = tk.Scrollbar(input_frame, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        # Thêm Canvas vào layout
        canvas.grid(row=1, column=0, columnspan=2, sticky="nsew")
        # Đặt thanh cuộn ở bên phải và giảm kích thước chiều rộng
        scrollbar.grid(row=1, column=2, sticky="ns", padx=5)
        scrollbar.config(width=15)  # Điều chỉnh độ rộng của thanh cuộn
        # Tạo frame chứa các trường nhập bên trong Canvas
        input_canvas_frame = tk.Frame(canvas)
        canvas.create_window((0, 0), window=input_canvas_frame, anchor="nw")
        # Cập nhật Scrollregion của Canvas
        input_canvas_frame.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))
        # Thêm tiêu đề cho các cột
        Label(input_canvas_frame, text="Giai đoạn", font=mini_font).grid(row=0, column=0, pady=5, padx=5)
        Label(input_canvas_frame, text="Nhiệt độ (°C)", font=mini_font).grid(row=0, column=1, pady=5, padx=5)
        Label(input_canvas_frame, text="Thời gian (phút)", font=mini_font).grid(row=0, column=2, pady=5, padx=5)
        # Tạo các trường nhập mới
        global temp_entries, time_entries
        temp_entries = []
        time_entries = []
        # Tính số giai đoạn có thể hiển thị trong 50px
        max_rows = 50 // 30  # Giả sử mỗi row chiếm khoảng 30px (bao gồm nhãn và trường nhập)
        for i in range(num_stages):
            if i >= max_rows:  # Nếu vượt quá số lượng hàng có thể hiển thị, dùng thanh cuộn
                input_canvas_frame.grid_rowconfigure(i, weight=1)           
            Label(input_canvas_frame, text=f"Giai đoạn {i + 1}", font=mini_font).grid(row=i + 1, column=0, pady=5, padx=5)
            temp_entry = Entry(input_canvas_frame, width=4, font=mini_font)
            temp_entry.grid(row=i + 1, column=1, pady=5, padx=5)
            temp_entries.append(temp_entry)
            time_entry = Entry(input_canvas_frame, width=4, font=mini_font)
            time_entry.grid(row=i + 1, column=2, pady=5, padx=5)
            time_entries.append(time_entry)
        # Cập nhật Scrollregion sau khi thêm các widget
        input_canvas_frame.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))
        # Xử lý phím mũi tên để cuộn
        def scroll_with_arrow(event):
            if event.keysym == 'Up':
                canvas.yview_scroll(-1, "units")  # Cuộn lên
            elif event.keysym == 'Down':
                canvas.yview_scroll(1, "units")  # Cuộn xuống
        canvas.bind_all("<Up>", scroll_with_arrow)
        canvas.bind_all("<Down>", scroll_with_arrow)
    except ValueError as e:
        messagebox.showerror("Lỗi", f"Dữ liệu không hợp lệ: {e}")
# Hàm lưu dữ liệu vào tệp JSON
def save_data():
    try:
        # Kiểm tra nếu số giai đoạn chưa được nhập
        num_stages = stage_entry.get().strip()
        if not num_stages:
            raise ValueError("Vui lòng nhập số giai đoạn trước khi lưu dữ liệu.")

        # Kiểm tra nếu số giai đoạn không hợp lệ (phải là số nguyên dương)
        num_stages = int(num_stages)
        if num_stages <= 0:
            raise ValueError("Số giai đoạn phải lớn hơn 0.")
        # Lấy dữ liệu từ các trường nhập
        data = []
        for i, (temp_entry, time_entry) in enumerate(zip(temp_entries, time_entries)):
            temp = temp_entry.get().strip()
            time = time_entry.get().strip()
           # Kiểm tra nếu có trường nào trống
            if not temp or not time:
                raise ValueError(f"Giai đoạn {i + 1} có trường dữ liệu trống. Vui lòng điền đầy đủ thông tin.")
            # Thêm dữ liệu vào danh sách
            data.append({
                "stage": i + 1,
                "temperature": float(temp),
                "time": int(time) * 60  # chuyển đổi từ phút sang giây
            })
        # Tạo thư mục "Recipe" nếu chưa có
        recipe_folder = "Desktop/Recipe"
        if not os.path.exists(recipe_folder):
            os.makedirs(recipe_folder)
        # Hỏi người dùng nhập tên tệp
        file_name = filedialog.asksaveasfilename(
            initialdir=recipe_folder,
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            title="Lưu dữ liệu dưới tên"
        )
        if not file_name:
            return
        # Lưu dữ liệu vào tệp
        with open(file_name, "w") as file:
            json.dump(data, file, indent=4)
        messagebox.showinfo("Thành công", f"Dữ liệu đã được lưu vào {file_name}.")
    except ValueError as e:
        messagebox.showerror("Lỗi", f"Dữ liệu không hợp lệ: {e}")
    except Exception as e:
        messagebox.showerror("Lỗi", f"Đã xảy ra lỗi: {e}")
# Hàm chạy dữ liệu với input
def run_with_input():
    try:
        # Kiểm tra xem người dùng đã nhập số giai đoạn chưa
        num_stages = stage_entry.get().strip()
        if not num_stages.isdigit() or int(num_stages) <= 0:
            messagebox.showerror("Lỗi", "Vui lòng nhập số giai đoạn hợp lệ trước khi bắt đầu.")
            return  # Dừng lại nếu số giai đoạn chưa hợp lệ hoặc chưa nhập
        # Kiểm tra xem các ô nhập liệu có trống không
        for i, (temp_entry, time_entry) in enumerate(zip(temp_entries, time_entries)):
            temp = temp_entry.get().strip()
            time = time_entry.get().strip()
            if not temp or not time:
                messagebox.showerror("Lỗi", f"Giai đoạn {i + 1} có trường dữ liệu trống. Vui lòng điền đầy đủ.")
                return  # Dừng lại nếu có ô trống
        # Lấy dữ liệu từ các trường nhập nhiệt độ và thời gian
        data = []
        for i, (temp_entry, time_entry) in enumerate(zip(temp_entries, time_entries)):
            temp = temp_entry.get().strip()
            time = time_entry.get().strip()
            data.append({
                "stage": i + 1,
                "temperature": float(temp),
                "time": int(time) * 60  # Convert minutes to seconds for storage
            })
        # Trích xuất danh sách nhiệt độ và thời gian từ dữ liệu
        temperatures = [item["temperature"] for item in data]
        times = [item["time"] for item in data]
        # Chạy chương trình với dữ liệu đã nhập
        start_program()
        threading.Thread(target=lambda: run_program(temperatures, times)).start()
        update_temp(temperatures, times)
    except ValueError as e:
        messagebox.showerror("Lỗi", f"Dữ liệu không hợp lệ: {e}")
    except Exception as e:
        messagebox.showerror("Lỗi", f"Đã xảy ra lỗi: {e}")
def load_and_render():
    try:
        # Chọn tệp JSON
        file_name = filedialog.askopenfilename(
            initialdir="Desktop/Recipe",  # Đặt thư mục ban đầu là "Recipe"
            filetypes=[("JSON files", "*.json")],
            title="Chọn tệp dữ liệu để chạy chương trình"
        )
        if not file_name:
            return
        # Đọc dữ liệu từ tệp
        with open(file_name, "r") as file:
            data = json.load(file)
        # Điền số giai đoạn vào trường nhập
        num_stages = len(data)
        stage_entry.delete(0, "end")  # Xóa dữ liệu cũ
        stage_entry.insert(0, str(num_stages))  # Điền lại số giai đoạn
        # Render lại các trường nhập
        generate_input_fields(num_stages)
        # Điền dữ liệu vào các trường nhập
        for i in range(len(data)):
            if i < len(temp_entries) and i < len(time_entries):
                temp_entries[i].delete(0, "end")  # Xóa dữ liệu cũ
                time_entries[i].delete(0, "end")  # Xóa dữ liệu cũ
                temp_entries[i].insert(0, str(data[i]["temperature"]))  # Điền lại nhiệt độ
                time_entries[i].insert(0, str(data[i]["time"] // 60))  # Điền lại thời gian (chuyển lại giây sang phút)
        messagebox.showinfo("Thông báo", f"Chương trình đã được cập nhật với dữ liệu từ {file_name}.")
    except Exception as e:
        messagebox.showerror("Lỗi", f"Không thể cập nhật chương trình: {e}")
# Tạo cửa sổ giao diện
root = Tk()
root.geometry("620x800")  # Đặt kích thước mặc định của cửa sổ là 320x420
root.title("Nhập nhiệt độ và thời gian cho từng giai đoạn")
# Khung nhập số giai đoạn
Label(root, text="Nhập số giai đoạn:", font=custom_font).pack(pady=5)
stage_entry = Entry(root, width=10, font=custom_font)
stage_entry.pack(pady=5)
Button(root, text="Tạo thông tin chi tiết", width=20, font=custom_font,
       command=lambda: generate_input_fields(stage_entry.get())).pack(pady=10)
# Khung hiển thị các trường nhập nhiệt độ và thời gian
input_frame = Frame(root)
input_frame.pack(pady=10)
# Danh sách lưu các trường nhập nhiệt độ và thời gian
temp_entries = []
time_entries = []
# Các nút chức năng
Button(root, text="Lưu dữ liệu", width=20, font=custom_font, command=save_data).pack(pady=5)
Button(root, text="Xuất dữ liệu đã lưu", width=20, font=custom_font, command=load_and_render).pack(pady=5)
Button(root, text="Bắt đầu", width=20, font=custom_font, command=lambda: run_with_input()).pack(pady=10)
root.mainloop()